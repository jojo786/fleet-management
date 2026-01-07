"""
Database Initialization Lambda Function for FLEET System
Creates initial database schema for vehicles table
"""

import json
import boto3
import os
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
rds_data = boto3.client('rds-data')
secrets_manager = boto3.client('secretsmanager')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Custom resource handler for database initialization
    
    Args:
        event: CloudFormation custom resource event
        context: Lambda context
        
    Returns:
        dict: Response for CloudFormation
    """
    try:
        logger.info(f"Database initialization event: {json.dumps(event, default=str)}")
        
        request_type = event.get('RequestType', 'Create')
        
        # Get configuration from environment variables
        cluster_arn = os.environ['DB_CLUSTER_ARN']
        secret_arn = os.environ['DB_SECRET_ARN']
        database_name = os.environ['DB_NAME']
        
        if request_type == 'Create':
            logger.info("Creating database schema...")
            create_database_schema(cluster_arn, secret_arn, database_name)
            
        elif request_type == 'Update':
            logger.info("Updating database schema...")
            # For now, we'll just log the update - schema migrations will be handled later
            logger.info("Schema updates will be handled in future versions")
            
        elif request_type == 'Delete':
            logger.info("Database deletion requested - no action taken for safety")
            # We don't delete the database on stack deletion for safety
            
        # Send success response to CloudFormation
        send_response(event, context, 'SUCCESS', {
            'Message': f'Database initialization completed for {request_type}',
            'ClusterArn': cluster_arn,
            'DatabaseName': database_name
        })
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        send_response(event, context, 'FAILED', {
            'Message': f'Database initialization failed: {str(e)}'
        })


def create_database_schema(cluster_arn: str, secret_arn: str, database_name: str) -> None:
    """
    Create the initial database schema for FLEET system
    
    Args:
        cluster_arn: Aurora cluster ARN
        secret_arn: Secrets Manager secret ARN
        database_name: Database name
    """
    logger.info("Creating vehicles table...")
    
    # SQL statements - each must be executed separately
    sql_statements = [
        # Create vehicles table
        """
        CREATE TABLE IF NOT EXISTS vehicles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            make VARCHAR(50) NOT NULL,
            model VARCHAR(50) NOT NULL,
            year INTEGER NOT NULL CHECK (year >= 1900 AND year <= 2100),
            registration VARCHAR(20) NOT NULL UNIQUE,
            vin VARCHAR(17),
            status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'in_service', 'out_of_order', 'retired')),
            current_driver_id UUID,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Create updated_at trigger function
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql'
        """,
        
        # Drop existing trigger if it exists
        "DROP TRIGGER IF EXISTS update_vehicles_updated_at ON vehicles",
        
        # Create trigger for vehicles table
        """
        CREATE TRIGGER update_vehicles_updated_at
            BEFORE UPDATE ON vehicles
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
        """,
        
        # Create indexes
        "CREATE INDEX IF NOT EXISTS idx_vehicles_registration ON vehicles(registration)",
        "CREATE INDEX IF NOT EXISTS idx_vehicles_status ON vehicles(status)",
        "CREATE INDEX IF NOT EXISTS idx_vehicles_current_driver ON vehicles(current_driver_id)",
        
        # Create maintenance_types lookup table
        """
        CREATE TABLE IF NOT EXISTS maintenance_types (
            id SERIAL PRIMARY KEY,
            type_name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT,
            typical_cost_range VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Insert default maintenance types
        """
        INSERT INTO maintenance_types (type_name, description, typical_cost_range) VALUES
        ('oil_change', 'Regular oil and filter change', 'R300-R800'),
        ('brake_service', 'Brake pad and disc service', 'R800-R2500'),
        ('tire_replacement', 'Tire replacement and alignment', 'R1500-R5000'),
        ('engine_repair', 'Engine diagnostic and repair', 'R2000-R15000'),
        ('transmission_service', 'Transmission service and repair', 'R1500-R8000'),
        ('accident_repair', 'Accident damage repair', 'R5000-R50000'),
        ('general_maintenance', 'General maintenance and inspection', 'R500-R2000')
        ON CONFLICT (type_name) DO NOTHING
        """,
        
        # Create service_records table
        """
        CREATE TABLE IF NOT EXISTS service_records (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
            driver_id UUID,
            maintenance_type_id INTEGER NOT NULL REFERENCES maintenance_types(id),
            description TEXT NOT NULL,
            cost DECIMAL(10,2) NOT NULL CHECK (cost >= 0),
            service_date DATE NOT NULL,
            mileage INTEGER CHECK (mileage >= 0),
            service_provider VARCHAR(100) NOT NULL,
            is_warranty BOOLEAN DEFAULT FALSE,
            next_service_due DATE,
            receipt_url VARCHAR(500),
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Drop existing trigger if it exists
        "DROP TRIGGER IF EXISTS update_service_records_updated_at ON service_records",
        
        # Create trigger for service_records table
        """
        CREATE TRIGGER update_service_records_updated_at
            BEFORE UPDATE ON service_records
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
        """,
        
        # Create indexes for service_records
        "CREATE INDEX IF NOT EXISTS idx_service_records_vehicle_id ON service_records(vehicle_id)",
        "CREATE INDEX IF NOT EXISTS idx_service_records_driver_id ON service_records(driver_id)",
        "CREATE INDEX IF NOT EXISTS idx_service_records_service_date ON service_records(service_date)",
        "CREATE INDEX IF NOT EXISTS idx_service_records_maintenance_type ON service_records(maintenance_type_id)",
        "CREATE INDEX IF NOT EXISTS idx_service_records_cost ON service_records(cost)",
        "CREATE INDEX IF NOT EXISTS idx_service_records_next_service_due ON service_records(next_service_due)",
        
        # Create drivers table
        """
        CREATE TABLE IF NOT EXISTS drivers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE,
            phone VARCHAR(20) NOT NULL,
            id_number VARCHAR(20) NOT NULL UNIQUE,
            license_number VARCHAR(50) NOT NULL UNIQUE,
            license_expiry_date DATE NOT NULL,
            address JSONB NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'terminated')),
            emergency_contact JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Drop existing trigger if it exists
        "DROP TRIGGER IF EXISTS update_drivers_updated_at ON drivers",
        
        # Create trigger for drivers table
        """
        CREATE TRIGGER update_drivers_updated_at
            BEFORE UPDATE ON drivers
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
        """,
        
        # Create indexes for drivers
        "CREATE INDEX IF NOT EXISTS idx_drivers_email ON drivers(email)",
        "CREATE INDEX IF NOT EXISTS idx_drivers_phone ON drivers(phone)",
        "CREATE INDEX IF NOT EXISTS idx_drivers_id_number ON drivers(id_number)",
        "CREATE INDEX IF NOT EXISTS idx_drivers_license_number ON drivers(license_number)",
        "CREATE INDEX IF NOT EXISTS idx_drivers_status ON drivers(status)",
        "CREATE INDEX IF NOT EXISTS idx_drivers_license_expiry ON drivers(license_expiry_date)",
        
        # Create driver_assignments table
        """
        CREATE TABLE IF NOT EXISTS driver_assignments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            driver_id UUID NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
            vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
            assignment_start_date DATE NOT NULL,
            assignment_end_date DATE,
            status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'terminated')),
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_active_vehicle_assignment UNIQUE (vehicle_id, assignment_end_date) DEFERRABLE INITIALLY DEFERRED
        )
        """,
        
        # Drop existing trigger if it exists
        "DROP TRIGGER IF EXISTS update_driver_assignments_updated_at ON driver_assignments",
        
        # Create trigger for driver_assignments table
        """
        CREATE TRIGGER update_driver_assignments_updated_at
            BEFORE UPDATE ON driver_assignments
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
        """,
        
        # Create indexes for driver_assignments
        "CREATE INDEX IF NOT EXISTS idx_driver_assignments_driver_id ON driver_assignments(driver_id)",
        "CREATE INDEX IF NOT EXISTS idx_driver_assignments_vehicle_id ON driver_assignments(vehicle_id)",
        "CREATE INDEX IF NOT EXISTS idx_driver_assignments_status ON driver_assignments(status)",
        "CREATE INDEX IF NOT EXISTS idx_driver_assignments_start_date ON driver_assignments(assignment_start_date)",
        "CREATE INDEX IF NOT EXISTS idx_driver_assignments_end_date ON driver_assignments(assignment_end_date)",
        
        # Create performance_records table
        """
        CREATE TABLE IF NOT EXISTS performance_records (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            driver_id UUID NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
            vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
            week_start_date DATE NOT NULL,
            week_end_date DATE NOT NULL,
            card_earnings DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (card_earnings >= 0),
            cash_trips_count INTEGER NOT NULL DEFAULT 0 CHECK (cash_trips_count >= 0),
            cash_trips_value DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (cash_trips_value >= 0),
            total_trips INTEGER NOT NULL DEFAULT 0 CHECK (total_trips >= 0),
            total_earnings DECIMAL(10,2) GENERATED ALWAYS AS (card_earnings + cash_trips_value) STORED,
            cash_trip_percentage DECIMAL(5,2) GENERATED ALWAYS AS (
                CASE 
                    WHEN total_trips > 0 THEN (cash_trips_count::DECIMAL / total_trips::DECIMAL) * 100
                    ELSE 0
                END
            ) STORED,
            target_achieved BOOLEAN GENERATED ALWAYS AS (card_earnings + cash_trips_value >= 5000) STORED,
            settlement_amount DECIMAL(10,2) GENERATED ALWAYS AS (
                CASE 
                    WHEN card_earnings >= 5000 THEN card_earnings - 5000
                    ELSE 0
                END
            ) STORED,
            shortfall_amount DECIMAL(10,2) GENERATED ALWAYS AS (
                CASE 
                    WHEN (card_earnings + cash_trips_value) < 5000 THEN 5000 - (card_earnings + cash_trips_value)
                    ELSE 0
                END
            ) STORED,
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_driver_week UNIQUE (driver_id, week_start_date)
        )
        """,
        
        # Drop existing trigger if it exists
        "DROP TRIGGER IF EXISTS update_performance_records_updated_at ON performance_records",
        
        # Create trigger for performance_records table
        """
        CREATE TRIGGER update_performance_records_updated_at
            BEFORE UPDATE ON performance_records
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
        """,
        
        # Create indexes for performance_records
        "CREATE INDEX IF NOT EXISTS idx_performance_records_driver_id ON performance_records(driver_id)",
        "CREATE INDEX IF NOT EXISTS idx_performance_records_vehicle_id ON performance_records(vehicle_id)",
        "CREATE INDEX IF NOT EXISTS idx_performance_records_week_start ON performance_records(week_start_date)",
        "CREATE INDEX IF NOT EXISTS idx_performance_records_week_end ON performance_records(week_end_date)",
        "CREATE INDEX IF NOT EXISTS idx_performance_records_target_achieved ON performance_records(target_achieved)",
        "CREATE INDEX IF NOT EXISTS idx_performance_records_cash_percentage ON performance_records(cash_trip_percentage)",
        
        # Add foreign key constraint to vehicles table for current_driver_id
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'fk_vehicles_current_driver'
            ) THEN
                ALTER TABLE vehicles 
                ADD CONSTRAINT fk_vehicles_current_driver 
                FOREIGN KEY (current_driver_id) REFERENCES drivers(id) ON DELETE SET NULL;
            END IF;
        END $$
        """,
        
        # Update service_records to reference drivers properly
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'fk_service_records_driver'
            ) THEN
                ALTER TABLE service_records 
                ADD CONSTRAINT fk_service_records_driver 
                FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE SET NULL;
            END IF;
        END $$
        """
    ]
    
    try:
        # Execute each statement separately
        for i, sql in enumerate(sql_statements):
            logger.info(f"Executing statement {i+1}/{len(sql_statements)}")
            execute_sql(cluster_arn, secret_arn, database_name, sql.strip())
        
        logger.info("Database schema initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to create database schema: {str(e)}")
        raise


