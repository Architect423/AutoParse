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
        # Determine runtime context and base directory
        self.is_frozen = getattr(sys, "frozen", False)
        self.base_dir = Path(sys.executable).parent if self.is_frozen else Path(__file__).parent
        self.project_root = Path(__file__).parent  # used for developer git flow

        # Load config (overrides defaults if present)
        cfg = self._load_config(self.base_dir / "version_config.json")

        self.repo_owner = cfg.get("repo_owner", repo_owner)
        self.repo_name = cfg.get("repo_name", repo_name)
        self.current_version = cfg.get("version", current_version)
        self.auto_update_enabled = cfg.get("auto_update_enabled", True)
        self.check_on_startup = cfg.get("check_on_startup", True)
        self.update_check_delay_seconds = int(cfg.get("update_check_delay_seconds", 2))
        self.release_asset_name = cfg.get("release_asset_name", None)
        
        # Try to override version from a state file written by the updater (survives EXE swaps)
        try:
            state_json = self.base_dir / "installed_version.json"
            state_txt = self.base_dir / "installed_version.txt"
            if state_json.exists():
                with open(state_json, "r", encoding="utf-8") as vf:
                    vobj = json.load(vf)
                    self.current_version = vobj.get("version", self.current_version)
            elif state_txt.exists():
                self.current_version = state_txt.read_text(encoding="utf-8").strip() or self.current_version
        except Exception as e:
            print(f"AutoUpdater: could not read installed version file: {e}")
        
        self.github_api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
        self.repo_url = f"https://github.com/{self.repo_owner}/{self.repo_name}"
        
        # Current executable path and platform info
        self.executable_path = Path(sys.executable) if self.is_frozen else Path(sys.argv[0]).resolve()
        self.executable_name = self.executable_path.name
        self.is_windows = os.name == "nt"
        
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

    # =========================
    # Release-based update path
    # =========================

    def _load_config(self, config_path: Path):
        """Load updater configuration from version_config.json if present"""
        try:
            if not config_path.exists():
                alt = self.project_root / "version_config.json"
                if alt.exists():
                    config_path = alt
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"AutoUpdater: could not load config ({e}); using defaults.")
        return {}

    def _normalize_version(self, v: str) -> str:
        if not v:
            return "0.0.0"
        v = v.strip()
        if v.lower().startswith("v"):
            v = v[1:]
        return v

    def _version_tuple(self, v: str):
        v = self._normalize_version(v)
        parts = v.split(".")
        nums = []
        for p in parts:
            try:
                nums.append(int(''.join(ch for ch in p if ch.isdigit())))
            except ValueError:
                nums.append(0)
        while len(nums) < 3:
            nums.append(0)
        return tuple(nums[:3])

    def _is_newer_version(self, latest: str, current: str) -> bool:
        return self._version_tuple(latest) > self._version_tuple(current)

    def _get_latest_release(self):
        """Fetch latest release info from GitHub Releases"""
        try:
            resp = requests.get(
                f"{self.github_api_url}/releases/latest",
                headers={"Accept": "application/vnd.github+json"},
                timeout=15
            )
            if resp.status_code == 200:
                return resp.json()
            print(f"GitHub releases returned status {resp.status_code}")
        except Exception as e:
            print(f"Error fetching latest release: {e}")
        return None

    def _select_release_asset(self, release_json):
        """Choose a suitable asset to download (prefer configured name, else .exe on Windows, else first asset)."""
        assets = release_json.get("assets", []) if release_json else []
        if not assets:
            return None

        # Exact name preference from config
        if self.release_asset_name:
            for a in assets:
                if a.get("name", "") == self.release_asset_name:
                    return a

        # Platform heuristic
        if self.is_windows:
            for a in assets:
                name = a.get("name", "").lower()
                if name.endswith(".exe"):
                    return a
            # Fallback to zip if no exe
            for a in assets:
                name = a.get("name", "").lower()
                if name.endswith(".zip"):
                    return a

        # Final fallback: first asset
        return assets[0]

    def _download_to_temp(self, url: str, suffix: str):
        """Download a file to a temporary path and return the file path"""
        try:
            with requests.get(url, stream=True, timeout=60, headers={"Accept": "application/octet-stream"}) as r:
                r.raise_for_status()
                fd, temp_path = tempfile.mkstemp(suffix=suffix)
                with os.fdopen(fd, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 256):
                        if chunk:
                            f.write(chunk)
            return temp_path
        except Exception as e:
            print(f"Download failed: {e}")
            return None

    def _apply_update_windows(self, new_file_path: str) -> bool:
        """Replace the running EXE safely on Windows using a temporary batch script and relaunch"""
        try:
            if not self.is_windows:
                print("Windows update routine called on non-Windows system.")
                return False

            target = str(self.executable_path)
            src = str(Path(new_file_path).resolve())

            # Create an updater batch that waits until this process exits, then replaces and relaunches
            bat_content = f"""@echo off
setlocal enableextensions
set SRC="{src}"
set DST="{target}"
:waitloop
timeout /t 1 /nobreak >NUL
move /Y %SRC% %DST% >NUL 2>&1
if errorlevel 1 goto waitloop
start "" "%DST%"
del "%~f0"
"""

            fd, bat_path = tempfile.mkstemp(suffix=".bat")
            with os.fdopen(fd, "w", encoding="utf-8") as bf:
                bf.write(bat_content)

            # Launch the batch and exit this process
            subprocess.Popen(["cmd", "/c", bat_path], close_fds=False)
            sys.exit(0)
            return True
        except Exception as e:
            print(f"Error applying Windows update: {e}")
            return False

    def check_and_update_from_release(self, show_gui=True):
        """Check GitHub Releases and update the running EXE if a newer version exists."""
        try:
            if not getattr(self, "auto_update_enabled", True):
                print("Auto-update disabled by configuration.")
                return False

            release = self._get_latest_release()
            if not release:
                print("No release information available.")
                return False

            latest_version = self._normalize_version(release.get("tag_name") or release.get("name") or "")
            if not latest_version:
                print("Latest release has no version tag/name; skipping.")
                return False

            if not self._is_newer_version(latest_version, self.current_version):
                print(f"No updates available. Current={self.current_version}, Latest={latest_version}")
                return False

            # Ask the user if interactive
            if show_gui:
                root = tk.Tk()
                root.withdraw()
                proceed = messagebox.askyesno(
                    "Update Available",
                    f"A new version of AutoParse is available.\n\n"
                    f"Current: {self.current_version}\nLatest:  {latest_version}\n\n"
                    f"Update now? The application will restart."
                )
                root.destroy()
                if not proceed:
                    print("Update skipped by user.")
                    return False

            asset = self._select_release_asset(release)
            if not asset:
                print("No suitable release asset found.")
                return False

            download_url = asset.get("browser_download_url")
            asset_name = asset.get("name", "")
            print(f"Downloading release asset: {asset_name}")

            suffix = ".zip" if asset_name.lower().endswith(".zip") else ".exe"
            temp_path = self._download_to_temp(download_url, suffix=suffix)
            if not temp_path:
                print("Download failed.")
                return False

            # If the asset is a zip, extract to find the new EXE
            new_exe_path = None
            if temp_path.lower().endswith(".zip"):
                extract_dir = Path(tempfile.mkdtemp(prefix="autoparse_update_"))
                try:
                    with zipfile.ZipFile(temp_path, "r") as zf:
                        zf.extractall(extract_dir)
                    # Prefer an EXE with the same name as the current executable
                    preferred = self.executable_name.lower()
                    fallback = None
                    for rootdir, _, files in os.walk(extract_dir):
                        for f in files:
                            if f.lower() == preferred:
                                new_exe_path = str(Path(rootdir) / f)
                                break
                            if f.lower().endswith(".exe") and fallback is None:
                                fallback = str(Path(rootdir) / f)
                        if new_exe_path:
                            break
                    if not new_exe_path:
                        new_exe_path = fallback
                except Exception as e:
                    print(f"Failed to extract update zip: {e}")
                    return False
            else:
                new_exe_path = temp_path

            if not new_exe_path or not os.path.exists(new_exe_path):
                print("Updated executable not found after download/extract.")
                return False
            
            # Persist the latest installed version next to the EXE so future runs don't loop updates
            try:
                ver_path_json = self.base_dir / "installed_version.json"
                with open(ver_path_json, "w", encoding="utf-8") as vf:
                    json.dump({"version": latest_version}, vf)
                # Also write a simple txt for easy inspection
                (self.base_dir / "installed_version.txt").write_text(latest_version, encoding="utf-8")
            except Exception as e:
                print(f"Warning: failed to write installed version file: {e}")
            
            if self.is_windows:
                print("Applying Windows update and restarting...")
                return self._apply_update_windows(new_exe_path)
            else:
                print("Auto-update installer only implemented for Windows in this build.")
                return False

        except Exception as e:
            print(f"Error during release update: {e}")
            return False
    
    def check_and_update_async(self, callback=None):
        """Check for updates asynchronously and update if available.
        Uses git pull when in a git repo; otherwise uses GitHub Releases to update the EXE."""
        def update_thread():
            try:
                if self._is_git_repo():
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
                else:
                    # Not a git checkout: use release-based updater suitable for packaged EXE
                    success = self.check_and_update_from_release(show_gui=True)
                    if callback:
                        callback(success)
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
            if self._is_git_repo():
                if self.check_for_updates():
                    print("Updates available. Updating silently...")
                    return self.update_from_github(show_gui=False)
                else:
                    print("No updates available.")
                    return False
            else:
                return self.check_and_update_from_release(show_gui=False)
        except Exception as e:
            print(f"Error in silent update: {e}")
            return False

def check_for_updates_on_startup():
    """Convenience function to check for updates on application startup.
    For packaged EXE runs (frozen), perform a silent release-based update so customers always get the latest."""
    updater = AutoUpdater()
    if not getattr(updater, "auto_update_enabled", True):
        print("Auto-update disabled by configuration.")
        return
    if not getattr(updater, "check_on_startup", True):
        print("Auto-update on startup disabled by configuration.")
        return
    
    # Check for updates in background with a configurable delay to not block startup
    def delayed_check():
        delay = getattr(updater, "update_check_delay_seconds", 2)
        try:
            delay = int(delay)
        except Exception:
            delay = 2
        time.sleep(max(0, delay))
        if getattr(updater, "is_frozen", False):
            # Packaged EXE: update silently from releases and restart automatically
            updater.check_and_update_silent()
        else:
            # Dev/git environment: allow prompts and git-based updates
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
