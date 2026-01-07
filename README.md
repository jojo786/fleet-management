# FLEET - Fleet Location, Efficiency, and Tracking Technology

A comprehensive serverless vehicle and driver management system for Uber rental operations built on AWS. Built using [Kiro](https://kiro.dev/)

## Overview

FLEET manages vehicle fleet operations, driver onboarding and performance tracking, financial settlements, GPS monitoring via Netstar integration, and insurance management.

## Architecture

- **Region**: AWS Ireland (eu-west-1)
- **Backend**: Python 3.11 on AWS Lambda
- **API**: AWS API Gateway
- **Database**: Aurora Serverless v2 (PostgreSQL) + DynamoDB
- **Frontend**: Vue.js 3 with TypeScript (coming soon)
- **Infrastructure**: AWS SAM (Serverless Application Model)

## Quick Start

### Prerequisites

- AWS CLI configured with appropriate permissions
- SAM CLI installed
- Python 3.11+

### Deployment

1. **Deploy to Development:**
   ```bash
   ./deploy.sh dev
   ```

2. **Deploy to Production:**
   ```bash
   ./deploy.sh prod
   ```

### Testing

After deployment, test the health endpoint:
```bash
curl https://your-api-url/health
```

## Project Structure

```
├── src/
│   └── health/          # Health check Lambda function
├── specs/               # System specifications
│   └── vehicle-driver-management/
│       ├── requirements.md
│       ├── design.md
│       └── tasks.md
├── template.yaml        # SAM template
├── deploy.sh           # Deployment script
└── README.md
```

## Development Status

✅ **Foundation** - Basic SAM template and health check deployed to dev and prod  
✅ **Database** - Aurora Serverless v2 with vehicles table deployed to dev and prod  
🔄 **In Progress** - Vehicle Management (Backend + Frontend)  
⏳ **Planned** - Driver Management, Financial Settlement, GPS Tracking, Alerts, Reporting

## API Endpoints

### Development Environment
- Base URL: `https://2ymbcmshsa.execute-api.eu-west-1.amazonaws.com/dev/`
- Health Check: `https://2ymbcmshsa.execute-api.eu-west-1.amazonaws.com/dev/health`

### Production Environment  
- Base URL: `https://15djnxah73.execute-api.eu-west-1.amazonaws.com/prod/`
- Health Check: `https://15djnxah73.execute-api.eu-west-1.amazonaws.com/prod/health`

### Available Endpoints
- `GET /health` - System health check (includes database status)

## Requirements Coverage

The system implements 9 core requirements:
1. Vehicle Fleet Management
2. Driver Onboarding and Management  
3. Financial Settlement Processing
4. GPS Tracking and Behavior Monitoring
5. Insurance Management
6. Performance Monitoring and Reporting
7. Netstar API Integration
8. Service Cost Analysis and Driver Correlation
9. Data Persistence and Security

## License

Private - Fleet Management System