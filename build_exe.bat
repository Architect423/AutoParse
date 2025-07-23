@echo off
echo ========================================
echo AutoParse - EXE Builder
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo [1/6] Python found - checking version...
python --version

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [2/6] Creating virtual environment...
    python -m venv venv
) else (
    echo [2/6] Virtual environment already exists
)

:: Activate virtual environment
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat

:: Upgrade pip
echo [4/6] Upgrading pip...
python -m pip install --upgrade pip

:: Install dependencies
echo [5/6] Installing dependencies...
pip install -r requirements.txt

:: Install PyInstaller for creating executable
echo Installing PyInstaller...
pip install pyinstaller

:: Clean previous builds
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "*.spec" del *.spec

:: Create executable with PyInstaller
echo [6/6] Building executable...
echo This may take a few minutes...

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "AutoParse" ^
    --icon=icon.ico ^
    --add-data "tesseract_manager.py;." ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=PIL.ImageTk ^
    --hidden-import=PIL.ImageGrab ^
    --hidden-import=pytesseract ^
    --hidden-import=pyautogui ^
    --hidden-import=keyboard ^
    --hidden-import=pyperclip ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.messagebox ^
    --hidden-import=tkinter.ttk ^
    --collect-all=PIL ^
    --collect-all=pytesseract ^
    main.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo Check the output above for details.
    pause
    exit /b 1
)

echo.
echo ========================================
echo BUILD SUCCESSFUL!
echo ========================================
echo.
echo Executable created: dist\AutoParse.exe
echo.
echo The executable includes:
echo - All Python dependencies
echo - Tesseract auto-installer
echo - GUI interface
echo - Hotkey functionality
echo.
echo You can now distribute the AutoParse.exe file
echo without requiring Python installation.
echo.

:: Deactivate virtual environment
deactivate

echo Press any key to open the dist folder...
pause >nul
explorer dist

exit /b 0
