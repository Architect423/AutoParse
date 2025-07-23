import tkinter as tk
from tkinter import messagebox
import json
import os
import threading
import time
from PIL import Image, ImageTk, ImageGrab
import pytesseract
import pyautogui
import keyboard
import pyperclip
import re
from tesseract_manager import TesseractManager

class ScreenCalibrator:
    def __init__(self):
        self.config_file = "calibration_config.json"
        self.calibrated_region = None
        self.is_calibrating = False
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.overlay_window = None
        self.canvas = None
        self.rect_id = None
        self.tesseract_manager = TesseractManager()
        self.tesseract_ready = False
        
        # Initialize Tesseract
        self.initialize_tesseract()
        
        # Load existing calibration if available
        self.load_calibration()
        
        # Start hotkey listener in background
        self.start_hotkey_listener()
        
        # Create main window
        self.create_main_window()
    
    def create_main_window(self):
        """Create the main application window"""
        self.root = tk.Tk()
        self.root.title("AutoParse - Screen Region OCR")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Main frame
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="AutoParse", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Status
        self.status_label = tk.Label(main_frame, text="", font=("Arial", 10))
        self.status_label.pack(pady=(0, 10))
        
        # Update status based on calibration and Tesseract
        self.update_status_display()
        
        # Buttons
        calibrate_btn = tk.Button(main_frame, text="Calibrate Screen Region", 
                                command=self.start_calibration, font=("Arial", 12))
        calibrate_btn.pack(pady=10, fill=tk.X)
        
        test_btn = tk.Button(main_frame, text="Test OCR (Press 'M' or click here)", 
                           command=self.capture_and_parse, font=("Arial", 12))
        test_btn.pack(pady=10, fill=tk.X)
        
        # Instructions
        instructions = tk.Text(main_frame, height=8, width=50, wrap=tk.WORD)
        instructions.pack(pady=(20, 0), fill=tk.BOTH, expand=True)
        
        instructions.insert(tk.END, """Instructions:
1. Click 'Calibrate Screen Region' to select the area to monitor
2. Draw a rectangle around the region containing vehicle info
3. Press 'M' hotkey anytime to capture and parse the region
4. Parsed data will be copied to your clipboard

Hotkey: Press 'M' to capture and parse the calibrated region

Expected fields: Name, Model, Plate, Owner""")
        
        instructions.config(state=tk.DISABLED)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def load_calibration(self):
        """Load calibration data from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.calibrated_region = tuple(data.get('region', []))
                    if len(self.calibrated_region) == 4:
                        print(f"Loaded calibration: {self.calibrated_region}")
                    else:
                        self.calibrated_region = None
        except Exception as e:
            print(f"Error loading calibration: {e}")
            self.calibrated_region = None
    
    def save_calibration(self):
        """Save calibration data to file"""
        try:
            data = {'region': self.calibrated_region}
            with open(self.config_file, 'w') as f:
                json.dump(data, f)
            print(f"Saved calibration: {self.calibrated_region}")
        except Exception as e:
            print(f"Error saving calibration: {e}")
    
    def start_calibration(self):
        """Start the calibration process"""
        self.is_calibrating = True
        self.root.withdraw()  # Hide main window
        
        # Create fullscreen overlay
        self.overlay_window = tk.Toplevel()
        self.overlay_window.attributes('-fullscreen', True)
        self.overlay_window.attributes('-alpha', 0.3)
        self.overlay_window.attributes('-topmost', True)
        self.overlay_window.configure(bg='black')
        
        # Create canvas for drawing
        self.canvas = tk.Canvas(self.overlay_window, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.configure(bg='black')
        
        # Bind mouse events
        self.canvas.bind('<Button-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        
        # Instructions
        self.canvas.create_text(
            self.overlay_window.winfo_screenwidth() // 2, 50,
            text="Draw a rectangle around the region to monitor. Press ESC to cancel.",
            fill='white', font=('Arial', 16)
        )
        
        # Bind escape key
        self.overlay_window.bind('<Escape>', self.cancel_calibration)
        self.overlay_window.focus_set()
    
    def on_mouse_down(self, event):
        """Handle mouse down event"""
        self.start_x = event.x
        self.start_y = event.y
        if self.rect_id:
            self.canvas.delete(self.rect_id)
    
    def on_mouse_drag(self, event):
        """Handle mouse drag event"""
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline='red', width=2, fill='', stipple='gray50'
        )
    
    def on_mouse_up(self, event):
        """Handle mouse up event"""
        self.end_x = event.x
        self.end_y = event.y
        
        # Ensure we have a valid rectangle
        if abs(self.end_x - self.start_x) > 10 and abs(self.end_y - self.start_y) > 10:
            # Convert to screen coordinates
            x1 = min(self.start_x, self.end_x)
            y1 = min(self.start_y, self.end_y)
            x2 = max(self.start_x, self.end_x)
            y2 = max(self.start_y, self.end_y)
            
            self.calibrated_region = (x1, y1, x2, y2)
            self.save_calibration()
            
            # Close overlay and show main window
            self.finish_calibration()
        else:
            messagebox.showwarning("Invalid Selection", "Please draw a larger rectangle.")
    
    def cancel_calibration(self, event=None):
        """Cancel calibration process"""
        self.finish_calibration()
    
    def finish_calibration(self):
        """Finish calibration and return to main window"""
        if self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None
        
        self.is_calibrating = False
        self.root.deiconify()  # Show main window
        
        # Update status
        self.update_status_display()
    
    def start_hotkey_listener(self):
        """Start the hotkey listener in a background thread"""
        def hotkey_thread():
            keyboard.add_hotkey('m', self.capture_and_parse)
            keyboard.wait()  # Keep the thread alive
        
        thread = threading.Thread(target=hotkey_thread, daemon=True)
        thread.start()
    
    def initialize_tesseract(self):
        """Initialize and verify Tesseract OCR"""
        try:
            if self.tesseract_manager.ensure_tesseract_available():
                self.tesseract_manager.configure_pytesseract()
                self.tesseract_ready = True
                print("Tesseract OCR initialized successfully")
            else:
                self.tesseract_ready = False
                print("Tesseract OCR not available")
        except Exception as e:
            print(f"Error initializing Tesseract: {e}")
            self.tesseract_ready = False
    
    def update_status_display(self):
        """Update the status display with calibration and Tesseract status"""
        status_parts = []
        
        # Tesseract status
        if self.tesseract_ready:
            status_parts.append("✓ Tesseract OCR ready")
        else:
            status_parts.append("⚠ Tesseract OCR not available")
        
        # Calibration status
        if self.calibrated_region:
            status_parts.append(f"✓ Region calibrated: {self.calibrated_region}")
        else:
            status_parts.append("⚠ No calibrated region")
        
        status_text = "\n".join(status_parts)
        
        if self.tesseract_ready and self.calibrated_region:
            self.status_label.config(text=status_text, fg="green")
        elif not self.tesseract_ready:
            self.status_label.config(text=status_text, fg="red")
        else:
            self.status_label.config(text=status_text, fg="orange")
    
    def capture_and_parse(self):
        """Capture screenshot of calibrated region and parse with OCR"""
        if not self.tesseract_ready:
            response = messagebox.askyesno(
                "Tesseract Not Ready", 
                "Tesseract OCR is not available. Would you like to try installing it now?"
            )
            if response:
                self.initialize_tesseract()
                self.update_status_display()
                if not self.tesseract_ready:
                    return
            else:
                return
        
        if not self.calibrated_region:
            messagebox.showwarning("No Calibration", "Please calibrate a screen region first.")
            return
        
        try:
            # Capture screenshot of the calibrated region
            screenshot = ImageGrab.grab(bbox=self.calibrated_region)
            
            # Perform OCR
            text = pytesseract.image_to_string(screenshot, config='--psm 6')
            
            # Parse the text for required fields
            parsed_data = self.parse_vehicle_data(text)
            
            # Format and copy to clipboard
            formatted_output = self.format_output(parsed_data)
            pyperclip.copy(formatted_output)
            
            # Show success message
            messagebox.showinfo("Success", f"Data captured and copied to clipboard!\n\n{formatted_output}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture and parse: {str(e)}")
    
    def parse_vehicle_data(self, text):
        """Parse OCR text to extract vehicle information"""
        data = {
            'Name': '',
            'Model': '',
            'Plate': '',
            'Owner': ''
        }
        
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to match patterns for each field
            line_lower = line.lower()
            
            # Name field
            if 'name' in line_lower and ':' in line:
                data['Name'] = line.split(':', 1)[1].strip()
            
            # Model field
            elif 'model' in line_lower and ':' in line:
                data['Model'] = line.split(':', 1)[1].strip()
            
            # Plate field
            elif 'plate' in line_lower and ':' in line:
                data['Plate'] = line.split(':', 1)[1].strip()
            
            # Owner field
            elif 'owner' in line_lower and ':' in line:
                data['Owner'] = line.split(':', 1)[1].strip()
        
        # If no structured data found, try to extract from unstructured text
        if not any(data.values()):
            # This is a fallback - you might need to adjust based on your specific format
            for i, line in enumerate(lines):
                line = line.strip()
                if line and i < len(list(data.keys())):
                    key = list(data.keys())[i]
                    data[key] = line
        
        return data
    
    def format_output(self, data):
        """Format the parsed data according to specifications"""
        return f"""```
Name:  {data.get('Name', '')}
Model: {data.get('Model', '')}
Plate: {data.get('Plate', '')}
Owner: {data.get('Owner', '')}
```"""
    
    def on_closing(self):
        """Handle application closing"""
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    # Check if required dependencies are available
    try:
        import pyautogui
        import keyboard
        import pyperclip
        from PIL import Image, ImageTk, ImageGrab
        # pytesseract will be handled by TesseractManager
    except ImportError as e:
        print(f"Missing required dependency: {e}")
        print("Please install required packages using: pip install -r requirements.txt")
        exit(1)
    
    try:
        app = ScreenCalibrator()
        app.run()
    except Exception as e:
        print(f"Application error: {e}")
        input("Press Enter to exit...")
