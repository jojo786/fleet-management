# FLEET - Fleet Location, Efficiency, and Tracking Technology

A comprehensive serverless vehicle and driver management system for Uber rental operations built on AWS. Built using [Kiro](https://kiro.dev/)

## Overview

FLEET manages vehicle fleet operations, driver onboarding and performance tracking, financial settlements, GPS monitoring via Netstar integration, and insurance management.

## Architecture

- **Region**: AWS Ireland (eu-west-1)
- **Backend**: Python 3.11 on AWS Lambda
- **API**: AWS API Gateway
- **Authentication**: AWS Cognito User Pools with JWT tokens
- **Database**: Aurora Serverless v2 (PostgreSQL) + DynamoDB
- **Frontend**: Vanilla JavaScript (ES6+) with HTML5 and CSS3
- **Infrastructure**: AWS SAM (Serverless Application Model)

## Quick Start

### Prerequisites

**Backend Requirements:**
- AWS CLI configured with appropriate permissions
- SAM CLI installed (`brew install aws-sam-cli` on macOS)
- Python 3.11+
- AWS account with permissions for Lambda, API Gateway, Aurora, DynamoDB, S3, CloudFront, Cognito

**Frontend Requirements:**
- AWS CLI configured
- S3 bucket access for static hosting
- CloudFront distribution (optional but recommended)

### Authentication Setup

FLEET uses **AWS Cognito** for authentication. Before using the system, you need to:

1. **Deploy Cognito User Pool** (included in SAM template)
2. **Create an admin user**
3. **Configure frontend with Cognito credentials**

See `docs/AUTHENTICATION_IMPLEMENTATION.md` for complete setup instructions.

**Quick Admin User Creation:**
```bash
# After deploying backend, create admin user
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name fleet-backend-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username admin@fleet.com \
  --user-attributes Name=email,Value=admin@fleet.com Name=name,Value="Fleet Admin" Name=custom:role,Value=admin \
  --temporary-password "TempPass123!" \
  --message-action SUPPRESS

aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username admin@fleet.com \
  --password "YourSecurePassword123!" \
  --permanent
```

### Backend Installation & Deployment

#### 1. Install Dependencies

```bash
# Install Python dependencies for each Lambda function
pip install -r src/health/requirements.txt
pip install -r src/vehicles/requirements.txt
pip install -r src/drivers/database/requirements.txt
```

#### 2. Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and default region (eu-west-1)
```

#### 3. Validate SAM Template

```bash
sam validate --lint
```

#### 4. Build the Backend

```bash
sam build
```

#### 5. Deploy to Development

```bash
# First deployment (guided)
sam deploy --guided --stack-name fleet-backend-dev --parameter-overrides Environment=dev

# Subsequent deployments
./deploy.sh dev
```

#### 6. Deploy to Production

```bash
sam deploy --stack-name fleet-backend-prod --parameter-overrides Environment=prod
# Or use the deployment script
./deploy.sh prod
```

#### 7. Get API Gateway URL

After deployment, retrieve your API Gateway URL:

```bash
# For dev environment
aws cloudformation describe-stacks \
  --stack-name fleet-backend-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`FleetApiUrl`].OutputValue' \
  --output text

# For prod environment
aws cloudformation describe-stacks \
  --stack-name fleet-backend-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`FleetApiUrl`].OutputValue' \
  --output text
```

### Frontend Installation & Deployment

#### 1. Configure Frontend Template

The frontend uses a separate SAM template (`frontend-template.yaml`) for S3 and CloudFront.

#### 2. Deploy Frontend Infrastructure

```bash
# Deploy frontend stack (S3 + CloudFront)
sam deploy --template-file frontend-template.yaml \
  --stack-name fleet-frontend-dev \
  --parameter-overrides Environment=dev

# For production
sam deploy --template-file frontend-template.yaml \
  --stack-name fleet-frontend-prod \
  --parameter-overrides Environment=prod
```

#### 3. Deploy Frontend Files

Use the deployment script to inject the API URL and upload files:

```bash
# Deploy to dev
./deploy-frontend.sh dev

# Deploy to prod
./deploy-frontend.sh prod
```

The script will:
- Fetch the API Gateway URL from the backend stack
- Replace `API_URL_PLACEHOLDER` in `frontend/app.js` with the actual URL
- Upload all frontend files to S3 with correct content types
- Invalidate CloudFront cache for immediate updates

#### 4. Access the Frontend

After deployment, get your CloudFront URL:

```bash
# For dev
aws cloudformation describe-stacks \
  --stack-name fleet-frontend-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
  --output text

# For prod
aws cloudformation describe-stacks \
  --stack-name fleet-frontend-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
  --output text
```

### Testing

#### Backend Health Check

```bash
# Test dev environment
curl https://your-dev-api-url/health

