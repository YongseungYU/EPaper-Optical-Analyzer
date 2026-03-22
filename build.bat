@echo off
setlocal

echo ==========================================
echo  E-Paper Optical Analyzer - Build Script
echo ==========================================

:: Check Python version
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.8+.
    exit /b 1
)

python --version
echo.

:: Change to script directory
cd /d "%~dp0"
echo Working directory: %cd%

:: Create or activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo Activating existing virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
)

:: Install dependencies
echo.
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements_desktop.txt

:: Run PyInstaller
echo.
echo Building executable with PyInstaller...
pyinstaller epaper_analyzer.spec --clean

echo.
echo ==========================================
echo  Build Complete!
echo ==========================================
echo  Output: dist\EPaper_Optical_Analyzer\
echo ==========================================

endlocal
