---
inclusion: always
---

# Serverless Deployment Best Practices

This steering file captures critical lessons learned from developing and deploying the FLEET serverless system on AWS. Follow these practices to avoid common pitfalls and ensure smooth deployments.

## 🏗️ Infrastructure & Template Management

### SAM Template Validation
- **ALWAYS validate before deploying**: `sam validate --lint`
- **Fix linting warnings**: Address security and best practice issues early
- **Test template changes**: Use `--disable-rollback` for safer deployments

### Template Organization
- **Separate backend and frontend templates**: Independent scaling and deployment
- **Use environment parameters**: Single template for dev/prod with parameter overrides
- **Consistent naming**: Use `${Environment}` suffix for all resources
- **Clean outputs**: Export values for cross-stack references

### Resource Naming Conflicts
- **CloudWatch Log Groups persist**: Add datetime suffixes to prevent conflicts
  ```yaml
  LogGroupName: !Sub "/aws/lambda/function-name-${Environment}-${RandomSuffix}"
  ```
- **Use RandomSuffix parameter**: Format `YYYYMMDDHHMISS` (e.g., `20260106162100`)
- **Let CloudFormation auto-name**: Avoid custom names for critical resources when possible

## 🗄️ Database & RDS Data API

### RDS Data API Column Naming Issue
- **CRITICAL**: RDS Data API returns generic column names (`column_0`, `column_1`, etc.) instead of actual field names
- **Impact**: Frontend receives `{column_0: "Toyota", column_1: "Camry"}` instead of `{make: "Toyota", model: "Camry"}`
- **Solution**: Always use column aliases or manual mapping in your Lambda functions

#### Column Mapping Strategies
1. **Use Column Aliases in SQL**:
   ```sql
   SELECT 
       v.make as make,
       v.model as model,
       v.registration as registration
   FROM vehicles v
   ```

2. **Manual Mapping in Lambda**:
   ```python
   def map_vehicle_columns(raw_data):
       return {
           'id': raw_data.get('column_0'),
           'make': raw_data.get('column_1'),
           'model': raw_data.get('column_2'),
           'registration': raw_data.get('column_3')
       }
   ```

3. **Use includeResultMetadata Parameter**:
   ```python
   response = rds_client.execute_statement(
       resourceArn=cluster_arn,
       secretArn=secret_arn,
       database=database_name,
       sql=sql,
       includeResultMetadata=True  # This provides column names
   )
   ```

### Database Connection Best Practices
- **Connection Pooling**: Use RDS Proxy for connection management
- **Error Handling**: Always wrap database calls in try-catch blocks
- **Parameterized Queries**: Use parameters to prevent SQL injection
- **Transaction Management**: Use transactions for multi-step operations

## 🧪 Testing Requirements

### Mandatory Testing for All Features
Every new feature MUST include comprehensive test coverage before deployment:

#### Required Test Types
1. **Unit Tests**: Test individual functions and components
   - Test all API endpoints with various input scenarios
   - Test business logic with edge cases and error conditions
   - Test data validation and sanitization
   - Minimum 80% code coverage required

2. **Property-Based Tests**: Test universal properties across randomized inputs
   - Each correctness property from design document must have a corresponding test
   - Minimum 100 iterations per property test
   - Use appropriate PBT library (Hypothesis for Python, fast-check for JavaScript)
   - Tag format: `Feature: {feature_name}, Property {number}: {property_text}`

3. **Integration Tests**: Test component interactions
   - API Gateway to Lambda integration
   - Lambda to database connectivity
   - External service integrations (with mocking)
   - End-to-end user workflows

4. **Error Handling Tests**: Test system resilience
   - Database connection failures
   - External API failures
   - Invalid input handling
   - Authentication/authorization failures

#### Testing Framework Requirements
- **Python Backend**: pytest + Hypothesis for property-based testing
- **JavaScript Frontend**: Jest + fast-check for property-based testing
- **AWS Integration**: moto for AWS service mocking
- **Database Testing**: pytest-postgresql for Aurora, moto for DynamoDB
- **API Testing**: requests library with proper error handling

#### Test Organization
```
tests/
├── unit/
│   ├── test_vehicle_management.py
│   ├── test_service_records.py
│   └── test_maintenance_alerts.py
├── property/
│   ├── test_vehicle_properties.py
│   ├── test_service_properties.py
│   └── test_cost_properties.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_database_operations.py
│   └── test_external_services.py
└── fixtures/
    ├── sample_vehicles.py
    ├── sample_service_records.py
    └── mock_responses.py
```

#### Testing Checklist
Before deploying any feature:
- [ ] All unit tests pass with ≥80% coverage
- [ ] All property-based tests pass (100+ iterations each)
- [ ] Integration tests validate end-to-end workflows
- [ ] Error handling tests verify system resilience
- [ ] Performance tests validate acceptable response times
- [ ] Security tests verify proper access controls
- [ ] Tests run successfully in CI/CD pipeline

#### Property-Based Testing Guidelines
- **Generate realistic test data**: Use domain-appropriate generators
- **Test invariants**: Properties that should always hold true
- **Test round-trip operations**: serialize/deserialize, create/retrieve
- **Test idempotent operations**: operations that can be repeated safely
- **Test error boundaries**: invalid inputs should be handled gracefully

