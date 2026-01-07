"""
Vehicle Management Lambda Function for FLEET System
Handles CRUD operations for vehicles
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import database utilities
import sys
sys.path.append('/opt/python')
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../database')

from db_utils import get_database_connection


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for vehicle management operations
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        dict: API Gateway response
    """
    try:
        # Log the incoming request
        logger.info(f"Vehicle management request: {json.dumps(event, default=str)}")
        
        # Extract HTTP method and path
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        # Parse request body if present
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except json.JSONDecodeError:
                return create_error_response(400, "Invalid JSON in request body")
        
        # Route to appropriate handler
        if path.startswith('/vehicles/') and '/service-records' in path:
            # Service record routes
            if http_method == 'POST':
                vehicle_id = path_parameters.get('id')
                if vehicle_id:
                    return add_service_record(vehicle_id, body)
                else:
                    return create_error_response(400, "Vehicle ID required for service record")
            elif http_method == 'GET':
                vehicle_id = path_parameters.get('id')
                if vehicle_id:
                    return get_service_history(vehicle_id, query_parameters)
                else:
                    return create_error_response(400, "Vehicle ID required for service history")
        elif path.startswith('/maintenance-alerts'):
            # Maintenance alerts route
            if http_method == 'GET':
                return get_maintenance_alerts(query_parameters)
        elif path.startswith('/cost-analysis'):
            # Cost analysis routes
            if http_method == 'GET':
                return get_cost_analysis(query_parameters)
        elif path.startswith('/fleet-cost-comparison'):
            # Fleet cost comparison route
            if http_method == 'GET':
                return get_fleet_cost_comparison(query_parameters)
        elif path.startswith('/high-cost-alerts'):
            # High cost alerts route
            if http_method == 'GET':
                return get_high_cost_alerts(query_parameters)
        elif http_method == 'GET':
            if path_parameters.get('id'):
                return get_vehicle(path_parameters['id'])
            else:
                return list_vehicles(query_parameters)
        elif http_method == 'POST':
            return create_vehicle(body)
        elif http_method == 'PUT':
            if path_parameters.get('id'):
                return update_vehicle(path_parameters['id'], body)
            else:
                return create_error_response(400, "Vehicle ID required for update")
        elif http_method == 'DELETE':
            if path_parameters.get('id'):
                return delete_vehicle(path_parameters['id'])
            else:
                return create_error_response(400, "Vehicle ID required for deletion")
        else:
            return create_error_response(405, f"Method {http_method} not allowed")
            
    except Exception as e:
        logger.error(f"Vehicle management error: {str(e)}")
        return create_error_response(500, f"Internal server error: {str(e)}")


