# Implementation Plan: Vehicle and Driver Management System

## Overview

This implementation plan creates a comprehensive serverless vehicle and driver management system using AWS services with an agile, incrementally deployable approach. Each feature is built, tested, and deployed independently to ensure the system is always deployable. The system uses Python Lambda functions for backend processing, Aurora Serverless v2 for relational data, DynamoDB for GPS time-series data, and various AWS services for notifications and monitoring - all without VPCs for pure serverless architecture.

## Tasks

- [x] 1. Create minimal SAM template and deploy foundation
  - Create basic SAM template with API Gateway
  - Set up minimal Lambda function for health check
  - Configure basic CloudWatch logging
  - Deploy to dev environment and test
  - _Requirements: 9.1, 9.2_

- [ ]* 1.1 Write infrastructure tests
  - Test SAM template deployment
  - Validate API Gateway health check endpoint
  - _Requirements: 9.1, 9.2_

- [x] 1.2 Deploy to production
  - Deploy foundation to production environment
  - Verify health check endpoint works
  - Set up basic monitoring alerts

- [x] 2. Add Aurora Serverless database and deploy
  - Add Aurora Serverless v2 to SAM template
  - Create initial database schema for vehicles table
  - Add database connection utilities
  - Deploy to dev and test database connectivity
  - _Requirements: 1.1_

- [ ]* 2.1 Write database connectivity tests
  - Test Aurora connection from Lambda
  - Validate schema creation
  - _Requirements: 1.1_

- [x] 2.2 Deploy database changes to production
  - Deploy Aurora Serverless to production
  - Run database schema migration
  - Verify connectivity

- [-] 3. Implement Vehicle Management (Backend + Frontend) and deploy
  - [x] 3.1 Create vehicle CRUD operations (Backend)
    - Implement create_vehicle function with validation
    - Implement get_vehicle and list_vehicles functions
    - Implement update_vehicle with status management
    - Add API Gateway routes for vehicle endpoints
    - _Requirements: 1.1_

  - [ ] 3.2 Create basic vehicle management interface (Frontend)
    - Create simple HTML/CSS/JavaScript frontend (no build tools needed)
    - Build vehicle registration form with validation
    - Implement vehicle list view with real-time data from API
    - Add basic vehicle editing and status management
    - Include API integration for all CRUD operations
    - Deploy as static files to S3 with CloudFront distribution
    - _Requirements: 1.1_

  - [ ]* 3.3 Write property test for vehicle data integrity
    - **Property 1: Vehicle Data Integrity**
    - **Validates: Requirements 1.1**

  - [x] 3.4 Deploy Vehicle Management to dev
    - Deploy vehicle Lambda and API routes
    - Deploy frontend with vehicle management features
    - Test all CRUD operations via UI and API
    - Verify data persistence in Aurora

  - [x] 3.5 Deploy Vehicle Management to production
    - Deploy vehicle management backend to production
    - Deploy frontend to production
    - Run smoke tests on production system

- [x] 4. Add service records to Vehicle Management (Backend + Frontend) and deploy
  - [x] 4.1 Extend database schema for service records
    - Add service_records table with foreign keys
    - Add maintenance_types lookup table
    - Update vehicle model to include service relationships
    - _Requirements: 1.2, 1.5_

  - [x] 4.2 Implement service record management (Backend)
    - Create add_service_record function with cost tracking
    - Implement get_service_history with driver correlation
    - Add maintenance alert generation logic
    - Add API routes for service record endpoints
    - _Requirements: 1.2, 1.4, 1.5_

  - [x] 4.3 Create service record interface (Frontend)
    - Build service record entry forms
    - Implement service history views
    - Add maintenance alert dashboard
    - Create cost tracking visualizations
    - _Requirements: 1.2, 1.4, 1.5_

  - [ ]* 4.4 Write property test for service record completeness
    - **Property 2: Service Record Completeness**
    - **Validates: Requirements 1.2, 1.5**

  - [x] 4.5 Deploy service records to dev
    - Deploy database schema changes
    - Deploy updated vehicle Lambda
    - Deploy updated frontend with service features
    - Test service record CRUD operations via UI

  - [x] 4.6 Deploy service records to production
    - Deploy schema and Lambda updates to production
    - Deploy frontend updates to production
    - Verify service record functionality

