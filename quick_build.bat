@echo off
echo ========================================
echo AutoParse - Quick Build
echo ========================================
echo.

:: Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Running full build...
    call build_exe.bat
    exit /b
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

:: Clean previous builds
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

echo Building executable (quick mode)...

:: Build with PyInstaller
pyinstaller --onefile --windowed --name "AutoParse" --icon=icon.ico main.py

if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo BUILD COMPLETE!
echo ========================================
echo.
echo Executable: dist\AutoParse.exe
echo.

deactivate
explorer dist
exit /b 0
