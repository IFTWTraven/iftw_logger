import os
import os.path
#import sys
import time
#import psutil
#import subprocess
#import openpyxl

import winreg
import re
from pywinauto import Desktop, Application
from pywinauto.keyboard import send_keys
from save import SaveToFile
import psutil
import subprocess
from log_utils import log_checkpoint, log_exception
try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

def activate_main_window(window):
    for _ in range(3):
        try:
            window.restore()
        except:
            pass

        try:
            window.wait('visible', timeout=1)
            window.wait('ready', timeout=1)
        except:
            pass

        try:
            window.set_focus()
            return True
        except:
            pass

        try:
            window.click_input()
            return True
        except:
            pass

        time.sleep(0.2)

    return False


def trigger_start_from_ui(main_window):
    # Try common labeled controls. Prefer invoke() so overlap/z-order does not block action.
    label_patterns = [
        r"start",
        r"record",
        r"run",
        r"resume",
        r"begin",
        r"capture",
    ]

    # Search buttons by label and click fastest candidate.
    for ctrl in main_window.descendants(control_type="Button"):
        try:
            if not ctrl.is_visible() or not ctrl.is_enabled():
                continue
        except:
            continue

        text = ""
        try:
            text = ctrl.window_text() or ""
        except:
            pass

        if any(re.search(p, text, re.IGNORECASE) for p in label_patterns):
            try:
                ctrl.invoke()
                return True
            except:
                pass
            try:
                ctrl.click_input()
                return True
            except:
                pass

    return False


def _has_button_with_label(main_window, label_patterns):
    for ctrl in main_window.descendants(control_type="Button"):
        try:
            if not ctrl.is_visible():
                continue
        except:
            continue

        text = ""
        try:
            text = ctrl.window_text() or ""
        except:
            pass

        if any(re.search(p, text, re.IGNORECASE) for p in label_patterns):
            return True

    return False


def _wait_for_cy4500_recording(main_window, timeout_seconds=2.0):
    # Validate recording by polling for a stop-like button that appears in capture state.
    stop_patterns = [r"stop", r"pause", r"end"]
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if _has_button_with_label(main_window, stop_patterns):
            return True
        time.sleep(0.1)
    return False


def _start_cy4500_with_retry(main_window, max_retries=3):
    for attempt in range(1, max_retries + 1):
        activate_main_window(main_window)

        used_method = "ui_button"
        action_sent = trigger_start_from_ui(main_window)
        if not action_sent:
            used_method = "ctrl_r"
            action_sent = send_ctrl_r(main_window)

        started = False
        if action_sent:
            started = _wait_for_cy4500_recording(main_window, timeout_seconds=1.5)

        log_checkpoint(
            "CY4500",
            "CAPTURE_START",
            "CY4500 start attempt",
            attempt=attempt,
            method=used_method,
            action_sent=action_sent,
            started=started,
        )

        if started:
            return True

        time.sleep(0.3)

    return False

# Function to send CTRL+R (Start) keyboard shortcut (deprecated - use mouse click instead)
def send_ctrl_r(window):
    # Kept for backwards compatibility; prefer trigger_start_from_ui for faster mouse click.
    try:
        activate_main_window(window)
        window.type_keys('^r', set_foreground=True)
        return True
    except:
        pass
    return False

# Function to send CTRL+Q (Stop) keyboard shortcut
def send_ctrl_q(window):
    activate_main_window(window)
    window.type_keys('^q', set_foreground=True)

# Function to send CTRL+S (Save) keyboard shortcut
def send_ctrl_s(window):
    window.type_keys('^s')

def restore_minimized_window(process_id):
    desktop = Desktop(backend="uia")
    
    for window in desktop.windows():
        if window.process_id() == process_id:
            if window.is_minimized():
                window.set_focus()  # This action can also restore a minimized window
#                print(f"Restored window for app with process ID {process_id}.")
                return True
            else:
#                print(f"Window for app with process ID {process_id} is not minimized.")
                return False
    
#    print(f"No window found for app with process ID {process_id}.")
    return False

def find_running_app(app_name):
    # Check if the application is already running
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == app_name:
            restore_minimized_window(proc.info['pid'])
            return proc

# Function to launch the application
def search_and_run_cysniffer():
#    app_name = "EZ-PD Protocol Analyzer Utility"  # Replace this with the name of the app you're searching for
    app_name2 = "EZ_PD_Protocol_Analyzer_Utility.exe"  # Replace this with the name of the app you're searching for
