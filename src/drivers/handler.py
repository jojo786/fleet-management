"""
Driver Management Lambda Function for FLEET System
Handles driver onboarding, assignments, and performance tracking
"""

import json
import logging
import os
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal

# Import database utilities
import sys
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.db_utils import get_database_connection

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for driver management operations
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        dict: API Gateway response
    """
    try:
        logger.info(f"Driver management request: {json.dumps(event, default=str)}")
        
        # Extract request information
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        body = event.get('body', '{}')
        
        # Parse request body if present
        request_data = {}
        if body and body != '{}':
            try:
                request_data = json.loads(body)
            except json.JSONDecodeError:
                return create_response(400, {'error': 'Invalid JSON in request body'})
        
        # Route the request
        if path == '/drivers' and http_method == 'GET':
            return list_drivers(query_parameters)
        elif path == '/drivers' and http_method == 'POST':
            return create_driver(request_data)
        # More specific routes first (assignments, performance)
        elif path.startswith('/drivers/') and path.endswith('/assignments') and http_method == 'GET':
            driver_id = path_parameters.get('id')
            if not driver_id:
                return create_response(400, {'error': 'Driver ID is required'})
            return get_driver_assignments(driver_id, query_parameters)
        elif path.startswith('/drivers/') and path.endswith('/assignments') and http_method == 'POST':
            driver_id = path_parameters.get('id')
            if not driver_id:
                return create_response(400, {'error': 'Driver ID is required'})
            return assign_vehicle(driver_id, request_data)
        elif path.startswith('/drivers/') and path.endswith('/performance') and http_method == 'GET':
            driver_id = path_parameters.get('id')
            if not driver_id:
                return create_response(400, {'error': 'Driver ID is required'})
            return get_driver_performance(driver_id, query_parameters)
        elif path.startswith('/drivers/') and path.endswith('/performance') and http_method == 'POST':
            driver_id = path_parameters.get('id')
            if not driver_id:
                return create_response(400, {'error': 'Driver ID is required'})
            return record_performance(driver_id, request_data)
        # Generic driver routes last
        elif path.startswith('/drivers/') and http_method == 'GET':
            driver_id = path_parameters.get('id')
            if not driver_id:
                return create_response(400, {'error': 'Driver ID is required'})
            return get_driver(driver_id, query_parameters)
        elif path.startswith('/drivers/') and http_method == 'PUT':
            driver_id = path_parameters.get('id')
            if not driver_id:
                return create_response(400, {'error': 'Driver ID is required'})
            return update_driver(driver_id, request_data)
        elif path.startswith('/drivers/') and http_method == 'DELETE':
            driver_id = path_parameters.get('id')
            if not driver_id:
                return create_response(400, {'error': 'Driver ID is required'})
            return delete_driver(driver_id)
        else:
            return create_response(404, {'error': 'Endpoint not found'})
            
    except Exception as e:
        logger.error(f"Unexpected error in driver management: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create standardized API Gateway response
    
    Args:
        status_code: HTTP status code
        body: Response body
        
    Returns:
        dict: API Gateway response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(body, default=str)
    }


def list_drivers(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    List all drivers with optional filtering
    
    Args:
        query_params: Query parameters for filtering
        
    Returns:
        dict: API Gateway response with drivers list
    """
    try:
        db = get_database_connection()
        
        # Build query with optional filters
        where_conditions = []
        parameters = []
        
        # Filter by status
        if query_params.get('status'):
            where_conditions.append("d.status = :status")
            parameters.append(db.create_parameter('status', query_params['status']))
        
        # Filter by active assignments
        if query_params.get('has_assignment') == 'true':
            where_conditions.append("""
                EXISTS (
                    SELECT 1 FROM driver_assignments da 
                    WHERE da.driver_id = d.id 
                    AND da.status = 'active'
                )
            """)
        elif query_params.get('has_assignment') == 'false':
            where_conditions.append("""
                NOT EXISTS (
                    SELECT 1 FROM driver_assignments da 
                    WHERE da.driver_id = d.id 
                    AND da.status = 'active'
                )
            """)
        
        # Build WHERE clause
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Execute query
        sql = f"""
            SELECT 
                d.id,
                d.first_name,
                d.last_name,
                d.email,
                d.phone,
                d.id_number,
                d.license_number,
                d.license_expiry_date,
                d.address,
                d.status,
                d.emergency_contact,
                d.created_at,
                d.updated_at,
                -- Current assignment info
                da.vehicle_id as current_vehicle_id,
                v.make as current_vehicle_make,
                v.model as current_vehicle_model,
                v.registration as current_vehicle_registration
            FROM drivers d
            LEFT JOIN driver_assignments da ON d.id = da.driver_id AND da.status = 'active'
            LEFT JOIN vehicles v ON da.vehicle_id = v.id
            {where_clause}
            ORDER BY d.last_name, d.first_name
        """
        
        response = db.execute_query(sql, parameters)
        drivers = db.format_results(response)
        
        logger.info(f"Retrieved {len(drivers)} drivers")
        
        return create_response(200, {
            'drivers': drivers,
            'count': len(drivers)
        })
        
    except Exception as e:
        logger.error(f"Error listing drivers: {str(e)}")
        return create_response(500, {'error': 'Failed to retrieve drivers'})


