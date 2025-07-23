import os
import sys
import subprocess
import platform
import urllib.request
import zipfile
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

class TesseractManager:
    def __init__(self):
        self.system = platform.system().lower()
        self.tesseract_path = None
        self.tesseract_dir = os.path.join(os.getcwd(), "tesseract")
        
    def check_tesseract_installed(self):
        """Check if Tesseract is installed and accessible"""
        try:
            # Try common installation paths first
            common_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                "/usr/bin/tesseract",
                "/usr/local/bin/tesseract",
                "/opt/homebrew/bin/tesseract",
                os.path.join(self.tesseract_dir, "tesseract.exe"),
                os.path.join(self.tesseract_dir, "tesseract")
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    try:
                        result = subprocess.run([path, "--version"], 
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            self.tesseract_path = path
                            return True
                    except:
                        continue
            
            # Try system PATH
            try:
                result = subprocess.run(["tesseract", "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.tesseract_path = "tesseract"
                    return True
            except:
                pass
                
            return False
        except Exception as e:
            print(f"Error checking Tesseract: {e}")
            return False
    
    def get_tesseract_path(self):
        """Get the path to Tesseract executable"""
        return self.tesseract_path
    
    def download_tesseract_windows(self, progress_callback=None):
        """Download and install Tesseract for Windows"""
        try:
            # Tesseract Windows installer URL (portable version)
            url = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3.20231005/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
            
            # Create tesseract directory
            os.makedirs(self.tesseract_dir, exist_ok=True)
            
            installer_path = os.path.join(self.tesseract_dir, "tesseract_installer.exe")
            
            # Download with progress
            def download_progress(block_num, block_size, total_size):
                if progress_callback and total_size > 0:
                    percent = min(100, (block_num * block_size * 100) // total_size)
                    progress_callback(percent)
            
            urllib.request.urlretrieve(url, installer_path, download_progress)
            
            # Run silent installation
            install_dir = os.path.join(self.tesseract_dir, "install")
            os.makedirs(install_dir, exist_ok=True)
            
            # Try to run installer silently
            try:
                subprocess.run([installer_path, "/S", f"/D={install_dir}"], 
                             check=True, timeout=300)
                
                # Find tesseract.exe in install directory
                for root, dirs, files in os.walk(install_dir):
                    if "tesseract.exe" in files:
                        self.tesseract_path = os.path.join(root, "tesseract.exe")
                        return True
                        
            except subprocess.TimeoutExpired:
                return False
            except subprocess.CalledProcessError:
                # If silent install fails, try manual approach
                return False
                
            return False
            
        except Exception as e:
            print(f"Error downloading Tesseract: {e}")
            return False
    
    def install_tesseract_with_gui(self):
        """Show GUI for Tesseract installation"""
        install_window = tk.Toplevel()
        install_window.title("Installing Tesseract OCR")
        install_window.geometry("400x200")
        install_window.resizable(False, False)
        install_window.grab_set()  # Make it modal
        
        # Center the window
        install_window.transient()
        install_window.focus_set()
        
        frame = tk.Frame(install_window, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        status_label = tk.Label(frame, text="Downloading Tesseract OCR...", font=("Arial", 12))
        status_label.pack(pady=(0, 20))
        
        progress = ttk.Progressbar(frame, mode='determinate', length=300)
        progress.pack(pady=(0, 20))
        
        def update_progress(percent):
            progress['value'] = percent
            install_window.update()
        
        def install_thread():
            try:
                if self.system == "windows":
                    success = self.download_tesseract_windows(update_progress)
                else:
                    # For non-Windows systems, show instructions
                    success = False
                
                if success:
                    status_label.config(text="✓ Tesseract installed successfully!")
                    progress['value'] = 100
                    install_window.after(2000, install_window.destroy)
                else:
                    status_label.config(text="❌ Installation failed. Please install manually.")
                    # Show manual installation instructions
                    self.show_manual_install_instructions(install_window)
                    
            except Exception as e:
                status_label.config(text=f"❌ Error: {str(e)}")
                self.show_manual_install_instructions(install_window)
        
        # Start installation in background
        import threading
        thread = threading.Thread(target=install_thread, daemon=True)
        thread.start()
        
        install_window.wait_window()  # Wait for window to close
        
        # Check if installation was successful
        return self.check_tesseract_installed()
    
    def show_manual_install_instructions(self, parent_window):
        """Show manual installation instructions"""
        instructions_window = tk.Toplevel(parent_window)
        instructions_window.title("Manual Installation Required")
        instructions_window.geometry("500x400")
        
        frame = tk.Frame(instructions_window, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(frame, text="Manual Tesseract Installation", 
                              font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        instructions_text = tk.Text(frame, wrap=tk.WORD, height=15)
        instructions_text.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        if self.system == "windows":
            instructions = """Windows Installation:

1. Download Tesseract from:
   https://github.com/UB-Mannheim/tesseract/wiki

2. Run the installer and follow the setup wizard

3. Default installation path:
   C:\\Program Files\\Tesseract-OCR\\

4. Restart this application after installation

Alternative: Add Tesseract to your system PATH"""
        
        elif self.system == "darwin":  # macOS
            instructions = """macOS Installation:

Option 1 - Using Homebrew (Recommended):
   brew install tesseract

Option 2 - Using MacPorts:
   sudo port install tesseract3

Option 3 - Download from:
   https://github.com/UB-Mannheim/tesseract/wiki

Restart this application after installation"""
        
        else:  # Linux
            instructions = """Linux Installation:

Ubuntu/Debian:
   sudo apt-get update
   sudo apt-get install tesseract-ocr

CentOS/RHEL/Fedora:
   sudo yum install tesseract
   # or
   sudo dnf install tesseract

Arch Linux:
   sudo pacman -S tesseract

Restart this application after installation"""
        
        instructions_text.insert(tk.END, instructions)
        instructions_text.config(state=tk.DISABLED)
        
        close_btn = tk.Button(frame, text="Close", command=instructions_window.destroy)
        close_btn.pack()
    
    def ensure_tesseract_available(self):
        """Ensure Tesseract is available, install if necessary"""
        if self.check_tesseract_installed():
            return True
        
        # Ask user if they want to install Tesseract
        response = messagebox.askyesno(
            "Tesseract OCR Required",
            "Tesseract OCR is required for text recognition but was not found.\n\n"
            "Would you like to install it automatically?\n\n"
            "Click 'No' to see manual installation instructions."
        )
        
        if response:
            # Try automatic installation
            success = self.install_tesseract_with_gui()
            if success:
                messagebox.showinfo("Success", "Tesseract OCR installed successfully!")
                return True
            else:
                messagebox.showerror("Installation Failed", 
                                   "Automatic installation failed. Please install manually.")
                return False
        else:
            # Show manual installation instructions
            root = tk.Tk()
            root.withdraw()  # Hide root window
            self.show_manual_install_instructions(root)
            root.destroy()
            return False
    
    def configure_pytesseract(self):
        """Configure pytesseract with the correct path"""
        if self.tesseract_path and self.tesseract_path != "tesseract":
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
                return True
            except ImportError:
                return False
        return True
