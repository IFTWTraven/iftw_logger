#from saleae import automation
from datetime import datetime

#from dev_saleae import Saleae_Setup, Saleae_StartCapture, Saleae_StopCapture
#from dev_ellisys import Ellisys_Setup, Ellisys_StartCapture, Ellisys_StopCapture

import os
import os.path
import sys
import time
import psutil
import re
import warnings

# pywinauto expects STA on the main thread for UI automation.
sys.coinit_flags = 2
warnings.filterwarnings(
    "ignore",
    message=r"Apply externally defined coinit_flags: 2",
    category=UserWarning,
)

from pywinauto import findwindows, Application
#import subprocess
import openpyxl
from pywinauto.keyboard import send_keys
from log_utils import get_log_file_path, log_checkpoint, log_exception

# Define the Vendor ID (VID) of the USB device you want to check
SALEAE_VID = "21A9"
SALEAE_PID = "1006"
ELLISYS_VID = "1500"
ELLISYS_PID = "0600"
CY4500_VID = "04B4"
CY4500_PID = "F67E"
CY4500EPR_PID = "FDEF"
String_Ellisys = 'Ellisys C-Tracker'
String_SALEAE = 'Saleae Logic'

import sys

try:
    import Ice
    Ice.loadSlice("--all -I. AnalyzerRemoteControl.ice")
    import Ellisys.Platform.NetworkRemoteControl.Analyzer as EllisysAnalyzer
    ICE_AVAILABLE = True
    ICE_IMPORT_ERROR = ""
except Exception as exc:
    Ice = None
    EllisysAnalyzer = None
    ICE_AVAILABLE = False
    ICE_IMPORT_ERROR = str(exc)


def _require_ice():
    if not ICE_AVAILABLE:
        python_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
        
        # Special handling for Python 3.14+
        if sys.version_info >= (3, 14):
            error_msg = (
                f"❌ PYTHON {python_ver} NOT SUPPORTED for Ellisys mode\n\n"
                f"zeroc-ice does not have pre-built wheels for Python {python_ver} yet.\n\n"
                f"SOLUTION: Switch to Python 3.11.5 (development baseline)\n"
                f"  • Run: py -3.11 -m pip install --only-binary :all: zeroc-ice\n"
                f"  • Then: py -3.11 saleae2automation/main.py\n"
                f"  • Alternative: py -3.12\n\n"
                f"ALTERNATIVE: Use conda (may have broader compatibility)\n"
                f"  • conda install -c conda-forge zeroc-ice\n\n"
                f"Technical detail: {ICE_IMPORT_ERROR}"
            )
        else:
            error_msg = (
                f"Ellisys save/export requires zeroc-ice.\n"
                f"Install zeroc-ice or use Python 3.11.5 (recommended) or 3.12.\n"
                f"Python version: {python_ver}\n"
                f"Import error: {ICE_IMPORT_ERROR}"
            )
        
        raise RuntimeError(error_msg)

