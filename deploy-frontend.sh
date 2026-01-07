#!/bin/bash

# FLEET Frontend Deployment Script

set -e

ENVIRONMENT=${1:-dev}
REGION="eu-west-1"
FRONTEND_STACK_NAME="fleet-frontend-$ENVIRONMENT"

# Get API URL from backend stack
BACKEND_STACK_NAME="fleet-backend-$ENVIRONMENT"
echo "📡 Getting API URL from backend stack: $BACKEND_STACK_NAME"

API_URL=$(aws cloudformation describe-stacks \
    --stack-name $BACKEND_STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`FleetApiUrl`].OutputValue' \
    --output text)

if [ -z "$API_URL" ]; then
    echo "❌ Error: Could not find API URL from backend stack. Make sure the backend is deployed first."
    exit 1
fi

# Remove trailing slash if present
API_URL=${API_URL%/}

echo "🚀 Deploying FLEET Frontend to $ENVIRONMENT environment..."
echo "📡 API URL: $API_URL"

# Deploy frontend infrastructure if it doesn't exist
echo "📋 Checking frontend infrastructure..."
if ! aws cloudformation describe-stacks --stack-name $FRONTEND_STACK_NAME --region $REGION >/dev/null 2>&1; then
    echo "🏗️  Deploying frontend infrastructure..."
    sam deploy \
        --template-file frontend-template.yaml \
        --stack-name $FRONTEND_STACK_NAME \
        --parameter-overrides Environment=$ENVIRONMENT \
        --region $REGION \
        --capabilities CAPABILITY_IAM \
        --resolve-s3 \
        --no-confirm-changeset
    
    echo "✅ Frontend infrastructure deployed!"
else
    echo "✅ Frontend infrastructure already exists"
fi

# Get the S3 bucket name from CloudFormation stack
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name $FRONTEND_STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' \
    --output text)

if [ -z "$BUCKET_NAME" ]; then
    echo "❌ Error: Could not find S3 bucket name. Frontend infrastructure deployment may have failed."
    exit 1
fi

echo "📦 S3 Bucket: $BUCKET_NAME"

# Create environment-specific app.js
echo "🔧 Creating environment-specific JavaScript..."
sed "s|API_URL_PLACEHOLDER|$API_URL|g" frontend/app.js > /tmp/app-$ENVIRONMENT.js

# Sync frontend files to S3
echo "📤 Uploading frontend files..."
aws s3 sync frontend/ s3://$BUCKET_NAME/ \
    --region $REGION \
    --delete \
    --cache-control "max-age=86400" \
    --exclude "app.js"

# Upload environment-specific app.js
aws s3 cp /tmp/app-$ENVIRONMENT.js s3://$BUCKET_NAME/app.js \
    --region $REGION \
    --content-type "application/javascript" \
    --cache-control "no-cache, no-store, must-revalidate"

# Set proper content types for other files
echo "🔧 Setting content types..."
aws s3 cp s3://$BUCKET_NAME/index.html s3://$BUCKET_NAME/index.html \
    --region $REGION \
    --content-type "text/html" \
    --metadata-directive REPLACE

aws s3 cp s3://$BUCKET_NAME/styles.css s3://$BUCKET_NAME/styles.css \
    --region $REGION \
    --content-type "text/css" \
    --metadata-directive REPLACE

# Clean up temp file
rm /tmp/app-$ENVIRONMENT.js

# Get URLs
FRONTEND_URL=$(aws cloudformation describe-stacks \
    --stack-name $FRONTEND_STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`FrontendUrl`].OutputValue' \
    --output text)

S3_WEBSITE_URL=$(aws cloudformation describe-stacks \
    --stack-name $FRONTEND_STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`S3WebsiteUrl`].OutputValue' \
    --output text)

# Get CloudFront distribution ID for cache invalidation
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
    --stack-name $FRONTEND_STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`DistributionId`].OutputValue' \
    --output text)

if [ ! -z "$DISTRIBUTION_ID" ]; then
    echo "🔄 Invalidating CloudFront cache..."
    aws cloudfront create-invalidation \
        --distribution-id $DISTRIBUTION_ID \
        --paths "/*" > /dev/null
    echo "✅ CloudFront cache invalidated"
fi

echo ""
echo "✅ Frontend deployed successfully!"
echo ""
echo "🌐 Access URLs:"
echo "   CloudFront (Recommended): $FRONTEND_URL"
echo "   S3 Website (Direct):      $S3_WEBSITE_URL"
echo ""
echo "🎉 You can now access the FLEET vehicle management interface!"