def create_vehicle(vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new vehicle
    
    Args:
        vehicle_data: Vehicle information
        
    Returns:
        dict: API response with created vehicle
    """
    try:
        # Validate required fields
        required_fields = ['make', 'model', 'year', 'registration']
        for field in required_fields:
            if field not in vehicle_data or not vehicle_data[field]:
                return create_error_response(400, f"Missing required field: {field}")
        
        # Validate year
        year = vehicle_data.get('year')
        if not isinstance(year, int) or year < 1900 or year > 2100:
            return create_error_response(400, "Year must be between 1900 and 2100")
        
        # Validate status if provided
        valid_statuses = ['active', 'in_service', 'out_of_order', 'retired']
        status = vehicle_data.get('status', 'active')
        if status not in valid_statuses:
            return create_error_response(400, f"Status must be one of: {', '.join(valid_statuses)}")
        
        # Get database connection
        db = get_database_connection()
        
        # Generate UUID for the vehicle
        vehicle_id = str(uuid.uuid4())
        
        # Prepare SQL statement
        sql = """
        INSERT INTO vehicles (id, make, model, year, registration, vin, status, current_driver_id)
        VALUES (:id::uuid, :make, :model, :year, :registration, :vin, :status, :current_driver_id::uuid)
        RETURNING id, make, model, year, registration, vin, status, current_driver_id, created_at, updated_at
        """
        
        # Prepare parameters
        parameters = [
            db.create_parameter('id', vehicle_id),
            db.create_parameter('make', vehicle_data['make']),
            db.create_parameter('model', vehicle_data['model']),
            db.create_parameter('year', vehicle_data['year']),
            db.create_parameter('registration', vehicle_data['registration']),
            db.create_parameter('vin', vehicle_data.get('vin')),
            db.create_parameter('status', status),
            db.create_parameter('current_driver_id', vehicle_data.get('current_driver_id'))
        ]
        
        # Execute query
        response = db.execute_query(sql, parameters)
        
        # Format and return result
        vehicles = db.format_results(response)
        if vehicles:
            logger.info(f"Vehicle created successfully: {vehicle_id}")
            return create_success_response(201, vehicles[0])
        else:
            return create_error_response(500, "Failed to create vehicle")
            
    except Exception as e:
        logger.error(f"Create vehicle error: {str(e)}")
        if "duplicate key" in str(e).lower():
            return create_error_response(409, "Vehicle with this registration already exists")
        return create_error_response(500, f"Failed to create vehicle: {str(e)}")


def get_vehicle(vehicle_id: str) -> Dict[str, Any]:
    """
    Get a vehicle by ID
    
    Args:
        vehicle_id: Vehicle UUID
        
    Returns:
        dict: API response with vehicle data
    """
    try:
        # Validate UUID format
        try:
            uuid.UUID(vehicle_id)
        except ValueError:
            return create_error_response(400, "Invalid vehicle ID format")
        
        # Get database connection
        db = get_database_connection()
        
        # Prepare SQL statement
        sql = """
        SELECT id, make, model, year, registration, vin, status, current_driver_id, created_at, updated_at
        FROM vehicles
        WHERE id = :id
        """
        
        # Prepare parameters
        parameters = [db.create_parameter('id', vehicle_id)]
        
        # Execute query
        response = db.execute_query(sql, parameters)
        
        # Format and return result
        vehicles = db.format_results(response)
        if vehicles:
            logger.info(f"Vehicle retrieved successfully: {vehicle_id}")
            return create_success_response(200, vehicles[0])
        else:
            return create_error_response(404, "Vehicle not found")
            
    except Exception as e:
        logger.error(f"Get vehicle error: {str(e)}")
        return create_error_response(500, f"Failed to retrieve vehicle: {str(e)}")


def list_vehicles(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    List vehicles with optional filtering
    
    Args:
        query_params: Query parameters for filtering
        
    Returns:
        dict: API response with list of vehicles
    """
    try:
        # Get database connection
        db = get_database_connection()
        
        # Build SQL query with optional filters
        sql = """
        SELECT id, make, model, year, registration, vin, status, current_driver_id, created_at, updated_at
        FROM vehicles
        WHERE 1=1
        """
        parameters = []
        
        # Add filters based on query parameters
        if query_params.get('status'):
            sql += " AND status = :status"
            parameters.append(db.create_parameter('status', query_params['status']))
        
        if query_params.get('make'):
            sql += " AND LOWER(make) LIKE LOWER(:make)"
            parameters.append(db.create_parameter('make', f"%{query_params['make']}%"))
        
        if query_params.get('model'):
            sql += " AND LOWER(model) LIKE LOWER(:model)"
            parameters.append(db.create_parameter('model', f"%{query_params['model']}%"))
        
        if query_params.get('registration'):
            sql += " AND LOWER(registration) LIKE LOWER(:registration)"
            parameters.append(db.create_parameter('registration', f"%{query_params['registration']}%"))
        
        # Add ordering
        sql += " ORDER BY created_at DESC"
        
        # Add pagination
        limit = min(int(query_params.get('limit', 50)), 100)  # Max 100 items
        offset = int(query_params.get('offset', 0))
        
        sql += " LIMIT :limit OFFSET :offset"
        parameters.extend([
            db.create_parameter('limit', limit),
            db.create_parameter('offset', offset)
        ])
        
        # Execute query
        response = db.execute_query(sql, parameters)
        
        # Format results
        vehicles = db.format_results(response)
        
        logger.info(f"Listed {len(vehicles)} vehicles")
        return create_success_response(200, {
            'vehicles': vehicles,
            'count': len(vehicles),
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"List vehicles error: {str(e)}")
        return create_error_response(500, f"Failed to list vehicles: {str(e)}")


def update_vehicle(vehicle_id: str, vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a vehicle
    
    Args:
        vehicle_id: Vehicle UUID
        vehicle_data: Updated vehicle information
        
    Returns:
        dict: API response with updated vehicle
    """
    try:
        # Validate UUID format
        try:
            uuid.UUID(vehicle_id)
        except ValueError:
            return create_error_response(400, "Invalid vehicle ID format")
        
        # Validate year if provided
        if 'year' in vehicle_data:
            year = vehicle_data['year']
            if not isinstance(year, int) or year < 1900 or year > 2100:
                return create_error_response(400, "Year must be between 1900 and 2100")
        
        # Validate status if provided
        if 'status' in vehicle_data:
            valid_statuses = ['active', 'in_service', 'out_of_order', 'retired']
            if vehicle_data['status'] not in valid_statuses:
                return create_error_response(400, f"Status must be one of: {', '.join(valid_statuses)}")
        
        # Get database connection
        db = get_database_connection()
        
        # Build dynamic update query
        update_fields = []
        parameters = []
        
        updatable_fields = ['make', 'model', 'year', 'registration', 'vin', 'status', 'current_driver_id']
        for field in updatable_fields:
            if field in vehicle_data:
                update_fields.append(f"{field} = :{field}")
                parameters.append(db.create_parameter(field, vehicle_data[field]))
        
        if not update_fields:
            return create_error_response(400, "No valid fields to update")
        
        # Add vehicle ID parameter
        parameters.append(db.create_parameter('id', vehicle_id))
        
        # Prepare SQL statement
        sql = f"""
        UPDATE vehicles
        SET {', '.join(update_fields)}
        WHERE id = :id
        RETURNING id, make, model, year, registration, vin, status, current_driver_id, created_at, updated_at
        """
        
        # Execute query
        response = db.execute_query(sql, parameters)
        
        # Format and return result
        vehicles = db.format_results(response)
        if vehicles:
            logger.info(f"Vehicle updated successfully: {vehicle_id}")
            return create_success_response(200, vehicles[0])
        else:
            return create_error_response(404, "Vehicle not found")
            
    except Exception as e:
        logger.error(f"Update vehicle error: {str(e)}")
        if "duplicate key" in str(e).lower():
            return create_error_response(409, "Vehicle with this registration already exists")
        return create_error_response(500, f"Failed to update vehicle: {str(e)}")


def delete_vehicle(vehicle_id: str) -> Dict[str, Any]:
    """
    Delete a vehicle (soft delete by setting status to retired)
    
    Args:
        vehicle_id: Vehicle UUID
        
    Returns:
        dict: API response confirming deletion
    """
    try:
        # Validate UUID format
        try:
            uuid.UUID(vehicle_id)
        except ValueError:
            return create_error_response(400, "Invalid vehicle ID format")
        
        # Get database connection
        db = get_database_connection()
        
        # Soft delete by setting status to retired
        sql = """
        UPDATE vehicles
        SET status = 'retired'
        WHERE id = :id::uuid AND status != 'retired'
        RETURNING id
        """
        
        # Prepare parameters
        parameters = [db.create_parameter('id', vehicle_id)]
        
        # Execute query
        response = db.execute_query(sql, parameters)
        
        # Check if vehicle was found and updated
        vehicles = db.format_results(response)
        if vehicles:
            logger.info(f"Vehicle deleted (retired) successfully: {vehicle_id}")
            return create_success_response(200, {'message': 'Vehicle retired successfully', 'id': vehicle_id})
        else:
            return create_error_response(404, "Vehicle not found or already retired")
            
    except Exception as e:
        logger.error(f"Delete vehicle error: {str(e)}")
        return create_error_response(500, f"Failed to delete vehicle: {str(e)}")


def create_success_response(status_code: int, data: Any) -> Dict[str, Any]:
    """
    Create a successful API response
    
    Args:
        status_code: HTTP status code
        data: Response data
        
    Returns:
        dict: API Gateway response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(data, default=str, indent=2)
    }


def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """
    Create an error API response
    
    Args:
        status_code: HTTP status code
        message: Error message
        
    Returns:
        dict: API Gateway response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps({
            'error': message,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }, indent=2)
    }


def add_service_record(vehicle_id: str, service_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a service record for a vehicle
    
    Args:
        vehicle_id: Vehicle UUID
        service_data: Service record information
        
    Returns:
        dict: API response with created service record
    """
    try:
        # Validate UUID format
        try:
            uuid.UUID(vehicle_id)
        except ValueError:
            return create_error_response(400, "Invalid vehicle ID format")
        
        # Validate required fields
        required_fields = ['maintenance_type_id', 'description', 'cost', 'service_date', 'service_provider']
        for field in required_fields:
            if field not in service_data or not service_data[field]:
                return create_error_response(400, f"Missing required field: {field}")
        
        # Validate cost
        try:
            cost = float(service_data['cost'])
            if cost < 0:
                return create_error_response(400, "Cost must be non-negative")
        except (ValueError, TypeError):
            return create_error_response(400, "Cost must be a valid number")
        
        # Validate maintenance_type_id
        try:
            maintenance_type_id = int(service_data['maintenance_type_id'])
        except (ValueError, TypeError):
            return create_error_response(400, "Maintenance type ID must be a valid integer")
        
        # Validate service_date format (YYYY-MM-DD)
        try:
            datetime.strptime(service_data['service_date'], '%Y-%m-%d')
        except ValueError:
            return create_error_response(400, "Service date must be in YYYY-MM-DD format")
        
        # Get database connection
        db = get_database_connection()
        
        # First, verify the vehicle exists
        vehicle_check_sql = "SELECT id FROM vehicles WHERE id = :vehicle_id::uuid"
        vehicle_check_params = [db.create_parameter('vehicle_id', vehicle_id)]
        vehicle_response = db.execute_query(vehicle_check_sql, vehicle_check_params)
        
        if not db.format_results(vehicle_response):
            return create_error_response(404, "Vehicle not found")
        
        # Generate UUID for the service record
        service_record_id = str(uuid.uuid4())
        
        # Prepare SQL statement
        sql = """
        INSERT INTO service_records (
            id, vehicle_id, driver_id, maintenance_type_id, description, cost, 
            service_date, mileage, service_provider, is_warranty, next_service_due, 
            receipt_url, notes
        )
        VALUES (
            :id::uuid, :vehicle_id::uuid, :driver_id::uuid, :maintenance_type_id, 
            :description, :cost, :service_date::date, :mileage, :service_provider, 
            CASE WHEN :is_warranty = 1 THEN true ELSE false END, :next_service_due::date, :receipt_url, :notes
        )
        RETURNING id, vehicle_id, driver_id, maintenance_type_id, description, cost, 
                  service_date, mileage, service_provider, is_warranty, next_service_due, 
                  receipt_url, notes, created_at, updated_at
        """
        
        # Prepare parameters
        parameters = [
            db.create_parameter('id', service_record_id),
            db.create_parameter('vehicle_id', vehicle_id),
            db.create_parameter('driver_id', service_data.get('driver_id')),
            db.create_parameter('maintenance_type_id', maintenance_type_id),
            db.create_parameter('description', service_data['description']),
            db.create_parameter('cost', cost),
            db.create_parameter('service_date', service_data['service_date']),
            db.create_parameter('mileage', service_data.get('mileage')),
            db.create_parameter('service_provider', service_data['service_provider']),
            db.create_parameter('is_warranty', 1 if service_data.get('is_warranty', False) else 0),
            db.create_parameter('next_service_due', service_data.get('next_service_due')),
            db.create_parameter('receipt_url', service_data.get('receipt_url')),
            db.create_parameter('notes', service_data.get('notes'))
        ]
        
        # Execute query
        response = db.execute_query(sql, parameters)
        
        # Format and return result
        service_records = db.format_results(response)
        if service_records:
            logger.info(f"Service record created successfully: {service_record_id}")
            return create_success_response(201, service_records[0])
        else:
            return create_error_response(500, "Failed to create service record")
            
    except Exception as e:
        logger.error(f"Add service record error: {str(e)}")
        return create_error_response(500, f"Failed to add service record: {str(e)}")


def get_service_history(vehicle_id: str, query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Get service history for a vehicle
    
    Args:
        vehicle_id: Vehicle UUID
        query_params: Query parameters for filtering
        
    Returns:
        dict: API response with service history
    """
    try:
        # Validate UUID format
        try:
            uuid.UUID(vehicle_id)
        except ValueError:
            return create_error_response(400, "Invalid vehicle ID format")
        
        # Get database connection
        db = get_database_connection()
        
        # Build SQL query with joins to get maintenance type names
        sql = """
        SELECT 
            sr.id, sr.vehicle_id, sr.driver_id, sr.maintenance_type_id, 
            mt.type_name as maintenance_type_name, mt.description as maintenance_type_description,
            sr.description, sr.cost, sr.service_date, sr.mileage, sr.service_provider, 
            sr.is_warranty, sr.next_service_due, sr.receipt_url, sr.notes, 
            sr.created_at, sr.updated_at
        FROM service_records sr
        JOIN maintenance_types mt ON sr.maintenance_type_id = mt.id
        WHERE sr.vehicle_id = :vehicle_id::uuid
        """
        parameters = [db.create_parameter('vehicle_id', vehicle_id)]
        
        # Add filters based on query parameters
        if query_params.get('maintenance_type'):
            sql += " AND mt.type_name = :maintenance_type"
            parameters.append(db.create_parameter('maintenance_type', query_params['maintenance_type']))
        
        if query_params.get('from_date'):
            sql += " AND sr.service_date >= :from_date"
            parameters.append(db.create_parameter('from_date', query_params['from_date']))
        
        if query_params.get('to_date'):
            sql += " AND sr.service_date <= :to_date"
            parameters.append(db.create_parameter('to_date', query_params['to_date']))
        
        if query_params.get('min_cost'):
            sql += " AND sr.cost >= :min_cost"
            parameters.append(db.create_parameter('min_cost', float(query_params['min_cost'])))
        
        if query_params.get('max_cost'):
            sql += " AND sr.cost <= :max_cost"
            parameters.append(db.create_parameter('max_cost', float(query_params['max_cost'])))
        
        # Add ordering
        sql += " ORDER BY sr.service_date DESC, sr.created_at DESC"
        
        # Add pagination
        limit = min(int(query_params.get('limit', 50)), 100)  # Max 100 items
        offset = int(query_params.get('offset', 0))
        
        sql += " LIMIT :limit OFFSET :offset"
        parameters.extend([
            db.create_parameter('limit', limit),
            db.create_parameter('offset', offset)
        ])
        
        # Execute query
        response = db.execute_query(sql, parameters)
        
        # Format results
        service_records = db.format_results(response)
        
        # Manual mapping for service records (RDS Data API column metadata issue)
        mapped_records = []
        for record in service_records:
            mapped_record = {
                'id': record.get('id') or record.get('column_0'),
                'vehicle_id': record.get('vehicle_id') or record.get('column_1'),
                'driver_id': record.get('driver_id') or record.get('column_2'),
                'maintenance_type_id': record.get('maintenance_type_id') or record.get('column_3'),
                'maintenance_type_name': record.get('maintenance_type_name') or record.get('column_4'),
                'maintenance_type_description': record.get('maintenance_type_description') or record.get('column_5'),
                'description': record.get('description') or record.get('column_6'),
                'cost': record.get('cost') or record.get('column_7'),
                'service_date': record.get('service_date') or record.get('column_8'),
                'mileage': record.get('mileage') or record.get('column_9'),
                'service_provider': record.get('service_provider') or record.get('column_10'),
                'is_warranty': record.get('is_warranty') or record.get('column_11'),
                'next_service_due': record.get('next_service_due') or record.get('column_12'),
                'receipt_url': record.get('receipt_url') or record.get('column_13'),
                'notes': record.get('notes') or record.get('column_14'),
                'created_at': record.get('created_at') or record.get('column_15'),
                'updated_at': record.get('updated_at') or record.get('column_16')
            }
            mapped_records.append(mapped_record)
        
        service_records = mapped_records
        
        # Calculate total cost
        total_cost = sum(float(record.get('cost', 0)) for record in service_records)
        
        logger.info(f"Retrieved {len(service_records)} service records for vehicle {vehicle_id}")
        return create_success_response(200, {
            'vehicle_id': vehicle_id,
            'service_records': service_records,
            'count': len(service_records),
            'total_cost': total_cost,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Get service history error: {str(e)}")
        return create_error_response(500, f"Failed to retrieve service history: {str(e)}")


def get_maintenance_alerts(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Get maintenance alerts for vehicles that need attention
    
    Args:
        query_params: Query parameters for filtering
        
    Returns:
        dict: API response with maintenance alerts
    """
    try:
        # Get database connection
        db = get_database_connection()
        
        # Get current date for calculations
        current_date = datetime.now().date()
        
        # Build SQL query to find vehicles needing maintenance
        sql = """
        WITH vehicle_last_service AS (
            SELECT 
                v.id as vehicle_id,
                v.make,
                v.model,
                v.registration,
                v.status,
                sr.service_date as last_service_date,
                sr.next_service_due,
                sr.cost as last_service_cost,
                mt.type_name as last_maintenance_type,
                ROW_NUMBER() OVER (PARTITION BY v.id ORDER BY sr.service_date DESC) as rn
            FROM vehicles v
            LEFT JOIN service_records sr ON v.id = sr.vehicle_id
            LEFT JOIN maintenance_types mt ON sr.maintenance_type_id = mt.id
            WHERE v.status IN ('active', 'in_service')
        ),
        high_cost_vehicles AS (
            SELECT 
                vehicle_id,
                SUM(cost) as total_cost,
                COUNT(*) as service_count,
                AVG(cost) as avg_cost
            FROM service_records 
            WHERE service_date >= CURRENT_DATE - INTERVAL '12 months'
            GROUP BY vehicle_id
            HAVING SUM(cost) > 15000 OR AVG(cost) > 3000
        )
        SELECT 
            vls.vehicle_id,
            vls.make,
            vls.model,
            vls.registration,
            vls.last_service_date,
            vls.next_service_due,
            vls.last_service_cost,
            vls.last_maintenance_type,
            hcv.total_cost,
            hcv.service_count,
            hcv.avg_cost,
            CASE 
                WHEN vls.next_service_due IS NOT NULL AND vls.next_service_due <= CURRENT_DATE + INTERVAL '7 days' THEN 'overdue_service'
                WHEN vls.last_service_date IS NULL THEN 'no_service_history'
                WHEN vls.last_service_date < CURRENT_DATE - INTERVAL '6 months' THEN 'service_overdue'
                WHEN hcv.vehicle_id IS NOT NULL THEN 'high_maintenance_cost'
                ELSE 'no_alert'
            END as alert_type,
            CASE 
                WHEN vls.next_service_due IS NOT NULL AND vls.next_service_due <= CURRENT_DATE + INTERVAL '7 days' THEN 'Service due within 7 days'
                WHEN vls.last_service_date IS NULL THEN 'No service history found'
                WHEN vls.last_service_date < CURRENT_DATE - INTERVAL '6 months' THEN 'No service in last 6 months'
                WHEN hcv.vehicle_id IS NOT NULL THEN 'High maintenance costs detected'
                ELSE 'No alerts'
            END as alert_message
        FROM vehicle_last_service vls
        LEFT JOIN high_cost_vehicles hcv ON vls.vehicle_id = hcv.vehicle_id
        WHERE vls.rn = 1 OR vls.rn IS NULL
        """
        
        # Add filters based on query parameters
        parameters = []
        
        if query_params.get('alert_type'):
            sql += " AND (CASE WHEN vls.next_service_due IS NOT NULL AND vls.next_service_due <= CURRENT_DATE + INTERVAL '7 days' THEN 'overdue_service' WHEN vls.last_service_date IS NULL THEN 'no_service_history' WHEN vls.last_service_date < CURRENT_DATE - INTERVAL '6 months' THEN 'service_overdue' WHEN hcv.vehicle_id IS NOT NULL THEN 'high_maintenance_cost' ELSE 'no_alert' END) = :alert_type"
            parameters.append(db.create_parameter('alert_type', query_params['alert_type']))
        
        if query_params.get('vehicle_id'):
            sql += " AND vls.vehicle_id = :vehicle_id"
            parameters.append(db.create_parameter('vehicle_id', query_params['vehicle_id']))
        
        # Only show vehicles with actual alerts unless specifically requested
        if query_params.get('include_no_alerts') != 'true':
            sql += " AND (CASE WHEN vls.next_service_due IS NOT NULL AND vls.next_service_due <= CURRENT_DATE + INTERVAL '7 days' THEN 'overdue_service' WHEN vls.last_service_date IS NULL THEN 'no_service_history' WHEN vls.last_service_date < CURRENT_DATE - INTERVAL '6 months' THEN 'service_overdue' WHEN hcv.vehicle_id IS NOT NULL THEN 'high_maintenance_cost' ELSE 'no_alert' END) != 'no_alert'"
        
        # Add ordering
        sql += " ORDER BY vls.next_service_due ASC NULLS LAST, vls.last_service_date ASC NULLS LAST"
        
        # Add pagination
        limit = min(int(query_params.get('limit', 50)), 100)  # Max 100 items
        offset = int(query_params.get('offset', 0))
        
        sql += " LIMIT :limit OFFSET :offset"
        parameters.extend([
            db.create_parameter('limit', limit),
            db.create_parameter('offset', offset)
        ])
        
        # Execute query
        response = db.execute_query(sql, parameters)
        
        # Format results
        alerts = db.format_results(response)
        
        # Manual mapping for maintenance alerts (RDS Data API column metadata issue)
        mapped_alerts = []
        for alert in alerts:
            mapped_alert = {
                'vehicle_id': alert.get('vehicle_id') or alert.get('column_0'),
                'make': alert.get('make') or alert.get('column_1'),
                'model': alert.get('model') or alert.get('column_2'),
                'registration': alert.get('registration') or alert.get('column_3'),
                'last_service_date': alert.get('last_service_date') or alert.get('column_4'),
                'next_service_due': alert.get('next_service_due') or alert.get('column_5'),
                'last_service_cost': alert.get('last_service_cost') or alert.get('column_6'),
                'last_maintenance_type': alert.get('last_maintenance_type') or alert.get('column_7'),
                'total_cost': alert.get('total_cost') or alert.get('column_8'),
                'service_count': alert.get('service_count') or alert.get('column_9'),
                'avg_cost': alert.get('avg_cost') or alert.get('column_10'),
                'alert_type': alert.get('alert_type') or alert.get('column_11'),
                'alert_message': alert.get('alert_message') or alert.get('column_12')
            }
            mapped_alerts.append(mapped_alert)
        
        alerts = mapped_alerts
        
        # Group alerts by type for summary
        alert_summary = {}
        for alert in alerts:
            alert_type = alert.get('alert_type', 'unknown')
            if alert_type not in alert_summary:
                alert_summary[alert_type] = 0
            alert_summary[alert_type] += 1
        
        logger.info(f"Retrieved {len(alerts)} maintenance alerts")
        return create_success_response(200, {
            'alerts': alerts,
            'count': len(alerts),
            'summary': alert_summary,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Get maintenance alerts error: {str(e)}")
        return create_error_response(500, f"Failed to retrieve maintenance alerts: {str(e)}")


def get_cost_analysis(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Get cost analysis for vehicles with breakdown by maintenance type
    
    Args:
        query_params: Query parameters for filtering
        
    Returns:
        dict: API response with cost analysis data
    """
    try:
        # Get database connection
        db = get_database_connection()
        
        # Build SQL query for cost analysis by maintenance type
        sql = """
        WITH cost_by_type AS (
            SELECT 
                v.id as vehicle_id,
                v.make,
                v.model,
                v.registration,
                mt.type_name as maintenance_type,
                mt.description as maintenance_type_description,
                COUNT(sr.id) as service_count,
                SUM(sr.cost) as total_cost,
                AVG(sr.cost) as avg_cost,
                MIN(sr.cost) as min_cost,
                MAX(sr.cost) as max_cost,
                MIN(sr.service_date) as first_service,
                MAX(sr.service_date) as last_service
            FROM vehicles v
            LEFT JOIN service_records sr ON v.id = sr.vehicle_id
            LEFT JOIN maintenance_types mt ON sr.maintenance_type_id = mt.id
            WHERE v.status IN ('active', 'in_service', 'out_of_order')
        """
        
        parameters = []
        
        # Add date filters
        if query_params.get('from_date'):
            sql += " AND sr.service_date >= :from_date"
            parameters.append(db.create_parameter('from_date', query_params['from_date']))
        
        if query_params.get('to_date'):
            sql += " AND sr.service_date <= :to_date"
            parameters.append(db.create_parameter('to_date', query_params['to_date']))
        
        # Add vehicle filter
        if query_params.get('vehicle_id'):
            sql += " AND v.id = :vehicle_id::uuid"
            parameters.append(db.create_parameter('vehicle_id', query_params['vehicle_id']))
        
        # Add maintenance type filter
        if query_params.get('maintenance_type'):
            sql += " AND mt.type_name = :maintenance_type"
            parameters.append(db.create_parameter('maintenance_type', query_params['maintenance_type']))
        
        sql += """
            GROUP BY v.id, v.make, v.model, v.registration, mt.type_name, mt.description
            HAVING COUNT(sr.id) > 0
        ),
        fleet_averages AS (
            SELECT 
                maintenance_type,
                AVG(total_cost) as fleet_avg_cost,
                AVG(service_count) as fleet_avg_count
            FROM cost_by_type
            GROUP BY maintenance_type
        )
        SELECT 
            cbt.*,
            fa.fleet_avg_cost,
            fa.fleet_avg_count,
            CASE 
                WHEN cbt.total_cost > fa.fleet_avg_cost * 1.2 THEN 'high'
                WHEN cbt.total_cost < fa.fleet_avg_cost * 0.8 THEN 'low'
                ELSE 'normal'
            END as cost_category
        FROM cost_by_type cbt
        LEFT JOIN fleet_averages fa ON cbt.maintenance_type = fa.maintenance_type
        ORDER BY cbt.total_cost DESC, cbt.vehicle_id, cbt.maintenance_type
        """
        
        # Add pagination
        limit = min(int(query_params.get('limit', 100)), 200)  # Max 200 items for analysis
        offset = int(query_params.get('offset', 0))
        
        sql += " LIMIT :limit OFFSET :offset"
        parameters.extend([
            db.create_parameter('limit', limit),
            db.create_parameter('offset', offset)
        ])
        
        # Execute query
        response = db.execute_query(sql, parameters)
        
        # Format results
        cost_analysis = db.format_results(response)
        
        # Calculate summary statistics
        total_vehicles = len(set(item.get('vehicle_id') for item in cost_analysis))
        total_cost = sum(float(item.get('total_cost', 0)) for item in cost_analysis)
        total_services = sum(int(item.get('service_count', 0)) for item in cost_analysis)
        
        # Group by maintenance type for summary
        type_summary = {}
        for item in cost_analysis:
            maintenance_type = item.get('maintenance_type', 'unknown')
            if maintenance_type not in type_summary:
                type_summary[maintenance_type] = {
                    'total_cost': 0,
                    'service_count': 0,
                    'vehicle_count': 0,
                    'vehicles': set()
                }
            
            type_summary[maintenance_type]['total_cost'] += float(item.get('total_cost', 0))
            type_summary[maintenance_type]['service_count'] += int(item.get('service_count', 0))
            type_summary[maintenance_type]['vehicles'].add(item.get('vehicle_id'))
        
        # Convert sets to counts
        for type_name in type_summary:
            type_summary[type_name]['vehicle_count'] = len(type_summary[type_name]['vehicles'])
            del type_summary[type_name]['vehicles']
        
        logger.info(f"Retrieved cost analysis for {total_vehicles} vehicles")
        return create_success_response(200, {
            'cost_analysis': cost_analysis,
            'summary': {
                'total_vehicles': total_vehicles,
                'total_cost': total_cost,
                'total_services': total_services,
                'avg_cost_per_vehicle': total_cost / total_vehicles if total_vehicles > 0 else 0,
                'avg_cost_per_service': total_cost / total_services if total_services > 0 else 0
            },
            'by_maintenance_type': type_summary,
            'count': len(cost_analysis),
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Get cost analysis error: {str(e)}")
        return create_error_response(500, f"Failed to retrieve cost analysis: {str(e)}")


def get_fleet_cost_comparison(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Get fleet-wide cost comparison across all vehicles
    
    Args:
        query_params: Query parameters for filtering
        
    Returns:
        dict: API response with fleet cost comparison data
    """
    try:
        # Get database connection
        db = get_database_connection()
        
        # Build SQL query for fleet cost comparison
        sql = """
        WITH vehicle_costs AS (
            SELECT 
                v.id as vehicle_id,
                v.make,
                v.model,
                v.registration,
                v.year,
                COUNT(sr.id) as total_services,
                COALESCE(SUM(sr.cost), 0) as total_cost,
                COALESCE(AVG(sr.cost), 0) as avg_service_cost,
                MIN(sr.service_date) as first_service_date,
                MAX(sr.service_date) as last_service_date,
                COALESCE(MAX(sr.service_date) - MIN(sr.service_date) + 1, 0) as service_period_days
            FROM vehicles v
            LEFT JOIN service_records sr ON v.id = sr.vehicle_id
            WHERE v.status IN ('active', 'in_service', 'out_of_order')
        """
        
        parameters = []
        
        # Add date filters
        if query_params.get('from_date'):
            sql += " AND (sr.service_date >= :from_date OR sr.service_date IS NULL)"
            parameters.append(db.create_parameter('from_date', query_params['from_date']))
        
        if query_params.get('to_date'):
            sql += " AND (sr.service_date <= :to_date OR sr.service_date IS NULL)"
            parameters.append(db.create_parameter('to_date', query_params['to_date']))
        
        sql += """
            GROUP BY v.id, v.make, v.model, v.registration, v.year
        ),
        fleet_stats AS (
            SELECT 
                AVG(total_cost) as fleet_avg_cost,
                STDDEV(total_cost) as fleet_stddev_cost,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_cost) as fleet_median_cost,
                MAX(total_cost) as fleet_max_cost,
                MIN(total_cost) as fleet_min_cost
            FROM vehicle_costs
            WHERE total_services > 0
        )
        SELECT 
            vc.*,
            fs.fleet_avg_cost,
            fs.fleet_median_cost,
            fs.fleet_max_cost,
            fs.fleet_min_cost,
            CASE 
                WHEN vc.total_cost > fs.fleet_avg_cost * 1.2 THEN 'high_cost'
                WHEN vc.total_cost < fs.fleet_avg_cost * 0.8 THEN 'low_cost'
                ELSE 'normal_cost'
            END as cost_category,
            CASE 
                WHEN vc.total_services = 0 THEN 0
                ELSE ROUND((vc.total_cost / NULLIF(vc.service_period_days, 0)) * 30, 2)
            END as estimated_monthly_cost,
            ROUND(((vc.total_cost - fs.fleet_avg_cost) / NULLIF(fs.fleet_avg_cost, 0)) * 100, 2) as cost_variance_percent
        FROM vehicle_costs vc
        CROSS JOIN fleet_stats fs
        ORDER BY vc.total_cost DESC
        """
        
        # Add pagination
        limit = min(int(query_params.get('limit', 50)), 100)  # Max 100 vehicles
        offset = int(query_params.get('offset', 0))
        
        sql += " LIMIT :limit OFFSET :offset"
        parameters.extend([
            db.create_parameter('limit', limit),
            db.create_parameter('offset', offset)
        ])
        
        # Execute query
        response = db.execute_query(sql, parameters)
        
        # Format results
        fleet_comparison = db.format_results(response)
        
        # Calculate additional statistics
        vehicles_with_service = [v for v in fleet_comparison if int(v.get('total_services', 0)) > 0]
        high_cost_vehicles = [v for v in vehicles_with_service if v.get('cost_category') == 'high_cost']
        low_cost_vehicles = [v for v in vehicles_with_service if v.get('cost_category') == 'low_cost']
        
        fleet_summary = {
            'total_vehicles': len(fleet_comparison),
            'vehicles_with_service': len(vehicles_with_service),
            'high_cost_vehicles': len(high_cost_vehicles),
            'low_cost_vehicles': len(low_cost_vehicles),
            'normal_cost_vehicles': len(vehicles_with_service) - len(high_cost_vehicles) - len(low_cost_vehicles)
        }
        
        if vehicles_with_service:
            fleet_summary.update({
                'fleet_total_cost': sum(float(v.get('total_cost', 0)) for v in vehicles_with_service),
                'fleet_avg_cost': sum(float(v.get('total_cost', 0)) for v in vehicles_with_service) / len(vehicles_with_service),
                'fleet_total_services': sum(int(v.get('total_services', 0)) for v in vehicles_with_service)
            })
        
        logger.info(f"Retrieved fleet cost comparison for {len(fleet_comparison)} vehicles")
        return create_success_response(200, {
            'fleet_comparison': fleet_comparison,
            'fleet_summary': fleet_summary,
            'high_cost_vehicles': [v.get('vehicle_id') for v in high_cost_vehicles],
            'count': len(fleet_comparison),
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Get fleet cost comparison error: {str(e)}")
        return create_error_response(500, f"Failed to retrieve fleet cost comparison: {str(e)}")


def get_high_cost_alerts(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Get high maintenance cost alerts for vehicles exceeding fleet average by 20%
    
    Args:
        query_params: Query parameters for filtering
        
    Returns:
        dict: API response with high cost alerts
    """
    try:
        # Get database connection
        db = get_database_connection()
        
        # Build SQL query for high cost alerts
        sql = """
        WITH vehicle_costs AS (
            SELECT 
                v.id as vehicle_id,
                v.make,
                v.model,
                v.registration,
                COUNT(sr.id) as service_count,
                SUM(sr.cost) as total_cost,
                AVG(sr.cost) as avg_service_cost,
                MAX(sr.service_date) as last_service_date,
                STRING_AGG(DISTINCT mt.type_name, ', ' ORDER BY mt.type_name) as maintenance_types
            FROM vehicles v
            JOIN service_records sr ON v.id = sr.vehicle_id
            JOIN maintenance_types mt ON sr.maintenance_type_id = mt.id
            WHERE v.status IN ('active', 'in_service', 'out_of_order')
        """
        
        parameters = []
        
        # Add date filters (default to last 12 months if not specified)
        from_date = query_params.get('from_date')
        if not from_date:
            from datetime import timedelta
            from_date = (datetime.now().date() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        sql += " AND sr.service_date >= :from_date::date"
        parameters.append(db.create_parameter('from_date', from_date))
        
        if query_params.get('to_date'):
            sql += " AND sr.service_date <= :to_date::date"
            parameters.append(db.create_parameter('to_date', query_params['to_date']))
        
        sql += """
            GROUP BY v.id, v.make, v.model, v.registration
            HAVING COUNT(sr.id) > 0
        ),
        fleet_average AS (
            SELECT AVG(total_cost) as avg_fleet_cost
            FROM vehicle_costs
        )
        SELECT 
            vc.*,
            fa.avg_fleet_cost,
            ROUND(((vc.total_cost - fa.avg_fleet_cost) / fa.avg_fleet_cost) * 100, 2) as cost_variance_percent,
            CASE 
                WHEN vc.total_cost > fa.avg_fleet_cost * 1.5 THEN 'critical'
                WHEN vc.total_cost > fa.avg_fleet_cost * 1.3 THEN 'high'
                WHEN vc.total_cost > fa.avg_fleet_cost * 1.2 THEN 'moderate'
                ELSE 'normal'
            END as alert_severity,
            CASE 
                WHEN vc.total_cost > fa.avg_fleet_cost * 1.5 THEN 'Vehicle maintenance costs are critically high (>50% above fleet average)'
                WHEN vc.total_cost > fa.avg_fleet_cost * 1.3 THEN 'Vehicle maintenance costs are significantly high (>30% above fleet average)'
                WHEN vc.total_cost > fa.avg_fleet_cost * 1.2 THEN 'Vehicle maintenance costs are moderately high (>20% above fleet average)'
                ELSE 'Vehicle maintenance costs are within normal range'
            END as alert_message
        FROM vehicle_costs vc
        CROSS JOIN fleet_average fa
        WHERE vc.total_cost > fa.avg_fleet_cost * 1.2
        ORDER BY vc.total_cost DESC
        """
        
        # Add pagination
        limit = min(int(query_params.get('limit', 50)), 100)
        offset = int(query_params.get('offset', 0))
        
        sql += " LIMIT :limit OFFSET :offset"
        parameters.extend([
            db.create_parameter('limit', limit),
            db.create_parameter('offset', offset)
        ])
        
        # Execute query
        response = db.execute_query(sql, parameters)
        
        # Format results
        high_cost_alerts = db.format_results(response)
        
        # Group alerts by severity
        alert_summary = {
            'critical': 0,
            'high': 0,
            'moderate': 0
        }
        
        for alert in high_cost_alerts:
            severity = alert.get('alert_severity', 'moderate')
            if severity in alert_summary:
                alert_summary[severity] += 1
        
        # Calculate total excess cost
        total_excess_cost = 0
        fleet_avg = float(high_cost_alerts[0].get('avg_fleet_cost', 0)) if high_cost_alerts else 0
        
        for alert in high_cost_alerts:
            vehicle_cost = float(alert.get('total_cost', 0))
            if vehicle_cost > fleet_avg:
                total_excess_cost += (vehicle_cost - fleet_avg)
        
        logger.info(f"Retrieved {len(high_cost_alerts)} high cost alerts")
        return create_success_response(200, {
            'high_cost_alerts': high_cost_alerts,
            'alert_summary': alert_summary,
            'fleet_average_cost': fleet_avg,
            'total_excess_cost': total_excess_cost,
            'analysis_period': {
                'from_date': from_date,
                'to_date': query_params.get('to_date', datetime.now().date().strftime('%Y-%m-%d'))
            },
            'count': len(high_cost_alerts),
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Get high cost alerts error: {str(e)}")
        return create_error_response(500, f"Failed to retrieve high cost alerts: {str(e)}")