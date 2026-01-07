#!/bin/bash

echo "🚀 Starting FLEET frontend locally..."
echo "📍 Frontend will be available at: http://localhost:8000"
echo "🔗 Using API: https://f8bf6be68k.execute-api.eu-west-1.amazonaws.com/dev"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd frontend

# Try different server options
if command -v python3 &> /dev/null; then
    echo "Using Python 3 HTTP server..."
    python3 -m http.server 8000
elif command -v python &> /dev/null; then
    echo "Using Python HTTP server..."
    python -m http.server 8000
elif command -v http-server &> /dev/null; then
    echo "Using Node.js http-server..."
    http-server -p 8000
elif command -v php &> /dev/null; then
    echo "Using PHP built-in server..."
    php -S localhost:8000
else
    echo "❌ No suitable HTTP server found."
    echo "Please install Python, Node.js (with http-server), or PHP to run locally."
    exit 1
fi