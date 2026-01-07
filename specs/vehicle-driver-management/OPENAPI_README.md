# FLEET API - OpenAPI Specification

## Overview

This directory contains the complete OpenAPI 3.0 specification for the FLEET (Fleet Location, Efficiency, and Tracking Technology) API.

## Files

- **openapi.yaml** - Complete OpenAPI 3.0 specification with all endpoints, schemas, and documentation

## What's Included

### API Endpoints

The specification documents all API endpoints organized by functional area:

#### Health Check
- `GET /health` - System health status (no auth required)

#### Vehicle Management
- `GET /vehicles` - List all vehicles with filtering
- `POST /vehicles` - Create new vehicle
- `GET /vehicles/{id}` - Get vehicle details
- `PUT /vehicles/{id}` - Update vehicle
- `DELETE /vehicles/{id}` - Delete vehicle (admin only)

#### Service Records
- `GET /vehicles/{id}/service-records` - Get service history
- `POST /vehicles/{id}/service-records` - Add service record

#### Maintenance & Cost Analysis
- `GET /maintenance-alerts` - Get pending maintenance alerts
- `GET /cost-analysis` - Get detailed cost analysis
- `GET /fleet-cost-comparison` - Compare costs across fleet
- `GET /high-cost-alerts` - Get high cost alerts (>20% above average)

#### Driver Management
- `GET /drivers` - List all drivers with filtering
- `POST /drivers` - Create new driver
- `GET /drivers/{id}` - Get driver details
- `PUT /drivers/{id}` - Update driver
- `DELETE /drivers/{id}` - Delete driver (admin only)

#### Driver Assignments
- `GET /drivers/{id}/assignments` - Get assignment history
- `POST /drivers/{id}/assignments` - Assign vehicle to driver

#### Performance Tracking
- `GET /drivers/{id}/performance` - Get performance metrics
- `POST /drivers/{id}/performance` - Record weekly performance

### Authentication

All endpoints (except `/health`) require AWS Cognito JWT authentication:
- **Security Scheme**: Bearer token in Authorization header
- **Format**: `Authorization: Bearer {jwt-token}`
- **Provider**: AWS Cognito User Pools

### Data Models

Complete schemas for all data types:
- **Vehicle** - Fleet vehicle information
- **ServiceRecord** - Maintenance and repair records
- **Driver** - Driver profiles and information
- **DriverAssignment** - Vehicle-driver assignments
- **PerformanceRecord** - Weekly earnings and performance
- **MaintenanceAlert** - Service due alerts
- **HighCostAlert** - Cost threshold alerts
- **CostAnalysis** - Detailed cost breakdowns
- **FleetCostComparison** - Fleet-wide cost comparison

### Business Rules Documented

The specification includes South African Uber rental business rules:
- **R5000 minimum weekly payment** - Deducted from card earnings only
- **R500 monthly insurance** - Per vehicle insurance premium
- **R200 monthly GPS** - Netstar subscription per vehicle
- **70% cash trip threshold** - Alert trigger for excessive cash trips
- **20% cost variance** - Alert trigger for high maintenance costs

## Using the Specification

### View in Swagger UI

1. Visit [Swagger Editor](https://editor.swagger.io/)
2. Copy the contents of `openapi.yaml`
3. Paste into the editor to view interactive documentation

### Generate Client SDKs

Use OpenAPI Generator to create client libraries:

```bash
# Install OpenAPI Generator
npm install @openapitools/openapi-generator-cli -g

# Generate Python client
openapi-generator-cli generate -i openapi.yaml -g python -o ./client/python

# Generate JavaScript/TypeScript client
openapi-generator-cli generate -i openapi.yaml -g typescript-axios -o ./client/typescript

# Generate Java client
openapi-generator-cli generate -i openapi.yaml -g java -o ./client/java
```

### API Testing

Use the specification for automated API testing:

```bash
# Using Postman
# Import openapi.yaml into Postman to generate collection

# Using Dredd for contract testing
npm install -g dredd
dredd openapi.yaml https://your-api-gateway-url.amazonaws.com/dev
```

### Documentation Generation

Generate static documentation:

```bash
# Using Redoc
npm install -g redoc-cli
redoc-cli bundle openapi.yaml -o api-docs.html

# Using Swagger UI
docker run -p 8080:8080 -e SWAGGER_JSON=/openapi.yaml -v $(pwd):/openapi swaggerapi/swagger-ui
```

## API Design Principles

### RESTful Design
- Resource-based URLs (`/vehicles`, `/drivers`)
- Standard HTTP methods (GET, POST, PUT, DELETE)
- Proper HTTP status codes
- JSON request/response bodies

### Pagination
- `limit` and `offset` query parameters
- Total count returned in responses
- Default limit: 50, max: 100

### Filtering
- Query parameters for common filters
- Status-based filtering
- Date range filtering
- Relationship filtering (e.g., by driver_id, vehicle_id)

### Error Handling
- Consistent error response format
- Descriptive error messages
- HTTP status codes aligned with error types
- Additional error details when available

### Security
- JWT-based authentication
- Role-based access control (RBAC)
- Admin-only operations clearly marked
- HTTPS required for all endpoints

## Validation Rules

### Vehicle Data
- Registration: 1-20 characters
- VIN: Exactly 17 characters
- Year: 1900-2100
- Mileage: Non-negative integer

### Driver Data
- Email: Valid email format
- Phone: 10-15 digits with optional + prefix
- ID Number: Exactly 13 digits (South African ID)
- License: Must have valid expiry date

### Financial Data
- All amounts: Non-negative floats
- Minimum deduction: R5000 (fixed)
- Cash percentage: 0-100%
- Dates: ISO 8601 format (YYYY-MM-DD)

## Response Formats

### Success Responses
- **200 OK** - Successful GET/PUT
- **201 Created** - Successful POST with resource creation
- **204 No Content** - Successful DELETE

### Error Responses
- **400 Bad Request** - Invalid input data
- **401 Unauthorized** - Missing/invalid auth token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource doesn't exist
- **409 Conflict** - Resource conflict (e.g., double assignment)
- **500 Internal Server Error** - Server-side error

## Integration with AWS

### API Gateway Configuration
- Deployed in eu-west-1 (Ireland)
- Stage-based URLs (dev/prod)
- CORS enabled for web clients
- CloudWatch logging enabled
- X-Ray tracing active

### Lambda Integration
- Each endpoint maps to Lambda function
- Event-driven architecture
- Automatic scaling
- 30-second timeout

### Database Integration
- Aurora Serverless v2 (PostgreSQL)
- RDS Data API for serverless access
- DynamoDB for GPS time-series data
- Automatic backups enabled

## Maintenance

### Updating the Specification

When adding new endpoints or modifying existing ones:

1. Update `openapi.yaml` with changes
2. Validate using Swagger Editor or CLI tools
3. Regenerate client SDKs if needed
4. Update this README if major changes
5. Version the API appropriately

### Versioning Strategy

- Current version: 1.0.0
- Semantic versioning (MAJOR.MINOR.PATCH)
- Breaking changes require major version bump
- New endpoints/fields are minor version bumps
- Bug fixes are patch version bumps

## Support

For questions or issues with the API specification:
- Review the design document: `design.md`
- Check requirements: `requirements.md`
- Review implementation tasks: `tasks.md`
- Contact: support@fleet-system.com

## License

Proprietary - All rights reserved