- [x] 5. Add Comprehensive Test Cases
  - [x] 5.1 Update steering file with testing requirements
    - Added comprehensive testing requirements section to `.kiro/steering/serverless-deployment-best-practices.md`
    - Defined mandatory test types: unit tests, property-based tests, integration tests, error handling tests
    - Specified testing framework requirements and organization structure
    - Created testing checklist and continuous testing guidelines
    - _Requirements: All features must have comprehensive test coverage_

  - [x] 5.2 Update design document with testing strategy
    - Enhanced testing strategy section in `specs/vehicle-driver-management/design.md`
    - Added detailed test coverage requirements and implementation guidelines
    - Defined property-based testing approach with Hypothesis
    - Specified integration testing requirements for API and database operations
    - _Requirements: Testing strategy must align with system architecture_

  - [x] 5.3 Create test infrastructure and fixtures
    - Set up complete test directory structure with `tests/{unit,property,integration,fixtures}` folders
    - Created comprehensive test fixtures in `tests/fixtures/sample_vehicles.py` and `mock_responses.py`
    - Implemented test requirements file with all necessary dependencies
    - Created test runner script `tests/run_tests.py` with multiple execution modes
    - _Requirements: Test infrastructure must support all test types_

  - [x] 5.4 Implement unit tests for vehicle management
    - Created comprehensive unit tests in `tests/unit/test_vehicle_management.py`
    - Tests cover all CRUD operations, validation, error handling, and CORS
    - Implemented tests for create, read, update, delete vehicle operations
    - Added tests for query parameter handling and database error scenarios
    - _Requirements: 1.1 - Vehicle management functionality_

  - [x] 5.5 Implement unit tests for service records
    - Created comprehensive unit tests in `tests/unit/test_service_records.py`
    - Tests cover service record creation, history retrieval, and maintenance alerts
    - Implemented tests for validation, error handling, and data formatting
    - Added tests for query filters and column metadata mapping
    - _Requirements: 1.2, 1.5 - Service record management and maintenance alerts_

  - [x] 5.6 Implement property-based tests for vehicles
    - Created property-based tests in `tests/property/test_vehicle_properties.py` using Hypothesis
    - **Property 1: Vehicle Data Integrity** - Vehicle data preservation during storage/retrieval
    - **Property 2: Service Record Completeness** - Service records capture all required fields
    - Tests use realistic data generators and validate universal properties across randomized inputs
    - _Requirements: 1.1, 1.2 - Data integrity and completeness_

  - [x] 5.7 Implement property-based tests for service records
    - Created property-based tests in `tests/property/test_service_properties.py`
    - **Property 3: Cost Threshold Alerting** - High-cost services generate appropriate alerts
    - **Property 4: Service History Persistence** - Service history returns all records chronologically
    - Tests validate cost calculations, data persistence, and error boundary handling
    - _Requirements: 1.2, 1.5, 1.8 - Service records, maintenance alerts, cost tracking_

  - [x] 5.8 Implement integration tests
    - Created API endpoint integration tests in `tests/integration/test_api_endpoints.py`
    - Created database operations integration tests in `tests/integration/test_database_operations.py`
    - Tests validate complete API Gateway to Lambda to Aurora Serverless integration
    - Tests cover end-to-end workflows, CORS headers, and error handling
    - _Requirements: System integration and end-to-end functionality_

  - [x] 5.9 Create test documentation and runner
    - Created comprehensive test documentation in `tests/README.md`
    - Implemented test runner script with multiple execution modes (unit, property, integration, coverage)
    - Added test configuration, debugging guides, and maintenance instructions
    - Created coverage reporting and CI/CD integration guidelines
    - _Requirements: Test maintainability and developer experience_

  - [x] 5.10 Validate test suite completeness
    - All unit tests pass with proper mocking and error handling
    - Property-based tests validate universal properties with 100+ iterations
    - Integration tests verify complete component interactions
    - Test coverage meets minimum 80% requirement
    - Test suite ready for CI/CD integration and continuous testing
    - _Requirements: Comprehensive test coverage for all implemented features_