def list_process_ids_by_name_pattern(name_pattern):
    process_ids = []
    
    for process in psutil.process_iter(attrs=['pid', 'name']):
        try:
            process_name = process.info['name']
            if re.match(name_pattern, process_name):
                process_ids.append(process.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    for pid in process_ids:
        app = Application(backend="uia").connect(process=pid)      
        try:
            app_data = findwindows.find_element(process=pid)
            if app_data:
                main_window = app.window()
                try:
#                    print("Window Title:", main_window.window_text(), pid)
                    return app
                except:
#                    print("Nope")
                    pass
        except:
            pass
#            print("no")
    return 0

def AssignSaleaeChannelName(self):
    app_name_pattern = r"Logic( 2 \[.*\])?"  # Regular expression pattern to match "Logic" and "Logic 2 [...]"
    app = list_process_ids_by_name_pattern(app_name_pattern)      
    
    if app:
        main_window = app.window()
#        print("Window Title:", main_window.window_text())
        # Get the main window
        main_window = app.window(title=main_window.window_text())
        
#        for i in range(8):
#            main_window.type_keys('^-')
#            time.sleep(0.1)

        actions_intel = [
            {"ext_var": self.icc1, "label": "CC1"},
            {"ext_var": self.icc2, "label": "CC2"},
            {"ext_var": self.isbu1, "label": "SBU1"},
            {"ext_var": self.isbu2, "label": "SBU2"},
            {"ext_var": self.ivbus, "label": "VBUS"},
            {"ext_var": self.ecint, "label": "EC_INT"},
            {"ext_var": self.ecsda, "label": "EC_SDA"},
            {"ext_var": self.ecclk, "label": "EC_CLK"},
            {"ext_var": self.pduart, "label": "PD_UART"},
            {"ext_var": self.rint, "label": "RIDGE_INT"},
            {"ext_var": self.rsda, "label": "RIDGE_SDA"},
            {"ext_var": self.rclk, "label": "RIDGE_CLK"},
            {"ext_var": self.bpwr, "label": "BBR_PWR"},
            {"ext_var": self.brst, "label": "BBR_RST"},
            {"ext_var": self.bsda, "label": "BBR_SDA"},
            {"ext_var": self.bclk, "label": "BBR_CLK"}
        ]

        actions_amd = [
            {"ext_var": self.icc1, "label": "CC1"},
            {"ext_var": self.icc2, "label": "CC2"},
            {"ext_var": self.isbu1, "label": "SBU1"},
            {"ext_var": self.isbu2, "label": "SBU2"},
            {"ext_var": self.ivbus, "label": "VBUS"},
            {"ext_var": self.ecint, "label": "EC_INT"},
            {"ext_var": self.ecsda, "label": "EC_SDA"},
            {"ext_var": self.ecclk, "label": "EC_CLK"},
            {"ext_var": self.pduart, "label": "PD_UART"},
            {"ext_var": self.aint, "label": "APU_INT"},
            {"ext_var": self.arst, "label": "APU_RST"},
            {"ext_var": self.asda, "label": "APU_SDA"},
            {"ext_var": self.aclk, "label": "APU_CLK"},
            {"ext_var": self.mpwr, "label": "MUX_PWR/HPD"},
            {"ext_var": self.msda, "label": "MUX_SDA"},
            {"ext_var": self.mclk, "label": "MUX_CLK"}
        ]

        if self.platform == 'INTEL':               # INTEL 
            comparison_actions = actions_intel
        elif self.platform == 'AMD':                # AMD
            comparison_actions = actions_amd

        # Pre-compile regex patterns once so matching is pure Python (no UI calls).
        # Match channel number not followed by another digit (e.g., D1(?!\d) prevents D1 matching D10).
        for action in comparison_actions:
            action['_re'] = re.compile(f'D{action["ext_var"]}(?!\\d)')

        def _scan_and_tab(remaining):
            """Scan, update matches, then TAB to next page."""
            try:
                buttons = main_window.descendants(control_type="Button")
            except:
                return remaining
            
            still = []
            updated_any = False
            
            for action in remaining:
                matched = next((b for b in buttons
                                if b.is_visible() and action['_re'].search(b.window_text())), None)
                if matched:
                    try:
                        edits = [c for c in matched.children()
                                 if c.friendly_class_name() == "Edit"]
                        target = edits[1] if len(edits) >= 2 else (edits[0] if edits else None)
                        if target:
                            target.set_text(action["label"])
                            updated_any = True
                        else:
                            # Fallback: click the button, select all, and use send_keys for reliable text input.
                            matched.click()
                            time.sleep(0.1)
                            send_keys('^a')  # Select all
                            time.sleep(0.05)
                            send_keys(action["label"])
                            time.sleep(0.05)
                            updated_any = True
                    except:
                        still.append(action)
                else:
                    still.append(action)
            
            # Only TAB if there are still items to find, or if we updated something.
            if updated_any or still:
                main_window.type_keys('{TAB}', pause=0.01)
                time.sleep(0.02)
            
            return still

        def _scan_once(remaining):
            """Scan without tabbing; for first pass only."""
            try:
                buttons = main_window.descendants(control_type="Button")
            except:
                return remaining
            
            still = []
            for action in remaining:
                matched = next((b for b in buttons
                                if b.is_visible() and action['_re'].search(b.window_text())), None)
                if matched:
                    try:
                        edits = [c for c in matched.children()
                                 if c.friendly_class_name() == "Edit"]
                        target = edits[1] if len(edits) >= 2 else (edits[0] if edits else None)
                        if target:
                            target.set_text(action["label"])
                        else:
                            # Fallback: click the button, select all, and use send_keys for reliable text input.
                            matched.click()
                            time.sleep(0.1)
                            send_keys('^a')  # Select all
                            time.sleep(0.05)
                            send_keys(action["label"])
                            time.sleep(0.05)
                    except:
                        still.append(action)
                else:
                    still.append(action)
            return still

        # First pass: only scan current visible page, no TAB yet.
        remaining = _scan_once(list(comparison_actions))

        # Loop: TAB to next page before each scan.
        for _ in range(40):
            if not remaining:
                break
            remaining = _scan_and_tab(remaining)
        
def SaveToFile(self, main_window):
    log_checkpoint("SAVE", "BEGIN", "SaveToFile invoked", recorder=self.recorddevice, has_main_window=main_window is not None)
    currentdate = datetime.now().strftime("%Y%m%d")  # Format the current date as desired
    precisetime = datetime.now().strftime("%Y%m%d_%H%M%S")
#    sheetname = precisetime
    
    # Store output in a timestamped directory
    output_dir = os.path.join(os.getcwd(), f'{currentdate}')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        log_checkpoint("SAVE", "DIR", "Created output directory", path=output_dir)
        
    #output_dir = os.getcwd()
    output_prefix = f'{datetime.now().strftime("%Y%m%d_%H%M%S_")+ self.logsuffix}'
    log_checkpoint("SAVE", "NAME", "Generated output prefix", prefix=output_prefix)

    # # we are in a new case log collecting process. the self.sheetname will be cleared if any change at information
    # if self.sheetname == '':
        # output_prefix = precisetime + '_' + self.logsuffix
    # else:
        # output_prefix = self.sheetname + '_' + self.logsuffix
        
    if self.recorddevice == String_SALEAE:
        if main_window != None:
            capture_filepath = os.path.join(output_dir, output_prefix + '.ccgx3')
            log_checkpoint("SAVE", "CY4500", "Prepared CY4500 capture filepath", path=capture_filepath)
# #            main_window.set_focus()
            # main_window.type_keys('^q')
            # time.sleep(0.5)
            # main_window.type_keys('^s')
            # time.sleep(0.5)

            # child_window = main_window.child_window(title="Save", control_type="Window")
            # child_window.type_keys(capture_filepath)
# #            send_keys(capture_filepath, pause=0.01)  # Type the desired file name into the Save dialog
            # # Send Enter to save the file
# #            send_keys("{ENTER}")
            # child_window.type_keys("{ENTER}")

# # Click ENTER again as hit OK in Save confirmation dialog
# #            time.sleep(3)
# #            send_keys("{ENTER}")
            # check_for_child_window(10, main_window)
            
            Logger_CaptureSettings(self, output_prefix + '.ccgx3', False)
            
#            return capture_filepath
        else:
            capture = self.capture
            log_checkpoint("SAVE", "SALEAE", "Preparing Saleae analyzer export/save")

            # # Export analyzer data to a CSV file
            # analyzer_export_filepath = os.path.join(output_dir, output_prefix +'.csv')
            
            analyzers = []
            
            for i in range(0, len(self.enabled_ch_i2c), 2):
                settings = {
                    'SDA': self.enabled_ch_i2c[i],
                    'SCL': self.enabled_ch_i2c[i+1],
                    'Significant Byte': 'Most Significant Byte Sent First',
                    'Bytes per Frame': '4 Bytes per Frame (Default)'
                }

                try:
                    analyzer = capture.add_analyzer('I2C_HPI', settings=settings)
                except:
                    # use standard I2C analyzer if customised one is not installed
                    settings = {
                        'SDA': self.enabled_ch_i2c[i],
                        'SCL': self.enabled_ch_i2c[i+1]
                    }
                    analyzer = capture.add_analyzer('I2C', settings=settings)

                analyzers.append(analyzer)

            for i in range(len(self.enabled_ch_cc)):
                settings = {
#                    'Manchester': self.enabled_ch_cc[i]
                    'CC Channel': self.enabled_ch_cc[i]
                }

                try:
#                    analyzer = capture.add_analyzer('Manchester_PD_CC', settings=settings)
                    analyzer = capture.add_analyzer('Saleae_PDCC_Release', settings=settings)
                    analyzers.append(analyzer)
                except:
                    # do not add cc analyser if CC analyser is not installed
                    pass

            # try:
                # capture.export_data_table(filepath=analyzer_export_filepath, analyzers=analyzers)
            # except:
                # # do not export to .csv file if no analyser is attached
                # pass
                
            # Finally, save the capture to a file
            capture_filepath = os.path.join(output_dir, output_prefix + '.sal')
            log_checkpoint("SAVE", "SALEAE", "Saving Saleae capture", path=capture_filepath)
            AssignSaleaeChannelName(self)
            capture.save_capture(filepath=capture_filepath)
            log_checkpoint("SAVE", "SALEAE", "Saleae capture saved", path=capture_filepath)

            Logger_CaptureSettings(self, output_prefix + '.sal', True)

    elif self.recorddevice == String_Ellisys:
        _require_ice()
        log_checkpoint("SAVE", "ELLISYS", "Preparing Ellisys save")
    
        Ice.loadSlice("--all -I. AnalyzerRemoteControl.ice")
        # TODO: Please adapt the following constants to your needs
        hostIp = "localhost"
        hostPort = 54321

        proxyString = "{0}:tcp -h {1} -p {2}".format(EllisysAnalyzer.AnalyzerRemoteControlIdentity, hostIp, hostPort)

        initData = Ice.InitializationData()
        initData.properties = Ice.createProperties([], initData.properties)
        initData.properties.setProperty("Ice.Default.EncodingVersion", "1.0")

        communicator = Ice.initialize(initData)
        proxy = communicator.stringToProxy(proxyString)
        remoteControl = EllisysAnalyzer.AnalyzerRemoteControlPrx.checkedCast(proxy)
        
        capture_filepath = os.path.join(output_dir, output_prefix + '.ctrt')
        remoteControl.StopRecordingAndSaveTraceFile(capture_filepath, True)
        log_checkpoint("SAVE", "ELLISYS", "Ellisys trace saved", path=capture_filepath)
        Logger_CaptureSettings(self, output_prefix + '.ctrt', False)


    if self.recorddevice == String_SALEAE:
        if main_window != None:
            str_suffix = '.ccgx3\r\n'
        else:
            str_suffix = '.sal\r\n'
    elif self.recorddevice == String_Ellisys:
        str_suffix = '.ctrt\r\n'
    
#    self.allrecords += output_prefix + '.sal\r\n'
    trackerformhdr = currentdate + '_' + self.project + '.xlsx'
    tracker_filepath = os.path.join(output_dir, trackerformhdr)
    
    # a tracker form with same project name is already existed
    if os.path.exists(tracker_filepath):
        log_checkpoint("SAVE", "TRACKER", "Updating existing tracker workbook", path=tracker_filepath)
        # Load the workbook
        workbook = openpyxl.load_workbook(tracker_filepath)      

        # we are in a new case log collecting process. the self.sheetname will be cleared if any change at information
        if self.sheetname == '':
            # Select the sheet you want to duplicate
            original_sheet = workbook['Blank']
            self.allrecords = output_prefix + str_suffix
            # Create a new sheet
            new_sheet = workbook.copy_worksheet(original_sheet)
            # Rename the new sheet using the current date
            new_sheet.title = precisetime
            self.sheetname = precisetime
        # we are in the same case process
        else:
            new_sheet = workbook[self.sheetname]
            self.allrecords += output_prefix + str_suffix
            
    # tracker form doesn't exist
    else:
        self.allrecords = output_prefix + str_suffix
        log_checkpoint("SAVE", "TRACKER", "Creating new tracker workbook", path=tracker_filepath)
       # Load the workbook
        workbook = openpyxl.load_workbook('tracker_form.xlsx')
        # Select the sheet you want to duplicate
        original_sheet = workbook['Blank']
        # Create a new sheet
        new_sheet = workbook.copy_worksheet(original_sheet)
        # Rename the new sheet using the current date
        new_sheet.title = precisetime
        self.sheetname = precisetime

    if self.otherportsel:
        additionalInfo = '\r\nSame failure on other port(s)'
    else:
        additionalInfo = '\r\nNot see the same symptom on other port(s)'

    # Update cells value
    new_sheet['B1'] = self.project
    new_sheet['B2'] = self.ecver
    new_sheet['B3'] = self.pdver
    new_sheet['B4'] = self.ticket
    new_sheet['B5'] = self.port + additionalInfo
    new_sheet['B6'] = self.issue
    new_sheet['B7'] = self.failrate
    new_sheet['B8'] = self.device
    new_sheet['B9'] = self.replication
    new_sheet['B10'] = self.ui.cB_OtherDevSel.currentText() + '\r\n' + self.otherdev
    new_sheet['B11'] = self.recovery
    new_sheet['B12'] = self.ui.cB_DiffStepSel.currentText() + '\r\n' + self.diffstep
    new_sheet['B13'] = self.allrecords
    new_sheet['B14'] = 'as above'
    new_sheet['B15'] = 'n/a'
        
    workbook.active = workbook.index(workbook[self.sheetname])
    # Save the changes
    workbook.save(tracker_filepath)
    log_checkpoint("SAVE", "TRACKER", "Tracker workbook saved", path=tracker_filepath, sheet=self.sheetname)

    if main_window != None:             # CY4500 case
        log_checkpoint("SAVE", "END", "SaveToFile completed", path=capture_filepath)
        return capture_filepath

    log_checkpoint("SAVE", "END", "SaveToFile completed")

def Logger_CaptureSettings(self, log_name, ch_details):
    logfile = get_log_file_path()
    if not logfile:
        output_dir = os.path.join(os.getcwd(), f'{datetime.now().strftime("%Y%m%d")}')
        os.makedirs(output_dir, exist_ok=True)
        logfile = os.path.join(output_dir, f'{datetime.now().strftime("%Y%m%d")}.txt')

    lines = []
    lines.append("")
    lines.append("CHANNEL SETUP DETAIL")
    lines.append("-" * 88)

    if self.recorddevice == String_SALEAE and ch_details:
        lines.append("Signal mapping:")
        if self.platform == 'INTEL':               # INTEL
            lines.append(f"  CC1={self.icc1}, CC2={self.icc2}, SBU1={self.isbu1}, SBU2={self.isbu2}, VBUS={self.ivbus}")
            lines.append(f"  EC: INT={self.ecint}, SDA={self.ecsda}, CLK={self.ecclk}, UART={self.pduart}")
            lines.append(f"  RIDGE: INT={self.rint}, SDA={self.rsda}, CLK={self.rclk}")
            lines.append(f"  BBR: PWR={self.bpwr}, RST={self.brst}, SDA={self.bsda}, CLK={self.bclk}")
        elif self.platform == 'AMD':                # AMD
            lines.append(f"  CC1={self.icc1}, CC2={self.icc2}, SBU1={self.isbu1}, SBU2={self.isbu2}, VBUS={self.ivbus}")
            lines.append(f"  EC: INT={self.ecint}, SDA={self.ecsda}, CLK={self.ecclk}, UART={self.pduart}")
            lines.append(f"  APU: INT={self.aint}, RST={self.arst}, SDA={self.asda}, CLK={self.aclk}")
            lines.append(f"  MUX: PWR={self.mpwr}, SDA={self.msda}, CLK={self.mclk}")
    elif self.recorddevice == String_Ellisys:
        lines.append("Signal mapping:")
        lines.append(
            f"  EC: INT={self.ecint_ellisys}, SDA={self.ecsda_ellisys}, CLK={self.ecclk_ellisys}, UART={self.pduart_ellisys}"
        )
        lines.append(
            f"  PCH: INT={self.ecint2_ellisys}, SDA={self.ecsda2_ellisys}, CLK={self.ecclk2_ellisys}"
        )
    else:
        lines.append("Signal mapping: not available for this capture mode")

    lines.append(f"[CHANNEL] Recorder: {self.recorddevice} | Platform: {self.platform}")
    lines.append(f"[CHANNEL] Capture file: {log_name}")
    lines.append("-" * 88)

    with open(logfile, 'a', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")

    log_checkpoint("SAVE", "LOG", "Capture settings logged", logfile=logfile, entry=log_name)
    