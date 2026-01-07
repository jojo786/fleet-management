"""
Database utilities for FLEET system
Provides connection and query utilities using RDS Data API
"""

import boto3
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import uuid

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Database connection class using RDS Data API"""
    
    def __init__(self, cluster_arn: str, secret_arn: str, database_name: str):
        """
        Initialize database connection
        
        Args:
            cluster_arn: Aurora cluster ARN
            secret_arn: Secrets Manager secret ARN  
            database_name: Database name
        """
        self.cluster_arn = cluster_arn
        self.secret_arn = secret_arn
        self.database_name = database_name
        self.rds_data = boto3.client('rds-data')
        
    def execute_query(self, sql: str, parameters: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Execute SQL query using RDS Data API
        
        Args:
            sql: SQL query string
            parameters: Query parameters
            
        Returns:
            dict: Query results
        """
        try:
            request_params = {
                'resourceArn': self.cluster_arn,
                'secretArn': self.secret_arn,
                'database': self.database_name,
                'sql': sql,
                'includeResultMetadata': True  # Include column names in response
            }
            
            if parameters:
                request_params['parameters'] = parameters
                
            response = self.rds_data.execute_statement(**request_params)
            
            logger.info(f"Query executed successfully: {sql[:100]}...")
            return response
            
        except Exception as e:
            logger.error(f"Database query failed: {sql[:100]}... Error: {str(e)}")
            raise
            
    def execute_transaction(self, statements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute multiple statements in a transaction
        
        Args:
            statements: List of SQL statements with parameters
            
        Returns:
            dict: Transaction results
        """
        try:
            # Begin transaction
            transaction = self.rds_data.begin_transaction(
                resourceArn=self.cluster_arn,
                secretArn=self.secret_arn,
                database=self.database_name
            )
            
            transaction_id = transaction['transactionId']
            
            try:
                # Execute statements
                results = []
                for statement in statements:
                    result = self.rds_data.execute_statement(
                        resourceArn=self.cluster_arn,
                        secretArn=self.secret_arn,
                        database=self.database_name,
                        transactionId=transaction_id,
                        sql=statement['sql'],
                        parameters=statement.get('parameters', []),
                        includeResultMetadata=True  # Include column names in response
                    )
                    results.append(result)
                
                # Commit transaction
                self.rds_data.commit_transaction(
                    resourceArn=self.cluster_arn,
                    secretArn=self.secret_arn,
                    transactionId=transaction_id
                )
                
                logger.info(f"Transaction completed successfully with {len(statements)} statements")
                return {'results': results, 'transactionId': transaction_id}
                
            except Exception as e:
                # Rollback transaction on error
                self.rds_data.rollback_transaction(
                    resourceArn=self.cluster_arn,
                    secretArn=self.secret_arn,
                    transactionId=transaction_id
                )
                logger.error(f"Transaction rolled back due to error: {str(e)}")
                raise
                
        except Exception as e:
            logger.error(f"Transaction failed: {str(e)}")
            raise
            
    def format_results(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Format RDS Data API response into readable format
        
        Args:
            response: RDS Data API response
            
        Returns:
            list: Formatted results
        """
        if 'records' not in response:
            return []
            
        records = response['records']
        column_metadata = response.get('columnMetadata', [])
        
        formatted_results = []
        
        for record in records:
            row = {}
            for i, field in enumerate(record):
                column_name = column_metadata[i]['name'] if i < len(column_metadata) else f'column_{i}'
                row[column_name] = self._extract_field_value(field)
            formatted_results.append(row)
            
        return formatted_results
        
    def _extract_field_value(self, field: Dict[str, Any]) -> Any:
        """
        Extract value from RDS Data API field
        
        Args:
            field: RDS Data API field
            
        Returns:
            Extracted value
        """
        if 'stringValue' in field:
            return field['stringValue']
        elif 'longValue' in field:
            return field['longValue']
        elif 'doubleValue' in field:
            return field['doubleValue']
        elif 'booleanValue' in field:
            return field['booleanValue']
        elif 'isNull' in field and field['isNull']:
            return None
        else:
            return str(field)
            
    def create_parameter(self, name: str, value: Any, type_hint: str = None) -> Dict[str, Any]:
        """
        Create parameter for RDS Data API
        
        Args:
            name: Parameter name
            value: Parameter value
            type_hint: Type hint for the parameter
            
        Returns:
            dict: RDS Data API parameter
        """
        param = {'name': name}
        
        if value is None:
            param['value'] = {'isNull': True}
        elif isinstance(value, str):
            param['value'] = {'stringValue': value}
        elif isinstance(value, int):
            param['value'] = {'longValue': value}
        elif isinstance(value, float):
            param['value'] = {'doubleValue': value}
        elif isinstance(value, bool):
            param['value'] = {'booleanValue': value}
        elif isinstance(value, (datetime, date)):
            param['value'] = {'stringValue': value.isoformat()}
        elif isinstance(value, uuid.UUID):
            param['value'] = {'stringValue': str(value)}
        else:
            param['value'] = {'stringValue': str(value)}
            
        return param


def get_database_connection() -> DatabaseConnection:
    """
    Get database connection using environment variables
    
    Returns:
        DatabaseConnection: Database connection instance
    """
    import os
    
    cluster_arn = os.environ.get('DB_CLUSTER_ARN')
    secret_arn = os.environ.get('DB_SECRET_ARN')
    database_name = os.environ.get('DB_NAME', 'fleet')
    
    if not cluster_arn or not secret_arn:
        raise ValueError("Database connection parameters not found in environment variables")
        
    return DatabaseConnection(cluster_arn, secret_arn, database_name)