def execute_sql(cluster_arn: str, secret_arn: str, database_name: str, sql: str) -> Dict[str, Any]:
    """
    Execute SQL statement using RDS Data API
    
    Args:
        cluster_arn: Aurora cluster ARN
        secret_arn: Secrets Manager secret ARN
        database_name: Database name
        sql: SQL statement to execute
        
    Returns:
        dict: RDS Data API response
    """
    try:
        response = rds_data.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql=sql
        )
        logger.info(f"SQL executed successfully: {sql[:100]}...")
        return response
        
    except Exception as e:
        logger.error(f"Failed to execute SQL: {sql[:100]}... Error: {str(e)}")
        raise


def send_response(event: Dict[str, Any], context, response_status: str, response_data: Dict[str, Any]) -> None:
    """
    Send response to CloudFormation custom resource
    
    Args:
        event: CloudFormation event
        context: Lambda context
        response_status: SUCCESS or FAILED
        response_data: Response data
    """
    import urllib3
    
    response_url = event['ResponseURL']
    
    response_body = {
        'Status': response_status,
        'Reason': f'See CloudWatch Log Stream: {context.log_stream_name}',
        'PhysicalResourceId': context.log_stream_name,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Data': response_data
    }
    
    json_response_body = json.dumps(response_body)
    
    headers = {
        'content-type': '',
        'content-length': str(len(json_response_body))
    }
    
    try:
        http = urllib3.PoolManager()
        response = http.request('PUT', response_url, body=json_response_body, headers=headers)
        logger.info(f"CloudFormation response sent: {response.status}")
    except Exception as e:
        logger.error(f"Failed to send response to CloudFormation: {str(e)}")
        raise