- [x] 6. Add cost analysis and alerting to Vehicle Management (Backend + Frontend) and deploy
  - [x] 6.1 Implement cost analysis features (Backend)
    - Add service cost comparison across vehicles
    - Implement high maintenance cost alert generation
    - Create cost categorization by maintenance type
    - Add cost analysis API endpoints
    - _Requirements: 1.6, 1.7, 1.8_

  - [x] 6.2 Create cost analysis interface (Frontend)
    - Build cost comparison dashboards
    - Implement alert notification displays
    - Add cost breakdown visualizations
    - Create fleet cost comparison charts
    - _Requirements: 1.6, 1.7, 1.8_

  - [ ]* 6.3 Write property test for cost threshold alerting
    - **Property 5: Cost Threshold Alerting**
    - **Validates: Requirements 1.8**

  - [x] 6.4 Deploy cost analysis to dev
    - Deploy updated vehicle Lambda with cost features
    - Deploy frontend with cost analysis UI
    - Test cost analysis and alert generation

  - [x] 6.5 Deploy cost analysis to production
    - Deploy cost analysis features to production
    - Deploy frontend updates to production
    - Verify alert generation works

- [x] 7. Checkpoint - Vehicle Management complete and deployed
  - Ensure all vehicle management features work in production
  - Verify data integrity and API functionality
  - Test complete vehicle management workflow end-to-end

- [ ] 8. Implement Driver Management (Backend + Frontend) and deploy
  - [x] 8.1 Add driver database schema
    - Create drivers table with personal information
    - Create driver_assignments table for vehicle assignments
    - Add driver status and performance tracking tables
    - _Requirements: 2.1, 2.3_

  - [x] 8.2 Create driver CRUD operations (Backend)
    - Implement create_driver with license validation
    - Implement get_driver with performance history
    - Add driver status management
    - Add API Gateway routes for driver endpoints
    - _Requirements: 2.1, 2.2_

  - [x] 8.3 Create driver management interface (Frontend)
    - Build driver onboarding forms
    - Implement driver list and profile views
    - Add driver status management UI
    - Create driver search and filtering
    - _Requirements: 2.1, 2.2_

  - [ ]* 8.4 Write property test for driver data integrity
    - **Property 6: Driver Data Integrity**
    - **Validates: Requirements 2.1**

  - [ ]* 8.5 Write property test for license validation
    - **Property 7: Driver License Validation**
    - **Validates: Requirements 2.2**

  - [x] 8.6 Deploy Driver Management to dev
    - Deploy driver Lambda and database schema
    - Deploy frontend with driver management features
    - Test driver CRUD operations via UI and API

  - [x] 8.7 Deploy Driver Management to production
    - Deploy driver management to production
    - Deploy frontend updates to production
    - Verify driver functionality

- [x] 9. Add vehicle assignment management (Backend + Frontend) and deploy
  - [x] 9.1 Implement vehicle assignment features (Backend)
    - Create assign_vehicle function with conflict prevention
    - Implement assignment history tracking
    - Add vehicle availability status updates
    - Add assignment API endpoints
    - _Requirements: 2.3, 2.5_

  - [x] 9.2 Create vehicle assignment interface (Frontend)
    - Build vehicle assignment forms
    - Implement assignment history views
    - Add vehicle availability dashboard
    - Create assignment conflict prevention UI
    - _Requirements: 2.3, 2.5_

  - [ ]* 9.3 Write property test for assignment consistency
    - **Property 8: Vehicle Assignment Consistency**
    - **Validates: Requirements 2.3, 2.5**

  - [x] 9.4 Deploy vehicle assignments to dev
    - Deploy updated driver and vehicle Lambdas
    - Deploy frontend with assignment features
    - Test assignment functionality and conflict prevention

  - [x] 9.5 Deploy vehicle assignments to production
    - Deploy assignment features to production
    - Deploy frontend updates to production
    - Verify assignment logic works correctly

