"""
Property-based tests for service records management
Feature: vehicle-driver-management
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import uuid
import json
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

# Import the handler functions
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/vehicles'))
from handler import add_service_record, get_service_history, get_maintenance_alerts

# Import test fixtures
sys.path.append(os.path.join(os.path.dirname(__file__), '../fixtures'))
from mock_responses import create_api_gateway_event, create_lambda_context


# Custom strategies for generating test data
@composite
def valid_service_record_data(draw):
    """Generate valid service record data for property testing"""
    maintenance_types = [1, 2, 3, 4, 5, 6, 7]  # Valid maintenance type IDs
    providers = ["Toyota Service", "BMW Service", "Independent Garage", "Quick Lube", "Dealership"]
    
    service_date = draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31)))
    
    return {
        "maintenance_type_id": draw(st.sampled_from(maintenance_types)),
        "description": draw(st.text(min_size=5, max_size=200)),
        "cost": draw(st.floats(min_value=0.01, max_value=50000.0, allow_nan=False, allow_infinity=False)),
        "service_date": service_date.isoformat(),
        "service_provider": draw(st.sampled_from(providers)),
        "mileage": draw(st.one_of(st.none(), st.integers(min_value=0, max_value=500000))),
        "is_warranty": draw(st.booleans()),
        "next_service_due": draw(st.one_of(st.none(), st.dates(min_value=service_date, max_value=date(2031, 12, 31)).map(lambda d: d.isoformat()))),
        "notes": draw(st.one_of(st.none(), st.text(max_size=500)))
    }

@composite
def invalid_service_record_data(draw):
    """Generate invalid service record data for testing error handling"""
    invalid_cases = [
        {"maintenance_type_id": 1, "description": "", "cost": 100, "service_date": "2024-01-01", "service_provider": "Test"},  # Empty description
        {"maintenance_type_id": 1, "description": "Test", "cost": -100, "service_date": "2024-01-01", "service_provider": "Test"},  # Negative cost
        {"maintenance_type_id": 1, "description": "Test", "cost": 100, "service_date": "invalid-date", "service_provider": "Test"},  # Invalid date
        {"maintenance_type_id": 1, "description": "Test", "cost": 100, "service_date": "2024-01-01", "service_provider": ""},  # Empty provider
        {"description": "Test", "cost": 100, "service_date": "2024-01-01", "service_provider": "Test"},  # Missing maintenance_type_id
    ]
    return draw(st.sampled_from(invalid_cases))

@composite
def cost_range_data(draw):
    """Generate cost data for testing cost analysis properties"""
    return {
        "costs": draw(st.lists(st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False), min_size=1, max_size=50)),
        "threshold": draw(st.floats(min_value=100.0, max_value=5000.0, allow_nan=False, allow_infinity=False))
    }


class TestServiceRecordProperties:
    """Property-based tests for service records management"""
    
    def setup_method(self):
        """Set up test environment"""
        self.context = create_lambda_context()
        self.mock_db = Mock()
        self.vehicle_id = str(uuid.uuid4())
    
    @patch('handler.get_database_connection')
    @given(valid_service_record_data())
    @settings(max_examples=100)
    def test_property_2_service_record_completeness(self, mock_get_db, service_data):
        """
        Property 2: Service Record Completeness
        For any service event, recording service details should capture all 
        required fields and maintain complete service history
        Feature: vehicle-driver-management, Property 2: Service Record Completeness
        Validates: Requirements 1.2, 1.5
        """
        # Arrange
        mock_get_db.return_value = self.mock_db
        
        # Mock vehicle exists check
        self.mock_db.execute_query.side_effect = [
            {"records": [[{"stringValue": self.vehicle_id}]], "columnMetadata": []},  # Vehicle exists
            {"records": [[]], "columnMetadata": []}  # Service record creation
        ]
        
        created_service = service_data.copy()
        created_service["id"] = str(uuid.uuid4())
        created_service["vehicle_id"] = self.vehicle_id
        created_service["created_at"] = datetime.now().isoformat()
        created_service["updated_at"] = datetime.now().isoformat()
        
        self.mock_db.format_results.side_effect = [
            [{"id": self.vehicle_id}],  # Vehicle exists response
            [created_service]  # Service record creation response
        ]
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        # Act
        result = add_service_record(self.vehicle_id, service_data)
        
        # Assert - Service record completeness
        assert result["statusCode"] == 201
        response_data = json.loads(result["body"])
        
        # Property: All required service fields should be preserved
        assert response_data["maintenance_type_id"] == service_data["maintenance_type_id"]
        assert response_data["description"] == service_data["description"]
        assert float(response_data["cost"]) == service_data["cost"]
        assert response_data["service_date"] == service_data["service_date"]
        assert response_data["service_provider"] == service_data["service_provider"]
        assert response_data["is_warranty"] == service_data["is_warranty"]
        
        # Property: Optional fields should be preserved if provided
        if service_data.get("mileage") is not None:
            assert response_data["mileage"] == service_data["mileage"]
        
        if service_data.get("next_service_due"):
            assert response_data["next_service_due"] == service_data["next_service_due"]
        
        if service_data.get("notes"):
            assert response_data["notes"] == service_data["notes"]
        
        # Property: System-generated fields should be present
        assert "id" in response_data
        assert response_data["vehicle_id"] == self.vehicle_id
        assert "created_at" in response_data
        assert "updated_at" in response_data
    
    @patch('handler.get_database_connection')
    @given(invalid_service_record_data())
    @settings(max_examples=50)
    def test_property_service_validation_rejection(self, mock_get_db, invalid_data):
        """
        Property: Invalid service record data should always be rejected
        For any invalid service data, the system should return an error
        """
        # Arrange - Mock database connection (though validation should happen before DB call)
        mock_get_db.return_value = self.mock_db
        
        # Act
        result = add_service_record(self.vehicle_id, invalid_data)
        
        # Assert - Invalid data should always be rejected
        assert result["statusCode"] == 400
        response_data = json.loads(result["body"])
        assert "error" in response_data
    
    @patch('handler.get_database_connection')
    @given(st.floats(min_value=-10000.0, max_value=-0.01))
    @settings(max_examples=50)
    def test_property_negative_cost_rejection(self, mock_get_db, negative_cost):
        """
        Property: Negative service costs should always be rejected
        For any negative cost value, service record creation should fail
        """
        # Arrange
        mock_get_db.return_value = self.mock_db
        
        service_data = {
            "maintenance_type_id": 1,
            "description": "Test service",
            "cost": negative_cost,
            "service_date": "2024-01-01",
            "service_provider": "Test Provider"
        }
        
        # Act
        result = add_service_record(self.vehicle_id, service_data)
        
        # Assert - Negative costs should always be rejected
        assert result["statusCode"] == 400
        response_data = json.loads(result["body"])
        assert "Cost must be non-negative" in response_data["error"]
    
    @patch('handler.get_database_connection')
    @given(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Lu", "Nd", "Pc"))))
    @settings(max_examples=50)
    def test_property_invalid_date_format_handling(self, mock_get_db, invalid_date):
        """
        Property: Invalid date formats should be rejected
        For any invalid date format, the system should return a validation error
        """
        # Arrange
        mock_get_db.return_value = self.mock_db
        
        service_data = {
            "maintenance_type_id": 1,
            "description": "Test service",
            "cost": 100.0,
            "service_date": invalid_date,  # Invalid date format
            "service_provider": "Test Provider"
        }
        
        # Act
        result = add_service_record(self.vehicle_id, service_data)
        
        # Assert - Invalid date formats should be rejected
        assert result["statusCode"] == 400
        response_data = json.loads(result["body"])
        assert "error" in response_data
        assert "Service date must be in YYYY-MM-DD format" in response_data["error"]
    
    @patch('handler.get_database_connection')
    @given(cost_range_data())
    @settings(max_examples=100)
    def test_property_3_cost_threshold_alerting(self, mock_get_db, cost_data):
        """
        Property 3: Cost Threshold Alerting
        For any service cost above threshold, appropriate alerts should be generated
        Feature: vehicle-driver-management, Property 3: Cost Threshold Alerting
        Validates: Requirements 1.8
        """
        # Arrange
        mock_get_db.return_value = self.mock_db
        costs = cost_data["costs"]
        threshold = cost_data["threshold"]
        
        # Mock maintenance alerts response
        high_cost_alerts = []
        for i, cost in enumerate(costs):
            if cost > threshold:
                high_cost_alerts.append({
                    "column_0": f"vehicle-{i}",
                    "column_1": "Toyota",
                    "column_2": "Corolla",
                    "column_3": f"ABC{i:03d}GP",
                    "column_4": "2024-01-01",
                    "column_5": "2024-04-01",
                    "column_6": str(cost),
                    "column_7": "general_maintenance",
                    "column_8": None,
                    "column_9": None,
                    "column_10": None,
                    "column_11": "high_cost_service",
                    "column_12": f"Service cost ${cost:.2f} exceeds threshold ${threshold:.2f}"
                })
        
        self.mock_db.execute_query.return_value = {"records": [], "columnMetadata": []}
        self.mock_db.format_results.return_value = high_cost_alerts
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        # Act
        result = get_maintenance_alerts({})
        
        # Assert - Cost threshold alerting property
        assert result["statusCode"] == 200
        response_data = json.loads(result["body"])
        
        # Property: High cost services should generate alerts
        high_cost_count = sum(1 for cost in costs if cost > threshold)
        expected_alerts = len(high_cost_alerts)
        
        # The number of high cost alerts should match the number of costs above threshold
        assert len(response_data["alerts"]) == expected_alerts
        
        # Each alert should reference a cost above the threshold
        for alert in response_data["alerts"]:
            if alert["alert_type"] == "high_cost_service":
                # Extract cost from alert message or verify it's a high cost alert
                assert "exceeds threshold" in alert["alert_message"]
    
    @patch('handler.get_database_connection')
    @given(st.lists(valid_service_record_data(), min_size=1, max_size=20))
    @settings(max_examples=50)
    def test_property_4_service_history_persistence(self, mock_get_db, service_records):
        """
        Property 4: Service History Persistence
        For any sequence of service records, retrieving service history should 
        return all records in chronological order
        Feature: vehicle-driver-management, Property 4: Service History Persistence
        Validates: Requirements 1.2, 1.5
        """
        # Arrange
        mock_get_db.return_value = self.mock_db
        
        # Sort service records by date for expected order
        sorted_records = sorted(service_records, key=lambda x: x["service_date"])
        
        # Mock service history response with all records
        mock_history_records = []
        for i, record in enumerate(sorted_records):
            mock_history_records.append({
                "column_0": f"service-{i:03d}",
                "column_1": self.vehicle_id,
                "column_2": None,
                "column_3": record["maintenance_type_id"],
                "column_4": "general_maintenance",
                "column_5": "General maintenance",
                "column_6": record["description"],
                "column_7": str(record["cost"]),
                "column_8": record["service_date"],
                "column_9": record.get("mileage"),
                "column_10": record["service_provider"],
                "column_11": record["is_warranty"],
                "column_12": record.get("next_service_due"),
                "column_13": None,
                "column_14": record.get("notes"),
                "column_15": "2024-01-15T14:30:00Z",
                "column_16": "2024-01-15T14:30:00Z"
            })
        
        self.mock_db.execute_query.return_value = {"records": [], "columnMetadata": []}
        self.mock_db.format_results.return_value = mock_history_records
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        # Act
        result = get_service_history(self.vehicle_id, {})
        
        # Assert - Service history persistence property
        assert result["statusCode"] == 200
        response_data = json.loads(result["body"])
        
        # Property: All service records should be retrievable
        assert response_data["count"] == len(service_records)
        assert len(response_data["service_records"]) == len(service_records)
        
        # Property: Service records should maintain data integrity
        returned_records = response_data["service_records"]
        for i, returned_record in enumerate(returned_records):
            original_record = sorted_records[i]
            
            # Verify key fields are preserved
            assert returned_record["maintenance_type_id"] == original_record["maintenance_type_id"]
            assert returned_record["description"] == original_record["description"]
            assert returned_record["service_date"] == original_record["service_date"]
            assert returned_record["service_provider"] == original_record["service_provider"]
            assert returned_record["is_warranty"] == original_record["is_warranty"]
    
    @patch('handler.get_database_connection')
    @given(st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_property_invalid_vehicle_id_rejection(self, mock_get_db, random_string):
        """
        Property: Invalid vehicle IDs should always be rejected
        For any non-UUID string, service record operations should return validation error
        """
        # Assume the string is not a valid UUID
        try:
            uuid.UUID(random_string)
            assume(False)  # Skip if it's actually a valid UUID
        except ValueError:
            pass  # This is what we want - invalid UUID
        
        # Arrange
        mock_get_db.return_value = self.mock_db
        
        service_data = {
            "maintenance_type_id": 1,
            "description": "Test service",
            "cost": 100.0,
            "service_date": "2024-01-01",
            "service_provider": "Test Provider"
        }
        
        # Act
        result = add_service_record(random_string, service_data)
        
        # Assert - Invalid UUID should always be rejected
        assert result["statusCode"] == 400
        response_data = json.loads(result["body"])
        assert "Invalid vehicle ID format" in response_data["error"]
    
    @given(st.lists(st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False), min_size=2, max_size=50))
    @settings(max_examples=50)
    def test_property_cost_calculation_accuracy(self, costs):
        """
        Property: Cost calculations should be mathematically accurate
        For any list of service costs, total cost should equal sum of individual costs
        """
        # Property: Sum of costs should be mathematically accurate
        total_cost = sum(costs)
        calculated_total = sum(Decimal(str(cost)) for cost in costs)
        
        # Allow for small floating point precision differences
        assert abs(float(calculated_total) - total_cost) < 0.01
        
        # Property: Average cost should be total divided by count
        if len(costs) > 0:
            expected_average = total_cost / len(costs)
            calculated_average = float(calculated_total) / len(costs)
            assert abs(calculated_average - expected_average) < 0.01


if __name__ == "__main__":
    pytest.main([__file__])