#    app_title = "CY4500 EZ-PD™ Protocol Analyzer Utility"
    app_title = "EZ-PD™ Protocol Analyzer Utility"
    # Check if the application is already running
    running_app = find_running_app(app_name2)
    if running_app:
        log_checkpoint("CY4500", "APP", "CY4500 app already running", pid=running_app.info['pid'])
#        print(f"{app_name} is already running (PID: {running_app.info['pid']}).")
        # You can return the information about the running app if needed
        app = Application(backend="uia").connect(process=running_app.info['pid'])
#        main_window = app.window(title=app_title)
        
        main_window = app.window(title_re=app_title)
        main_window.set_focus()
        try:
            main_window.restore()
        except:
            pass
        return app

    # get current user's home directory and check if default installation is existed
    cy4500_path = r"C:\Infineon\Tools"  
    cy4500_bin = os.path.join(cy4500_path, 'EZ-PD Protocol Analyzer Utility', app_name2)

    if os.path.exists(cy4500_bin):
        log_checkpoint("CY4500", "APP", "Launching CY4500 app", path=cy4500_bin)
        app = Application(backend="uia").start(cy4500_bin)
        main_window = app.window(title_re=app_title)
        main_window.set_focus()
        try:
            main_window.restore()
        except:
            pass
        return app    
    """
    else:
        installation_path = find_app_installation_path_suppress(app_name)
        if installation_path != None:
            app_path = installation_path + app_name2  # Replace with the actual path of your 3rd party application
            app = Application(backend="uia").start(app_path)
            main_window = app.window(title_re_=app_title)
            main_window.set_focus()

            try:
                main_window.restore()
            except:
                pass
            return app
        else:
            return None       
    """

# def find_app_installation_path_suppress(app_name):
#     try:
#         with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall") as key:
#             for i in range(winreg.QueryInfoKey(key)[0]):
#                 subkey_name = winreg.EnumKey(key, i)
#                 with winreg.OpenKey(key, subkey_name) as subkey:
#                     try:
#                         display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
#                         # Remove numeric characters from the display name for comparison
#                         cleaned_display_name = re.sub(r'\d+', '', display_name)
#                         if app_name.lower() in cleaned_display_name.lower():
#                             install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
#                             return install_location
#                     except FileNotFoundError:
#                         pass
#     except OSError:
#         pass

#     return None

def CySniffer_StartCapture():
    log_checkpoint("CY4500", "CAPTURE_START", "Starting CY4500 capture request")
    app = search_and_run_cysniffer()

    if app != None:
        # Get the main window
#        main_window = app.window(title="CY4500 EZ-PD™ Protocol Analyzer Utility")
        main_window = app.window(title_re="EZ-PD™ Protocol Analyzer Utility")

        started = _start_cy4500_with_retry(main_window, max_retries=3)
        if started:
            log_checkpoint("CY4500", "CAPTURE_START", "CY4500 capture started")
            return

        log_checkpoint(
            "CY4500",
            "CAPTURE_START",
            "CY4500 start could not be verified; possible window overlap or focus issue",
        )
        raise RuntimeError("CY4500 start could not be verified. Ensure CY4500 app is visible and not overlapped.")
    else:
        log_checkpoint("CY4500", "CAPTURE_START", "CY4500 app not found; start skipped")

def _is_save_dialog_open(main_window):
    """Check if a save dialog is currently open by detecting window changes."""
    try:
        dialogs = main_window.descendants(control_type="Window")
        for dialog in dialogs:
            try:
                # Check window title (case-insensitive with .lower())
                title = (dialog.window_text() or "").lower()
                title_keywords = ["save", "another", "export", "另存", "保存", "储存"]
                
                if any(keyword in title for keyword in title_keywords):
                    if dialog.is_visible():
                        # Additional validation: check if there's an Edit field (likely the filename field)
                        try:
                            edits = dialog.descendants(control_type="Edit")
                            if edits:
                                print(f"[Save] Dialog detected: title='{dialog.window_text()}', found {len(edits)} edit fields")
                                return True
                        except:
                            # If we can't verify, trust the title match
                            print(f"[Save] Dialog detected by title: '{dialog.window_text()}'")
                            return True
            except:
                pass
    except Exception as e:
        print(f"[Save] Exception while checking dialogs: {e}")
    return False