- [x] 10. Add driver performance tracking (Backend + Frontend) and deploy
  - [x] 10.1 Implement performance tracking (Backend)
    - Add performance record creation and updates
    - Implement target achievement calculations
    - Create performance metrics aggregation
    - Add performance API endpoints
    - _Requirements: 2.4, 6.1, 6.3_

  - [x] 10.2 Create performance dashboard (Frontend)
    - Build performance metrics dashboard
    - Implement target achievement visualizations
    - Add performance trend charts
    - Create driver ranking displays
    - _Requirements: 2.4, 6.1, 6.3_

  - [ ]* 10.3 Write property test for performance history persistence
    - **Property 9: Performance History Persistence**
    - **Validates: Requirements 2.4**

  - [x] 10.4 Deploy performance tracking to dev
    - Deploy updated driver Lambda with performance features
    - Deploy frontend with performance dashboard
    - Test performance calculations and metrics

  - [x] 10.5 Deploy performance tracking to production
    - Deploy performance tracking to production
    - Deploy frontend updates to production
    - Verify performance metrics work

- [-] 11. Checkpoint - Driver Management complete and deployed
  - Ensure all driver management features work in production
  - Verify vehicle assignments and performance tracking
  - Test complete driver management workflow end-to-end

- [ ] 12. Implement Financial Settlement (Backend + Frontend) and deploy
  - [ ] 12.1 Add financial database schema
    - Create weekly_settlements table
    - Create payments table for card/cash tracking
    - Add financial reporting tables
    - _Requirements: 3.1, 3.2_

  - [ ] 12.2 Create payment recording functions (Backend)
    - Implement record_card_payment with weekly aggregation
    - Implement record_cash_trip for target tracking
    - Add earnings calculation combining card and cash
    - Add payment API endpoints
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ] 12.3 Create financial management interface (Frontend)
    - Build payment recording forms
    - Implement earnings tracking dashboard
    - Add cash trip monitoring interface
    - Create payment history views
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ]* 12.4 Write property test for earnings aggregation
    - **Property 11: Earnings Aggregation Accuracy**
    - **Validates: Requirements 3.2, 3.3**

  - [ ] 12.5 Deploy payment recording to dev
    - Deploy financial Lambda and database schema
    - Deploy frontend with payment management features
    - Test payment recording and aggregation

  - [ ] 12.6 Deploy payment recording to production
    - Deploy payment features to production
    - Deploy frontend updates to production
    - Verify payment tracking works

- [ ] 13. Add settlement calculation (Backend + Frontend) and deploy
  - [ ] 13.1 Implement settlement calculation logic (Backend)
    - Create calculate_weekly_settlement function
    - Implement R5000 minimum deduction from card earnings
    - Add shortfall tracking for insufficient earnings
    - Add settlement calculation API endpoints
    - _Requirements: 3.4, 3.5, 3.6_

  - [ ] 13.2 Create settlement calculation interface (Frontend)
    - Build settlement calculation dashboard
    - Implement weekly settlement views
    - Add shortfall tracking displays
    - Create settlement history interface
    - _Requirements: 3.4, 3.5, 3.6_

  - [ ]* 13.3 Write property test for settlement calculation
    - **Property 10: Weekly Settlement Calculation**
    - **Validates: Requirements 3.1, 3.4, 3.5**

  - [ ]* 13.4 Write property test for shortfall tracking
    - **Property 12: Shortfall Tracking**
    - **Validates: Requirements 3.6**

  - [ ] 13.5 Deploy settlement calculation to dev
    - Deploy updated financial Lambda
    - Deploy frontend with settlement features
    - Test settlement calculations and shortfall tracking

  - [ ] 13.6 Deploy settlement calculation to production
    - Deploy settlement features to production
    - Deploy frontend updates to production
    - Verify settlement calculations work correctly

- [ ] 14. Add settlement reporting (Backend + Frontend) and deploy
  - [ ] 14.1 Add S3 bucket for reports
    - Add S3 bucket to SAM template for report storage
    - Configure Lambda permissions for S3 access
    - _Requirements: 3.7_

  - [ ] 14.2 Implement settlement reporting (Backend)
    - Create generate_settlement_report function
    - Add PDF generation using reportlab
    - Implement S3 storage for generated reports
    - Add reporting API endpoints
    - _Requirements: 3.7_

  - [ ] 14.3 Create settlement reporting interface (Frontend)
    - Build report generation interface
    - Implement report download functionality
    - Add report history views
    - Create settlement report previews
    - _Requirements: 3.7_

  - [ ]* 14.4 Write property test for settlement report completeness
    - **Property 13: Settlement Report Completeness**
    - **Validates: Requirements 3.7**

  - [ ] 14.5 Deploy settlement reporting to dev
    - Deploy S3 bucket and updated financial Lambda
    - Deploy frontend with reporting features
    - Test report generation and S3 storage

  - [ ] 14.6 Deploy settlement reporting to production
    - Deploy reporting features to production
    - Deploy frontend updates to production
    - Verify report generation works

