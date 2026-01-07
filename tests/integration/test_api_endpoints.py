"""
Integration tests for API endpoints
Tests the complete API Gateway to Lambda integration
"""
import pytest
import json
import uuid
from unittest.mock import Mock, patch, MagicMock

# Import the main handler
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/vehicles'))
from handler import lambda_handler

# Import test fixtures
sys.path.append(os.path.join(os.path.dirname(__file__), '../fixtures'))
from sample_vehicles import SAMPLE_VEHICLES, SAMPLE_SERVICE_RECORDS
from mock_responses import create_api_gateway_event, create_lambda_context, MOCK_RDS_EXECUTE_RESPONSE


class TestAPIEndpointsIntegration:
    """Integration tests for all API endpoints"""
    
    def setup_method(self):
        """Set up test environment"""
        self.context = create_lambda_context()
        self.mock_db = Mock()
        self.vehicle_id = "550e8400-e29b-41d4-a716-446655440000"
    
    @patch('handler.get_database_connection')
    def test_list_vehicles_endpoint_as_health_check(self, mock_get_db):
        """Test vehicle listing endpoint as a health check integration"""
        # Arrange
        mock_get_db.return_value = self.mock_db
        self.mock_db.execute_query.return_value = {"records": [], "columnMetadata": []}
        self.mock_db.format_results.return_value = []
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        event = create_api_gateway_event(method="GET", path="/vehicles")
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "vehicles" in body
        assert "count" in body
        
        # Verify CORS headers
        assert "Access-Control-Allow-Origin" in response["headers"]
        assert "Access-Control-Allow-Methods" in response["headers"]
    
    @patch('handler.get_database_connection')
    def test_create_vehicle_endpoint_integration(self, mock_get_db):
        """Test vehicle creation endpoint integration"""
        # Arrange
        mock_get_db.return_value = self.mock_db
        
        vehicle_data = {
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "registration": "ABC123GP",
            "vin": "1HGBH41JXMN109186"
        }
        
        created_vehicle = vehicle_data.copy()
        created_vehicle["id"] = self.vehicle_id
        created_vehicle["status"] = "active"
        created_vehicle["created_at"] = "2024-01-01T10:00:00Z"
        created_vehicle["updated_at"] = "2024-01-01T10:00:00Z"
        
        self.mock_db.execute_query.return_value = {"records": [[]], "columnMetadata": []}
        self.mock_db.format_results.return_value = [created_vehicle]
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        event = create_api_gateway_event(
            method="POST",
            path="/vehicles",
            body=json.dumps(vehicle_data)
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["make"] == vehicle_data["make"]
        assert body["model"] == vehicle_data["model"]
        assert body["year"] == vehicle_data["year"]
        assert body["registration"] == vehicle_data["registration"]
        assert "id" in body
        
        # Verify database interaction
        assert self.mock_db.execute_query.called
        assert self.mock_db.format_results.called
    
    @patch('handler.get_database_connection')
    def test_get_vehicle_endpoint_integration(self, mock_get_db):
        """Test vehicle retrieval endpoint integration"""
        # Arrange
        mock_get_db.return_value = self.mock_db
        
        vehicle = SAMPLE_VEHICLES[0]
        self.mock_db.execute_query.return_value = MOCK_RDS_EXECUTE_RESPONSE
        self.mock_db.format_results.return_value = [vehicle]
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        event = create_api_gateway_event(
            method="GET",
            path=f"/vehicles/{self.vehicle_id}",
            path_parameters={"id": self.vehicle_id}
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["id"] == vehicle["id"]
        assert body["make"] == vehicle["make"]
        assert body["model"] == vehicle["model"]
        
        # Verify database query with correct vehicle ID
        call_args = self.mock_db.execute_query.call_args
        assert self.vehicle_id in str(call_args)
    
    @patch('handler.get_database_connection')
    def test_list_vehicles_endpoint_integration(self, mock_get_db):
        """Test vehicle listing endpoint integration"""
        # Arrange
        mock_get_db.return_value = self.mock_db
        
        self.mock_db.execute_query.return_value = {"records": [], "columnMetadata": []}
        self.mock_db.format_results.return_value = SAMPLE_VEHICLES
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        event = create_api_gateway_event(
            method="GET",
            path="/vehicles",
            query_parameters={"status": "active", "limit": "10"}
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "vehicles" in body
        assert "count" in body
        assert body["count"] == len(SAMPLE_VEHICLES)
        
        # Verify query parameters are processed
        call_args = self.mock_db.execute_query.call_args
        sql_query = call_args[0][0]
        assert "status" in sql_query
        assert "LIMIT" in sql_query
    
    @patch('handler.get_database_connection')
    def test_update_vehicle_endpoint_integration(self, mock_get_db):
        """Test vehicle update endpoint integration"""
        # Arrange
        mock_get_db.return_value = self.mock_db
        
        update_data = {
            "status": "in_service",
            "current_driver_id": "driver-123"
        }
        
        updated_vehicle = SAMPLE_VEHICLES[0].copy()
        updated_vehicle.update(update_data)
        updated_vehicle["updated_at"] = "2024-01-02T10:00:00Z"
        
        # Mock vehicle exists check and update
        self.mock_db.execute_query.side_effect = [
            {"records": [[{"stringValue": self.vehicle_id}]], "columnMetadata": []},  # Vehicle exists
            {"records": [[]], "columnMetadata": []}  # Update operation
        ]
        self.mock_db.format_results.side_effect = [
            [{"id": self.vehicle_id}],  # Vehicle exists response
            [updated_vehicle]  # Update response
        ]
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        event = create_api_gateway_event(
            method="PUT",
            path=f"/vehicles/{self.vehicle_id}",
            path_parameters={"id": self.vehicle_id},
            body=json.dumps(update_data)
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["status"] == update_data["status"]
        assert body["current_driver_id"] == update_data["current_driver_id"]
        
        # Verify both vehicle check and update queries
        assert self.mock_db.execute_query.call_count == 2
    
    @patch('handler.get_database_connection')
    def test_delete_vehicle_endpoint_integration(self, mock_get_db):
        """Test vehicle deletion endpoint integration"""
        # Arrange
        mock_get_db.return_value = self.mock_db
        
        # Mock vehicle exists check and deletion
        self.mock_db.execute_query.side_effect = [
            {"records": [[{"stringValue": self.vehicle_id}]], "columnMetadata": []},  # Vehicle exists
            {"records": [[]], "columnMetadata": []}  # Delete operation
        ]
        self.mock_db.format_results.side_effect = [
            [{"id": self.vehicle_id}],  # Vehicle exists response
            []  # Delete response (no return data)
        ]
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        event = create_api_gateway_event(
            method="DELETE",
            path=f"/vehicles/{self.vehicle_id}",
            path_parameters={"id": self.vehicle_id}
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 204
        assert response["body"] == ""
        
        # Verify both vehicle check and delete queries
        assert self.mock_db.execute_query.call_count == 2
    
    @patch('handler.get_database_connection')
    def test_add_service_record_endpoint_integration(self, mock_get_db):
        """Test service record creation endpoint integration"""
        # Arrange
        mock_get_db.return_value = self.mock_db
        
        service_data = {
            "maintenance_type_id": 1,
            "description": "Regular oil and filter change",
            "cost": 350.00,
            "service_date": "2024-01-15",
            "service_provider": "Toyota Service Center",
            "mileage": 15000,
            "is_warranty": False,
            "notes": "Used synthetic oil"
        }
        
        created_service = service_data.copy()
        created_service["id"] = "service-001"
        created_service["vehicle_id"] = self.vehicle_id
        created_service["created_at"] = "2024-01-15T14:30:00Z"
        created_service["updated_at"] = "2024-01-15T14:30:00Z"
        
        # Mock vehicle exists check and service record creation
        self.mock_db.execute_query.side_effect = [
            {"records": [[{"stringValue": self.vehicle_id}]], "columnMetadata": []},  # Vehicle exists
            {"records": [[]], "columnMetadata": []}  # Service record creation
        ]
        self.mock_db.format_results.side_effect = [
            [{"id": self.vehicle_id}],  # Vehicle exists response
            [created_service]  # Service record creation response
        ]
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        event = create_api_gateway_event(
            method="POST",
            path=f"/vehicles/{self.vehicle_id}/service-records",
            path_parameters={"id": self.vehicle_id},
            body=json.dumps(service_data)
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["description"] == service_data["description"]
        assert float(body["cost"]) == service_data["cost"]
        assert body["service_provider"] == service_data["service_provider"]
        assert body["vehicle_id"] == self.vehicle_id
    
    @patch('handler.get_database_connection')
    def test_get_service_history_endpoint_integration(self, mock_get_db):
        """Test service history retrieval endpoint integration"""
        # Arrange
        mock_get_db.return_value = self.mock_db
        
        # Mock service history response with column-based data
        mock_history_records = [
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
        
        self.mock_db.execute_query.return_value = {"records": [], "columnMetadata": []}
        self.mock_db.format_results.return_value = mock_history_records
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        event = create_api_gateway_event(
            method="GET",
            path=f"/vehicles/{self.vehicle_id}/service-records",
            path_parameters={"id": self.vehicle_id},
            query_parameters={"from_date": "2024-01-01", "to_date": "2024-12-31"}
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["vehicle_id"] == self.vehicle_id
        assert "service_records" in body
        assert body["count"] == 1
        
        # Verify query parameters are processed
        call_args = self.mock_db.execute_query.call_args
        sql_query = call_args[0][0]
        assert "service_date >=" in sql_query
        assert "service_date <=" in sql_query
    
    @patch('handler.get_database_connection')
    def test_get_maintenance_alerts_endpoint_integration(self, mock_get_db):
        """Test maintenance alerts endpoint integration"""
        # Arrange
        mock_get_db.return_value = self.mock_db
        
        # Mock alerts response
        mock_alerts = [
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
        
        self.mock_db.execute_query.return_value = {"records": [], "columnMetadata": []}
        self.mock_db.format_results.return_value = mock_alerts
        self.mock_db.create_parameter.side_effect = lambda name, value: {"name": name, "value": {"stringValue": str(value)}}
        
        event = create_api_gateway_event(
            method="GET",
            path="/maintenance-alerts",
            query_parameters={"alert_type": "service_overdue"}
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "alerts" in body
        assert body["count"] == 1
        
        alert = body["alerts"][0]
        assert alert["vehicle_id"] == self.vehicle_id
        assert alert["alert_type"] == "service_overdue"
        assert alert["alert_message"] == "No service in last 6 months"
    
    @patch('handler.get_database_connection')
    def test_invalid_endpoint_integration(self, mock_get_db):
        """Test invalid endpoint handling"""
        # Arrange
        event = create_api_gateway_event(
            method="GET",
            path="/invalid-endpoint"
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert "error" in body
        assert "not found" in body["error"].lower()
    
    @patch('handler.get_database_connection')
    def test_method_not_allowed_integration(self, mock_get_db):
        """Test method not allowed handling"""
        # Arrange
        event = create_api_gateway_event(
            method="PATCH",  # Not supported method
            path="/vehicles"
        )
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response["statusCode"] == 405
        body = json.loads(response["body"])
        assert "error" in body
        assert "method not allowed" in body["error"].lower()
    
    @patch('handler.get_database_connection')
    def test_cors_headers_integration(self, mock_get_db):
        """Test CORS headers are properly set on all responses"""
        # Arrange
        mock_get_db.return_value = self.mock_db
        self.mock_db.execute_query.return_value = {"records": [[{"longValue": 1}]], "columnMetadata": []}
        self.mock_db.format_results.return_value = [{"count": 1}]
        
        event = create_api_gateway_event(method="GET", path="/health")
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        headers = response["headers"]
        assert "Access-Control-Allow-Origin" in headers
        assert "Access-Control-Allow-Methods" in headers
        assert "Access-Control-Allow-Headers" in headers
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert "GET" in headers["Access-Control-Allow-Methods"]
        assert "POST" in headers["Access-Control-Allow-Methods"]
        assert "PUT" in headers["Access-Control-Allow-Methods"]
        assert "DELETE" in headers["Access-Control-Allow-Methods"]


if __name__ == "__main__":
    pytest.main([__file__])