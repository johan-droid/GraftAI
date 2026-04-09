#!/bin/bash

# GraftAI Development Setup Script
# This script sets up the development environment

set -e

echo "🚀 GraftAI Development Setup"
echo "=============================="
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 20+"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Backend setup
echo "🔧 Setting up backend..."
cd backend

if [ ! -f ".env" ]; then
    echo "📝 Creating backend .env file..."
    cp .env.example .env
    echo "⚠️  Please edit backend/.env with your credentials"
fi

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Backend setup complete"
echo ""

# Frontend setup
cd ../frontend
echo "🎨 Setting up frontend..."

if [ ! -f ".env.local" ]; then
    echo "📝 Creating frontend .env.local file..."
    cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_URL=http://localhost:3000
EOF
fi

echo "📦 Installing Node dependencies..."
npm install

echo "✅ Frontend setup complete"
echo ""

# Final instructions
echo "🎉 Setup complete!"
echo ""
echo "To start development:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd backend"
echo "  uvicorn api.main:app --reload"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then visit: http://localhost:3000"
echo ""
echo "⚠️  Don't forget to:"
echo "  1. Set up PostgreSQL database"
echo "  2. Set up Redis instance"
echo "  3. Configure OAuth credentials in backend/.env"
echo ""
