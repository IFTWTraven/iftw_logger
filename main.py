import sys
import time
import argparse
from prerequisites import ensure_prerequisites
from log_utils import init_log_session, get_log_file_path, log_checkpoint


init_log_session(script_name="main.py")
log_checkpoint("MAIN", "BOOT", "Application bootstrap started", logfile=get_log_file_path())
if not ensure_prerequisites():
    log_checkpoint("MAIN", "PREREQ", "Prerequisite check failed; exiting")
    sys.exit(1)
log_checkpoint("MAIN", "PREREQ", "Prerequisite check completed")


from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox
from logo import Ui_Dlg_logo
from installation_checks import validate_installed_applications
from usb_detection import (
    build_usb_device_list_fast_only,
    build_usb_device_list_fast_then_slow,
    build_vid_to_pids_map,
    evaluate_usb_device_match,
)


def parse_cli_args(argv):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--fast-device-check",
        action="store_true",
        help="Use fast USB checks only and skip slower fallback methods.",
    )
    parser.add_argument(
        "--periodic-device-check",
        action="store_true",
        help="Enable periodic attached-device refresh in the main window.",
    )
    parser.add_argument(
        "--periodic-device-check-interval",
        type=float,
        default=3.0,
        help="Periodic device refresh interval in seconds (default: 3.0).",
    )
    args, qt_args = parser.parse_known_args(argv[1:])
    if args.periodic_device_check_interval <= 0:
        args.periodic_device_check_interval = 3.0
    log_checkpoint(
        "MAIN",
        "CLI",
        "Parsed CLI arguments",
        fast_device_check=args.fast_device_check,
        periodic_device_check=args.periodic_device_check,
        periodic_device_check_interval=args.periodic_device_check_interval,
    )
    return args, [argv[0]] + qt_args

def showLogo():
    log_checkpoint("UI", "SPLASH", "Showing splash screen")
    logo = QtWidgets.QMainWindow()
    ui = Ui_Dlg_logo()
    ui.setupUi(logo)
    logo.setWindowFlags(Qt.FramelessWindowHint)
    logo.show()

    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(1000, loop.quit)
    loop.exec_()
    logo.close()
    log_checkpoint("UI", "SPLASH", "Splash screen closed")


