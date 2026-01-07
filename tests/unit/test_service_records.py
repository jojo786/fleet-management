"""
Unit tests for service records functionality
"""
import pytest
import json
import uuid
from unittest.mock import Mock, patch
from datetime import datetime, date

# Import the handler functions
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/vehicles'))
from handler import add_service_record, get_service_history, get_maintenance_alerts

# Import test fixtures
sys.path.append(os.path.join(os.path.dirname(__file__), '../fixtures'))
from sample_vehicles import SAMPLE_SERVICE_RECORDS, MAINTENANCE_TYPES
from mock_responses import (
    create_api_gateway_event, 
    create_lambda_context, 
    MOCK_SERVICE_RECORD_RESPONSE
)


class TestServiceRecords:
    """Test suite for service records functionality"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        self.context = create_lambda_context()
        self.mock_db = Mock()
        self.vehicle_id = "550e8400-e29b-41d4-a716-446655440000"
        
    @patch('handler.get_database_connection')
    def test_add_service_record_success(self, mock_get_db):
        """Test successful service record creation"""
        # Arrange
        mock_get_db.return_value = self.mock_db
        
        # Mock vehicle exists check and service record creation
        self.mock_db.execute_query.side_effect = [
            {"records": [[{"stringValue": self.vehicle_id}]], "columnMetadata": []},  # Vehicle exists
            MOCK_SERVICE_RECORD_RESPONSE  # Service record creation
        ]
        self.mock_db.format_results.side_effect = [
            [{"id": self.vehicle_id}],  # Vehicle exists response
            [SAMPLE_SERVICE_RECORDS[0]]  # Service record creation response
        ]
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        service_data = {
            "maintenance_type_id": 1,
            "description": "Regular oil and filter change",
            "cost": 350.00,
            "service_date": "2024-01-15",
            "service_provider": "Toyota Service Center",
            "mileage": 15000,
            "is_warranty": False,
            "next_service_due": "2024-04-15",
            "notes": "Used synthetic oil"
        }
        
        # Act
        response = add_service_record(self.vehicle_id, service_data)
        
        # Assert
        assert response["statusCode"] == 201
        response_body = json.loads(response["body"])
        assert response_body["description"] == "Regular oil and filter change"
        assert float(response_body["cost"]) == 350.00
        assert response_body["service_provider"] == "Toyota Service Center"
        
        # Verify database interactions
        assert self.mock_db.execute_query.call_count == 2  # Vehicle check + insert
        
    @patch('handler.get_database_connection')
    def test_add_service_record_vehicle_not_found(self, mock_get_db):
        """Test service record creation when vehicle doesn't exist"""
        # Arrange
        mock_get_db.return_value = self.mock_db
        self.mock_db.execute_query.return_value = {"records": [], "columnMetadata": []}
        self.mock_db.format_results.return_value = []
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        service_data = {
            "maintenance_type_id": 1,
            "description": "Test service",
            "cost": 100.00,
            "service_date": "2024-01-15",
            "service_provider": "Test Provider"
        }
        
        # Act
        response = add_service_record(self.vehicle_id, service_data)
        
        # Assert
        assert response["statusCode"] == 404
        response_body = json.loads(response["body"])
        assert "Vehicle not found" in response_body["error"]
        
    @patch('handler.get_database_connection')
    def test_add_service_record_missing_required_fields(self, mock_get_db):
        """Test service record creation with missing required fields"""
        # Arrange
        service_data = {
            "maintenance_type_id": 1,
            # Missing description, cost, service_date, service_provider
        }
        
        # Act
        response = add_service_record(self.vehicle_id, service_data)
        
        # Assert
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "Missing required field" in response_body["error"]
        
    @patch('handler.get_database_connection')
    def test_add_service_record_invalid_cost(self, mock_get_db):
        """Test service record creation with invalid cost"""
        # Arrange
        service_data = {
            "maintenance_type_id": 1,
            "description": "Test service",
            "cost": -100.00,  # Negative cost
            "service_date": "2024-01-15",
            "service_provider": "Test Provider"
        }
        
        # Act
        response = add_service_record(self.vehicle_id, service_data)
        
        # Assert
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "Cost must be non-negative" in response_body["error"]
        
    @patch('handler.get_database_connection')
    def test_add_service_record_invalid_date_format(self, mock_get_db):
        """Test service record creation with invalid date format"""
        # Arrange
        service_data = {
            "maintenance_type_id": 1,
            "description": "Test service",
            "cost": 100.00,
            "service_date": "invalid-date",  # Invalid date format
            "service_provider": "Test Provider"
        }
        
        # Act
        response = add_service_record(self.vehicle_id, service_data)
        
        # Assert
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "Service date must be in YYYY-MM-DD format" in response_body["error"]
        
    @patch('handler.get_database_connection')
    def test_get_service_history_success(self, mock_get_db):
        """Test successful service history retrieval"""
        # Arrange
        mock_get_db.return_value = self.mock_db
        self.mock_db.execute_query.return_value = MOCK_SERVICE_RECORD_RESPONSE
        
        # Mock the manual column mapping
        mapped_records = [
            {
                "id": "service-001",
                "vehicle_id": self.vehicle_id,
                "driver_id": None,
                "maintenance_type_id": 1,
                "maintenance_type_name": "oil_change",
                "maintenance_type_description": "Regular oil and filter change",
                "description": "Regular oil and filter change",
                "cost": "350.00",
                "service_date": "2024-01-15",
                "mileage": 15000,
                "service_provider": "Toyota Service Center",
                "is_warranty": False,
                "next_service_due": "2024-04-15",
                "receipt_url": None,
                "notes": "Used synthetic oil",
                "created_at": "2024-01-15T14:30:00Z",
                "updated_at": "2024-01-15T14:30:00Z"
            }
        ]
        
        # Mock format_results to return column-based data, then we'll test the mapping
        self.mock_db.format_results.return_value = [
            {
                "column_0": "service-001",
                "column_1": self.vehicle_id,
                "column_2": None,
                "column_3": 1,
                "column_4": "oil_change",
                "column_5": "Regular oil and filter change",
                "column_6": "Regular oil and filter change",
                "column_7": "350.00",
                "column_8": "2024-01-15",
                "column_9": 15000,
                "column_10": "Toyota Service Center",
                "column_11": False,
                "column_12": "2024-04-15",
                "column_13": None,
                "column_14": "Used synthetic oil",
                "column_15": "2024-01-15T14:30:00Z",
                "column_16": "2024-01-15T14:30:00Z"
            }
        ]
        
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        query_params = {}
        
        # Act
        response = get_service_history(self.vehicle_id, query_params)
        
        # Assert
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert response_body["vehicle_id"] == self.vehicle_id
        assert "service_records" in response_body
        assert response_body["count"] == 1
        
        # Verify service record data mapping
        service_record = response_body["service_records"][0]
        assert service_record["id"] == "service-001"
        assert service_record["maintenance_type_name"] == "oil_change"
        assert service_record["cost"] == "350.00"
        assert service_record["service_provider"] == "Toyota Service Center"
        
    @patch('handler.get_database_connection')
    def test_get_service_history_with_filters(self, mock_get_db):
        """Test service history retrieval with query filters"""
        # Arrange
        mock_get_db.return_value = self.mock_db
        self.mock_db.execute_query.return_value = MOCK_SERVICE_RECORD_RESPONSE
        self.mock_db.format_results.return_value = []  # Empty result for filtered query
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        query_params = {
            "maintenance_type": "oil_change",
            "from_date": "2024-01-01",
            "to_date": "2024-12-31",
            "min_cost": "100",
            "max_cost": "1000"
        }
        
        # Act
        response = get_service_history(self.vehicle_id, query_params)
        
        # Assert
        assert response["statusCode"] == 200
        
        # Verify SQL query includes filters
        call_args = self.mock_db.execute_query.call_args
        sql_query = call_args[0][0]
        assert "maintenance_type" in sql_query
        assert "service_date >=" in sql_query
        assert "service_date <=" in sql_query
        assert "cost >=" in sql_query
        assert "cost <=" in sql_query
        
    @patch('handler.get_database_connection')
    def test_get_maintenance_alerts_success(self, mock_get_db):
        """Test successful maintenance alerts retrieval"""
        # Arrange
        mock_get_db.return_value = self.mock_db
        
        # Mock alerts response with column-based data
        mock_alerts_response = {
            "records": [
                [
                    {"stringValue": self.vehicle_id},
                    {"stringValue": "Toyota"},
                    {"stringValue": "Corolla"},
                    {"stringValue": "ABC123GP"},
                    {"stringValue": "2024-01-01"},
                    {"stringValue": "2024-04-01"},
                    {"stringValue": "350.00"},
                    {"stringValue": "oil_change"},
                    {"isNull": True},
                    {"isNull": True},
                    {"isNull": True},
                    {"stringValue": "service_overdue"},
                    {"stringValue": "No service in last 6 months"}
                ]
            ],
            "columnMetadata": []
        }
        
        self.mock_db.execute_query.return_value = mock_alerts_response
        self.mock_db.format_results.return_value = [
            {
                "column_0": self.vehicle_id,
                "column_1": "Toyota",
                "column_2": "Corolla", 
                "column_3": "ABC123GP",
                "column_4": "2024-01-01",
                "column_5": "2024-04-01",
                "column_6": "350.00",
                "column_7": "oil_change",
                "column_8": None,
                "column_9": None,
                "column_10": None,
                "column_11": "service_overdue",
                "column_12": "No service in last 6 months"
            }
        ]
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        query_params = {}
        
        # Act
        response = get_maintenance_alerts(query_params)
        
        # Assert
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert "alerts" in response_body
        assert response_body["count"] == 1
        
        # Verify alert data mapping
        alert = response_body["alerts"][0]
        assert alert["vehicle_id"] == self.vehicle_id
        assert alert["make"] == "Toyota"
        assert alert["model"] == "Corolla"
        assert alert["registration"] == "ABC123GP"
        assert alert["alert_type"] == "service_overdue"
        assert alert["alert_message"] == "No service in last 6 months"
        
    @patch('handler.get_database_connection')
    def test_get_maintenance_alerts_with_filters(self, mock_get_db):
        """Test maintenance alerts retrieval with filters"""
        # Arrange
        mock_get_db.return_value = self.mock_db
        self.mock_db.execute_query.return_value = {"records": [], "columnMetadata": []}
        self.mock_db.format_results.return_value = []
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        query_params = {
            "alert_type": "service_overdue",
            "vehicle_id": self.vehicle_id
        }
        
        # Act
        response = get_maintenance_alerts(query_params)
        
        # Assert
        assert response["statusCode"] == 200
        
        # Verify SQL query includes filters
        call_args = self.mock_db.execute_query.call_args
        sql_query = call_args[0][0]
        assert "alert_type" in sql_query or "CASE WHEN" in sql_query
        assert "vehicle_id" in sql_query


if __name__ == "__main__":
    pytest.main([__file__])