"""
Integration tests for database operations
Tests Lambda to Aurora Serverless integration
"""
import pytest
import json
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import database utilities
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/vehicles'))
from db_utils import DatabaseConnection

# Import test fixtures
sys.path.append(os.path.join(os.path.dirname(__file__), '../fixtures'))
from sample_vehicles import SAMPLE_VEHICLES, SAMPLE_SERVICE_RECORDS


class TestDatabaseOperationsIntegration:
    """Integration tests for database operations"""
    
    def setup_method(self):
        """Set up test environment"""
        self.mock_rds_client = Mock()
        self.db_connection = DatabaseConnection()
        self.db_connection.rds_client = self.mock_rds_client
    
    @patch('boto3.client')
    def test_database_connection_initialization(self, mock_boto_client):
        """Test database connection initialization"""
        # Arrange
        mock_boto_client.return_value = self.mock_rds_client
        
        # Act
        db = DatabaseConnection()
        
        # Assert
        mock_boto_client.assert_called_with('rds-data')
        assert db.cluster_arn is not None
        assert db.secret_arn is not None
        assert db.database_name is not None
    
    def test_create_parameter_string_value(self):
        """Test parameter creation for string values"""
        # Act
        param = self.db_connection.create_parameter("test_param", "test_value")
        
        # Assert
        assert param["name"] == "test_param"
        assert param["value"]["stringValue"] == "test_value"
    
    def test_create_parameter_integer_value(self):
        """Test parameter creation for integer values"""
        # Act
        param = self.db_connection.create_parameter("test_param", 123)
        
        # Assert
        assert param["name"] == "test_param"
        assert param["value"]["longValue"] == 123
    
    def test_create_parameter_float_value(self):
        """Test parameter creation for float values"""
        # Act
        param = self.db_connection.create_parameter("test_param", 123.45)
        
        # Assert
        assert param["name"] == "test_param"
        assert param["value"]["doubleValue"] == 123.45
    
    def test_create_parameter_boolean_value(self):
        """Test parameter creation for boolean values"""
        # Act
        param_true = self.db_connection.create_parameter("test_param", True)
        param_false = self.db_connection.create_parameter("test_param", False)
        
        # Assert
        assert param_true["name"] == "test_param"
        assert param_true["value"]["booleanValue"] is True
        assert param_false["name"] == "test_param"
        assert param_false["value"]["booleanValue"] is False
    
    def test_create_parameter_none_value(self):
        """Test parameter creation for None values"""
        # Act
        param = self.db_connection.create_parameter("test_param", None)
        
        # Assert
        assert param["name"] == "test_param"
        assert param["value"]["isNull"] is True
    
    def test_execute_query_success(self):
        """Test successful query execution"""
        # Arrange
        sql = "SELECT * FROM vehicles WHERE id = :vehicle_id"
        parameters = [self.db_connection.create_parameter("vehicle_id", "test-id")]
        
        expected_response = {
            "records": [
                [
                    {"stringValue": "test-id"},
                    {"stringValue": "Toyota"},
                    {"stringValue": "Corolla"}
                ]
            ],
            "columnMetadata": [
                {"name": "id", "type": "VARCHAR"},
                {"name": "make", "type": "VARCHAR"},
                {"name": "model", "type": "VARCHAR"}
            ]
        }
        
        self.mock_rds_client.execute_statement.return_value = expected_response
        
        # Act
        result = self.db_connection.execute_query(sql, parameters)
        
        # Assert
        assert result == expected_response
        self.mock_rds_client.execute_statement.assert_called_once_with(
            resourceArn=self.db_connection.cluster_arn,
            secretArn=self.db_connection.secret_arn,
            database=self.db_connection.database_name,
            sql=sql,
            parameters=parameters
        )
    
    def test_execute_query_without_parameters(self):
        """Test query execution without parameters"""
        # Arrange
        sql = "SELECT COUNT(*) FROM vehicles"
        expected_response = {
            "records": [[{"longValue": 5}]],
            "columnMetadata": [{"name": "count", "type": "BIGINT"}]
        }
        
        self.mock_rds_client.execute_statement.return_value = expected_response
        
        # Act
        result = self.db_connection.execute_query(sql)
        
        # Assert
        assert result == expected_response
        self.mock_rds_client.execute_statement.assert_called_once_with(
            resourceArn=self.db_connection.cluster_arn,
            secretArn=self.db_connection.secret_arn,
            database=self.db_connection.database_name,
            sql=sql
        )
    
    def test_execute_query_database_error(self):
        """Test query execution with database error"""
        # Arrange
        sql = "INVALID SQL QUERY"
        self.mock_rds_client.execute_statement.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            self.db_connection.execute_query(sql)
        
        assert "Database error" in str(exc_info.value)
    
    def test_format_results_with_column_metadata(self):
        """Test result formatting with column metadata"""
        # Arrange
        raw_response = {
            "records": [
                [
                    {"stringValue": "vehicle-1"},
                    {"stringValue": "Toyota"},
                    {"longValue": 2020}
                ],
                [
                    {"stringValue": "vehicle-2"},
                    {"stringValue": "BMW"},
                    {"longValue": 2021}
                ]
            ],
            "columnMetadata": [
                {"name": "id", "type": "VARCHAR"},
                {"name": "make", "type": "VARCHAR"},
                {"name": "year", "type": "INTEGER"}
            ]
        }
        
        # Act
        result = self.db_connection.format_results(raw_response)
        
        # Assert
        assert len(result) == 2
        
        assert result[0]["id"] == "vehicle-1"
        assert result[0]["make"] == "Toyota"
        assert result[0]["year"] == 2020
        
        assert result[1]["id"] == "vehicle-2"
        assert result[1]["make"] == "BMW"
        assert result[1]["year"] == 2021
    
    def test_format_results_without_column_metadata(self):
        """Test result formatting without column metadata (fallback to column_N)"""
        # Arrange
        raw_response = {
            "records": [
                [
                    {"stringValue": "vehicle-1"},
                    {"stringValue": "Toyota"},
                    {"longValue": 2020}
                ]
            ],
            "columnMetadata": []
        }
        
        # Act
        result = self.db_connection.format_results(raw_response)
        
        # Assert
        assert len(result) == 1
        assert result[0]["column_0"] == "vehicle-1"
        assert result[0]["column_1"] == "Toyota"
        assert result[0]["column_2"] == 2020
    
    def test_format_results_with_null_values(self):
        """Test result formatting with null values"""
        # Arrange
        raw_response = {
            "records": [
                [
                    {"stringValue": "vehicle-1"},
                    {"isNull": True},
                    {"stringValue": "Toyota"}
                ]
            ],
            "columnMetadata": [
                {"name": "id", "type": "VARCHAR"},
                {"name": "driver_id", "type": "VARCHAR"},
                {"name": "make", "type": "VARCHAR"}
            ]
        }
        
        # Act
        result = self.db_connection.format_results(raw_response)
        
        # Assert
        assert len(result) == 1
        assert result[0]["id"] == "vehicle-1"
        assert result[0]["driver_id"] is None
        assert result[0]["make"] == "Toyota"
    
    def test_format_results_with_boolean_values(self):
        """Test result formatting with boolean values"""
        # Arrange
        raw_response = {
            "records": [
                [
                    {"stringValue": "service-1"},
                    {"booleanValue": True},
                    {"booleanValue": False}
                ]
            ],
            "columnMetadata": [
                {"name": "id", "type": "VARCHAR"},
                {"name": "is_warranty", "type": "BOOLEAN"},
                {"name": "is_completed", "type": "BOOLEAN"}
            ]
        }
        
        # Act
        result = self.db_connection.format_results(raw_response)
        
        # Assert
        assert len(result) == 1
        assert result[0]["id"] == "service-1"
        assert result[0]["is_warranty"] is True
        assert result[0]["is_completed"] is False
    
    def test_format_results_with_decimal_values(self):
        """Test result formatting with decimal values"""
        # Arrange
        raw_response = {
            "records": [
                [
                    {"stringValue": "service-1"},
                    {"stringValue": "350.75"}  # Decimal values come as strings from RDS Data API
                ]
            ],
            "columnMetadata": [
                {"name": "id", "type": "VARCHAR"},
                {"name": "cost", "type": "DECIMAL"}
            ]
        }
        
        # Act
        result = self.db_connection.format_results(raw_response)
        
        # Assert
        assert len(result) == 1
        assert result[0]["id"] == "service-1"
        assert result[0]["cost"] == "350.75"
    
    def test_format_results_empty_response(self):
        """Test result formatting with empty response"""
        # Arrange
        raw_response = {
            "records": [],
            "columnMetadata": [
                {"name": "id", "type": "VARCHAR"},
                {"name": "make", "type": "VARCHAR"}
            ]
        }
        
        # Act
        result = self.db_connection.format_results(raw_response)
        
        # Assert
        assert result == []
    
    @patch('handler.get_database_connection')
    def test_vehicle_crud_operations_integration(self, mock_get_db):
        """Test complete vehicle CRUD operations integration"""
        # Arrange
        mock_get_db.return_value = self.db_connection
        
        vehicle_data = SAMPLE_VEHICLES[0]
        vehicle_id = vehicle_data["id"]
        
        # Mock responses for different operations
        create_response = {
            "records": [[]],
            "columnMetadata": []
        }
        
        read_response = {
            "records": [
                [
                    {"stringValue": vehicle_id},
                    {"stringValue": vehicle_data["make"]},
                    {"stringValue": vehicle_data["model"]},
                    {"longValue": vehicle_data["year"]},
                    {"stringValue": vehicle_data["registration"]},
                    {"stringValue": vehicle_data["vin"]},
                    {"stringValue": vehicle_data["status"]},
                    {"isNull": True},
                    {"stringValue": vehicle_data["created_at"]},
                    {"stringValue": vehicle_data["updated_at"]}
                ]
            ],
            "columnMetadata": [
                {"name": "id", "type": "VARCHAR"},
                {"name": "make", "type": "VARCHAR"},
                {"name": "model", "type": "VARCHAR"},
                {"name": "year", "type": "INTEGER"},
                {"name": "registration", "type": "VARCHAR"},
                {"name": "vin", "type": "VARCHAR"},
                {"name": "status", "type": "VARCHAR"},
                {"name": "current_driver_id", "type": "VARCHAR"},
                {"name": "created_at", "type": "TIMESTAMP"},
                {"name": "updated_at", "type": "TIMESTAMP"}
            ]
        }
        
        # Test CREATE operation
        self.mock_rds_client.execute_statement.return_value = create_response
        create_result = self.db_connection.execute_query(
            "INSERT INTO vehicles (id, make, model, year, registration, vin, status) VALUES (:id, :make, :model, :year, :registration, :vin, :status)",
            [
                self.db_connection.create_parameter("id", vehicle_id),
                self.db_connection.create_parameter("make", vehicle_data["make"]),
                self.db_connection.create_parameter("model", vehicle_data["model"]),
                self.db_connection.create_parameter("year", vehicle_data["year"]),
                self.db_connection.create_parameter("registration", vehicle_data["registration"]),
                self.db_connection.create_parameter("vin", vehicle_data["vin"]),
                self.db_connection.create_parameter("status", vehicle_data["status"])
            ]
        )
        
        # Test READ operation
        self.mock_rds_client.execute_statement.return_value = read_response
        read_result = self.db_connection.execute_query(
            "SELECT * FROM vehicles WHERE id = :id",
            [self.db_connection.create_parameter("id", vehicle_id)]
        )
        
        formatted_result = self.db_connection.format_results(read_result)
        
        # Assert
        assert create_result == create_response
        assert read_result == read_response
        assert len(formatted_result) == 1
        assert formatted_result[0]["id"] == vehicle_id
        assert formatted_result[0]["make"] == vehicle_data["make"]
        assert formatted_result[0]["model"] == vehicle_data["model"]
    
    @patch('handler.get_database_connection')
    def test_service_record_operations_integration(self, mock_get_db):
        """Test service record database operations integration"""
        # Arrange
        mock_get_db.return_value = self.db_connection
        
        service_data = SAMPLE_SERVICE_RECORDS[0]
        service_id = service_data["id"]
        vehicle_id = service_data["vehicle_id"]
        
        # Mock service record creation response
        create_response = {
            "records": [[]],
            "columnMetadata": []
        }
        
        # Mock service history query response
        history_response = {
            "records": [
                [
                    {"stringValue": service_id},
                    {"stringValue": vehicle_id},
                    {"isNull": True},
                    {"longValue": service_data["maintenance_type_id"]},
                    {"stringValue": service_data["maintenance_type_name"]},
                    {"stringValue": "Regular oil and filter change"},
                    {"stringValue": service_data["description"]},
                    {"stringValue": str(service_data["cost"])},
                    {"stringValue": service_data["service_date"]},
                    {"longValue": service_data["mileage"]},
                    {"stringValue": service_data["service_provider"]},
                    {"booleanValue": service_data["is_warranty"]},
                    {"stringValue": service_data["next_service_due"]},
                    {"isNull": True},
                    {"stringValue": service_data["notes"]},
                    {"stringValue": service_data["created_at"]},
                    {"stringValue": service_data["updated_at"]}
                ]
            ],
            "columnMetadata": [
                {"name": "id", "type": "VARCHAR"},
                {"name": "vehicle_id", "type": "VARCHAR"},
                {"name": "driver_id", "type": "VARCHAR"},
                {"name": "maintenance_type_id", "type": "INTEGER"},
                {"name": "maintenance_type_name", "type": "VARCHAR"},
                {"name": "maintenance_type_description", "type": "VARCHAR"},
                {"name": "description", "type": "VARCHAR"},
                {"name": "cost", "type": "DECIMAL"},
                {"name": "service_date", "type": "DATE"},
                {"name": "mileage", "type": "INTEGER"},
                {"name": "service_provider", "type": "VARCHAR"},
                {"name": "is_warranty", "type": "BOOLEAN"},
                {"name": "next_service_due", "type": "DATE"},
                {"name": "receipt_url", "type": "VARCHAR"},
                {"name": "notes", "type": "VARCHAR"},
                {"name": "created_at", "type": "TIMESTAMP"},
                {"name": "updated_at", "type": "TIMESTAMP"}
            ]
        }
        
        # Test service record creation
        self.mock_rds_client.execute_statement.return_value = create_response
        create_result = self.db_connection.execute_query(
            """INSERT INTO service_records 
               (id, vehicle_id, maintenance_type_id, description, cost, service_date, service_provider, is_warranty, notes)
               VALUES (:id, :vehicle_id, :maintenance_type_id, :description, :cost, :service_date, :service_provider, :is_warranty, :notes)""",
            [
                self.db_connection.create_parameter("id", service_id),
                self.db_connection.create_parameter("vehicle_id", vehicle_id),
                self.db_connection.create_parameter("maintenance_type_id", service_data["maintenance_type_id"]),
                self.db_connection.create_parameter("description", service_data["description"]),
                self.db_connection.create_parameter("cost", service_data["cost"]),
                self.db_connection.create_parameter("service_date", service_data["service_date"]),
                self.db_connection.create_parameter("service_provider", service_data["service_provider"]),
                self.db_connection.create_parameter("is_warranty", service_data["is_warranty"]),
                self.db_connection.create_parameter("notes", service_data["notes"])
            ]
        )
        
        # Test service history retrieval
        self.mock_rds_client.execute_statement.return_value = history_response
        history_result = self.db_connection.execute_query(
            """SELECT sr.*, mt.type_name as maintenance_type_name, mt.description as maintenance_type_description
               FROM service_records sr
               JOIN maintenance_types mt ON sr.maintenance_type_id = mt.id
               WHERE sr.vehicle_id = :vehicle_id
               ORDER BY sr.service_date DESC""",
            [self.db_connection.create_parameter("vehicle_id", vehicle_id)]
        )
        
        formatted_history = self.db_connection.format_results(history_result)
        
        # Assert
        assert create_result == create_response
        assert history_result == history_response
        assert len(formatted_history) == 1
        assert formatted_history[0]["id"] == service_id
        assert formatted_history[0]["vehicle_id"] == vehicle_id
        assert formatted_history[0]["maintenance_type_id"] == service_data["maintenance_type_id"]
        assert formatted_history[0]["cost"] == str(service_data["cost"])
        assert formatted_history[0]["is_warranty"] == service_data["is_warranty"]


if __name__ == "__main__":
    pytest.main([__file__])