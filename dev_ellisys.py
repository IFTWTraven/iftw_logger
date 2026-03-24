from datetime import datetime

import os
import os.path
#import time
import psutil
import subprocess
#import openpyxl

#import sys, traceback
import traceback
from save import SaveToFile
from log_utils import log_checkpoint, log_exception

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
        raise RuntimeError(
            "Ellisys automation requires zeroc-ice. "
            "Install zeroc-ice (or use Python 3.11/3.12 / conda-forge package) before using Ellisys mode. "
            f"Import error: {ICE_IMPORT_ERROR}"
        )
    
def trim_brackets(input_list):
    # Check if the input_list is a list with exactly one element
    if isinstance(input_list, list) and len(input_list) == 1 and isinstance(input_list[0], str):
        # Use replace() to remove [' and '] from the string element
        trimmed_string = input_list[0].replace("['", "").replace("']", "")
        return trimmed_string
    else:
        # If the input format is not as expected, return the original list
        return input_list    

def search_and_run_ellisys(self):
    app_args = ['/remote_control_port=54321']    # List of directories to search in

    program_files_path = os.environ.get('ProgramFiles(x86)')
    ellisys_bin = os.path.join(program_files_path, 'Ellisys\Ellisys Type-C Tracker Analyzer', 'Ellisys.TypeCTrackerAnalyzer.exe')
    log_checkpoint("ELLISYS", "LAUNCH", "Launching Ellisys app", path=ellisys_bin)
    process = subprocess.Popen([ellisys_bin] + app_args)
    self.need_close_ellisys_while_exit = True
    log_checkpoint("ELLISYS", "LAUNCH", "Ellisys launch command sent")

def close_ellisys_thread(self):
    # Provide the name of the application you want to close
    app_name = 'Ellisys.TypeCTrackerAnalyzer.exe'

    # Iterate over all running processes
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == app_name:
            log_checkpoint("ELLISYS", "CLOSE", "Killing Ellisys process")
            proc.kill()
#            print('Application terminated successfully.')
            self.need_close_ellisys_while_exit = False
#            return

#    print('Application not found or already terminated.')

def Ellisys_Setup(self):
    log_checkpoint("ELLISYS", "SETUP", "Building Ellisys configuration string", platform=self.platform)
    config_strings_1st = '{General: {RecordUsb20: true,RecordUsbCc: true,RecordSbu: true,RecordI2c: true,RecordI2cSecondary: true,RecordUart: true,RecordLogicPort: true,RecordStatistics: true,SbuProtocol: '

    if self.platform == 'AMD':
        config_strings_2nd = '"DpAux"'
    if self.platform == 'INTEL':
        config_strings_2nd = '"TbUart"'
        
    config_strings_3rd = ',UartBitRate: "Br115200",I2cAlertType: "ActiveLow",I2cSecondaryAlertType: "ActiveLow"    },'
    config_strings_4th = 'LogicPort: {Level: 3.3,Threshold: 1.2,GlitchFilterPeriodCount: 4,Signals: {I2cScl: { Signal: '
    config_strings_4th_ch = str(self.ecclk_ellisys)
    config_strings_4th_end = ', DisplayName: "EC SCL" },I2cSda: { Signal: '
    config_strings_5th_ch = str(self.ecsda_ellisys)
    config_strings_5th_end = ', DisplayName: "EC SDA" },I2cAlert: { Signal: '
    config_strings_6th_ch = str(self.ecint_ellisys)
    config_strings_6th_end = ', DisplayName: "EC INT" },I2cSecondaryScl: { Signal: '
    config_strings_7th_ch = str(self.ecclk2_ellisys)
    config_strings_7th_end = ', DisplayName: "PCH SCL" },I2cSecondarySda: { Signal: '
    config_strings_8th_ch = str(self.ecsda2_ellisys)
    config_strings_8th_end = ', DisplayName: "PCH SDA" },I2cSecondaryAlert: { Signal: '
    config_strings_9th_ch = str(self.ecint2_ellisys)
    config_strings_9th_end = ', DisplayName: "PCH INT" },UartOut: { Signal: '
    config_strings_10th_ch = str(self.pduart_ellisys)
    config_strings_10th_end = ', DisplayName: "Tx" },UartIn: { Signal: '
    config_strings_11th_ch = str(self.pduart_ellisys)
    config_strings_11th_end = ', DisplayName: "Rx" }        }    },BasicFilter.LimitDataPacketsPayloadSize: 32}'

    config_strings = config_strings_1st + config_strings_2nd + config_strings_3rd + config_strings_4th + config_strings_4th_ch + config_strings_4th_end +\
                        config_strings_5th_ch + config_strings_5th_end + config_strings_6th_ch + config_strings_6th_end + config_strings_7th_ch + config_strings_7th_end +\
                        config_strings_8th_ch + config_strings_8th_end + config_strings_9th_ch + config_strings_9th_end + config_strings_10th_ch + config_strings_10th_end +\
                        config_strings_11th_ch + config_strings_11th_end

    log_checkpoint("ELLISYS", "SETUP", "Ellisys configuration string ready", length=len(config_strings))
    return config_strings

def Ellisys_StartCapture(self):
    _require_ice()
    Ice.loadSlice("--all -I. AnalyzerRemoteControl.ice")
    hostIp = "localhost"
    hostPort = 54321

    proxyString = "{0}:tcp -h {1} -p {2}".format(EllisysAnalyzer.AnalyzerRemoteControlIdentity, hostIp, hostPort)

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        communicator = None
        try:
            log_checkpoint("ELLISYS", "CAPTURE_START", "Connecting remote control", attempt=attempt, host=hostIp, port=hostPort)
            initData = Ice.InitializationData()
            initData.properties = Ice.createProperties([], initData.properties)
            initData.properties.setProperty("Ice.Default.EncodingVersion", "1.0")

            communicator = Ice.initialize(initData)
            proxy = communicator.stringToProxy(proxyString)

            remoteControl = EllisysAnalyzer.AnalyzerRemoteControlPrx.checkedCast(proxy)
            datasrc = remoteControl.GetAvailableDataSources()
            devstr = trim_brackets(datasrc)
            remoteControl.SelectDataSource(devstr)

            if not remoteControl:
                raise RuntimeError("Invalid Ellisys proxy")

            remoteControl.ConfigureRecordingOptions(self.ellisys_configstr)
            remoteControl.StartRecording()
            log_checkpoint("ELLISYS", "CAPTURE_START", "Ellisys recording started", datasource=devstr)
            return
        except Exception as exc:
            traceback.print_exc()
            log_exception("ELLISYS", "CAPTURE_START", exc)
            if attempt == max_retries:
                raise RuntimeError(f"Ellisys start capture failed after {max_retries} attempts: {exc}")
        finally:
            if communicator is not None:
                try:
                    communicator.destroy()
                except Exception:
                    pass
        # if communicator:
            # try:
                # communicator.destroy()
            # except:
                # traceback.print_exc()

def Ellisys_StopCapture(self):
    _require_ice()
    log_checkpoint("ELLISYS", "CAPTURE_STOP", "Stopping Ellisys capture", save=self.savetofile)
#    print(self.ellisysremote)
#    remoteControl = self.ellisysremote

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
    
    if self.savetofile:
        log_checkpoint("ELLISYS", "SAVE", "Saving Ellisys trace")
        SaveToFile(self, None)
#    else:
    remoteControl.AbortRecordingAndDiscardTraceFile()
    log_checkpoint("ELLISYS", "CAPTURE_STOP", "Ellisys recording stop command issued")