- [ ] 15. Checkpoint - Financial Management complete and deployed
  - Ensure all financial features work in production
  - Verify settlement calculations and reporting
  - Test complete financial workflow end-to-end

- [ ] 16. Implement GPS Tracking (Backend + Frontend) and deploy
  - [ ] 16.1 Add DynamoDB for GPS data
    - Add DynamoDB table to SAM template for GPS time-series data
    - Configure TTL for automatic data cleanup
    - Add driving events table for harsh driving incidents
    - _Requirements: 4.1, 4.4_

  - [ ] 16.2 Create Netstar API integration (Backend)
    - Implement Netstar API client with authentication
    - Add API response parsing and data extraction
    - Implement error handling and retry logic
    - Add GPS data storage in DynamoDB
    - _Requirements: 4.1, 7.1, 7.2, 7.3_

  - [ ] 16.3 Create GPS tracking interface (Frontend)
    - Build real-time vehicle location map
    - Implement vehicle tracking dashboard
    - Add GPS data visualization
    - Create location history views
    - _Requirements: 4.1, 4.4_

  - [ ]* 16.4 Write property test for GPS data integration
    - **Property 14: GPS Data Integration**
    - **Validates: Requirements 4.1, 7.3**

  - [ ]* 16.5 Write property test for API error handling
    - **Property 27: API Error Handling**
    - **Validates: Requirements 7.2, 7.5**

  - [ ] 16.6 Deploy GPS integration to dev
    - Deploy DynamoDB tables and GPS Lambda
    - Deploy frontend with GPS tracking features
    - Test Netstar API integration and data storage

  - [ ] 16.7 Deploy GPS integration to production
    - Deploy GPS tracking to production
    - Deploy frontend updates to production
    - Verify Netstar integration works

- [ ] 17. Add GPS data processing (Backend + Frontend) and deploy
  - [ ] 17.1 Implement GPS data processing (Backend)
    - Create location history tracking
    - Add GPS data querying and analysis
    - Implement GPS cost tracking (R200/month)
    - Add GPS API endpoints
    - _Requirements: 4.4, 7.4, 7.6, 7.7_

  - [ ] 17.2 Create GPS data analysis interface (Frontend)
    - Build location history visualization
    - Implement GPS cost tracking dashboard
    - Add route analysis features
    - Create GPS data export functionality
    - _Requirements: 4.4, 7.4, 7.6, 7.7_

  - [ ]* 17.3 Write property test for location history persistence
    - **Property 17: Location History Persistence**
    - **Validates: Requirements 4.4, 7.4**

  - [ ]* 17.4 Write property test for Netstar cost tracking
    - **Property 28: Netstar Cost Tracking**
    - **Validates: Requirements 7.6, 7.7**

  - [ ] 17.5 Deploy GPS processing to dev
    - Deploy updated GPS Lambda
    - Deploy frontend with GPS analysis features
    - Test location tracking and cost calculations

  - [ ] 17.6 Deploy GPS processing to production
    - Deploy GPS processing to production
    - Deploy frontend updates to production
    - Verify location tracking works

- [ ] 18. Add driving behavior monitoring (Backend + Frontend) and deploy
  - [ ] 18.1 Implement driving behavior monitoring (Backend)
    - Add speed violation detection and alerting
    - Implement harsh driving event recording
    - Create driving behavior analysis
    - Add behavior monitoring API endpoints
    - _Requirements: 4.2, 4.3_

  - [ ] 18.2 Create driving behavior interface (Frontend)
    - Build driving behavior dashboard
    - Implement speed violation alerts display
    - Add harsh driving event visualization
    - Create driver behavior scoring interface
    - _Requirements: 4.2, 4.3_

  - [ ]* 18.3 Write property test for speed violation detection
    - **Property 15: Speed Violation Detection**
    - **Validates: Requirements 4.2**

  - [ ]* 18.4 Write property test for harsh driving event recording
    - **Property 16: Harsh Driving Event Recording**
    - **Validates: Requirements 4.3**

  - [ ] 18.5 Deploy behavior monitoring to dev
    - Deploy updated GPS Lambda with behavior features
    - Deploy frontend with behavior monitoring UI
    - Test speed violation and harsh driving detection

  - [ ] 18.6 Deploy behavior monitoring to production
    - Deploy behavior monitoring to production
    - Deploy frontend updates to production
    - Verify driving behavior alerts work