def _wait_for_dialog(main_window, should_appear=True, timeout_seconds=5):
    """Wait for save/confirmation dialog to appear or disappear with polling."""
    end_time = time.time() + timeout_seconds
    poll_interval = 0.05  # Check every 50ms for responsiveness
    attempt = 0
    
    while time.time() < end_time:
        attempt += 1
        is_open = _is_save_dialog_open(main_window)
        
        if should_appear and is_open:
            print(f"[Save] Dialog appeared (attempt {attempt})")
            return True
        elif not should_appear and not is_open:
            print(f"[Save] Dialog closed (attempt {attempt})")
            return True
        
        time.sleep(poll_interval)
    
    if should_appear:
        print(f"[Save] Timeout after {timeout_seconds}s and {attempt} attempts: Save dialog did not appear")
    else:
        print(f"[Save] Timeout after {timeout_seconds}s and {attempt} attempts: Dialog did not close")
    return False

def _copy_to_clipboard(filepath):
    try:
        if HAS_PYPERCLIP:
            pyperclip.copy(filepath)
            print("[Save] Used pyperclip to copy path")
        else:
            process = subprocess.Popen(['clip'], stdin=subprocess.PIPE)
            process.communicate(filepath.encode('utf-8'))
            print("[Save] Used clip.exe to copy path")
        return True
    except Exception as e:
        print(f"[Save] Failed to copy to clipboard: {e}")
        return False

def CySniffer_StopCapture(self):
    log_checkpoint("CY4500", "CAPTURE_STOP", "Stopping CY4500 capture request", save=self.savetofile)
    app = search_and_run_cysniffer()

    if app != None:
        # Get the main window
#        main_window = app.window(title="CY4500 EZ-PD™ Protocol Analyzer Utility")
        main_window = app.window(title_re="EZ-PD™ Protocol Analyzer Utility")

        #Send CTRL+Q
        send_ctrl_q(main_window)
        log_checkpoint("CY4500", "CAPTURE_STOP", "Sent Ctrl+Q to CY4500")
        
        if self.savetofile:
            # Bring the window into focus (optional, only if it's not already focused)
#            main_window.set_focus()
            capture_filepath = SaveToFile(self, main_window)

            print(f"[Save] Starting save sequence for: {capture_filepath}")
            log_checkpoint("CY4500", "SAVE", "Starting CY4500 save sequence", filepath=capture_filepath)
            
            # Send CTRL+S to open the save dialog
            main_window.set_focus()
            main_window.type_keys('^s')
            print("[Save] Sent Ctrl+S")
            
            # Wait for save dialog to appear with polling (handles slow/fast PCs)
            dialog_appeared = _wait_for_dialog(main_window, should_appear=True, timeout_seconds=10)
            
            if not dialog_appeared:
                print("[Save] Warning: Save dialog did not appear, attempting direct keyboard input anyway")
                log_checkpoint("CY4500", "SAVE", "Save dialog did not appear within timeout")
                # Fallback: assume dialog already appeared even if we couldn't detect it
                # This can happen if dialog detection fails but dialog is actually there
            
            # The save dialog focuses on the filename field by default
            # Simply type the filename and hit ENTER
            try:
                print(f"[Save] Sending filename via clipboard: {capture_filepath}")
                # Use clipboard to paste filepath instead of typing (handles backslashes & special chars)
                if not _copy_to_clipboard(capture_filepath):
                    raise RuntimeError("Failed to copy filepath to clipboard")
                # Important: once Save dialog is modal, parent main_window can be disabled.
                # Use global send_keys so input goes to focused filename field in the dialog.
                send_keys('^a')  # Select all in filename field
                time.sleep(0.05)
                send_keys('^v')  # Paste from clipboard
                time.sleep(0.1)
                print("[Save] Sent first ENTER")
                send_keys("{ENTER}")
                
                # Wait a bit for confirmation dialog to potentially appear
                time.sleep(0.2)
                
                # Hit ENTER again to confirm the confirmation dialog
                print("[Save] Sent second ENTER")
                send_keys("{ENTER}")
                
                # Wait for dialogs to close
                time.sleep(0.2)
                dialog_closed = _wait_for_dialog(main_window, should_appear=False, timeout_seconds=5)
                
                if dialog_closed:
                    print("[Save] File saved successfully")
                    log_checkpoint("CY4500", "SAVE", "CY4500 save sequence completed", filepath=capture_filepath)
                else:
                    print("[Save] Warning: Dialog may not have closed, but save sequence completed")
                    log_checkpoint("CY4500", "SAVE", "CY4500 save sequence ended with dialog-close warning", filepath=capture_filepath)
                    
            except Exception as e:
                print(f"[Save] Error during save: {e}")
                import traceback
                traceback.print_exc()
                log_exception("CY4500", "SAVE", e)
                raise RuntimeError(f"Failed to save file: {e}")
    else:
        log_checkpoint("CY4500", "CAPTURE_STOP", "CY4500 app not found; stop skipped")
