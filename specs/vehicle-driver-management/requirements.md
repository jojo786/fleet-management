# Requirements Document

## Introduction

A comprehensive vehicle and driver management system for Uber rental operations. The system manages vehicle fleet operations, driver onboarding and performance tracking, financial settlements, GPS monitoring via Netstar integration, and insurance management.

## Glossary

- **Vehicle_Management_System**: The complete system managing vehicles, drivers, and operations
- **Driver**: Individual contracted to operate rental vehicles for Uber services
- **Vehicle**: Car owned by the operator and rented to drivers for Uber operations
- **Financial_Settlement**: Weekly payment calculation and processing between operator and drivers, accounting for card and cash payments
- **GPS_Monitor**: Real-time vehicle tracking and behavior monitoring via Netstar API
- **Insurance_Tracker**: System component managing vehicle insurance policies and renewals
- **Netstar_API**: Third-party GPS tracking service providing vehicle location and behavior data (R200 monthly per vehicle)
- **Service_Record**: Maintenance and repair history for vehicles including costs and driver assignments
- **Performance_Target**: Minimum weekly payment requirement (R5000) for drivers
- **Card_Payment**: Uber payment processed through card that goes directly to operator
- **Cash_Payment**: Uber payment made in cash directly to driver
- **Cash_Trip_Alert**: System alert triggered when driver exceeds acceptable cash trip percentage
- **Insurance_Premium**: Monthly R500 insurance cost per vehicle
- **Netstar_Subscription**: Monthly R200 GPS tracking cost per vehicle
- **Service_Cost_Alert**: System alert when vehicle maintenance costs exceed fleet average
- **Accident_Repair**: Unplanned repair costs due to vehicle accidents or damage
- **Maintenance_Type**: Categories of service including brakes, oil, tires, engine, transmission, etc.

## Requirements

### Requirement 1: Vehicle Fleet Management

**User Story:** As a fleet operator, I want to manage my vehicle inventory and maintenance, so that I can ensure optimal vehicle availability and condition.

#### Acceptance Criteria

1. THE Vehicle_Management_System SHALL store vehicle details including make, model, year, registration, and current status
2. WHEN a vehicle requires service, THE Vehicle_Management_System SHALL record service details including type, cost, date, and assigned driver
3. THE Vehicle_Management_System SHALL track vehicle usage metrics including mileage and operational hours
4. WHEN a service is due, THE Vehicle_Management_System SHALL generate maintenance alerts based on mileage or time intervals
5. THE Vehicle_Management_System SHALL maintain complete service history for each vehicle with cost breakdown by service type
6. THE Vehicle_Management_System SHALL track ad hoc repair costs including accident repairs and emergency maintenance
7. THE Vehicle_Management_System SHALL generate service cost reports comparing expenses across vehicles and drivers
8. WHEN service costs for a vehicle exceed average fleet costs by 20%, THE Vehicle_Management_System SHALL generate high maintenance cost alerts

### Requirement 2: Driver Onboarding and Management

**User Story:** As a fleet operator, I want to onboard and manage drivers, so that I can maintain a qualified driver pool for my vehicles.

#### Acceptance Criteria

1. THE Vehicle_Management_System SHALL store driver information including personal details, license information, and contact details
2. WHEN onboarding a driver, THE Vehicle_Management_System SHALL validate driver license and required documentation
3. THE Vehicle_Management_System SHALL assign vehicles to drivers and track current assignments
4. THE Vehicle_Management_System SHALL maintain driver performance records and target achievement history
5. WHEN a driver assignment changes, THE Vehicle_Management_System SHALL update vehicle availability and driver status

### Requirement 3: Financial Settlement Processing

**User Story:** As a fleet operator, I want to process weekly financial settlements with drivers, so that I can collect my minimum fee and distribute remaining earnings.

#### Acceptance Criteria

1. WHEN Uber card payments are received, THE Vehicle_Management_System SHALL record total card earnings per vehicle per week
2. WHEN cash trips are completed, THE Vehicle_Management_System SHALL record cash trip values for target tracking purposes
3. THE Vehicle_Management_System SHALL calculate total weekly earnings combining card payments and cash trip values
4. THE Vehicle_Management_System SHALL calculate driver settlements by deducting R5000 minimum payment from card earnings only
5. IF card earnings exceed R5000, THEN THE Vehicle_Management_System SHALL calculate driver payout as the excess card amount
6. IF total weekly earnings (card + cash) are less than R5000, THEN THE Vehicle_Management_System SHALL record the shortfall amount that driver owes
7. THE Vehicle_Management_System SHALL generate weekly settlement reports showing card earnings, cash trips, total earnings, deductions, and final settlement amount

### Requirement 4: GPS Tracking and Behavior Monitoring

**User Story:** As a fleet operator, I want to monitor vehicle location and driver behavior, so that I can ensure safe driving and vehicle security.

#### Acceptance Criteria