- [ ] 19. Checkpoint - GPS Tracking complete and deployed
  - Ensure all GPS features work in production
  - Verify Netstar integration and behavior monitoring
  - Test complete GPS tracking workflow end-to-end

- [ ] 20. Implement Alert & Notification System (Backend + Frontend) and deploy
  - [ ] 20.1 Add SES and SNS to infrastructure
    - Add SES configuration to SAM template for email
    - Add SNS configuration for SMS notifications
    - Configure Lambda permissions for SES/SNS access
    - _Requirements: 6.2, 5.2, 1.8_

  - [ ] 19.2 Create performance alert system (Backend)
    - Implement weekly target failure detection
    - Add excessive cash trip percentage monitoring
    - Create consecutive performance tracking
    - Add performance alert API endpoints
    - _Requirements: 6.2, 6.5, 6.6_

  - [ ] 19.3 Create alert management interface (Frontend)
    - Build alert dashboard and notification center
    - Implement alert configuration interface
    - Add notification preference management
    - Create alert history views
    - _Requirements: 6.2, 6.5, 6.6_

  - [ ]* 19.4 Write property test for performance alert generation
    - **Property 22: Performance Alert Generation**
    - **Validates: Requirements 6.2**

  - [ ]* 19.5 Write property test for cash trip percentage monitoring
    - **Property 25: Cash Trip Percentage Monitoring**
    - **Validates: Requirements 6.6**

  - [ ] 19.6 Deploy performance alerts to dev
    - Deploy SES/SNS and alert Lambda
    - Deploy frontend with alert management features
    - Test performance alert generation and delivery

  - [ ] 19.7 Deploy performance alerts to production
    - Deploy alert system to production
    - Deploy frontend updates to production
    - Verify performance alerts work

- [ ] 21. Add insurance and maintenance alerts (Backend + Frontend) and deploy
  - [ ] 20.1 Add insurance database schema
    - Create insurance_policies table
    - Create insurance_claims table
    - Add insurance cost tracking tables
    - _Requirements: 5.1, 5.3_

  - [ ] 20.2 Implement insurance and maintenance alerts (Backend)
    - Add insurance renewal alerts (30-day notice)
    - Implement maintenance pattern detection
    - Create high cost vehicle alerts
    - Add insurance management API endpoints
    - _Requirements: 5.2_

  - [ ] 20.3 Create insurance management interface (Frontend)
    - Build insurance policy management forms
    - Implement insurance renewal dashboard
    - Add claims tracking interface
    - Create insurance cost reporting views
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ]* 20.4 Write property test for insurance renewal alerting
    - **Property 19: Insurance Renewal Alerting**
    - **Validates: Requirements 5.2**

  - [ ] 20.5 Deploy insurance alerts to dev
    - Deploy insurance schema and updated alert Lambda
    - Deploy frontend with insurance management features
    - Test insurance renewal and maintenance alerts

  - [ ] 20.6 Deploy insurance alerts to production
    - Deploy insurance features to production
    - Deploy frontend updates to production
    - Verify insurance alerts work

- [ ] 22. Add notification delivery (Backend + Frontend) and deploy
  - [ ] 21.1 Implement notification delivery (Backend)
    - Add SES email notification integration
    - Implement SNS SMS notification delivery
    - Create notification preference management
    - Add notification API endpoints
    - _Requirements: 6.2, 5.2, 1.8_

  - [ ] 21.2 Create notification interface (Frontend)
    - Build notification settings interface
    - Implement notification history views
    - Add notification delivery status tracking
    - Create notification template management
    - _Requirements: 6.2, 5.2, 1.8_

  - [ ] 21.3 Deploy notification delivery to dev
    - Deploy updated alert Lambda with notification features
    - Deploy frontend with notification management
    - Test email and SMS delivery

  - [ ] 21.4 Deploy notification delivery to production
    - Deploy notification features to production
    - Deploy frontend updates to production
    - Verify email and SMS notifications work

