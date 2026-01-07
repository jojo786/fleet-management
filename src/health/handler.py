"""
Health Check Lambda Function for FLEET System
Provides basic health status and system information
"""

import json
import os
from datetime import datetime


def lambda_handler(event, context):
    """
    Health check endpoint handler
    
    Returns:
        dict: Health status response with system information
    """
    try:
        # Get environment information
        environment = os.environ.get('Environment', 'unknown')
        region = os.environ.get('REGION', 'eu-west-1')
        
        # Check if database is configured
        db_cluster_arn = os.environ.get('DB_CLUSTER_ARN')
        database_status = 'configured' if db_cluster_arn else 'not_configured'
        
        # Create health response
        health_response = {
            'status': 'healthy',
            'service': 'FLEET - Fleet Location, Efficiency, and Tracking Technology',
            'version': '1.0.0',
            'environment': environment,
            'region': region,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'request_id': context.aws_request_id,
            'components': {
                'api_gateway': 'operational',
                'lambda': 'operational',
                'database': database_status
            }
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': json.dumps(health_response, indent=2)
        }
        
    except Exception as e:
        # Return error response
        error_response = {
            'status': 'unhealthy',
            'service': 'FLEET System',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'request_id': context.aws_request_id if context else 'unknown'
        }
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': json.dumps(error_response, indent=2)
        }