# Test prod environment
curl https://your-prod-api-url/health
```

#### Run Test Suite

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run all tests
python tests/run_tests.py --all

# Run specific test types
python tests/run_tests.py --unit
python tests/run_tests.py --property
python tests/run_tests.py --integration

# Run with coverage
python tests/run_tests.py --coverage
```

### Local Development

#### Run Backend Locally

```bash
# Start local API Gateway and Lambda
./run-local.sh

# Test local endpoint
curl http://localhost:3000/health
```

#### Test Frontend Locally

```bash
# Serve frontend files locally (requires Python)
cd frontend
python -m http.server 8000

# Open browser to http://localhost:8000
```

### Troubleshooting

#### Backend Issues

**CloudWatch Log Group Conflicts:**
If deployment fails with log group conflicts, update the `RandomSuffix` parameter in `template.yaml` to a new timestamp (format: `YYYYMMDDHHMISS`).

**Database Connection Issues:**
Check Aurora Serverless v2 is running and accessible. View logs in CloudWatch:
```bash
sam logs -n HealthFunction --stack-name fleet-backend-dev --tail
```

**RDS Data API Column Names:**
The RDS Data API returns generic column names (`column_0`, `column_1`). Always use `includeResultMetadata=True` or column aliases in SQL queries.

#### Frontend Issues

**Stale Cache:**
If changes don't appear, invalidate CloudFront cache:
```bash
DIST_ID=$(aws cloudformation describe-stacks \
  --stack-name fleet-frontend-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`DistributionId`].OutputValue' \
  --output text)

aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
```

**API Connection Errors:**
Verify the API URL in `app.js` matches your backend API Gateway URL. Check CORS headers are properly configured in Lambda responses.

**Type Conversion Errors:**
RDS Data API returns numeric values as strings. Always use `parseFloat()` before calling `.toFixed()` on numeric values.

## Project Structure

```
├── src/                          # Backend Lambda functions
│   ├── health/                   # Health check endpoint
│   │   ├── handler.py
│   │   └── requirements.txt
│   ├── vehicles/                 # Vehicle management
│   │   ├── handler.py
│   │   ├── db_utils.py
│   │   └── requirements.txt
│   ├── drivers/                  # Driver management
│   │   ├── handler.py
│   │   └── database/
│   └── database/                 # Shared database utilities
│       ├── db_utils.py
│       └── init_handler.py
├── frontend/                     # Frontend static files
│   ├── index.html               # Main HTML page
│   ├── app.js                   # Vue.js application
│   └── styles.css               # Styling
├── tests/                        # Comprehensive test suite
│   ├── unit/                    # Unit tests
│   ├── property/                # Property-based tests (Hypothesis)
│   ├── integration/             # Integration tests
│   ├── fixtures/                # Test fixtures and mock data
│   ├── run_tests.py            # Test runner script
│   └── requirements.txt         # Test dependencies
├── specs/                        # System specifications
│   └── vehicle-driver-management/
│       ├── requirements.md      # EARS requirements
│       ├── design.md           # System design & architecture
│       └── tasks.md            # Implementation tasks
├── .kiro/                       # Kiro configuration
│   └── steering/               # Development best practices
├── template.yaml                # Backend SAM template
├── frontend-template.yaml       # Frontend SAM template
├── deploy.sh                    # Backend deployment script
├── deploy-frontend.sh          # Frontend deployment script
├── run-local.sh                # Local development script
└── README.md
```

## Development Status

✅ **Foundation** - Basic SAM template and health check deployed to dev and prod  
✅ **Database** - Aurora Serverless v2 with vehicles and drivers tables deployed  
✅ **Vehicle Management** - Complete CRUD operations, service records, cost analysis (Backend + Frontend)  
✅ **Driver Management** - Driver onboarding, assignments, performance tracking (Backend + Frontend)  
✅ **Testing** - Comprehensive test suite with unit, property-based, and integration tests  
🔄 **In Progress** - Financial Settlement features  
⏳ **Planned** - GPS Tracking, Alerts & Notifications, Reporting System, Security & Compliance

### Completed Features

**Vehicle Management:**
- Vehicle registration and profile management
- Service record tracking with cost analysis
- Maintenance alerts and scheduling
- Fleet cost comparison and reporting
- High maintenance cost alerts

**Driver Management:**
- Driver onboarding with license validation
- Vehicle assignment management
- Performance tracking and metrics
- Target achievement monitoring
- Driver ranking and trend analysis

**Testing Infrastructure:**
- 80%+ code coverage with unit tests
- Property-based tests using Hypothesis (100+ iterations per property)
- Integration tests for API Gateway → Lambda → Aurora Serverless
- Comprehensive test fixtures and mock data

## API Endpoints

