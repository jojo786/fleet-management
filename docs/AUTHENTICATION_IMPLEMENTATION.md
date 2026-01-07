# Authentication Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing AWS Cognito authentication in the FLEET application.

## Architecture

```
User → Frontend (Login UI) → Cognito User Pool → JWT Tokens
                                                      ↓
Frontend (with tokens) → API Gateway (Cognito Authorizer) → Lambda Functions
```

## Implementation Steps

### Phase 1: Backend - Add Cognito to SAM Template

#### 1.1 Add Cognito User Pool

Add to `template.yaml`:

```yaml
Resources:
  # Cognito User Pool
  FleetUserPool:
    Type: AWS::Cognito::UserPool
    Properties:
      UserPoolName: !Sub 'fleet-users-${Environment}'
      AutoVerifiedAttributes:
        - email
      UsernameAttributes:
        - email
      Schema:
        - Name: email
          AttributeDataType: String
          Required: true
          Mutable: false
        - Name: name
          AttributeDataType: String
          Required: true
          Mutable: true
        - Name: role
          AttributeDataType: String
          Required: false
          Mutable: true
      Policies:
        PasswordPolicy:
          MinimumLength: 8
          RequireUppercase: true
          RequireLowercase: true
          RequireNumbers: true
          RequireSymbols: true
      AccountRecoverySetting:
        RecoveryMechanisms:
          - Name: verified_email
            Priority: 1
      UserPoolTags:
        Environment: !Ref Environment
        Application: FLEET

  # Cognito User Pool Client
  FleetUserPoolClient:
    Type: AWS::Cognito::UserPoolClient
    Properties:
      ClientName: !Sub 'fleet-web-client-${Environment}'
      UserPoolId: !Ref FleetUserPool
      GenerateSecret: false
      ExplicitAuthFlows:
        - ALLOW_USER_PASSWORD_AUTH
        - ALLOW_REFRESH_TOKEN_AUTH
        - ALLOW_USER_SRP_AUTH
      PreventUserExistenceErrors: ENABLED
      AccessTokenValidity: 1  # 1 hour
      IdTokenValidity: 1      # 1 hour
      RefreshTokenValidity: 30 # 30 days
      TokenValidityUnits:
        AccessToken: hours
        IdToken: hours
        RefreshToken: days

  # Cognito User Pool Domain (for hosted UI - optional)
  FleetUserPoolDomain:
    Type: AWS::Cognito::UserPoolDomain
    Properties:
      Domain: !Sub 'fleet-${Environment}-${AWS::AccountId}'
      UserPoolId: !Ref FleetUserPool

  # API Gateway Cognito Authorizer
  FleetApiAuthorizer:
    Type: AWS::ApiGateway::Authorizer
    Properties:
      Name: FleetCognitoAuthorizer
      Type: COGNITO_USER_POOLS
      IdentitySource: method.request.header.Authorization
      RestApiId: !Ref FleetApi
      ProviderARNs:
        - !GetAtt FleetUserPool.Arn

# Add outputs for frontend configuration
Outputs:
  UserPoolId:
    Description: Cognito User Pool ID
    Value: !Ref FleetUserPool
    Export:
      Name: !Sub '${AWS::StackName}-UserPoolId'
  
  UserPoolClientId:
    Description: Cognito User Pool Client ID
    Value: !Ref FleetUserPoolClient
    Export:
      Name: !Sub '${AWS::StackName}-UserPoolClientId'
  
  UserPoolDomain:
    Description: Cognito User Pool Domain
    Value: !Sub 'https://fleet-${Environment}-${AWS::AccountId}.auth.${AWS::Region}.amazoncognito.com'
    Export:
      Name: !Sub '${AWS::StackName}-UserPoolDomain'
```

#### 1.2 Update API Gateway to Require Authentication

Update your API Gateway resources in `template.yaml`:

```yaml
Resources:
  FleetApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: !Ref Environment
      Cors:
        AllowMethods: "'GET,POST,PUT,DELETE,OPTIONS'"
        AllowHeaders: "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
        AllowOrigin: "'*'"
      Auth:
        DefaultAuthorizer: FleetCognitoAuthorizer
        Authorizers:
          FleetCognitoAuthorizer:
            UserPoolArn: !GetAtt FleetUserPool.Arn
```

#### 1.3 Update Lambda Functions to Use Authorizer

For each Lambda function that needs authentication:

```yaml
  VehicleManagementFunction:
    Type: AWS::Serverless::Function
    Properties:
      # ... existing properties ...
      Events:
        GetVehicles:
          Type: Api
          Properties:
            Path: /vehicles
            Method: GET
            RestApiId: !Ref FleetApi
            Auth:
              Authorizer: FleetCognitoAuthorizer
```

#### 1.4 Access User Information in Lambda

Update Lambda handlers to access authenticated user info:

```python
# src/vehicles/handler.py

def lambda_handler(event, context):
    # Get authenticated user information from Cognito
    claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
    
    user_email = claims.get('email')
    user_sub = claims.get('sub')  # Unique user ID
    user_role = claims.get('custom:role', 'user')  # Custom attribute
    
    print(f"Request from user: {user_email} (role: {user_role})")
    
    # Implement role-based access control
    if user_role not in ['admin', 'operator']:
        return {
            'statusCode': 403,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Insufficient permissions'})
        }
    
    # Continue with normal logic...
```

### Phase 2: Frontend - Add Authentication UI

#### 2.1 Create Authentication Module

Create `frontend/auth.js`:

```javascript
// FLEET Authentication Module using AWS Cognito

class FleetAuth {
    constructor(userPoolId, clientId, region = 'eu-west-1') {
        this.userPoolId = userPoolId;
        this.clientId = clientId;
        this.region = region;
        this.cognitoUrl = `https://cognito-idp.${region}.amazonaws.com/`;
        
        // Token storage keys
        this.TOKEN_KEY = 'fleet_id_token';
        this.ACCESS_TOKEN_KEY = 'fleet_access_token';
        this.REFRESH_TOKEN_KEY = 'fleet_refresh_token';
        this.USER_KEY = 'fleet_user';
    }

    // Sign up new user
    async signUp(email, password, name) {
        const params = {
            ClientId: this.clientId,
            Username: email,
            Password: password,
            UserAttributes: [
                { Name: 'email', Value: email },
                { Name: 'name', Value: name }
            ]
        };

        try {
            const response = await this.cognitoRequest('AWSCognitoIdentityProviderService.SignUp', params);
            return { success: true, data: response };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Confirm sign up with verification code
    async confirmSignUp(email, code) {
        const params = {
            ClientId: this.clientId,
            Username: email,
            ConfirmationCode: code
        };

        try {
            await this.cognitoRequest('AWSCognitoIdentityProviderService.ConfirmSignUp', params);
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Sign in user
    async signIn(email, password) {
        const params = {
            AuthFlow: 'USER_PASSWORD_AUTH',
            ClientId: this.clientId,
            AuthParameters: {
                USERNAME: email,
                PASSWORD: password
            }
        };

        try {
            const response = await this.cognitoRequest('AWSCognitoIdentityProviderService.InitiateAuth', params);
            
            if (response.AuthenticationResult) {
                const { IdToken, AccessToken, RefreshToken } = response.AuthenticationResult;
                
                // Store tokens
                localStorage.setItem(this.TOKEN_KEY, IdToken);
                localStorage.setItem(this.ACCESS_TOKEN_KEY, AccessToken);
                localStorage.setItem(this.REFRESH_TOKEN_KEY, RefreshToken);
                
                // Decode and store user info
                const userInfo = this.decodeToken(IdToken);
                localStorage.setItem(this.USER_KEY, JSON.stringify(userInfo));
                
                return { success: true, user: userInfo };
            }
            
            return { success: false, error: 'Authentication failed' };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Sign out user
    signOut() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.ACCESS_TOKEN_KEY);
        localStorage.removeItem(this.REFRESH_TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
        window.location.href = '/login.html';
    }

    // Check if user is authenticated
    isAuthenticated() {
        const token = localStorage.getItem(this.TOKEN_KEY);
        if (!token) return false;
        
        // Check if token is expired
        const decoded = this.decodeToken(token);
        const currentTime = Math.floor(Date.now() / 1000);
        
        return decoded.exp > currentTime;
    }

    // Get current user
    getCurrentUser() {
        const userStr = localStorage.getItem(this.USER_KEY);
        return userStr ? JSON.parse(userStr) : null;
    }

    // Get ID token for API requests
    getIdToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    }

    // Refresh tokens
    async refreshTokens() {
        const refreshToken = localStorage.getItem(this.REFRESH_TOKEN_KEY);
        if (!refreshToken) {
            this.signOut();
            return { success: false, error: 'No refresh token' };
        }

        const params = {
            AuthFlow: 'REFRESH_TOKEN_AUTH',
            ClientId: this.clientId,
            AuthParameters: {
                REFRESH_TOKEN: refreshToken
            }
        };

        try {
            const response = await this.cognitoRequest('AWSCognitoIdentityProviderService.InitiateAuth', params);
            
            if (response.AuthenticationResult) {
                const { IdToken, AccessToken } = response.AuthenticationResult;
                
                localStorage.setItem(this.TOKEN_KEY, IdToken);
                localStorage.setItem(this.ACCESS_TOKEN_KEY, AccessToken);
                
                const userInfo = this.decodeToken(IdToken);
                localStorage.setItem(this.USER_KEY, JSON.stringify(userInfo));
                
                return { success: true };
            }
            
            return { success: false, error: 'Token refresh failed' };
        } catch (error) {
            this.signOut();
            return { success: false, error: error.message };
        }
    }

    // Forgot password
    async forgotPassword(email) {
        const params = {
            ClientId: this.clientId,
            Username: email
        };

        try {
            await this.cognitoRequest('AWSCognitoIdentityProviderService.ForgotPassword', params);
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Confirm forgot password with code
    async confirmForgotPassword(email, code, newPassword) {
        const params = {
            ClientId: this.clientId,
            Username: email,
            ConfirmationCode: code,
            Password: newPassword
        };

        try {
            await this.cognitoRequest('AWSCognitoIdentityProviderService.ConfirmForgotPassword', params);
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Helper: Make Cognito API request
    async cognitoRequest(action, params) {
        const response = await fetch(this.cognitoUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-amz-json-1.1',
                'X-Amz-Target': action
            },
            body: JSON.stringify(params)
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || data.__type || 'Cognito request failed');
        }
        
        return data;
    }

    // Helper: Decode JWT token
    decodeToken(token) {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        
        return JSON.parse(jsonPayload);
    }
}

// Export for use in other modules
window.FleetAuth = FleetAuth;
```

#### 2.2 Create Login Page

Create `frontend/login.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FLEET - Login</title>
    <link rel="stylesheet" href="styles.css">
    <style>
        .auth-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 40px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .auth-form {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .auth-form input {
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .auth-form button {
            padding: 12px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        .auth-form button:hover {
            background: #0056b3;
        }
        .error-message {
            color: #dc3545;
            font-size: 14px;
            margin-top: 10px;
        }
        .success-message {
            color: #28a745;
            font-size: 14px;
            margin-top: 10px;
        }
        .auth-links {
            margin-top: 20px;
            text-align: center;
        }
        .auth-links a {
            color: #007bff;
            text-decoration: none;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="auth-container">
        <h1>🚗 FLEET Login</h1>
        <p>Fleet Location, Efficiency, and Tracking Technology</p>
        
        <form id="loginForm" class="auth-form">
            <input type="email" id="email" placeholder="Email" required>
            <input type="password" id="password" placeholder="Password" required>
            <button type="submit">Sign In</button>
        </form>
        
        <div id="message"></div>
        
        <div class="auth-links">
            <a href="signup.html">Don't have an account? Sign up</a><br>
            <a href="forgot-password.html">Forgot password?</a>
        </div>
    </div>

    <script src="auth.js"></script>
    <script>
        // Initialize auth (values will be injected during deployment)
        const auth = new FleetAuth(
            'USER_POOL_ID_PLACEHOLDER',
            'CLIENT_ID_PLACEHOLDER',
            'eu-west-1'
        );

        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const messageDiv = document.getElementById('message');
            
            messageDiv.innerHTML = '<p>Signing in...</p>';
            
            const result = await auth.signIn(email, password);
            
            if (result.success) {
                messageDiv.innerHTML = '<p class="success-message">Login successful! Redirecting...</p>';
                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 1000);
            } else {
                messageDiv.innerHTML = `<p class="error-message">Error: ${result.error}</p>`;
            }
        });
    </script>
</body>
</html>
```

#### 2.3 Update Main App to Require Authentication

Update `frontend/app.js`:

```javascript
// Add at the beginning of FleetApp class
class FleetApp {
    constructor() {
        // Initialize auth
        this.auth = new FleetAuth(
            'USER_POOL_ID_PLACEHOLDER',
            'CLIENT_ID_PLACEHOLDER',
            'eu-west-1'
        );
        
        // Check authentication
        if (!this.auth.isAuthenticated()) {
            window.location.href = 'login.html';
            return;
        }
        
        // Get current user
        this.currentUser = this.auth.getCurrentUser();
        console.log('Logged in as:', this.currentUser.email);
        
        // Environment-specific API URL
        this.apiUrl = 'API_URL_PLACEHOLDER';
        
        // ... rest of constructor
    }
    
    // Update API calls to include authentication token
    async apiCall(endpoint, options = {}) {
        const token = this.auth.getIdToken();
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        };
        
        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...(options.headers || {})
            }
        };
        
        try {
            const response = await fetch(`${this.apiUrl}${endpoint}`, mergedOptions);
            
            // Handle token expiration
            if (response.status === 401) {
                const refreshResult = await this.auth.refreshTokens();
                if (refreshResult.success) {
                    // Retry request with new token
                    mergedOptions.headers.Authorization = `Bearer ${this.auth.getIdToken()}`;
                    return await fetch(`${this.apiUrl}${endpoint}`, mergedOptions);
                } else {
                    this.auth.signOut();
                    return;
                }
            }
            
            return response;
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }
    
    // Add logout functionality
    logout() {
        this.auth.signOut();
    }
}
```

#### 2.4 Update Deployment Script

Update `deploy-frontend.sh` to inject Cognito configuration:

```bash
#!/bin/bash

# ... existing code ...

# Get Cognito configuration
USER_POOL_ID=$(aws cloudformation describe-stacks \
    --stack-name $BACKEND_STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
    --output text)

CLIENT_ID=$(aws cloudformation describe-stacks \
    --stack-name $BACKEND_STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
    --output text)

# Replace placeholders in auth.js
sed "s|USER_POOL_ID_PLACEHOLDER|$USER_POOL_ID|g; s|CLIENT_ID_PLACEHOLDER|$CLIENT_ID|g" \
    frontend/auth.js > /tmp/auth-$ENVIRONMENT.js

# Replace placeholders in app.js
sed "s|API_URL_PLACEHOLDER|$API_URL|g; s|USER_POOL_ID_PLACEHOLDER|$USER_POOL_ID|g; s|CLIENT_ID_PLACEHOLDER|$CLIENT_ID|g" \
    frontend/app.js > /tmp/app-$ENVIRONMENT.js

# Upload files
aws s3 cp /tmp/auth-$ENVIRONMENT.js s3://$BUCKET/auth.js --content-type "application/javascript"
aws s3 cp /tmp/app-$ENVIRONMENT.js s3://$BUCKET/app.js --content-type "application/javascript"
# ... rest of uploads
```

### Phase 3: Testing

#### 3.1 Create Test User

```bash
# Create a test user via AWS CLI
aws cognito-idp admin-create-user \
    --user-pool-id YOUR_USER_POOL_ID \
    --username test@example.com \
    --user-attributes Name=email,Value=test@example.com Name=name,Value="Test User" \
    --temporary-password TempPass123! \
    --message-action SUPPRESS

# Set permanent password
aws cognito-idp admin-set-user-password \
    --user-pool-id YOUR_USER_POOL_ID \
    --username test@example.com \
    --password YourPassword123! \
    --permanent
```

#### 3.2 Test Authentication Flow

1. Navigate to login page
2. Sign in with test credentials
3. Verify redirect to main app
4. Check that API calls include Authorization header
5. Test token refresh by waiting for expiration
6. Test logout functionality

### Phase 4: Role-Based Access Control (Optional)

#### 4.1 Add Custom Attributes for Roles

Update Cognito User Pool schema to include role attribute, then assign roles:

```bash
# Assign admin role to user
aws cognito-idp admin-update-user-attributes \
    --user-pool-id YOUR_USER_POOL_ID \
    --username test@example.com \
    --user-attributes Name=custom:role,Value=admin
```

#### 4.2 Implement Role Checks in Lambda

```python
def check_permission(claims, required_role):
    user_role = claims.get('custom:role', 'user')
    role_hierarchy = {'admin': 3, 'operator': 2, 'user': 1}
    
    return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)

def lambda_handler(event, context):
    claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
    
    if not check_permission(claims, 'operator'):
        return {
            'statusCode': 403,
            'body': json.dumps({'error': 'Insufficient permissions'})
        }
    
    # Continue with logic...
```

## Security Best Practices

1. **Always use HTTPS** - Cognito requires HTTPS for production
2. **Store tokens securely** - Use localStorage (or sessionStorage for more security)
3. **Implement token refresh** - Refresh tokens before they expire
4. **Use strong password policies** - Enforce complexity requirements
5. **Enable MFA** - Add multi-factor authentication for sensitive operations
6. **Implement rate limiting** - Protect against brute force attacks
7. **Log authentication events** - Monitor for suspicious activity
8. **Use custom domains** - Brand your Cognito hosted UI (optional)

## Cost Estimation

**AWS Cognito Pricing (as of 2024):**
- First 50,000 MAUs (Monthly Active Users): Free
- 50,001 - 100,000 MAUs: $0.0055 per MAU
- Additional features (MFA, advanced security): Extra cost

For a small fleet operation with <50 users, Cognito will be **free**.

## Troubleshooting

### Common Issues

1. **CORS errors**: Ensure API Gateway CORS includes Authorization header
2. **Token expiration**: Implement automatic token refresh
3. **Invalid tokens**: Check token format and expiration
4. **User not confirmed**: Verify email confirmation process
5. **Password policy**: Ensure passwords meet requirements

### Debug Commands

```bash
# List users in pool
aws cognito-idp list-users --user-pool-id YOUR_USER_POOL_ID

# Get user details
aws cognito-idp admin-get-user \
    --user-pool-id YOUR_USER_POOL_ID \
    --username test@example.com

# Delete user (for testing)
aws cognito-idp admin-delete-user \
    --user-pool-id YOUR_USER_POOL_ID \
    --username test@example.com
```

## Next Steps

1. Deploy updated SAM template with Cognito resources
2. Create frontend authentication pages
3. Update main app to require authentication
4. Test authentication flow
5. Implement role-based access control
6. Add MFA for admin users (optional)
7. Set up CloudWatch alarms for authentication failures

## References

- [AWS Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [Cognito User Pool API Reference](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/)
- [API Gateway Cognito Authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html)
