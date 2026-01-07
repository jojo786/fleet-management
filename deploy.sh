#!/bin/bash

# FLEET System Deployment Script
# Usage: ./deploy.sh [dev|prod]

set -e

ENVIRONMENT=${1:-dev}
STACK_NAME="fleet-system-${ENVIRONMENT}"
REGION="eu-west-1"

echo "🚀 Deploying FLEET system to ${ENVIRONMENT} environment..."
echo "Stack Name: ${STACK_NAME}"
echo "Region: ${REGION}"

# Validate SAM template
echo "📋 Validating SAM template..."
sam validate --region ${REGION}

# Build the application
echo "🔨 Building SAM application..."
sam build

# Deploy the application
echo "🚀 Deploying to AWS..."
sam deploy \
  --stack-name ${STACK_NAME} \
  --region ${REGION} \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides Environment=${ENVIRONMENT} \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset

# Get the API endpoint
echo "📡 Getting API endpoint..."
API_URL=$(aws cloudformation describe-stacks \
  --stack-name ${STACK_NAME} \
  --region ${REGION} \
  --query 'Stacks[0].Outputs[?OutputKey==`FleetApiUrl`].OutputValue' \
  --output text)

echo "✅ Deployment complete!"
echo "🌐 API Endpoint: ${API_URL}"
echo "🏥 Health Check: ${API_URL}health"

# Test the health endpoint
echo "🔍 Testing health endpoint..."
curl -s "${API_URL}health" | python3 -m json.tool

echo "🎉 FLEET system foundation deployed successfully!"