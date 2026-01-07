"""
Unit tests for vehicle management functionality
"""
import pytest
import json
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the handler function
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/vehicles'))
from handler import lambda_handler, create_vehicle, get_vehicle, list_vehicles, delete_vehicle

# Import test fixtures
sys.path.append(os.path.join(os.path.dirname(__file__), '../fixtures'))
from sample_vehicles import SAMPLE_VEHICLES, create_test_vehicle
from mock_responses import (
    create_api_gateway_event, 
    create_lambda_context, 
    MOCK_RDS_EXECUTE_RESPONSE,
    ERROR_RESPONSES
)


class TestVehicleManagement:
    """Test suite for vehicle management operations"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        self.context = create_lambda_context()
        self.mock_db = Mock()
        
    @patch('handler.get_database_connection')
    def test_create_vehicle_success(self, mock_get_db):
        """Test successful vehicle creation"""
        # Arrange
        mock_get_db.return_value = self.mock_db
        self.mock_db.execute_query.return_value = MOCK_RDS_EXECUTE_RESPONSE
        self.mock_db.format_results.return_value = [SAMPLE_VEHICLES[0]]
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        vehicle_data = {
            "make": "Toyota",
            "model": "Corolla", 
            "year": 2020,
            "registration": "ABC123GP",
            "vin": "1HGBH41JXMN109186"
        }
        
        event = create_api_gateway_event(
            method="POST",
            path="/vehicles",
            body=json.dumps(vehicle_data)
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 201
        response_body = json.loads(response["body"])
        assert response_body["make"] == "Toyota"
        assert response_body["model"] == "Corolla"
        assert response_body["registration"] == "ABC123GP"
        
        # Verify database interaction
        self.mock_db.execute_query.assert_called_once()
        call_args = self.mock_db.execute_query.call_args
        assert "INSERT INTO vehicles" in call_args[0][0]
        
    @patch('handler.get_database_connection')
    def test_create_vehicle_missing_required_field(self, mock_get_db):
        """Test vehicle creation with missing required field"""
        # Arrange
        vehicle_data = {
            "model": "Corolla",  # Missing 'make' field
            "year": 2020,
            "registration": "ABC123GP"
        }
        
        event = create_api_gateway_event(
            method="POST",
            path="/vehicles",
            body=json.dumps(vehicle_data)
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "Missing required field: make" in response_body["error"]
        
    @patch('handler.get_database_connection')
    def test_create_vehicle_invalid_year(self, mock_get_db):
        """Test vehicle creation with invalid year"""
        # Arrange
        vehicle_data = {
            "make": "Toyota",
            "model": "Corolla",
            "year": 1800,  # Invalid year
            "registration": "ABC123GP"
        }
        
        event = create_api_gateway_event(
            method="POST",
            path="/vehicles",
            body=json.dumps(vehicle_data)
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "Year must be between 1900 and 2100" in response_body["error"]
        
    @patch('handler.get_database_connection')
    def test_get_vehicle_success(self, mock_get_db):
        """Test successful vehicle retrieval"""
        # Arrange
        vehicle_id = "550e8400-e29b-41d4-a716-446655440000"
        mock_get_db.return_value = self.mock_db
        self.mock_db.execute_query.return_value = MOCK_RDS_EXECUTE_RESPONSE
        self.mock_db.format_results.return_value = [SAMPLE_VEHICLES[0]]
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        event = create_api_gateway_event(
            method="GET",
            path=f"/vehicles/{vehicle_id}",
            path_parameters={"id": vehicle_id}
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert response_body["id"] == vehicle_id
        assert response_body["make"] == "Toyota"
        
    @patch('handler.get_database_connection')
    def test_get_vehicle_invalid_uuid(self, mock_get_db):
        """Test vehicle retrieval with invalid UUID"""
        # Arrange
        invalid_id = "invalid-uuid"
        
        event = create_api_gateway_event(
            method="GET",
            path=f"/vehicles/{invalid_id}",
            path_parameters={"id": invalid_id}
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "Invalid vehicle ID format" in response_body["error"]
        
    @patch('handler.get_database_connection')
    def test_get_vehicle_not_found(self, mock_get_db):
        """Test vehicle retrieval when vehicle doesn't exist"""
        # Arrange
        vehicle_id = "550e8400-e29b-41d4-a716-446655440000"
        mock_get_db.return_value = self.mock_db
        self.mock_db.execute_query.return_value = {"records": []}
        self.mock_db.format_results.return_value = []
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        event = create_api_gateway_event(
            method="GET",
            path=f"/vehicles/{vehicle_id}",
            path_parameters={"id": vehicle_id}
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 404
        response_body = json.loads(response["body"])
        assert "Vehicle not found" in response_body["error"]
        
    @patch('handler.get_database_connection')
    def test_list_vehicles_success(self, mock_get_db):
        """Test successful vehicle listing"""
        # Arrange
        mock_get_db.return_value = self.mock_db
        mock_response = {
            "records": [
                # Multiple vehicle records
                MOCK_RDS_EXECUTE_RESPONSE["records"][0],
                MOCK_RDS_EXECUTE_RESPONSE["records"][0]  # Duplicate for testing
            ],
            "columnMetadata": MOCK_RDS_EXECUTE_RESPONSE["columnMetadata"]
        }
        self.mock_db.execute_query.return_value = mock_response
        self.mock_db.format_results.return_value = SAMPLE_VEHICLES[:2]
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"longValue": value}}
        
        event = create_api_gateway_event(
            method="GET",
            path="/vehicles"
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert "vehicles" in response_body
        assert response_body["count"] == 2
        assert len(response_body["vehicles"]) == 2
        
    @patch('handler.get_database_connection')
    def test_list_vehicles_with_filters(self, mock_get_db):
        """Test vehicle listing with query filters"""
        # Arrange
        mock_get_db.return_value = self.mock_db
        self.mock_db.execute_query.return_value = MOCK_RDS_EXECUTE_RESPONSE
        self.mock_db.format_results.return_value = [SAMPLE_VEHICLES[0]]
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        event = create_api_gateway_event(
            method="GET",
            path="/vehicles",
            query_parameters={
                "make": "Toyota",
                "status": "active",
                "limit": "10"
            }
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 200
        
        # Verify SQL query includes filters
        call_args = self.mock_db.execute_query.call_args
        sql_query = call_args[0][0]
        assert "make" in sql_query
        assert "status" in sql_query
        assert "LIMIT" in sql_query
        
    @patch('handler.get_database_connection')
    def test_delete_vehicle_success(self, mock_get_db):
        """Test successful vehicle deletion (soft delete)"""
        # Arrange
        vehicle_id = "550e8400-e29b-41d4-a716-446655440000"
        mock_get_db.return_value = self.mock_db
        self.mock_db.execute_query.return_value = MOCK_RDS_EXECUTE_RESPONSE
        self.mock_db.format_results.return_value = [{"id": vehicle_id}]
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        event = create_api_gateway_event(
            method="DELETE",
            path=f"/vehicles/{vehicle_id}",
            path_parameters={"id": vehicle_id}
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert "Vehicle retired successfully" in response_body["message"]
        assert response_body["id"] == vehicle_id
        
        # Verify SQL query is UPDATE (soft delete)
        call_args = self.mock_db.execute_query.call_args
        sql_query = call_args[0][0]
        assert "UPDATE vehicles" in sql_query
        assert "SET status = 'retired'" in sql_query
        
    @patch('handler.get_database_connection')
    def test_database_connection_error(self, mock_get_db):
        """Test handling of database connection errors"""
        # Arrange
        mock_get_db.side_effect = Exception("Database connection failed")
        
        event = create_api_gateway_event(
            method="GET",
            path="/vehicles"
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 500
        response_body = json.loads(response["body"])
        assert "Failed to list vehicles" in response_body["error"]
        
    def test_cors_headers_present(self):
        """Test that CORS headers are present in all responses"""
        # Arrange
        event = create_api_gateway_event(
            method="GET",
            path="/invalid-path"
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        headers = response.get("headers", {})
        assert "Access-Control-Allow-Origin" in headers
        assert "Access-Control-Allow-Headers" in headers
        assert "Access-Control-Allow-Methods" in headers
        assert headers["Access-Control-Allow-Origin"] == "*"


if __name__ == "__main__":
    pytest.main([__file__])