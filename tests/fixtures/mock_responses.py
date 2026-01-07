"""
Mock API responses for testing
"""
from typing import Dict, Any, List

# Mock RDS Data API responses
MOCK_RDS_EXECUTE_RESPONSE = {
    "records": [
        [
            {"stringValue": "550e8400-e29b-41d4-a716-446655440000"},
            {"stringValue": "Toyota"},
            {"stringValue": "Corolla"},
            {"longValue": 2020},
            {"stringValue": "ABC123GP"},
            {"stringValue": "1HGBH41JXMN109186"},
            {"stringValue": "active"},
            {"isNull": True},
            {"stringValue": "2024-01-01T10:00:00Z"},
            {"stringValue": "2024-01-01T10:00:00Z"}
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

MOCK_SERVICE_RECORD_RESPONSE = {
    "records": [
        [
            {"stringValue": "service-001"},
            {"stringValue": "550e8400-e29b-41d4-a716-446655440000"},
            {"isNull": True},
            {"longValue": 1},
            {"stringValue": "oil_change"},
            {"stringValue": "Regular oil and filter change"},
            {"stringValue": "Regular oil and filter change"},
            {"stringValue": "350.00"},
            {"stringValue": "2024-01-15"},
            {"longValue": 15000},
            {"stringValue": "Toyota Service Center"},
            {"booleanValue": False},
            {"stringValue": "2024-04-15"},
            {"isNull": True},
            {"stringValue": "Used synthetic oil"},
            {"stringValue": "2024-01-15T14:30:00Z"},
            {"stringValue": "2024-01-15T14:30:00Z"}
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

# Mock API Gateway events
def create_api_gateway_event(
    method: str = "GET",
    path: str = "/vehicles",
    body: str = None,
    path_parameters: Dict[str, str] = None,
    query_parameters: Dict[str, str] = None
) -> Dict[str, Any]:
    """Create a mock API Gateway event"""
    return {
        "httpMethod": method,
        "path": path,
        "body": body,
        "pathParameters": path_parameters or {},
        "queryStringParameters": query_parameters or {},
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://example.com"
        },
        "requestContext": {
            "requestId": "test-request-id",
            "stage": "test",
            "httpMethod": method,
            "path": path
        }
    }

def create_lambda_context():
    """Create a mock Lambda context"""
    class MockContext:
        def __init__(self):
            self.function_name = "test-function"
            self.function_version = "$LATEST"
            self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-function"
            self.memory_limit_in_mb = 128
            self.remaining_time_in_millis = 30000
            self.log_group_name = "/aws/lambda/test-function"
            self.log_stream_name = "2024/01/01/[$LATEST]test-stream"
            self.aws_request_id = "test-request-id"
    
    return MockContext()

# Error responses for testing
ERROR_RESPONSES = {
    "invalid_uuid": {
        "statusCode": 400,
        "body": '{"error": "Invalid vehicle ID format"}'
    },
    "vehicle_not_found": {
        "statusCode": 404,
        "body": '{"error": "Vehicle not found"}'
    },
    "database_error": {
        "statusCode": 500,
        "body": '{"error": "Database connection failed"}'
    },
    "validation_error": {
        "statusCode": 400,
        "body": '{"error": "Missing required field: make"}'
    }
}