def runMainWindow(
    app,
    fast_device_check=False,
    periodic_device_check=False,
    periodic_device_check_interval=3.0,
):
    # Import backend only after QApplication exists to avoid COM apartment conflicts on startup.
    log_checkpoint(
        "MAIN",
        "WINDOW",
        "Creating backend main window",
        fast_device_check=fast_device_check,
        periodic_device_check=periodic_device_check,
        periodic_device_check_interval=periodic_device_check_interval,
    )
    import backend

    window = backend.MainWindow_controller(
        periodic_device_check=periodic_device_check,
        periodic_device_check_interval=periodic_device_check_interval,
    )

    target_devices = [
        (backend.SALEAE_VID, backend.SALEAE_PID, True),
        (backend.ELLISYS_VID, backend.ELLISYS_PID, True),
        (backend.CY4500_VID, backend.CY4500_PID, False),
        (backend.CY4500_VID, backend.CY4500EPR_PID, False),
    ]
    if fast_device_check:
        log_checkpoint("USB", "ENUM", "Running fast-only USB device scan")
        usb_device_list = build_usb_device_list_fast_only()
    else:
        log_checkpoint("USB", "ENUM", "Running fast-then-slow USB device scan")
        usb_device_list = build_usb_device_list_fast_then_slow(target_devices=target_devices)
    log_checkpoint("USB", "ENUM", "USB enumeration finished", entries=len(usb_device_list))
    print(f"[USB] Enumerated entries: {len(usb_device_list)}")
    if usb_device_list:
        print("[USB] Device list start")
        for index, entry in enumerate(usb_device_list, start=1):
            print(f"[USB] {index:03d}: {entry}")
        print("[USB] Device list end")
    else:
        print("[USB] No USB entries found.")

    vid_to_pids = build_vid_to_pids_map(usb_device_list)

    saleae_present, saleae_reason, saleae_matched_pids = evaluate_usb_device_match(
        usb_device_list,
        backend.SALEAE_VID,
        backend.SALEAE_PID,
        allow_vid_only=True,
        vid_to_pids=vid_to_pids,
    )
    ellisys_present, ellisys_reason, ellisys_matched_pids = evaluate_usb_device_match(
        usb_device_list,
        backend.ELLISYS_VID,
        backend.ELLISYS_PID,
        allow_vid_only=True,
        vid_to_pids=vid_to_pids,
    )
    cy4500_present, cy4500_reason, cy4500_matched_pids = evaluate_usb_device_match(
        usb_device_list,
        backend.CY4500_VID,
        backend.CY4500_PID,
        allow_vid_only=False,
        vid_to_pids=vid_to_pids,
    )
    cy4500epr_present, cy4500epr_reason, cy4500epr_matched_pids = evaluate_usb_device_match(
        usb_device_list,
        backend.CY4500_VID,
        backend.CY4500EPR_PID,
        allow_vid_only=False,
        vid_to_pids=vid_to_pids,
    )

    def print_usb_status(name, vid, pid, present, reason, matched_pids):
        if reason == "exact":
            print(f"[USB] {name} ({vid}:{pid}) status: FOUND")
            return
        if reason == "vid_only":
            print(
                f"[USB] {name} ({vid}:{pid}) status: FOUND (VID fallback, PID(s): {', '.join(matched_pids)})"
            )
            return
        if reason == "vid_mismatch":
            print(
                f"[USB] {name} ({vid}:{pid}) status: NOT FOUND (VID matched, different PID(s): {', '.join(matched_pids)})"
            )
            return
        print(f"[USB] {name} ({vid}:{pid}) status: NOT FOUND (VID not present)")

    print_usb_status("Saleae", backend.SALEAE_VID, backend.SALEAE_PID, saleae_present, saleae_reason, saleae_matched_pids)
    print_usb_status("CY4500", backend.CY4500_VID, backend.CY4500_PID, cy4500_present, cy4500_reason, cy4500_matched_pids)
    print_usb_status(
        "CY4500 EPR",
        backend.CY4500_VID,
        backend.CY4500EPR_PID,
        cy4500epr_present,
        cy4500epr_reason,
        cy4500epr_matched_pids,
    )
    print_usb_status("Ellisys", backend.ELLISYS_VID, backend.ELLISYS_PID, ellisys_present, ellisys_reason, ellisys_matched_pids)
    
    if not saleae_present and not ellisys_present:
        log_checkpoint("USB", "GATE", "No Saleae or Ellisys device detected; blocking startup")
        message = 'Please attach Saleae Logic 16 Pro or Ellisys C-Tracker and try again.'
        QMessageBox.warning(None, "No Device", message)
        sys.exit(1)

    # Saleae is being attached, and CY4500 is also required 
#    if is_usb_device_present(SALEAE_VID, SALEAE_PID) and not is_usb_device_present(CY4500_VID, CY4500_PID):
    if saleae_present and not (cy4500_present or cy4500epr_present):
        log_checkpoint("USB", "GATE", "Saleae detected but CY4500/CY4500 EPR missing")
        message = 'Please attach CY4500/CY4500 EPR EZ-PD Protocol Analyzer and try again.'
        QMessageBox.warning(None, "No Device", message)
        sys.exit(1)

    install_ok, install_title, install_message = validate_installed_applications(
        saleae_present,
        ellisys_present,
        cy4500_present,
        cy4500epr_present,
    )
    if not install_ok:
        log_checkpoint("INSTALL", "CHECK", "Installation validation failed", title=install_title)
        QMessageBox.warning(None, install_title, install_message)
        sys.exit(1)
    log_checkpoint("INSTALL", "CHECK", "Installation validation passed")
    # All checked.
    """
    # Temporary switch to skip original UI lines (76-78) while validating USB detection.
    skip_window_display = True
    if skip_window_display:
        print("[UI] Skipping window display lines (76-78) temporarily.")
        return 0
    """
    # Set the window flags to always stay on top
    window.setWindowFlags(window.windowFlags() | Qt.WindowStaysOnTopHint)
    window.setWindowFlags(window.windowFlags() & ~Qt.WindowMaximizeButtonHint)
    window.show()
    log_checkpoint("UI", "WINDOW", "Main window shown; entering app event loop")

    return app.exec_()
    
if __name__ == '__main__':
    cli_args, qt_argv = parse_cli_args(sys.argv)
    app = QApplication(qt_argv)
    log_checkpoint("MAIN", "QT", "QApplication initialized")
    showLogo()
    sys.exit(
        runMainWindow(
            app,
            fast_device_check=cli_args.fast_device_check,
            periodic_device_check=cli_args.periodic_device_check,
            periodic_device_check_interval=cli_args.periodic_device_check_interval,
        )
    )