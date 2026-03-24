# Import libraries
#from saleae import automation
#from datetime import datetime

from dev_saleae import *
from dev_ellisys import *
from dev_cysniffer import *
from save import *

#import os
#import os.path
#import sys
#import time
import psutil
#import subprocess
#import openpyxl
from log_utils import log_checkpoint, log_exception

def run_StartCapture(self):
    log_checkpoint("RUN", "START", "Start capture requested", recorder=self.recorddevice, platform=getattr(self, "platform", ""))
    if self.recorddevice == String_SALEAE:
        log_checkpoint("RUN", "CY4500", "Triggering CY4500 start before Saleae")

        CySniffer_StartCapture()

        # check if saleae is running or not
        # self.saleae_is_running = chk_LogApplicationRunning("Logic.exe")
        
        # if self.saleae_is_running:
            # self.apistr = 'connect'         # run automation.Manager.connect()
        # else:
            # search_and_run_saleae(self)
# #            self.apistr = 'launch'          # run automation.Manager.launch()
            # self.apistr = 'connect'         # run automation.Manager.connect()
            # self.saleae_is_running = True
        
        if not chk_LogApplicationRunning("Logic.exe"):
            log_checkpoint("RUN", "SALEAE", "Logic.exe not running, launching application")
            search_and_run_saleae(self)
        else:
            log_checkpoint("RUN", "SALEAE", "Logic.exe already running")
        self.apistr = 'connect'         # run automation.Manager.connect()
            
        # init saleae
        log_checkpoint("RUN", "SALEAE", "Initializing Saleae setup")
        self.manager, self.sdevice, self.config, self.capture_settings, \
        self.enabled_ch, self.enabled_ch_i2c, self.enabled_ch_cc = Saleae_Setup(self)
        log_checkpoint("RUN", "SALEAE", "Starting Saleae capture")
        self.capture = Saleae_StartCapture(self)
        log_checkpoint("RUN", "SALEAE", "Saleae capture started")
        
    elif self.recorddevice == String_Ellisys:
        log_checkpoint("RUN", "ELLISYS", "Initializing Ellisys setup")
        self.ellisys_configstr = Ellisys_Setup(self)
        if not chk_LogApplicationRunning("Ellisys.TypeCTrackerAnalyzer.exe"):
            log_checkpoint("RUN", "ELLISYS", "Ellisys app not running, launching application")
            search_and_run_ellisys(self)
        else:
            log_checkpoint("RUN", "ELLISYS", "Ellisys app already running")
        log_checkpoint("RUN", "ELLISYS", "Starting Ellisys capture")
        Ellisys_StartCapture(self)
        log_checkpoint("RUN", "ELLISYS", "Ellisys capture started")
    else:
        log_checkpoint("RUN", "START", "Unknown recorder device selected", recorder=self.recorddevice)

def run_StopCapture(self):
    log_checkpoint("RUN", "STOP", "Stop capture requested", recorder=self.recorddevice, save=self.savetofile)
    if self.recorddevice == String_SALEAE:
        Saleae_StopCapture(self)      
        CySniffer_StopCapture(self)
        log_checkpoint("RUN", "STOP", "Saleae and CY4500 stop sequence complete")
    elif self.recorddevice == String_Ellisys:
        Ellisys_StopCapture(self)
        log_checkpoint("RUN", "STOP", "Ellisys stop sequence complete")
    else:
        log_checkpoint("RUN", "STOP", "Unknown recorder device on stop", recorder=self.recorddevice)

def chk_LogApplicationRunning(app_name):
    log_checkpoint("RUN", "PROC", "Checking process state", process=app_name)
    for proc in psutil.process_iter(['name']):
        if proc.info['name'].lower() == app_name.lower():
            log_checkpoint("RUN", "PROC", "Process is running", process=app_name)
            return True
    log_checkpoint("RUN", "PROC", "Process is not running", process=app_name)
    return False
