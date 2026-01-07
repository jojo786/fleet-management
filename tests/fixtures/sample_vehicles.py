"""
Sample vehicle data for testing
"""
from datetime import datetime
from typing import Dict, List, Any

SAMPLE_VEHICLES = [
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "make": "Toyota",
        "model": "Corolla",
        "year": 2020,
        "registration": "ABC123GP",
        "vin": "1HGBH41JXMN109186",
        "status": "active",
        "current_driver_id": None,
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z"
    },
    {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "make": "BMW",
        "model": "X5",
        "year": 2021,
        "registration": "XYZ789GP",
        "vin": "WBAFR7C50BC123456",
        "status": "active",
        "current_driver_id": "driver-123",
        "created_at": "2024-01-02T10:00:00Z",
        "updated_at": "2024-01-02T10:00:00Z"
    },
    {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "make": "Mercedes",
        "model": "C-Class",
        "year": 2019,
        "registration": "DEF456GP",
        "vin": "WDDGF4HB1CA123456",
        "status": "in_service",
        "current_driver_id": None,
        "created_at": "2024-01-03T10:00:00Z",
        "updated_at": "2024-01-03T10:00:00Z"
    }
]

SAMPLE_SERVICE_RECORDS = [
    {
        "id": "service-001",
        "vehicle_id": "550e8400-e29b-41d4-a716-446655440000",
        "driver_id": None,
        "maintenance_type_id": 1,
        "maintenance_type_name": "oil_change",
        "description": "Regular oil and filter change",
        "cost": 350.00,
        "service_date": "2024-01-15",
        "mileage": 15000,
        "service_provider": "Toyota Service Center",
        "is_warranty": False,
        "next_service_due": "2024-04-15",
        "receipt_url": None,
        "notes": "Used synthetic oil",
        "created_at": "2024-01-15T14:30:00Z",
        "updated_at": "2024-01-15T14:30:00Z"
    },
    {
        "id": "service-002",
        "vehicle_id": "550e8400-e29b-41d4-a716-446655440001",
        "driver_id": "driver-123",
        "maintenance_type_id": 2,
        "maintenance_type_name": "brake_service",
        "description": "Brake pad replacement",
        "cost": 1200.00,
        "service_date": "2024-01-20",
        "mileage": 25000,
        "service_provider": "BMW Service Center",
        "is_warranty": True,
        "next_service_due": None,
        "receipt_url": "https://example.com/receipt-002.pdf",
        "notes": "Warranty repair",
        "created_at": "2024-01-20T11:15:00Z",
        "updated_at": "2024-01-20T11:15:00Z"
    }
]

MAINTENANCE_TYPES = [
    {"id": 1, "type_name": "oil_change", "description": "Regular oil and filter change"},
    {"id": 2, "type_name": "brake_service", "description": "Brake system maintenance"},
    {"id": 3, "type_name": "tire_replacement", "description": "Tire replacement and alignment"},
    {"id": 4, "type_name": "engine_repair", "description": "Engine diagnostic and repair"},
    {"id": 5, "type_name": "transmission_service", "description": "Transmission maintenance"},
    {"id": 6, "type_name": "accident_repair", "description": "Accident damage repair"},
    {"id": 7, "type_name": "general_maintenance", "description": "General maintenance and inspection"}
]

def create_test_vehicle(**overrides) -> Dict[str, Any]:
    """Create a test vehicle with optional field overrides"""
    vehicle = SAMPLE_VEHICLES[0].copy()
    vehicle.update(overrides)
    return vehicle

def create_test_service_record(**overrides) -> Dict[str, Any]:
    """Create a test service record with optional field overrides"""
    record = SAMPLE_SERVICE_RECORDS[0].copy()
    record.update(overrides)
    return record