def create_driver(driver_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new driver
    
    Args:
        driver_data: Driver information
        
    Returns:
        dict: API Gateway response with created driver
    """
    try:
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'phone', 'id_number', 'license_number', 'license_expiry_date', 'address']
        for field in required_fields:
            if not driver_data.get(field):
                return create_response(400, {'error': f'Missing required field: {field}'})
        
        # Validate license expiry date
        try:
            license_expiry = datetime.strptime(driver_data['license_expiry_date'], '%Y-%m-%d').date()
            if license_expiry <= date.today():
                return create_response(400, {'error': 'License expiry date must be in the future'})
        except ValueError:
            return create_response(400, {'error': 'Invalid license expiry date format. Use YYYY-MM-DD'})
        
        # Validate address structure
        address = driver_data.get('address', {})
        if not isinstance(address, dict) or not address.get('street') or not address.get('city'):
            return create_response(400, {'error': 'Address must include street and city'})
        
        db = get_database_connection()
        
        # Generate driver ID
        driver_id = str(uuid.uuid4())
        
        # Prepare parameters
        parameters = [
            db.create_parameter('id', driver_id),
            db.create_parameter('first_name', driver_data['first_name'].strip()),
            db.create_parameter('last_name', driver_data['last_name'].strip()),
            db.create_parameter('email', driver_data.get('email', '').strip() or None),
            db.create_parameter('phone', driver_data['phone'].strip()),
            db.create_parameter('id_number', driver_data['id_number'].strip()),
            db.create_parameter('license_number', driver_data['license_number'].strip()),
            db.create_parameter('license_expiry_date', driver_data['license_expiry_date']),
            db.create_parameter('address', json.dumps(address)),
            db.create_parameter('emergency_contact', json.dumps(driver_data.get('emergency_contact', {}))),
            db.create_parameter('status', driver_data.get('status', 'active'))
        ]
        
        # Insert driver
        sql = """
            INSERT INTO drivers (
                id, first_name, last_name, email, phone, id_number, 
                license_number, license_expiry_date, address, emergency_contact, status
            ) VALUES (
                :id::uuid, :first_name, :last_name, :email, :phone, :id_number,
                :license_number, :license_expiry_date::date, :address::jsonb, :emergency_contact::jsonb, :status
            )
        """
        
        db.execute_query(sql, parameters)
        
        # Retrieve the created driver
        return get_driver(driver_id, {})
        
    except Exception as e:
        logger.error(f"Error creating driver: {str(e)}")
        if "duplicate key" in str(e).lower():
            if "id_number" in str(e):
                return create_response(409, {'error': 'Driver with this ID number already exists'})
            elif "license_number" in str(e):
                return create_response(409, {'error': 'Driver with this license number already exists'})
            elif "email" in str(e):
                return create_response(409, {'error': 'Driver with this email already exists'})
        return create_response(500, {'error': 'Failed to create driver'})


def get_driver(driver_id: str, query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Get driver by ID with optional related data
    
    Args:
        driver_id: Driver ID
        query_params: Query parameters for including related data
        
    Returns:
        dict: API Gateway response with driver data
    """
    try:
        db = get_database_connection()
        
        # Get driver basic information
        sql = """
            SELECT 
                d.id,
                d.first_name,
                d.last_name,
                d.email,
                d.phone,
                d.id_number,
                d.license_number,
                d.license_expiry_date,
                d.address,
                d.status,
                d.emergency_contact,
                d.created_at,
                d.updated_at
            FROM drivers d
            WHERE d.id = :driver_id::uuid
        """
        
        parameters = [db.create_parameter('driver_id', driver_id)]
        response = db.execute_query(sql, parameters)
        drivers = db.format_results(response)
        
        if not drivers:
            return create_response(404, {'error': 'Driver not found'})
        
        driver = drivers[0]
        
        # Include current assignment if requested
        if query_params.get('include_assignment') == 'true':
            assignment_sql = """
                SELECT 
                    da.id as assignment_id,
                    da.vehicle_id,
                    da.assignment_start_date,
                    da.assignment_end_date,
                    da.status as assignment_status,
                    da.notes as assignment_notes,
                    v.make,
                    v.model,
                    v.year,
                    v.registration,
                    v.status as vehicle_status
                FROM driver_assignments da
                JOIN vehicles v ON da.vehicle_id = v.id
                WHERE da.driver_id = :driver_id::uuid AND da.status = 'active'
                ORDER BY da.assignment_start_date DESC
                LIMIT 1
            """
            
            assignment_response = db.execute_query(assignment_sql, parameters)
            assignments = db.format_results(assignment_response)
            driver['current_assignment'] = assignments[0] if assignments else None
        
        # Include performance summary if requested
        if query_params.get('include_performance') == 'true':
            performance_sql = """
                SELECT 
                    COUNT(*) as total_weeks,
                    COUNT(*) FILTER (WHERE target_achieved = true) as weeks_target_achieved,
                    AVG(total_earnings) as avg_weekly_earnings,
                    AVG(cash_trip_percentage) as avg_cash_percentage,
                    MAX(week_start_date) as last_performance_week
                FROM performance_records
                WHERE driver_id = :driver_id::uuid
            """
            
            performance_response = db.execute_query(performance_sql, parameters)
            performance_data = db.format_results(performance_response)
            driver['performance_summary'] = performance_data[0] if performance_data else None
        
        logger.info(f"Retrieved driver: {driver_id}")
        
        return create_response(200, {'driver': driver})
        
    except Exception as e:
        logger.error(f"Error retrieving driver {driver_id}: {str(e)}")
        return create_response(500, {'error': 'Failed to retrieve driver'})


def update_driver(driver_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update driver information
    
    Args:
        driver_id: Driver ID
        update_data: Fields to update
        
    Returns:
        dict: API Gateway response with updated driver
    """
    try:
        # Check if driver exists
        db = get_database_connection()
        
        check_sql = "SELECT id FROM drivers WHERE id = :driver_id::uuid"
        check_params = [db.create_parameter('driver_id', driver_id)]
        check_response = db.execute_query(check_sql, check_params)
        
        if not db.format_results(check_response):
            return create_response(404, {'error': 'Driver not found'})
        
        # Build update query dynamically
        update_fields = []
        parameters = [db.create_parameter('driver_id', driver_id)]
        
        # Allowed fields for update
        allowed_fields = {
            'first_name': str,
            'last_name': str,
            'email': str,
            'phone': str,
            'license_number': str,
            'license_expiry_date': str,
            'address': dict,
            'emergency_contact': dict,
            'status': str
        }
        
        for field, value in update_data.items():
            if field in allowed_fields and value is not None:
                if field == 'license_expiry_date':
                    # Validate date format and future date
                    try:
                        license_expiry = datetime.strptime(value, '%Y-%m-%d').date()
                        if license_expiry <= date.today():
                            return create_response(400, {'error': 'License expiry date must be in the future'})
                    except ValueError:
                        return create_response(400, {'error': 'Invalid license expiry date format. Use YYYY-MM-DD'})
                
                if field in ['address', 'emergency_contact']:
                    update_fields.append(f"{field} = :{field}::jsonb")
                    parameters.append(db.create_parameter(field, json.dumps(value)))
                else:
                    update_fields.append(f"{field} = :{field}")
                    parameters.append(db.create_parameter(field, value))
        
        if not update_fields:
            return create_response(400, {'error': 'No valid fields to update'})
        
        # Execute update
        sql = f"""
            UPDATE drivers 
            SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = :driver_id
        """
        
        db.execute_query(sql, parameters)
        
        # Return updated driver
        return get_driver(driver_id, {})
        
    except Exception as e:
        logger.error(f"Error updating driver {driver_id}: {str(e)}")
        if "duplicate key" in str(e).lower():
            if "license_number" in str(e):
                return create_response(409, {'error': 'Driver with this license number already exists'})
            elif "email" in str(e):
                return create_response(409, {'error': 'Driver with this email already exists'})
        return create_response(500, {'error': 'Failed to update driver'})


def delete_driver(driver_id: str) -> Dict[str, Any]:
    """
    Delete driver (soft delete by setting status to terminated)
    
    Args:
        driver_id: Driver ID
        
    Returns:
        dict: API Gateway response
    """
    try:
        db = get_database_connection()
        
        # Check if driver exists and has active assignments
        check_sql = """
            SELECT 
                d.id,
                d.status,
                COUNT(da.id) as active_assignments
            FROM drivers d
            LEFT JOIN driver_assignments da ON d.id = da.driver_id AND da.status = 'active'
            WHERE d.id = :driver_id
            GROUP BY d.id, d.status
        """
        
        parameters = [db.create_parameter('driver_id', driver_id)]
        response = db.execute_query(check_sql, parameters)
        results = db.format_results(response)
        
        if not results:
            return create_response(404, {'error': 'Driver not found'})
        
        driver_info = results[0]
        
        if driver_info['active_assignments'] > 0:
            return create_response(400, {'error': 'Cannot delete driver with active vehicle assignments'})
        
        # Soft delete by updating status
        update_sql = """
            UPDATE drivers 
            SET status = 'terminated', updated_at = CURRENT_TIMESTAMP
            WHERE id = :driver_id
        """
        
        db.execute_query(update_sql, parameters)
        
        logger.info(f"Driver {driver_id} marked as terminated")
        
        return create_response(200, {'message': 'Driver successfully terminated'})
        
    except Exception as e:
        logger.error(f"Error deleting driver {driver_id}: {str(e)}")
        return create_response(500, {'error': 'Failed to delete driver'})


def get_driver_assignments(driver_id: str, query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Get driver's vehicle assignments
    
    Args:
        driver_id: Driver ID
        query_params: Query parameters for filtering
        
    Returns:
        dict: API Gateway response with assignments
    """
    try:
        db = get_database_connection()
        
        # Check if driver exists
        check_sql = "SELECT id FROM drivers WHERE id = :driver_id::uuid"
        check_params = [db.create_parameter('driver_id', driver_id)]
        check_response = db.execute_query(check_sql, check_params)
        
        if not db.format_results(check_response):
            return create_response(404, {'error': 'Driver not found'})
        
        # Build query with optional filters
        where_conditions = ["da.driver_id = :driver_id::uuid"]
        parameters = [db.create_parameter('driver_id', driver_id)]
        
        # Filter by status
        if query_params.get('status'):
            where_conditions.append("da.status = :status")
            parameters.append(db.create_parameter('status', query_params['status']))
        
        # Filter by date range
        if query_params.get('from_date'):
            where_conditions.append("da.assignment_start_date >= :from_date")
            parameters.append(db.create_parameter('from_date', query_params['from_date']))
        
        if query_params.get('to_date'):
            where_conditions.append("da.assignment_start_date <= :to_date")
            parameters.append(db.create_parameter('to_date', query_params['to_date']))
        
        where_clause = " AND ".join(where_conditions)
        
        # Execute query
        sql = f"""
            SELECT 
                da.id,
                da.driver_id,
                da.vehicle_id,
                da.assignment_start_date,
                da.assignment_end_date,
                da.status,
                da.notes,
                da.created_at,
                da.updated_at,
                v.make,
                v.model,
                v.year,
                v.registration,
                v.status as vehicle_status
            FROM driver_assignments da
            JOIN vehicles v ON da.vehicle_id = v.id
            WHERE {where_clause}
            ORDER BY da.assignment_start_date DESC
        """
        
        response = db.execute_query(sql, parameters)
        assignments = db.format_results(response)
        
        logger.info(f"Retrieved {len(assignments)} assignments for driver {driver_id}")
        
        return create_response(200, {
            'assignments': assignments,
            'count': len(assignments)
        })
        
    except Exception as e:
        logger.error(f"Error retrieving assignments for driver {driver_id}: {str(e)}")
        return create_response(500, {'error': 'Failed to retrieve driver assignments'})


def assign_vehicle(driver_id: str, assignment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assign vehicle to driver
    
    Args:
        driver_id: Driver ID
        assignment_data: Assignment information
        
    Returns:
        dict: API Gateway response with assignment
    """
    try:
        # Validate required fields
        if not assignment_data.get('vehicle_id'):
            return create_response(400, {'error': 'Vehicle ID is required'})
        
        vehicle_id = assignment_data['vehicle_id']
        assignment_start_date = assignment_data.get('assignment_start_date', date.today().isoformat())
        
        db = get_database_connection()
        
        # Check if driver and vehicle exist and are available
        check_sql = """
            SELECT 
                d.id as driver_id,
                d.status as driver_status,
                v.id as vehicle_id,
                v.status as vehicle_status,
                v.current_driver_id,
                EXISTS(
                    SELECT 1 FROM driver_assignments da 
                    WHERE da.driver_id = :driver_id::uuid AND da.status = 'active'
                ) as driver_has_active_assignment,
                EXISTS(
                    SELECT 1 FROM driver_assignments da 
                    WHERE da.vehicle_id = :vehicle_id::uuid AND da.status = 'active'
                ) as vehicle_has_active_assignment
            FROM drivers d
            CROSS JOIN vehicles v
            WHERE d.id = :driver_id::uuid AND v.id = :vehicle_id::uuid
        """
        
        parameters = [
            db.create_parameter('driver_id', driver_id),
            db.create_parameter('vehicle_id', vehicle_id)
        ]
        
        response = db.execute_query(check_sql, parameters)
        results = db.format_results(response)
        
        if not results:
            return create_response(404, {'error': 'Driver or vehicle not found'})
        
        check_result = results[0]
        
        # Validate driver status
        if check_result['driver_status'] != 'active':
            return create_response(400, {'error': 'Driver must be active to receive vehicle assignment'})
        
        # Validate vehicle status
        if check_result['vehicle_status'] not in ['active']:
            return create_response(400, {'error': 'Vehicle must be active to be assigned'})
        
        # Check for existing assignments
        if check_result['driver_has_active_assignment']:
            return create_response(400, {'error': 'Driver already has an active vehicle assignment'})
        
        if check_result['vehicle_has_active_assignment']:
            return create_response(400, {'error': 'Vehicle is already assigned to another driver'})
        
        # Create assignment in transaction
        assignment_id = str(uuid.uuid4())
        
        statements = [
            {
                'sql': """
                    INSERT INTO driver_assignments (
                        id, driver_id, vehicle_id, assignment_start_date, status, notes
                    ) VALUES (
                        :assignment_id::uuid, :driver_id::uuid, :vehicle_id::uuid, :assignment_start_date::date, 'active', :notes
                    )
                """,
                'parameters': [
                    db.create_parameter('assignment_id', assignment_id),
                    db.create_parameter('driver_id', driver_id),
                    db.create_parameter('vehicle_id', vehicle_id),
                    db.create_parameter('assignment_start_date', assignment_start_date),
                    db.create_parameter('notes', assignment_data.get('notes', ''))
                ]
            },
            {
                'sql': """
                    UPDATE vehicles 
                    SET current_driver_id = :driver_id::uuid, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :vehicle_id::uuid
                """,
                'parameters': [
                    db.create_parameter('driver_id', driver_id),
                    db.create_parameter('vehicle_id', vehicle_id)
                ]
            }
        ]
        
        db.execute_transaction(statements)
        
        # Retrieve the created assignment
        get_assignment_sql = """
            SELECT 
                da.id,
                da.driver_id,
                da.vehicle_id,
                da.assignment_start_date,
                da.assignment_end_date,
                da.status,
                da.notes,
                da.created_at,
                da.updated_at,
                v.make,
                v.model,
                v.year,
                v.registration,
                v.status as vehicle_status
            FROM driver_assignments da
            JOIN vehicles v ON da.vehicle_id = v.id
            WHERE da.id = :assignment_id::uuid
        """
        
        assignment_params = [db.create_parameter('assignment_id', assignment_id)]
        assignment_response = db.execute_query(get_assignment_sql, assignment_params)
        assignment = db.format_results(assignment_response)[0]
        
        logger.info(f"Created assignment {assignment_id} for driver {driver_id} and vehicle {vehicle_id}")
        
        return create_response(201, {'assignment': assignment})
        
    except Exception as e:
        logger.error(f"Error creating assignment for driver {driver_id}: {str(e)}")
        return create_response(500, {'error': 'Failed to create vehicle assignment'})


def get_driver_performance(driver_id: str, query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Get driver performance records
    
    Args:
        driver_id: Driver ID
        query_params: Query parameters for filtering
        
    Returns:
        dict: API Gateway response with performance data
    """
    try:
        db = get_database_connection()
        
        # Check if driver exists
        check_sql = "SELECT id FROM drivers WHERE id = :driver_id::uuid"
        check_params = [db.create_parameter('driver_id', driver_id)]
        check_response = db.execute_query(check_sql, check_params)
        
        if not db.format_results(check_response):
            return create_response(404, {'error': 'Driver not found'})
        
        # Build query with optional filters
        where_conditions = ["pr.driver_id = :driver_id::uuid"]
        parameters = [db.create_parameter('driver_id', driver_id)]
        
        # Filter by date range
        if query_params.get('from_date'):
            where_conditions.append("pr.week_start_date >= :from_date")
            parameters.append(db.create_parameter('from_date', query_params['from_date']))
        
        if query_params.get('to_date'):
            where_conditions.append("pr.week_start_date <= :to_date")
            parameters.append(db.create_parameter('to_date', query_params['to_date']))
        
        # Limit results
        limit = min(int(query_params.get('limit', 50)), 100)
        
        where_clause = " AND ".join(where_conditions)
        
        # Execute query
        sql = f"""
            SELECT 
                pr.id,
                pr.driver_id,
                pr.vehicle_id,
                pr.week_start_date,
                pr.week_end_date,
                pr.card_earnings,
                pr.cash_trips_count,
                pr.cash_trips_value,
                pr.total_trips,
                pr.total_earnings,
                pr.cash_trip_percentage,
                pr.target_achieved,
                pr.settlement_amount,
                pr.shortfall_amount,
                pr.notes,
                pr.created_at,
                pr.updated_at,
                v.make,
                v.model,
                v.registration
            FROM performance_records pr
            JOIN vehicles v ON pr.vehicle_id = v.id
            WHERE {where_clause}
            ORDER BY pr.week_start_date DESC
            LIMIT {limit}
        """
        
        response = db.execute_query(sql, parameters)
        performance_records = db.format_results(response)
        
        # Get summary statistics
        summary_sql = f"""
            SELECT 
                COUNT(*) as total_weeks,
                COUNT(*) FILTER (WHERE pr.target_achieved = true) as weeks_target_achieved,
                AVG(pr.total_earnings) as avg_weekly_earnings,
                AVG(pr.cash_trip_percentage) as avg_cash_percentage,
                SUM(pr.settlement_amount) as total_settlements,
                SUM(pr.shortfall_amount) as total_shortfalls
            FROM performance_records pr
            WHERE {where_clause}
        """
        
        summary_response = db.execute_query(summary_sql, parameters)
        summary = db.format_results(summary_response)[0] if db.format_results(summary_response) else {}
        
        logger.info(f"Retrieved {len(performance_records)} performance records for driver {driver_id}")
        
        return create_response(200, {
            'performance_records': performance_records,
            'summary': summary,
            'count': len(performance_records)
        })
        
    except Exception as e:
        logger.error(f"Error retrieving performance for driver {driver_id}: {str(e)}")
        return create_response(500, {'error': 'Failed to retrieve driver performance'})


def record_performance(driver_id: str, performance_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Record driver performance for a week
    
    Args:
        driver_id: Driver ID
        performance_data: Performance information
        
    Returns:
        dict: API Gateway response with performance record
    """
    try:
        # Validate required fields
        required_fields = ['vehicle_id', 'week_start_date', 'card_earnings', 'cash_trips_count', 'cash_trips_value', 'total_trips']
        for field in required_fields:
            if field not in performance_data:
                return create_response(400, {'error': f'Missing required field: {field}'})
        
        # Validate data types and ranges
        try:
            card_earnings = float(performance_data['card_earnings'])
            cash_trips_count = int(performance_data['cash_trips_count'])
            cash_trips_value = float(performance_data['cash_trips_value'])
            total_trips = int(performance_data['total_trips'])
            
            if card_earnings < 0 or cash_trips_value < 0 or cash_trips_count < 0 or total_trips < 0:
                return create_response(400, {'error': 'Earnings, trips, and counts must be non-negative'})
            
            if cash_trips_count > total_trips:
                return create_response(400, {'error': 'Cash trips count cannot exceed total trips'})
                
        except (ValueError, TypeError):
            return create_response(400, {'error': 'Invalid numeric values in performance data'})
        
        # Validate date format
        try:
            week_start = datetime.strptime(performance_data['week_start_date'], '%Y-%m-%d').date()
            week_end = week_start + timedelta(days=6)
        except ValueError:
            return create_response(400, {'error': 'Invalid week start date format. Use YYYY-MM-DD'})
        
        db = get_database_connection()
        
        # Check if driver and vehicle exist
        check_sql = """
            SELECT d.id as driver_id, v.id as vehicle_id
            FROM drivers d
            CROSS JOIN vehicles v
            WHERE d.id = :driver_id::uuid AND v.id = :vehicle_id::uuid
        """
        
        check_params = [
            db.create_parameter('driver_id', driver_id),
            db.create_parameter('vehicle_id', performance_data['vehicle_id'])
        ]
        
        check_response = db.execute_query(check_sql, check_params)
        if not db.format_results(check_response):
            return create_response(404, {'error': 'Driver or vehicle not found'})
        
        # Generate performance record ID
        performance_id = str(uuid.uuid4())
        
        # Prepare parameters
        parameters = [
            db.create_parameter('id', performance_id),
            db.create_parameter('driver_id', driver_id),
            db.create_parameter('vehicle_id', performance_data['vehicle_id']),
            db.create_parameter('week_start_date', week_start.isoformat()),
            db.create_parameter('week_end_date', week_end.isoformat()),
            db.create_parameter('card_earnings', card_earnings),
            db.create_parameter('cash_trips_count', cash_trips_count),
            db.create_parameter('cash_trips_value', cash_trips_value),
            db.create_parameter('total_trips', total_trips),
            db.create_parameter('notes', performance_data.get('notes', ''))
        ]
        
        # Insert performance record (calculated fields are handled by database)
        sql = """
            INSERT INTO performance_records (
                id, driver_id, vehicle_id, week_start_date, week_end_date,
                card_earnings, cash_trips_count, cash_trips_value, total_trips, notes
            ) VALUES (
                :id::uuid, :driver_id::uuid, :vehicle_id::uuid, :week_start_date::date, :week_end_date::date,
                :card_earnings, :cash_trips_count, :cash_trips_value, :total_trips, :notes
            )
            ON CONFLICT (driver_id, week_start_date) 
            DO UPDATE SET
                vehicle_id = EXCLUDED.vehicle_id,
                week_end_date = EXCLUDED.week_end_date,
                card_earnings = EXCLUDED.card_earnings,
                cash_trips_count = EXCLUDED.cash_trips_count,
                cash_trips_value = EXCLUDED.cash_trips_value,
                total_trips = EXCLUDED.total_trips,
                notes = EXCLUDED.notes,
                updated_at = CURRENT_TIMESTAMP
        """
        
        db.execute_query(sql, parameters)
        
        # Retrieve the created/updated performance record
        get_performance_sql = """
            SELECT 
                pr.id,
                pr.driver_id,
                pr.vehicle_id,
                pr.week_start_date,
                pr.week_end_date,
                pr.card_earnings,
                pr.cash_trips_count,
                pr.cash_trips_value,
                pr.total_trips,
                pr.total_earnings,
                pr.cash_trip_percentage,
                pr.target_achieved,
                pr.settlement_amount,
                pr.shortfall_amount,
                pr.notes,
                pr.created_at,
                pr.updated_at
            FROM performance_records pr
            WHERE pr.id = :performance_id::uuid
        """
        
        performance_params = [db.create_parameter('performance_id', performance_id)]
        performance_response = db.execute_query(get_performance_sql, performance_params)
        performance_record = db.format_results(performance_response)[0]
        
        logger.info(f"Recorded performance for driver {driver_id}, week {week_start}")
        
        return create_response(201, {'performance_record': performance_record})
        
    except Exception as e:
        logger.error(f"Error recording performance for driver {driver_id}: {str(e)}")
        if "duplicate key" in str(e).lower():
            return create_response(409, {'error': 'Performance record for this driver and week already exists'})
        return create_response(500, {'error': 'Failed to record performance'})