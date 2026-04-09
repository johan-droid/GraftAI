@echo off
REM GraftAI Development Setup Script for Windows

echo.
echo 🚀 GraftAI Development Setup
echo ==============================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.11+
    exit /b 1
)

REM Check Node
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js 20+
    exit /b 1
)

echo ✅ Prerequisites check passed
echo.

REM Backend setup
echo 🔧 Setting up backend...
cd backend

if not exist ".env" (
    echo 📝 Creating backend .env file...
    copy .env.example .env
    echo ⚠️  Please edit backend\.env with your credentials
)

echo 📦 Installing Python dependencies...
pip install -r requirements.txt

echo ✅ Backend setup complete
echo.

REM Frontend setup
cd ..\frontend
echo 🎨 Setting up frontend...

if not exist ".env.local" (
    echo 📝 Creating frontend .env.local file...
    (
        echo NEXT_PUBLIC_API_URL=http://localhost:8000
        echo NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
        echo NEXT_PUBLIC_APP_URL=http://localhost:3000
    ) > .env.local
)

echo 📦 Installing Node dependencies...
call npm install

echo ✅ Frontend setup complete
echo.

REM Final instructions
echo 🎉 Setup complete!
echo.
echo To start development:
echo.
echo Terminal 1 (Backend):
echo   cd backend
echo   uvicorn api.main:app --reload
echo.
echo Terminal 2 (Frontend):
echo   cd frontend
echo   npm run dev
echo.
echo Then visit: http://localhost:3000
echo.
echo ⚠️  Don't forget to:
echo   1. Set up PostgreSQL database
echo   2. Set up Redis instance
echo   3. Configure OAuth credentials in backend\.env
echo.

cd ..
pause
