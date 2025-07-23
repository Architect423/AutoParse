# AutoParse - Build Guide

This guide explains how to build AutoParse into a standalone executable file.

## Quick Start

### Option 1: Full Build (Recommended for first time)
```bash
build_exe.bat
```
This will:
- Create a virtual environment
- Install all dependencies
- Build the executable with all features

### Option 2: Quick Build (If environment already exists)
```bash
quick_build.bat
```
This will:
- Use existing virtual environment
- Quick build without dependency reinstall

## What the Build Process Does

1. **Environment Setup**
   - Creates Python virtual environment
   - Installs all required packages
   - Installs PyInstaller for executable creation

2. **Dependency Management**
   - Pillow (Image processing)
   - pytesseract (OCR functionality)
   - pyautogui (Screenshot capture)
   - keyboard (Global hotkey detection)
   - pyperclip (Clipboard operations)
   - PyInstaller (Executable creation)

3. **Executable Creation**
   - Packages all Python code and dependencies
   - Creates single-file executable
   - Includes Tesseract auto-installer
   - Adds application icon
   - Enables windowed mode (no console)

## Output

After successful build:
- **Executable**: `dist\AutoParse.exe`
- **Size**: ~50-100MB (includes all dependencies)
- **Requirements**: None (standalone executable)

## Distribution

The `AutoParse.exe` file can be distributed independently:
- No Python installation required on target machine
- No additional dependencies needed
- Tesseract OCR will be auto-installed when needed
- Calibration settings are saved locally

## Troubleshooting

### Build Fails
- Ensure Python 3.7+ is installed
- Check that all files are present in the directory
- Run `pip install -r requirements.txt` manually if needed

### Executable Issues
- Run from command line to see error messages
- Ensure Windows Defender isn't blocking the file
- Check that the executable has proper permissions

### Missing Features
- If hotkeys don't work, run as administrator
- If OCR fails, the app will prompt to install Tesseract
- Calibration data is stored in the same directory as the executable

## File Structure After Build

```
AutoParse/
├── dist/
│   └── AutoParse.exe          # Final executable
├── build/                     # Temporary build files
├── venv/                      # Virtual environment
├── main.py                    # Source code
├── tesseract_manager.py       # OCR manager
├── requirements.txt           # Dependencies
├── build_exe.bat             # Full build script
├── quick_build.bat           # Quick build script
├── icon.ico                  # Application icon
└── BUILD_GUIDE.md            # This guide
```

## Advanced Options

To customize the build, modify the PyInstaller command in `build_exe.bat`:

- `--onefile`: Creates single executable file
- `--windowed`: Hides console window
- `--icon=icon.ico`: Sets application icon
- `--name "AutoParse"`: Sets executable name
- `--add-data`: Includes additional files

## System Requirements

**Development:**
- Windows 10/11
- Python 3.7+
- 500MB free space for build environment

**Distribution:**
- Windows 10/11
- 100MB free space
- Administrator rights (for hotkey functionality)