#### Continuous Testing
- **Pre-commit hooks**: Run unit tests before code commits
- **CI/CD integration**: All tests must pass before deployment
- **Automated regression testing**: Run full test suite on every change
- **Performance monitoring**: Track test execution times and system performance

## 🌐 Frontend Deployment & API Integration

### Dynamic API URL Configuration
- **CRITICAL**: Never hardcode API URLs in deployment scripts
- **Issue**: API Gateway URLs change when stacks are recreated
- **Solution**: Always fetch API URLs dynamically from CloudFormation outputs

#### Correct Frontend Deployment Pattern
```bash
# Get API URL from backend stack
API_URL=$(aws cloudformation describe-stacks \
    --stack-name $BACKEND_STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`FleetApiUrl`].OutputValue' \
    --output text)

# Replace placeholder in JavaScript
sed "s|API_URL_PLACEHOLDER|$API_URL|g" frontend/app.js > /tmp/app-$ENVIRONMENT.js
```

### CORS and Browser Caching Issues
- **Browser Cache**: Use aggressive cache invalidation for JavaScript files
- **CloudFront**: Set `Cache-Control: no-cache, no-store, must-revalidate` for app.js
- **CORS Headers**: Ensure all API endpoints return proper CORS headers
- **Preflight Requests**: Handle OPTIONS requests for complex CORS scenarios

### Common Frontend Issues
1. **"Failed to fetch" errors**: Usually indicates wrong API URL or CORS issues
2. **Undefined values**: Often caused by RDS Data API column naming (see Database section)
3. **Stale cache**: CloudFront may serve old files - always invalidate cache after deployment
4. **JavaScript type conversion errors**: RDS Data API returns numeric values as strings, causing `.toFixed()` errors
   - **Issue**: Database returns `{total_cost: "150.50"}` but JavaScript expects `{total_cost: 150.50}`
   - **Solution**: Always convert string values to numbers before calling numeric methods:
     ```javascript
     const totalCost = parseFloat(item.total_cost) || 0;
     const formattedCost = totalCost.toFixed(2); // Now works correctly
     ```

## 🚀 Deployment Workflow

### Feature Development Cycle
For each feature, follow this exact sequence:
1. **Backend Development** → Deploy to Dev → Test API endpoints
2. **Frontend Development** → Deploy to Dev → Test UI integration  
3. **Dev Environment Testing** → Full end-to-end validation
4. **Production Deployment** → Backend to Prod → Frontend to Prod
5. **Production Testing** → Smoke tests and validation

### Environment Strategy
- **Complete separation**: No environment switchers in frontend
- **Independent stacks**: `app-backend-dev`, `app-frontend-dev`, `app-backend-prod`, `app-frontend-prod`
- **Environment-specific builds**: Inject API URLs during deployment
- **Parity enforcement**: Dev and prod must mirror each other exactly

### Deployment Commands
```bash
# Always validate first
sam validate --lint

# Build and deploy backend with rollback disabled
sam build
sam deploy --stack-name app-backend-dev --parameter-overrides Environment=dev --disable-rollback

# Deploy frontend with environment-specific configuration
./deploy-frontend.sh dev
```

## 🔧 CloudFormation Troubleshooting

### Stack Failure Recovery
- **Check stack events**: `aws cloudformation describe-stack-events`
- **Use describe-change-set**: For AWS::EarlyValidation errors
- **Delete and recreate**: Better than fixing rollback states
- **Always update RandomSuffix after deletion**: Prevents resource conflicts on redeploy
- **Wait for completion**: Use CloudFormation waiters for automation

### Common Error Patterns
- **Resource conflicts**: Existing resources prevent stack creation
- **Deletion protection**: Aurora clusters need manual protection disabling
- **Custom resource naming**: Can cause replacement issues during updates
- **IAM permissions**: Ensure sufficient permissions for all resource operations

### Stack State Management
```bash
# Check stack status
aws cloudformation describe-stacks --stack-name STACK_NAME --query 'Stacks[0].StackStatus'

# Wait for operations to complete
aws cloudformation wait stack-delete-complete --stack-name STACK_NAME

# Delete failed stacks
aws cloudformation delete-stack --stack-name STACK_NAME

# CRITICAL: Always update RandomSuffix after stack deletion
# Update template.yaml RandomSuffix parameter to new timestamp before redeploying
```

## 🔒 Security & Access Control

### S3 & CloudFront Best Practices
- **Use Origin Access Control (OAC)**: Modern replacement for OAI
- **Avoid public S3 buckets**: Account-level Block Public Access overrides bucket settings
- **CloudFront + S3**: More secure than public buckets with global CDN benefits
- **Proper bucket policies**: Use correct ARN format and CloudFront service principal

