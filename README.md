# Gadget - Infineon HOST PD Logger

## Youtube

[![WCS Logger - The assistant in Infineon WCS USBC host applications](/docs/host_logger_yt.png)](https://www.youtube.com/watch?v=Zy7FzoSF6Ks)

## Screenshot

## Code members

- [main.py](main.py): Application entry point. Initializes logging, validates prerequisites, and starts the Qt app.
- [backend.py](backend.py): Main window controller. Handles UI state, device selection, validation, and capture flow orchestration.
- [run.py](run.py): Start/stop dispatcher for recorder backends (Saleae + CY4500 or Ellisys).
- [dev_saleae.py](dev_saleae.py): Saleae Logic automation setup and capture control.
- [dev_cysniffer.py](dev_cysniffer.py): CY4500 EZ-PD Protocol Analyzer start/stop automation.
- [dev_ellisys.py](dev_ellisys.py): Ellisys C-Tracker setup and remote recording control.
- [save.py](save.py): Save/export pipeline, analyzer post-processing, and tracker workbook updates.
- [log_utils.py](log_utils.py): Central logging utilities, session log file handling, and checkpoint formatting.
- [prerequisites.py](prerequisites.py): Startup prerequisite checks and dependency gating before UI launch.
- [installation_checks.py](installation_checks.py): Recorder/application installation validation and user-facing status messaging.
- [usb_detection.py](usb_detection.py): USB enumeration helpers, VID/PID matching, and fast/slow detection fallbacks.
- [detect_devices.py](detect_devices.py): Standalone CLI utility to diagnose recorder USB detection outside the UI.
- [diagnose_ice.py](diagnose_ice.py): Environment diagnostic utility for zeroc-ice/Ice import and Python-version compatibility issues.
- [fix_ice_windows.bat](fix_ice_windows.bat): One-click Windows batch helper to diagnose and install zeroc-ice.
- [fix_ice_powershell.ps1](fix_ice_powershell.ps1): PowerShell troubleshooting helper for Ice installation and compatibility guidance.
- [run_device_detection.bat](run_device_detection.bat): User-friendly launcher for standalone USB device detection.
- [ui.py](ui.py): Auto-generated Qt UI bindings from ui.ui.
- [logo.py](logo.py): Auto-generated splash screen UI bindings from logo.ui.
- [ui_rc.py](ui_rc.py): Auto-generated Qt resource bindings from ui.qrc.

## Pre-requisite

- A CY4500 / CY4500 EPR sniffer
- A 16ch Saleae Pro unit
- An Ellisys C-Tracker
- Install Python: https://www.python.org/
  - Recommended: Python 3.11.5 (development PC baseline)
  - Supported for Ellisys/zeroc-ice: 3.11.5 and 3.12
  - Not recommended currently: Python 3.14+ (zeroc-ice wheels may be unavailable and can cause `DLL load failed while importing IcePy`)
- Install CY4500 EZ-PD Protocol Analyzer Utility: https://www.infineon.com
- Install SALEAE Logic2 (2.4.0+): https://www.saleae.com/downloads/
  - Install SALEAE Python Automation package
  - (Recommended) Install CC analyzer plugin “Manchester_PD_CC” (binary/manchester_analyzer_dist.dll) (supports Saleae Pro only)
  - (Optional) Install HPI I2C analyzer plugin “I2CHPI” (binary/i2c_analyzer_for_HPI.dll)
- Install Ellisys Type-C Tracker Analyzer: https://www.ellisys.com
- Install Ellisys Type-C Tracker Analyzer Remote Control Plugin
  - (Optional) Install QT Designer: https://build-system.fman.io/qt-designer-download

## How to use

- Connect CY4500 sniffer and Saleae 16 Pro and Ellisys C-Tracker (optional) to PC
- Fill in all fields and platform type in Issue Information.
- Map pins with the pre-defined channel numbers, or change them to your preferred mapping.
- Enabling "Analogue Mode" adds analogue traces on CC/SBU/VBUS pins and can produce very large log files. Use it only when necessary.
- Execute Python command (Python 3.11.5 recommended):
  ```
  py main.py
  ```
- This app will
  - Check and confirm log applications (EZ-PD Protocol Analyzer Utility, Saleae Logic2, Ellisys Type-C Tracker Analyzer) installation status
  - Generate logs based on device selection (Saleae + CY4500 or Ellisys C-Tracker)
  - Scenario A: Log applications are not running (***recommended***)
    1. Launch log applications with automation support enabled.
    2. Hit "Start Recording" and start log capturing per setup.
    3. Assign analyzers to captured logs (Saleae Mode) after clicking "Pass Case" or "Fail Case".
    4. Create a folder using current time and save log filename with Issue Information data.
    5. Ready for another capture cycle.
    6. The app will shut down log applications when you quit the Python app.
  - Scenario B: Log applications are running
    1. Hit "Start Recording" and start log capturing per setup.
    2. Assign analyzers to captured logs (Saleae Mode) after clicking "Pass Case" or "Fail Case".
    3. Create a folder using current time and save log filename with Issue Information data.
    4. Ready for another capture cycle.
    5. The app will NOT shut down log applications on exit.

## Standalone Device Detection (Troubleshooting)

- Use this when USB device detection fails on another PC/VM and you want to test detection without launching the full UI app.
- Run:
  ```
  py detect_devices.py --verbose --list
  ```
- Optional checks:
  ```
  py detect_devices.py
  py detect_devices.py --fast-device-check
  py detect_devices.py --require saleae
  py detect_devices.py --require ellisys
  py detect_devices.py --all-methods --verbose --list
  py detect_devices.py --all-methods --verbose --list --vid-summary
  ```
- Default mode uses fast methods first and runs slower checks only if no target device is found.
- `--fast-device-check` skips the slower fallback methods.
- `--all-methods` forces all methods regardless of fast-scan result.
- `--require` returns exit code `1` if the required device is not detected, useful for quick pass/fail checks.
- If output shows `VID matched, different PID(s)`, your hardware/firmware revision uses a different PID than the current hardcoded one.

## Ellisys + zeroc-ice Python Compatibility

- If you see this error while starting Ellisys mode:
  - `RuntimeError: Ellisys automation requires zeroc-ice ... DLL load failed while importing IcePy`
- Most common cause is Python 3.14+ compatibility with `zeroc-ice` binary wheels.
- Recommended fix: run this app with Python 3.11.5 (development baseline), or Python 3.12.

### Quick Fix Commands (Windows)

```
py -3.11 -m pip install --upgrade --only-binary :all: zeroc-ice
py -3.11 main.py
```

Alternative with Python 3.12:

```
py -3.12 -m pip install --upgrade --only-binary :all: zeroc-ice
py -3.12 main.py
```

If needed, run diagnostics:

```
py -3.11 diagnose_ice.py
```

## Faster App Startup (Optional)

- To skip slower fallback USB methods at startup, run:
  ```
  py main.py --fast-device-check
  ```
- This uses only fast USB checks (`WMIC` / `PNPUTIL`) and can reduce startup time when slow PowerShell/CIM paths are not needed.

### For Non-Python Users

- Double-click `run_device_detection.bat`.
- It auto-generates a log under `logs/device_detection_YYYYMMDD_HHMMSS.log`.
- If Python is not installed, the launcher will use `binary/detect_devices.exe` when available.

### Build Standalone EXE (for sharing)

- On a build machine with Python + PyInstaller:
  ```
  build_detect_devices_standalone.bat
  ```
- This creates `binary/detect_devices.exe`.
- Share these two files to non-Python users:
  - `run_device_detection.bat`
  - `binary/detect_devices.exe`

## Limitation

- The app might halt if you close SALEAE Logic2 during log collection.
- The app will crash if Saleae Logic application does not enable "Automation Server" in Scenario B.
- Doesn't support Saleae 8ch.

---

# Build UI

## QT Designer

- add/modify QT objects in QT Designer and save to .ui file
- translate to Python script:
  ```
  pyrcc5 ui.qrc -o ui_rc.py
  pyuic5 ui.ui -o ui.py
  pyuic5 logo.ui -o logo.py
  ```

---

# Build Standalone Application

```
pyinstaller -F --noconsole main.py -i docs/IFX_Logo.ico --name iftw_logger.exe
```
