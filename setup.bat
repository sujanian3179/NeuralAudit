@echo off
REM NeuralAudit Quick Start Script (Windows)
REM This script helps you get started with NeuralAudit in minutes

setlocal enabledelayedexpansion

echo.
echo ============================================
echo 🚀 NeuralAudit Quick Start Setup (Windows)
echo ============================================
echo.

REM Step 1: Check Python
echo Step 1: Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python %PYTHON_VERSION% found
echo.

REM Step 2: Create virtual environment
echo Step 2: Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)
echo.

REM Step 3: Activate virtual environment
echo Step 3: Activating virtual environment...
call venv\Scripts\activate.bat
echo ✓ Virtual environment activated
echo.

REM Step 4: Install dependencies
echo Step 4: Installing dependencies...
pip install --upgrade pip setuptools wheel >nul 2>&1
pip install -r requirements.txt >nul 2>&1
echo ✓ Dependencies installed
echo.

REM Step 5: Setup configuration
echo Step 5: Setting up configuration...
if not exist ".env" (
    copy .env.example .env >nul
    echo ✓ Configuration file created (.env)
    echo   Note: Review .env file for customization
) else (
    echo ✓ Configuration file already exists
)
echo.

REM Step 6: Create necessary directories
echo Step 6: Creating directories...
if not exist "logs" mkdir logs
if not exist "models" mkdir models
if not exist "data" mkdir data
if not exist "screenshots" mkdir screenshots
if not exist "results" mkdir results
echo ✓ Directories created
echo.

REM Step 7: Verify installation
echo Step 7: Verifying installation...
python -c "import config, logger, scraper, preprocessing, model, auditor, database, pipeline; print('✓ All modules imported successfully')" 2>nul
if errorlevel 1 (
    echo ❌ Module import failed. Please check installation.
    exit /b 1
)
echo.

REM Step 8: Display quick usage
echo ============================================
echo ✅ Setup Complete!
echo ============================================
echo.
echo Next Steps:
echo.
echo 1. Review configuration:
echo    notepad .env
echo.
echo 2. Run tests (optional):
echo    python integration_tests.py
echo.
echo 3. Try examples:
echo    python examples.py
echo.
echo 4. Process a product:
echo    python main.py --product "https://example.com/product"
echo.
echo 5. Start API server:
echo    python main.py --api
echo    Then visit: http://localhost:8000/docs
echo.
echo 6. Process batch from CSV:
echo    python main.py --csv products.csv
echo.
echo Documentation:
echo   - USAGE.md: User guide
echo   - IMPLEMENTATION.md: Detailed setup
echo   - README.md: Project overview
echo.
echo ============================================
echo.