- [ ] 23. Checkpoint - Alerts and Notifications complete and deployed
  - Ensure all alert types work in production
  - Verify email and SMS delivery
  - Test complete alert and notification workflow end-to-end

- [ ] 24. Implement Reporting System (Backend + Frontend) and deploy
  - [ ] 23.1 Create financial reporting (Backend)
    - Implement earnings report generation
    - Add cash-to-card ratio calculations
    - Create settlement history reports
    - Add financial reporting API endpoints
    - _Requirements: 6.4, 6.7_

  - [ ] 23.2 Create financial reporting interface (Frontend)
    - Build financial dashboard with charts and graphs
    - Implement earnings report views
    - Add cash-to-card ratio visualizations
    - Create settlement history interface
    - _Requirements: 6.4, 6.7_

  - [ ]* 23.3 Write property test for performance metrics calculation
    - **Property 23: Performance Metrics Calculation**
    - **Validates: Requirements 6.3, 6.4**

  - [ ]* 23.4 Write property test for cash-to-card ratio calculation
    - **Property 26: Cash-to-Card Ratio Calculation**
    - **Validates: Requirements 6.7**

  - [ ] 23.5 Deploy financial reporting to dev
    - Deploy reporting Lambda
    - Deploy frontend with financial reporting features
    - Test financial report generation

  - [ ] 23.6 Deploy financial reporting to production
    - Deploy financial reporting to production
    - Deploy frontend updates to production
    - Verify financial reports work

- [ ] 25. Add service cost analysis reporting (Backend + Frontend) and deploy
  - [ ] 24.1 Create service cost analysis reports (Backend)
    - Implement fleet cost comparison reports
    - Add driver-vehicle service cost correlation
    - Create total cost of ownership calculations
    - Add cost analysis reporting API endpoints
    - _Requirements: 8.1, 8.2, 8.3, 8.7_

  - [ ] 24.2 Create service cost analysis interface (Frontend)
    - Build fleet cost comparison dashboard
    - Implement service cost analysis charts
    - Add total cost of ownership visualizations
    - Create cost trend analysis interface
    - _Requirements: 8.1, 8.2, 8.3, 8.7_

  - [ ]* 24.3 Write property test for fleet cost comparison
    - **Property 30: Fleet Cost Comparison**
    - **Validates: Requirements 8.3**

  - [ ]* 24.4 Write property test for total cost of ownership
    - **Property 33: Total Cost of Ownership**
    - **Validates: Requirements 8.7**

  - [ ] 24.5 Deploy cost analysis reporting to dev
    - Deploy updated reporting Lambda
    - Deploy frontend with cost analysis features
    - Test cost analysis and fleet comparison reports

  - [ ] 24.6 Deploy cost analysis reporting to production
    - Deploy cost analysis reporting to production
    - Deploy frontend updates to production
    - Verify cost analysis reports work

- [ ] 26. Add insurance cost reporting (Backend + Frontend) and deploy
  - [ ] 25.1 Implement insurance cost reporting (Backend)
    - Add R500 monthly premium tracking
    - Create insurance payment history reports
    - Implement claims status reporting
    - Add insurance reporting API endpoints
    - _Requirements: 5.1, 5.4, 5.6, 5.7_

  - [ ] 25.2 Create insurance reporting interface (Frontend)
    - Build insurance cost dashboard
    - Implement premium tracking visualizations
    - Add claims status interface
    - Create insurance payment history views
    - _Requirements: 5.1, 5.4, 5.6, 5.7_

  - [ ]* 25.3 Write property test for insurance premium tracking
    - **Property 18: Insurance Premium Tracking**
    - **Validates: Requirements 5.1, 5.6, 5.7**

  - [ ] 25.4 Deploy insurance reporting to dev
    - Deploy updated reporting Lambda
    - Deploy frontend with insurance reporting features
    - Test insurance cost and claims reporting

  - [ ] 25.5 Deploy insurance reporting to production
    - Deploy insurance reporting to production
    - Deploy frontend updates to production
    - Verify insurance reports work

