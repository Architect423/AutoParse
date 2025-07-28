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
from auto_updater import check_for_updates_on_startup

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
        self.capture_hotkey = 'm'  # Default hotkey
        self.hotkey_thread = None
        
        # Initialize Tesseract
        self.initialize_tesseract()
        
        # Load existing calibration and settings
        self.load_calibration()
        
        # Check for updates from GitHub
        check_for_updates_on_startup()
        
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
        
        # Hotkey configuration frame
        hotkey_frame = tk.Frame(main_frame)
        hotkey_frame.pack(pady=(0, 10), fill=tk.X)
        
        tk.Label(hotkey_frame, text="Capture Hotkey:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.hotkey_var = tk.StringVar(value=self.capture_hotkey)
        hotkey_entry = tk.Entry(hotkey_frame, textvariable=self.hotkey_var, width=5, font=("Arial", 10))
        hotkey_entry.pack(side=tk.LEFT, padx=(5, 5))
        
        set_hotkey_btn = tk.Button(hotkey_frame, text="Set Hotkey", 
                                 command=self.set_hotkey, font=("Arial", 9))
        set_hotkey_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Buttons
        calibrate_btn = tk.Button(main_frame, text="Calibrate Screen Region", 
                                command=self.start_calibration, font=("Arial", 12))
        calibrate_btn.pack(pady=10, fill=tk.X)
        
        test_btn = tk.Button(main_frame, text=f"Test OCR (Press '{self.capture_hotkey}' or click here)", 
                           command=self.capture_and_parse, font=("Arial", 12))
        test_btn.pack(pady=10, fill=tk.X)
        self.test_btn = test_btn  # Store reference for updating
        
        # Instructions
        instructions = tk.Text(main_frame, height=8, width=50, wrap=tk.WORD)
        instructions.pack(pady=(20, 0), fill=tk.BOTH, expand=True)
        
        instructions.insert(tk.END, f"""Instructions:
1. Set your preferred capture hotkey above (default: 'm')
2. Click 'Calibrate Screen Region' to select the area to monitor
3. Draw a rectangle around the region containing vehicle info
4. Press '{self.capture_hotkey}' hotkey anytime to capture and parse the region
5. Parsed data will be copied to your clipboard

Gaming Tips:
- Use a key that doesn't conflict with your game (e.g., 'f9', 'f10')
- The hotkey works even when tabbed into games
- Try function keys (f1-f12) for best game compatibility

Expected input fields: Name, Model, Plate, Owner
Output format: Customer Name, Vehicle Make/Model, Plate""")
        
        instructions.config(state=tk.DISABLED)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def set_hotkey(self):
        """Set a new capture hotkey"""
        new_hotkey = self.hotkey_var.get().strip().lower()
        
        if not new_hotkey:
            messagebox.showwarning("Invalid Hotkey", "Please enter a valid hotkey.")
            return
        
        if len(new_hotkey) > 10:  # Reasonable limit
            messagebox.showwarning("Invalid Hotkey", "Hotkey too long. Please use a shorter key combination.")
            return
        
        try:
            # Test if the hotkey is valid by trying to parse it
            old_hotkey = self.capture_hotkey
            self.capture_hotkey = new_hotkey
            
            # Restart the hotkey listener with the new hotkey
            self.start_hotkey_listener()
            
            # Update the test button text
            self.test_btn.config(text=f"Test OCR (Press '{self.capture_hotkey}' or click here)")
            
            # Save the new configuration
            self.save_calibration()
            
            messagebox.showinfo("Hotkey Updated", f"Capture hotkey changed to '{new_hotkey}'")
            
        except Exception as e:
            # Revert to old hotkey if there was an error
            self.capture_hotkey = old_hotkey
            self.hotkey_var.set(old_hotkey)
            messagebox.showerror("Error", f"Failed to set hotkey '{new_hotkey}': {str(e)}")
    
    def load_calibration(self):
        """Load calibration data and settings from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.calibrated_region = tuple(data.get('region', []))
                    if len(self.calibrated_region) == 4:
                        print(f"Loaded calibration: {self.calibrated_region}")
                    else:
                        self.calibrated_region = None
                    
                    # Load hotkey setting
                    self.capture_hotkey = data.get('hotkey', 'm')
                    print(f"Loaded hotkey: {self.capture_hotkey}")
        except Exception as e:
            print(f"Error loading calibration: {e}")
            self.calibrated_region = None
            self.capture_hotkey = 'm'
    
    def save_calibration(self):
        """Save calibration data and settings to file"""
        try:
            data = {
                'region': self.calibrated_region,
                'hotkey': self.capture_hotkey
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f)
            print(f"Saved calibration: {self.calibrated_region}")
            print(f"Saved hotkey: {self.capture_hotkey}")
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
        """Start the hotkey listener in a background thread with improved reliability"""
        def hotkey_thread():
            try:
                # Clear any existing hotkeys first
                keyboard.clear_all_hotkeys()
                
                print(f"Setting up hotkey listener for '{self.capture_hotkey}'")
                
                # Add the configurable hotkey with suppress=False for better game compatibility
                keyboard.add_hotkey(self.capture_hotkey, self.capture_and_parse, suppress=False)
                
                print(f"Hotkey '{self.capture_hotkey}' registered successfully")
                
                # Keep the thread alive with a simple loop
                while True:
                    time.sleep(1)  # Check every second
                    
            except Exception as e:
                print(f"Failed to start hotkey listener: {e}")
                # Try a simpler approach if the above fails
                try:
                    keyboard.on_press_key(self.capture_hotkey, lambda _: self.capture_and_parse())
                    print(f"Fallback hotkey listener started for '{self.capture_hotkey}'")
                    while True:
                        time.sleep(1)
                except Exception as e2:
                    print(f"Fallback hotkey listener also failed: {e2}")
        
        # Stop existing thread if running
        if self.hotkey_thread and self.hotkey_thread.is_alive():
            keyboard.clear_all_hotkeys()
        
        self.hotkey_thread = threading.Thread(target=hotkey_thread, daemon=True)
        self.hotkey_thread.start()
        print(f"Started hotkey listener thread for '{self.capture_hotkey}'")
    
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
        """Capture screenshot of calibrated region and parse with OCR - Gaming optimized"""
        # Check if Tesseract is ready
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
            # Add a small delay to ensure game rendering is complete
            time.sleep(0.1)
            
            # Capture screenshot of the calibrated region with retry logic
            screenshot = None
            for attempt in range(3):  # Try up to 3 times
                try:
                    screenshot = ImageGrab.grab(bbox=self.calibrated_region)
                    if screenshot:
                        break
                except Exception as e:
                    print(f"Screenshot attempt {attempt + 1} failed: {e}")
                    time.sleep(0.05)  # Brief pause before retry
            
            if not screenshot:
                raise Exception("Failed to capture screenshot after multiple attempts")
            
            # Perform OCR with gaming-optimized settings
            text = pytesseract.image_to_string(screenshot, config='--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789: ')
            
            # Parse the text for required fields
            parsed_data = self.parse_vehicle_data(text)
            
            # Format and copy to clipboard
            formatted_output = self.format_output(parsed_data)
            pyperclip.copy(formatted_output)
            
            # Show success message (only if not in game mode - check if main window is focused)
            try:
                if self.root.focus_get():
                    messagebox.showinfo("Success", f"Data captured and copied to clipboard!\n\n{formatted_output}")
                else:
                    # Just print to console if game is likely focused
                    print(f"Data captured and copied to clipboard: {formatted_output}")
            except:
                print(f"Data captured and copied to clipboard: {formatted_output}")
            
        except Exception as e:
            error_msg = f"Failed to capture and parse: {str(e)}"
            print(error_msg)
            try:
                if self.root.focus_get():
                    messagebox.showerror("Error", error_msg)
            except:
                pass  # Don't show error dialog if game is focused
    
    def parse_vehicle_data(self, text):
        """Parse OCR text to extract vehicle information"""
        data = {
            'Name': '',
            'Model': '',
            'Plate': '',
            'Owner': ''
        }
        
        # Clean up the text
        text = text.strip()
        print(f"Raw OCR text: '{text}'")  # Debug output
        
        import re
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        print(f"OCR lines: {lines}")  # Debug output
        
        # Define field labels to look for
        field_labels = ['name', 'model', 'plate', 'owner']
        
        # Parse multi-line fields
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this line contains a field label
            if ':' in line:
                field_name, field_value = line.split(':', 1)
                field_name = field_name.strip().lower()
                field_value = field_value.strip()
                
                # If this is a recognized field, collect all lines until the next field
                if field_name in field_labels:
                    # Start with the value on the same line as the field label
                    full_value = field_value
                    
                    # Look ahead to collect continuation lines
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j]
                        
                        # Stop if we hit another field label
                        if ':' in next_line:
                            next_field = next_line.split(':', 1)[0].strip().lower()
                            if next_field in field_labels:
                                break
                        
                        # This line is a continuation of the current field
                        if full_value:
                            full_value += ' ' + next_line
                        else:
                            full_value = next_line
                        j += 1
                    
                    # Store the complete field value
                    if field_name == 'name':
                        data['Name'] = full_value
                        print(f"Parsed Name: '{data['Name']}'")
                        
                    elif field_name == 'model':
                        # Fix common spacing issues in model names
                        if re.search(r'[a-z][A-Z]', full_value):
                            full_value = re.sub(r'([a-z])([A-Z])', r'\1 \2', full_value)
                            print(f"Fixed model spacing: '{full_value}'")
                        
                        data['Model'] = full_value
                        print(f"Parsed Model: '{data['Model']}'")
                        
                    elif field_name == 'plate':
                        data['Plate'] = full_value
                        print(f"Parsed Plate: '{data['Plate']}'")
                        
                    elif field_name == 'owner':
                        # Fix common spacing issues in owner names
                        if re.search(r'[a-z][A-Z]', full_value):
                            full_value = re.sub(r'([a-z])([A-Z])', r'\1 \2', full_value)
                            print(f"Fixed owner spacing: '{full_value}'")
                        
                        data['Owner'] = full_value
                        print(f"Parsed Owner: '{data['Owner']}'")
                    
                    # Skip the lines we've already processed
                    i = j - 1
            
            i += 1
        
        # Fallback: try line-by-line parsing if no fields were found
        if not any(data.values()):
            print("Fallback parsing: No field labels found, trying line-by-line")
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
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
        
        return data
    
    def format_output(self, data):
        """Format the parsed data according to specifications"""
        # Customer Name comes from Owner field
        customer_name = data.get('Owner', '')
        
        # Vehicle Make/Model combines Name and Model fields
        name = data.get('Name', '').strip()
        model = data.get('Model', '').strip()
        
        # Ensure proper spacing between name and model
        if name and model:
            vehicle_make_model = f"{name} {model}"
        elif name:
            vehicle_make_model = name
        elif model:
            vehicle_make_model = model
        else:
            vehicle_make_model = ""
        
        # Plate stays the same
        plate = data.get('Plate', '')
        
        return f"""```
Customer Name: {customer_name}
Vehicle | [Make/Model]: {vehicle_make_model}
Plate: {plate}
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
