# Import libraries
from saleae import automation
#from datetime import datetime

import os
import os.path
#import sys
#import time
import psutil
import subprocess
#import openpyxl
from save import SaveToFile
from log_utils import log_checkpoint, log_exception
   
def search_and_run_saleae(self):
    app_args = ['--automation']    # List of directories to search in

    program_files_path = os.environ.get('programw6432')
    logic2_bin = os.path.join(program_files_path, 'Logic', 'Logic.exe')
    log_checkpoint("SALEAE", "LAUNCH", "Launching Logic2 with automation flag", path=logic2_bin)
    process = subprocess.Popen([logic2_bin] + app_args)
    self.need_close_saleae_while_exit = True
    log_checkpoint("SALEAE", "LAUNCH", "Logic2 launch command sent")
    
def close_saleae_thread(self):
    # Provide the name of the application you want to close
    app_name = 'Logic.exe'

    # Iterate over all running processes
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == app_name:
            log_checkpoint("SALEAE", "CLOSE", "Killing Logic.exe process")
            proc.kill()
#            print('Application terminated successfully.')
            self.need_close_saleae_while_exit = False
#            return
 
def Saleae_StartCapture(self):
    manager = self.manager
    log_checkpoint("SALEAE", "CAPTURE_START", "Starting Saleae capture session")
  
    with manager.start_capture(
        device_id = self.sdevice[0].device_id,
        device_configuration = self.config,
        capture_configuration = self.capture_settings) as capture:               
            pass
    log_checkpoint("SALEAE", "CAPTURE_START", "Saleae capture session created")
            
    return capture
    
def Saleae_StopCapture(self):
    capture = self.capture
    log_checkpoint("SALEAE", "CAPTURE_STOP", "Stopping Saleae capture", save=self.savetofile)
    capture.stop()

    if self.savetofile:
        log_checkpoint("SALEAE", "SAVE", "Saving Saleae capture to file")
        SaveToFile(self, None)

    # close captured session to release memory consumption
    capture.close()
    log_checkpoint("SALEAE", "CAPTURE_STOP", "Saleae capture closed")

def Saleae_Close(self):
    manager = self.manager

    manager.close()
    log_checkpoint("SALEAE", "MANAGER", "Saleae manager connection closed")
    
    return manager
       
def Saleae_Setup(self):
    log_checkpoint("SALEAE", "SETUP", "Preparing Saleae capture settings", platform=self.platform, analog_mode=self.analogmode)

    digital_ch_cc = [self.icc1, self.icc2, self.isbu1, self.isbu2, self.ivbus, self.ecint, self.ecsda, self.ecclk, self.pduart]
    digital_ch_amd = [self.aint, self.arst, self.asda, self.aclk, self.mpwr, self.msda, self.mclk]
    digital_ch_intel = [self.rint, self.rsda, self.rclk, self.bpwr, self.brst, self.bsda, self.bclk]

    analog_ch_cc = [self.icc1, self.icc2, self.isbu1, self.isbu2, self.ivbus]
#    analog_ch_amd = [self.mpwr, self.mrst]
#    analog_ch_intel = [self.bpwr, self.brst]

    enabled_ch_cc = [self.icc1, self.icc2]
    enabled_analog_ch = analog_ch_cc

    if self.platform == 'INTEL':                                        # INTEL 
        enabled_ch = digital_ch_cc + digital_ch_intel
        enabled_ch_i2c = [self.ecsda, self.ecclk, self.rsda, self.rclk, self.bsda, self.bclk]
#        enabled_analog_ch = analog_ch_cc + analog_ch_intel
    elif self.platform == 'AMD':                                        # AMD
        enabled_ch = digital_ch_cc + digital_ch_amd
        enabled_ch_i2c = [self.ecsda, self.ecclk, self.asda, self.aclk, self.msda, self.mclk]
#        enabled_analog_ch = analog_ch_cc + analog_ch_amd
    
    try:
        hdr = getattr(automation.Manager, self.apistr)
        manager = hdr()
#        manager = automation.Manager.connect()
        log_checkpoint("SALEAE", "SETUP", "Saleae manager connected", api=self.apistr)

        sdevice = manager.get_devices()
        if sdevice:
            device_type = sdevice[0].device_type
            log_checkpoint("SALEAE", "SETUP", "Detected Saleae devices", count=len(sdevice), device_type=device_type)
        else:
            device_type = "Demo"
            log_checkpoint("SALEAE", "SETUP", "No Saleae device found; using demo device")

        if not len(sdevice):
            demo_device = automation.DeviceDesc(device_id='F4241', device_type='Demo', is_simulation=True)
            sdevice = [demo_device]
        else:
            # attached saleae is 8ch, fixed ch setting for test only
            if str(device_type) != 'DeviceType.LOGIC_PRO_16' and str(device_type) != 'DeviceType.LOGIC_16':
                enabled_ch = [0, 1, 6, 7]
                enabled_ch_i2c = [6, 7]
                enabled_ch_cc = [0, 1]
                log_checkpoint("SALEAE", "SETUP", "Applied non-16ch fallback channel map")
            
            if (self.analogmode):
                analogue_rate_setting = 781_250
                if sdevice:
                    config = automation.LogicDeviceConfiguration(
                        enabled_digital_channels = enabled_ch,
                        enabled_analog_channels = enabled_analog_ch,
                        digital_sample_rate = 6_250_000,
                        digital_threshold_volts = 1.2,
                        analog_sample_rate = analogue_rate_setting
                    )
                else:
                    config = automation.LogicDeviceConfiguration(
                        enabled_digital_channels = enabled_ch,
                        enabled_analog_channels = enabled_analog_ch,
                        digital_sample_rate = 5_000_000,
                        analog_sample_rate = analogue_rate_setting
                    )
            else:
                if sdevice:
                    config = automation.LogicDeviceConfiguration(
                        enabled_digital_channels = enabled_ch,
                        digital_sample_rate = 6_250_000,
                        digital_threshold_volts = 1.2,
                    )
                else:
                    config = automation.LogicDeviceConfiguration(
                        enabled_digital_channels = enabled_ch,
                        digital_sample_rate = 5_000_000,
                    )
       
        duration_seconds = 1200     # need a number for timer capture mode
        capture_settings = automation.CaptureConfiguration(
            capture_mode = automation.TimedCaptureMode(duration_seconds)
        )
        log_checkpoint(
            "SALEAE",
            "SETUP",
            "Saleae setup completed",
            digital_channels=len(enabled_ch),
            i2c_channels=len(enabled_ch_i2c),
            cc_channels=len(enabled_ch_cc),
            duration_seconds=duration_seconds,
        )

        return manager, sdevice, config, capture_settings, enabled_ch, enabled_ch_i2c, enabled_ch_cc
    except Exception as exc:
        log_exception("SALEAE", "SETUP", exc)
        raise RuntimeError(f"Saleae setup failed: {exc}")