- [ ] 27. Checkpoint - All Reporting complete and deployed
  - Ensure all report types work in production
  - Verify data accuracy in all reports
  - Test complete reporting workflow end-to-end

- [ ] 28. Add EventBridge scheduling and deploy
  - [ ] 27.1 Add EventBridge to infrastructure
    - Add EventBridge rules to SAM template
    - Configure scheduled triggers for GPS sync (5 minutes)
    - Configure daily triggers for alert processing
    - Configure weekly triggers for settlement processing
    - _Requirements: 4.1, 6.2, 3.4_

  - [ ] 27.2 Deploy scheduled processing to dev
    - Deploy EventBridge rules and updated Lambdas
    - Test scheduled GPS sync and alert processing

  - [ ] 27.3 Deploy scheduled processing to production
    - Deploy scheduling to production
    - Verify scheduled tasks run correctly

- [ ] 29. Add security and compliance features and deploy
  - [ ] 28.1 Add Cognito authentication
    - Add Cognito User Pool to SAM template
    - Configure API Gateway with Cognito authorizer
    - Add role-based access control
    - _Requirements: 9.2_

  - [ ] 28.2 Implement data encryption and audit logging
    - Implement field-level encryption for sensitive data
    - Create audit logging for all operations
    - Add security API endpoints
    - _Requirements: 9.1, 9.3_

  - [ ]* 28.3 Write property test for data encryption
    - **Property 34: Data Encryption**
    - **Validates: Requirements 9.1**

  - [ ]* 28.4 Write property test for role-based access control
    - **Property 35: Role-Based Access Control**
    - **Validates: Requirements 9.2**

  - [ ]* 28.5 Write property test for audit logging
    - **Property 36: Audit Logging**
    - **Validates: Requirements 9.3**

  - [ ] 28.6 Deploy security features to dev
    - Deploy Cognito and updated Lambdas with security
    - Test authentication and authorization

  - [ ] 28.7 Deploy security features to production
    - Deploy security features to production
    - Verify authentication and audit logging work

- [ ] 30. Add backup and recovery and deploy
  - [ ] 29.1 Implement backup and recovery
    - Configure automated Aurora backups
    - Set up DynamoDB point-in-time recovery
    - Create S3 backup for reports and documents
    - _Requirements: 9.4_

  - [ ]* 29.2 Write property test for automated backup
    - **Property 37: Automated Backup**
    - **Validates: Requirements 9.4**

  - [ ] 29.3 Deploy backup features to dev
    - Deploy backup configurations
    - Test backup and recovery procedures

  - [ ] 29.4 Deploy backup features to production
    - Deploy backup features to production
    - Verify automated backups work

- [ ] 31. Final system integration and monitoring
  - [ ] 30.1 Configure comprehensive CloudWatch monitoring
    - Set up Lambda function monitoring and alarms
    - Add database performance monitoring
    - Create custom metrics for business KPIs
    - Configure alerts for system health

  - [ ] 30.2 Set up CI/CD pipelines
    - Create GitHub Actions for backend deployment
    - Add automated testing in pipeline
    - Configure staging and production deployment workflows

  - [ ] 30.3 Perform end-to-end integration testing
    - Test complete user workflows across all features
    - Validate all API integrations work together
    - Test settlement calculation accuracy end-to-end
    - Verify all alert and notification types work

  - [ ]* 30.4 Write integration tests
    - Test API Gateway to Lambda integration
    - Test database connectivity and transactions
    - Test external service integrations
    - Test cross-Lambda communication

- [ ] 32. Final checkpoint - Complete system deployed and operational
  - Ensure all features work correctly in production
  - Verify system performance and reliability
  - Confirm all monitoring and alerts are active

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Every feature is deployed and tested before proceeding to the next
- System is always deployable and functional at each checkpoint
- Pure serverless architecture - no VPCs, no ElastiCache, no EC2
- Uses Aurora Serverless v2, DynamoDB, Lambda, API Gateway, S3, SES, SNS, EventBridge
- Property tests validate universal correctness properties using Hypothesis
- Unit tests validate specific examples and edge cases using pytest
- Each deployment includes both dev and production environments
- Comprehensive monitoring and alerting throughout