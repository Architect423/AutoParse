# AutoParse - Screen Region OCR Tool

A Python application that allows you to calibrate a screen region and automatically parse text from screenshots using OCR technology.

## Features

- **Screen Region Calibration**: Draw a rectangle to select the area you want to monitor
- **Persistent Storage**: Calibrated region is saved and restored on next launch
- **Hotkey Support**: Press 'M' to instantly capture and parse the calibrated region
- **OCR Text Parsing**: Extracts vehicle information (Name, Make, Model, Plate, Owner)
- **Clipboard Integration**: Automatically copies formatted results to clipboard

## Prerequisites

- Python 3.7 or higher
- Tesseract OCR engine

### Installing Tesseract OCR

**Windows:**
1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install it (default location: `C:\Program Files\Tesseract-OCR\`)
3. Add Tesseract to your PATH or update the script if installed elsewhere

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

## Installation

1. Clone or download this repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the application:**
   ```bash
   python main.py
   ```

2. **Calibrate the screen region:**
   - Click "Calibrate Screen Region"
   - Draw a rectangle around the area containing vehicle information
   - The region will be saved for future use

3. **Capture and parse:**
   - Press the 'M' hotkey anytime to capture the calibrated region
   - Or click "Test OCR" in the application
   - Parsed data will be automatically copied to your clipboard

## Output Format

The application outputs data in the following format:
```
Name:  [Extracted Name]
Make:  [Extracted Make]
Model: [Extracted Model]
Plate: [Extracted Plate]
```

## Configuration

- Calibration data is stored in `calibration_config.json`
- Delete this file to recalibrate the region

## Troubleshooting

- **OCR not working**: Ensure Tesseract is properly installed and in your PATH
- **Hotkey not responding**: Make sure the application is running and has proper permissions
- **Poor OCR results**: Try recalibrating with a clearer, larger region

## Dependencies

- Pillow: Image processing
- pytesseract: OCR functionality
- pyautogui: Screenshot capture
- keyboard: Global hotkey detection
- pyperclip: Clipboard operations
