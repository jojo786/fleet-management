"""
Property-based tests for vehicle management
Feature: vehicle-driver-management
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import uuid
import json
from datetime import datetime, date
from unittest.mock import Mock, patch

# Import the handler functions
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/vehicles'))
from handler import create_vehicle, get_vehicle, add_service_record

# Import test fixtures
sys.path.append(os.path.join(os.path.dirname(__file__), '../fixtures'))
from mock_responses import create_api_gateway_event, create_lambda_context


# Custom strategies for generating test data
@composite
def valid_vehicle_data(draw):
    """Generate valid vehicle data for property testing"""
    makes = ["Toyota", "BMW", "Mercedes", "Audi", "Ford", "Volkswagen", "Nissan", "Honda"]
    models = ["Sedan", "SUV", "Hatchback", "Coupe", "Wagon", "Convertible"]
    
    return {
        "make": draw(st.sampled_from(makes)),
        "model": draw(st.sampled_from(models)),
        "year": draw(st.integers(min_value=1900, max_value=2030)),
        "registration": draw(st.text(min_size=6, max_size=10, alphabet=st.characters(whitelist_categories=("Lu", "Nd")))),
        "vin": draw(st.one_of(st.none(), st.text(min_size=17, max_size=17, alphabet=st.characters(whitelist_categories=("Lu", "Nd"))))),
        "status": draw(st.sampled_from(["active", "in_service", "out_of_order", "retired"]))
    }

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
def invalid_vehicle_data(draw):
    """Generate invalid vehicle data for testing error handling"""
    invalid_cases = [
        {"make": "", "model": "Test", "year": 2020, "registration": "ABC123"},  # Empty make
        {"make": "Toyota", "model": "", "year": 2020, "registration": "ABC123"},  # Empty model
        {"make": "Toyota", "model": "Test", "year": 1800, "registration": "ABC123"},  # Invalid year (too old)
        {"make": "Toyota", "model": "Test", "year": 2150, "registration": "ABC123"},  # Invalid year (too new)
        {"make": "Toyota", "model": "Test", "year": 2020, "registration": ""},  # Empty registration
    ]
    return draw(st.sampled_from(invalid_cases))


class TestVehicleProperties:
    """Property-based tests for vehicle management"""
    
    def setup_method(self):
        """Set up test environment"""
        self.context = create_lambda_context()
        self.mock_db = Mock()
    
    @patch('handler.get_database_connection')
    @given(valid_vehicle_data())
    @settings(max_examples=100)
    def test_property_1_vehicle_data_integrity(self, mock_get_db, vehicle_data):
        """
        Property 1: Vehicle Data Integrity
        For any vehicle record with complete details, storing and retrieving 
        should preserve all field values exactly
        Feature: vehicle-driver-management, Property 1: Vehicle Data Integrity
        Validates: Requirements 1.1
        """
        # Arrange
        mock_get_db.return_value = self.mock_db
        
        # Mock successful creation response
        created_vehicle = vehicle_data.copy()
        created_vehicle["id"] = str(uuid.uuid4())
        created_vehicle["created_at"] = datetime.now().isoformat()
        created_vehicle["updated_at"] = datetime.now().isoformat()
        
        self.mock_db.execute_query.return_value = {"records": [[]], "columnMetadata": []}
        self.mock_db.format_results.return_value = [created_vehicle]
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        # Act - Create vehicle
        result = create_vehicle(vehicle_data)
        
        # Assert - All original data should be preserved
        assert result["statusCode"] == 201
        response_data = json.loads(result["body"])
        
        # Property: All input fields should be preserved exactly
        assert response_data["make"] == vehicle_data["make"]
        assert response_data["model"] == vehicle_data["model"]
        assert response_data["year"] == vehicle_data["year"]
        assert response_data["registration"] == vehicle_data["registration"]
        
        if vehicle_data.get("vin"):
            assert response_data["vin"] == vehicle_data["vin"]
        
        # Property: Generated fields should be present
        assert "id" in response_data
        assert "created_at" in response_data
        assert "updated_at" in response_data
    
    @patch('handler.get_database_connection')
    @given(invalid_vehicle_data())
    @settings(max_examples=50)
    def test_property_vehicle_validation_rejection(self, mock_get_db, invalid_data):
        """
        Property: Invalid vehicle data should always be rejected
        For any invalid vehicle data, the system should return an error
        """
        # Arrange - Mock database connection (though validation should happen before DB call)
        mock_get_db.return_value = self.mock_db
        
        # Act
        result = create_vehicle(invalid_data)
        
        # Assert - Invalid data should always be rejected
        assert result["statusCode"] == 400
        response_data = json.loads(result["body"])
        assert "error" in response_data
    
    @patch('handler.get_database_connection')
    @given(st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_property_uuid_validation(self, mock_get_db, random_string):
        """
        Property: Invalid UUIDs should always be rejected
        For any non-UUID string, vehicle retrieval should return validation error
        """
        # Assume the string is not a valid UUID
        try:
            uuid.UUID(random_string)
            assume(False)  # Skip if it's actually a valid UUID
        except ValueError:
            pass  # This is what we want - invalid UUID
        
        # Act
        result = get_vehicle(random_string)
        
        # Assert - Invalid UUID should always be rejected
        assert result["statusCode"] == 400
        response_data = json.loads(result["body"])
        assert "Invalid vehicle ID format" in response_data["error"]
    
    @patch('handler.get_database_connection')
    @given(valid_vehicle_data(), valid_service_record_data())
    @settings(max_examples=100)
    def test_property_2_service_record_completeness(self, mock_get_db, vehicle_data, service_data):
        """
        Property 2: Service Record Completeness
        For any service event, recording service details should capture all 
        required fields and maintain complete service history
        Feature: vehicle-driver-management, Property 2: Service Record Completeness
        Validates: Requirements 1.2, 1.5
        """
        # Arrange
        vehicle_id = str(uuid.uuid4())
        mock_get_db.return_value = self.mock_db
        
        # Mock vehicle exists check
        self.mock_db.execute_query.side_effect = [
            {"records": [[{"stringValue": vehicle_id}]], "columnMetadata": []},  # Vehicle exists
            {"records": [[]], "columnMetadata": []}  # Service record creation
        ]
        
        created_service = service_data.copy()
        created_service["id"] = str(uuid.uuid4())
        created_service["vehicle_id"] = vehicle_id
        created_service["created_at"] = datetime.now().isoformat()
        created_service["updated_at"] = datetime.now().isoformat()
        
        self.mock_db.format_results.side_effect = [
            [{"id": vehicle_id}],  # Vehicle exists response
            [created_service]  # Service record creation response
        ]
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        # Act
        result = add_service_record(vehicle_id, service_data)
        
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
        assert response_data["vehicle_id"] == vehicle_id
        assert "created_at" in response_data
        assert "updated_at" in response_data
    
    @given(st.floats(min_value=-1000.0, max_value=-0.01))
    @settings(max_examples=50)
    def test_property_negative_cost_rejection(self, negative_cost):
        """
        Property: Negative service costs should always be rejected
        For any negative cost value, service record creation should fail
        """
        # Arrange
        vehicle_id = str(uuid.uuid4())
        service_data = {
            "maintenance_type_id": 1,
            "description": "Test service",
            "cost": negative_cost,
            "service_date": "2024-01-01",
            "service_provider": "Test Provider"
        }
        
        # Act
        result = add_service_record(vehicle_id, service_data)
        
        # Assert - Negative costs should always be rejected
        assert result["statusCode"] == 400
        response_data = json.loads(result["body"])
        assert "Cost must be non-negative" in response_data["error"]
    
    @patch('handler.get_database_connection')
    @given(st.integers(min_value=2101, max_value=3000))
    @settings(max_examples=50)
    def test_property_future_year_rejection(self, mock_get_db, future_year):
        """
        Property: Future years beyond reasonable range should be rejected
        For any year beyond 2100, vehicle creation should fail
        """
        # Arrange
        mock_get_db.return_value = self.mock_db
        
        vehicle_data = {
            "make": "Toyota",
            "model": "Test",
            "year": future_year,
            "registration": "TEST123"
        }
        
        # Act
        result = create_vehicle(vehicle_data)
        
        # Assert - Future years should be rejected
        assert result["statusCode"] == 400
        response_data = json.loads(result["body"])
        assert "Year must be between 1900 and 2100" in response_data["error"]


if __name__ == "__main__":
    pytest.main([__file__])