1. THE GPS_Monitor SHALL integrate with Netstar API to retrieve real-time vehicle location data
2. WHEN vehicle speed exceeds safe limits, THE GPS_Monitor SHALL generate speed violation alerts
3. WHEN excessive braking events are detected, THE GPS_Monitor SHALL record harsh driving incidents
4. THE GPS_Monitor SHALL track vehicle routes and provide location history for each vehicle
5. THE GPS_Monitor SHALL generate daily driving behavior reports including speed violations and harsh driving events

### Requirement 5: Insurance Management

**User Story:** As a fleet operator, I want to track vehicle insurance policies, so that I can ensure continuous coverage and timely renewals.

#### Acceptance Criteria

1. THE Insurance_Tracker SHALL store insurance policy details including provider, policy number, coverage dates, and R500 monthly premium amounts
2. WHEN insurance renewal is due within 30 days, THE Insurance_Tracker SHALL generate renewal alerts
3. THE Insurance_Tracker SHALL track insurance claims and their status for each vehicle
4. THE Insurance_Tracker SHALL maintain insurance payment history and calculate annual insurance costs per vehicle
5. WHEN a vehicle is involved in an incident, THE Insurance_Tracker SHALL record claim details and update vehicle status
6. THE Insurance_Tracker SHALL track monthly R500 insurance premium payments per vehicle
7. THE Insurance_Tracker SHALL generate monthly insurance cost reports showing total premiums due and paid

### Requirement 6: Performance Monitoring and Reporting

**User Story:** As a fleet operator, I want to monitor driver performance against targets, so that I can identify underperforming drivers and take corrective action.

#### Acceptance Criteria

1. THE Vehicle_Management_System SHALL track weekly earnings per driver against the R5000 minimum target including both card and cash trips
2. WHEN a driver fails to meet weekly targets, THE Vehicle_Management_System SHALL generate performance alerts
3. THE Vehicle_Management_System SHALL calculate driver performance metrics including target achievement rate and average weekly earnings
4. THE Vehicle_Management_System SHALL generate performance reports showing driver rankings and trend analysis
5. THE Vehicle_Management_System SHALL track consecutive weeks of target achievement or failure for each driver
6. WHEN cash trip percentage exceeds 70% of total trips in a week, THE Vehicle_Management_System SHALL generate excessive cash trip alerts
7. THE Vehicle_Management_System SHALL calculate and display cash-to-card ratio for each driver weekly

### Requirement 7: Netstar API Integration

**User Story:** As a fleet operator, I want to integrate with Netstar GPS system, so that I can access real-time vehicle tracking and behavior data.

#### Acceptance Criteria

1. THE Vehicle_Management_System SHALL authenticate with Netstar API using valid credentials
2. WHEN requesting vehicle data, THE Vehicle_Management_System SHALL handle API rate limits and error responses gracefully
3. THE Vehicle_Management_System SHALL parse Netstar API responses and extract location, speed, and behavior data
4. THE Vehicle_Management_System SHALL store GPS data locally for historical analysis and reporting
5. IF Netstar API is unavailable, THEN THE Vehicle_Management_System SHALL log the outage and continue operating with cached data
6. THE Vehicle_Management_System SHALL track monthly R200 Netstar subscription costs per vehicle
7. THE Vehicle_Management_System SHALL generate monthly Netstar cost reports showing total subscription fees due and paid

### Requirement 8: Service Cost Analysis and Driver Correlation

**User Story:** As a fleet operator, I want to analyze service costs per vehicle and correlate them with driver assignments, so that I can identify patterns and address excessive maintenance costs.

#### Acceptance Criteria

1. THE Vehicle_Management_System SHALL track all service costs categorized by maintenance type (brakes, oil, tires, engine, transmission, etc.)
2. THE Vehicle_Management_System SHALL correlate service costs with driver assignments at the time of service
3. THE Vehicle_Management_System SHALL calculate average service costs per vehicle per month and compare across the fleet
4. WHEN a specific maintenance type (e.g., brakes) occurs more frequently on one vehicle, THE Vehicle_Management_System SHALL generate maintenance pattern alerts
5. THE Vehicle_Management_System SHALL generate driver-vehicle service cost reports showing maintenance expenses per driver assignment period
6. THE Vehicle_Management_System SHALL track accident repair costs separately from routine maintenance costs
7. THE Vehicle_Management_System SHALL calculate total cost of ownership per vehicle including insurance, GPS, maintenance, and repairs

### Requirement 9: Data Persistence and Security

**User Story:** As a fleet operator, I want secure data storage and backup, so that I can protect sensitive business and personal information.

#### Acceptance Criteria

1. THE Vehicle_Management_System SHALL encrypt sensitive data including driver personal information and financial records
2. THE Vehicle_Management_System SHALL implement role-based access control for different user types
3. THE Vehicle_Management_System SHALL maintain audit logs of all system access and data modifications
4. THE Vehicle_Management_System SHALL perform automated daily backups of all system data
5. THE Vehicle_Management_System SHALL comply with data protection regulations for personal information handling