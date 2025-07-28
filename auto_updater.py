import os
import sys
import subprocess
import json
import requests
import shutil
import tempfile
import zipfile
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import threading
import time

class AutoUpdater:
    def __init__(self, repo_owner="Architect423", repo_name="AutoParse", current_version="1.0.0"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.current_version = current_version
        self.github_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.repo_url = f"https://github.com/{repo_owner}/{repo_name}"
        self.project_root = Path(__file__).parent
        
    def check_for_updates(self):
        """Check if updates are available from GitHub"""
        try:
            # Check if we're in a git repository
            if not self._is_git_repo():
                print("Not a git repository. Skipping update check.")
                return False
                
            # Get current commit hash
            current_commit = self._get_current_commit()
            if not current_commit:
                print("Could not determine current commit. Skipping update check.")
                return False
                
            # Get latest commit from GitHub
            latest_commit = self._get_latest_commit()
            if not latest_commit:
                print("Could not fetch latest commit from GitHub. Skipping update check.")
                return False
                
            print(f"Current commit: {current_commit[:8]}")
            print(f"Latest commit: {latest_commit[:8]}")
            
            return current_commit != latest_commit
            
        except Exception as e:
            print(f"Error checking for updates: {e}")
            return False
    
    def _is_git_repo(self):
        """Check if current directory is a git repository"""
        return (self.project_root / ".git").exists()
    
    def _get_current_commit(self):
        """Get current git commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            print(f"Error getting current commit: {e}")
        return None
    
    def _get_latest_commit(self):
        """Get latest commit hash from GitHub"""
        try:
            response = requests.get(
                f"{self.github_api_url}/commits/main",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data["sha"]
        except Exception as e:
            print(f"Error fetching latest commit: {e}")
        return None
    
    def update_from_github(self, show_gui=True):
        """Update the application from GitHub"""
        try:
            print("Updating from GitHub...")
            
            # Use git pull to update
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("Successfully updated from GitHub!")
                print(result.stdout)
                
                if show_gui:
                    messagebox.showinfo(
                        "Update Complete", 
                        "AutoParse has been updated successfully!\n\n"
                        "The application will restart to apply changes."
                    )
                
                # Restart the application
                self._restart_application()
                return True
            else:
                error_msg = f"Git pull failed: {result.stderr}"
                print(error_msg)
                
                if show_gui:
                    messagebox.showerror("Update Failed", error_msg)
                return False
                
        except subprocess.TimeoutExpired:
            error_msg = "Update timed out. Please check your internet connection."
            print(error_msg)
            if show_gui:
                messagebox.showerror("Update Failed", error_msg)
            return False
        except Exception as e:
            error_msg = f"Error during update: {e}"
            print(error_msg)
            if show_gui:
                messagebox.showerror("Update Failed", error_msg)
            return False
    
    def _restart_application(self):
        """Restart the application"""
        try:
            # Get the current script path
            script_path = sys.argv[0]
            
            # If running as a .py file, restart with Python
            if script_path.endswith('.py'):
                subprocess.Popen([sys.executable, script_path])
            else:
                # If running as an executable, restart the executable
                subprocess.Popen([script_path])
            
            # Exit current instance
            sys.exit(0)
            
        except Exception as e:
            print(f"Error restarting application: {e}")
    
    def check_and_update_async(self, callback=None):
        """Check for updates asynchronously and update if available"""
        def update_thread():
            try:
                if self.check_for_updates():
                    print("Updates available!")
                    
                    # Ask user if they want to update
                    root = tk.Tk()
                    root.withdraw()  # Hide the root window
                    
                    result = messagebox.askyesno(
                        "Update Available",
                        "A new version of AutoParse is available on GitHub.\n\n"
                        "Would you like to update now?\n\n"
                        "The application will restart after updating."
                    )
                    
                    root.destroy()
                    
                    if result:
                        success = self.update_from_github(show_gui=True)
                        if callback:
                            callback(success)
                    else:
                        print("Update skipped by user.")
                        if callback:
                            callback(False)
                else:
                    print("No updates available.")
                    if callback:
                        callback(False)
                        
            except Exception as e:
                print(f"Error in update thread: {e}")
                if callback:
                    callback(False)
        
        # Run update check in background thread
        thread = threading.Thread(target=update_thread, daemon=True)
        thread.start()
    
    def check_and_update_silent(self):
        """Check for updates silently without GUI prompts"""
        try:
            if self.check_for_updates():
                print("Updates available. Updating silently...")
                return self.update_from_github(show_gui=False)
            else:
                print("No updates available.")
                return False
        except Exception as e:
            print(f"Error in silent update: {e}")
            return False

def check_for_updates_on_startup():
    """Convenience function to check for updates on application startup"""
    updater = AutoUpdater()
    
    # Check for updates in background with a small delay to not block startup
    def delayed_check():
        time.sleep(2)  # Wait 2 seconds after startup
        updater.check_and_update_async()
    
    thread = threading.Thread(target=delayed_check, daemon=True)
    thread.start()

if __name__ == "__main__":
    # Test the updater
    updater = AutoUpdater()
    
    print("Checking for updates...")
    if updater.check_for_updates():
        print("Updates available!")
        updater.update_from_github()
    else:
        print("No updates available.")