### Development Environment
- Base URL: `https://2ymbcmshsa.execute-api.eu-west-1.amazonaws.com/dev/`
- Health Check: `https://2ymbcmshsa.execute-api.eu-west-1.amazonaws.com/dev/health`

### Production Environment  
- Base URL: `https://15djnxah73.execute-api.eu-west-1.amazonaws.com/prod/`
- Health Check: `https://15djnxah73.execute-api.eu-west-1.amazonaws.com/prod/health`

### Available Endpoints

**Health & System:**
- `GET /health` - System health check (includes database status)

**Vehicle Management:**
- `POST /vehicles` - Create new vehicle
- `GET /vehicles` - List all vehicles
- `GET /vehicles/{id}` - Get vehicle by ID
- `PUT /vehicles/{id}` - Update vehicle
- `DELETE /vehicles/{id}` - Delete vehicle
- `POST /vehicles/{id}/service-records` - Add service record
- `GET /vehicles/{id}/service-history` - Get service history
- `GET /vehicles/maintenance-alerts` - Get maintenance alerts
- `GET /vehicles/service-costs` - Get service cost analysis

**Driver Management:**
- `POST /drivers` - Create new driver
- `GET /drivers` - List all drivers
- `GET /drivers/{id}` - Get driver by ID
- `PUT /drivers/{id}` - Update driver
- `DELETE /drivers/{id}` - Delete driver
- `POST /drivers/{id}/assign-vehicle` - Assign vehicle to driver
- `GET /drivers/{id}/assignments` - Get driver assignments
- `GET /drivers/{id}/performance` - Get driver performance metrics

**Coming Soon:**
- Financial settlement endpoints
- GPS tracking endpoints
- Alert and notification endpoints
- Reporting endpoints

## Requirements Coverage

The system implements 9 core requirements with comprehensive testing:

1. **Vehicle Fleet Management** ✅
   - Vehicle inventory and maintenance tracking
   - Service records with cost analysis
   - Maintenance alerts and scheduling
   - Fleet cost comparison and reporting

2. **Driver Onboarding and Management** ✅
   - Driver registration with license validation
   - Vehicle assignment management
   - Performance tracking and metrics
   - Target achievement monitoring

3. **Financial Settlement Processing** 🔄
   - Weekly settlement calculations (planned)
   - Card and cash payment tracking (planned)
   - R5000 minimum deduction logic (planned)

4. **GPS Tracking and Behavior Monitoring** ⏳
   - Netstar API integration (planned)
   - Real-time location tracking (planned)
   - Speed violation detection (planned)

5. **Insurance Management** ⏳
   - Policy tracking and renewals (planned)
   - Claims management (planned)
   - R500 monthly premium tracking (planned)

6. **Performance Monitoring and Reporting** ✅
   - Weekly earnings tracking
   - Performance metrics and rankings
   - Target achievement analysis

7. **Netstar API Integration** ⏳
   - GPS data synchronization (planned)
   - R200 monthly cost tracking (planned)

8. **Service Cost Analysis and Driver Correlation** ✅
   - Cost categorization by maintenance type
   - Driver-vehicle service cost correlation
   - Fleet cost comparison

9. **Data Persistence and Security** ✅
   - Aurora Serverless v2 for relational data
   - DynamoDB for time-series data (ready)
   - Comprehensive test coverage

## Technology Stack

**Backend:**
- Python 3.11 on AWS Lambda
- Aurora Serverless v2 (PostgreSQL) for relational data
- DynamoDB for GPS time-series data
- AWS API Gateway for REST API
- AWS Cognito User Pools for authentication
- JWT tokens for API authorization
- boto3 for AWS service integration

**Frontend:**
- Vanilla JavaScript (ES6+) with class-based architecture
- HTML5 and CSS3 for UI
- No build tools required - pure static files
- S3 for static hosting
- CloudFront for CDN and caching

**Infrastructure:**
- AWS SAM (Serverless Application Model)
- CloudFormation for infrastructure as code
- CloudWatch for logging and monitoring
- EventBridge for scheduled tasks (planned)
- SES/SNS for notifications (planned)

**Testing:**
- pytest for unit testing
- Hypothesis for property-based testing
- moto for AWS service mocking
- pytest-postgresql for database testing

**Development:**
- Built with [Kiro](https://kiro.dev/) - AI-powered development assistant
- Spec-driven development methodology
- EARS (Easy Approach to Requirements Syntax) for requirements
- Property-based testing for correctness validation

## Contributing

This is a private project. For questions or issues, please contact the development team.

## Documentation

Comprehensive documentation is available in the `specs/` directory:
- **requirements.md** - Detailed EARS requirements with acceptance criteria
- **design.md** - System architecture, data models, and correctness properties
- **tasks.md** - Implementation plan with 32 major tasks
- **ARCHITECTURE.md** - Architecture diagrams and component descriptions

## License

Private - Fleet Management System