### Secure S3 Bucket Policy Example
```yaml
FrontendBucketPolicy:
  Type: AWS::S3::BucketPolicy
  Properties:
    Bucket: !Ref FrontendBucket
    PolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Sid: AllowCloudFrontServicePrincipal
          Effect: Allow
          Principal:
            Service: cloudfront.amazonaws.com
          Action: 's3:GetObject'
          Resource: !Sub 'arn:aws:s3:::${FrontendBucket}/*'
          Condition:
            StringEquals:
              'AWS:SourceArn': !Sub 'arn:aws:cloudfront::${AWS::AccountId}:distribution/${Distribution}'
```

## 📊 Monitoring & Observability

### Built-in AWS Monitoring
- **Enable X-Ray tracing**: Add `Tracing: Active` to all Lambda functions
- **CloudWatch logs**: Automatic logging with proper retention policies
- **API Gateway logs**: Use single-line JSON format for access logs
- **Custom metrics**: Track business KPIs through CloudWatch

### API Gateway Logging
```yaml
AccessLogSetting:
  DestinationArn: !GetAtt ApiGatewayLogGroup.Arn
  Format: '{"requestId":"$context.requestId","ip":"$context.identity.sourceIp","status":"$context.status"}'
```

## 🔄 Automation & Scripting

### Deployment Script Best Practices
- **Environment-specific builds**: Dynamic configuration injection
- **Content type management**: Set proper MIME types for web assets
- **Cache invalidation**: Clear CloudFront cache for immediate updates
- **Error handling**: Graceful failure with informative messages

### Frontend Deployment Pattern
```bash
# Create environment-specific JavaScript
sed "s|API_URL_PLACEHOLDER|$API_URL|g" frontend/app.js > /tmp/app-$ENVIRONMENT.js

# Upload with proper content types
aws s3 cp /tmp/app-$ENVIRONMENT.js s3://$BUCKET/app.js --content-type "application/javascript"

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
```

## 🎯 Architecture Decisions

### Serverless Benefits
- **No server management**: Pure Lambda + managed services
- **Automatic scaling**: Handles traffic without configuration
- **Cost efficiency**: Pay-per-use model for development
- **Regional deployment**: Choose region closest to users

### Template Separation Strategy
- **Backend template**: Lambda functions, databases, API Gateway
- **Frontend template**: S3, CloudFront, static hosting
- **Independent deployment**: Frontend and backend can deploy separately
- **Cross-stack references**: Use CloudFormation exports when needed

## ⚠️ Common Pitfalls to Avoid

### Database Issues
- ❌ **RDS Data API column names**: Forgetting that Data API returns `column_0`, `column_1` instead of field names
- ❌ **Missing includeResultMetadata**: Not setting this parameter to get proper column names
- ❌ **Hardcoded column mapping**: Assuming column order will never change

### Deployment Failures
- ❌ **Skipping validation**: Always run `sam validate --lint` first
- ❌ **Resource name conflicts**: Use datetime suffixes for Log Groups
- ❌ **Public S3 buckets**: Use CloudFront OAC instead
- ❌ **Mixed environments**: Keep dev/prod completely separate
- ❌ **Hardcoded API URLs**: Always fetch URLs dynamically from CloudFormation

### Frontend Issues
- ❌ **Stale browser cache**: Users may see old JavaScript files
- ❌ **CORS configuration**: Missing or incorrect CORS headers cause "Failed to fetch"
- ❌ **API URL mismatches**: Frontend pointing to wrong or non-existent API Gateway
- ❌ **JavaScript type conversion**: Calling `.toFixed()` on string values from RDS Data API

### Development Workflow Issues
- ❌ **Environment switchers**: Deploy separate frontend instances
- ❌ **Incomplete features**: Always deploy backend + frontend together
- ❌ **Skipping prod deployment**: Every feature must work in production
- ❌ **Manual processes**: Automate everything with scripts

### Security Mistakes
- ❌ **Public bucket policies**: Account-level settings override bucket settings
- ❌ **Hardcoded credentials**: Use IAM roles and managed secrets
- ❌ **Open CORS policies**: Restrict origins in production
- ❌ **Missing encryption**: Enable encryption at rest for all data stores

## 📋 Deployment Checklist

Before deploying any feature:
- [ ] SAM template validates with `--lint`
- [ ] Backend APIs tested locally or in dev
- [ ] Frontend integrates with backend APIs
- [ ] Environment-specific configuration handled
- [ ] Monitoring and logging configured
- [ ] Security best practices followed
- [ ] Deployment scripts tested
- [ ] Rollback plan prepared

After deployment:
- [ ] Health checks pass
- [ ] API endpoints respond correctly
- [ ] Frontend loads and functions
- [ ] Monitoring dashboards show green
- [ ] End-to-end workflows tested
- [ ] Production smoke tests pass

## 🎓 Key Takeaways

1. **Validate early, validate often** - Prevents deployment failures
2. **Separate concerns cleanly** - Independent deployment enables faster iteration
3. **Embrace managed services** - Less infrastructure, more features
4. **Environment parity is crucial** - Dev/prod differences cause production issues
5. **Security by default** - Use modern AWS security patterns
6. **Automate everything** - Scripts eliminate manual errors
7. **Monitor comprehensively** - Built-in observability catches issues early
8. **Deploy incrementally** - Each feature fully functional before next

Following these practices ensures reliable, secure, and maintainable serverless applications on AWS.