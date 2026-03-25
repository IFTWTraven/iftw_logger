from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import QTimer, QObject

from ui import Ui_Dg_Main
from run import *
#from saleae import automation
from datetime import datetime
import subprocess
import os
import os.path
import time
from usb_detection import build_usb_device_list_fast_then_slow_cached, build_vid_to_pids_map, evaluate_usb_device_match
from log_utils import log_checkpoint, log_exception

def is_usb_device_present(vid, pid, allow_vid_only=False):
    target_devices = [(vid, pid, allow_vid_only)]
    usb_device_list = build_usb_device_list_fast_then_slow_cached(
        cache_ttl_seconds=3.0,
        target_devices=target_devices,
    )
    present, _, _ = evaluate_usb_device_match(
        usb_device_list,
        vid,
        pid,
        allow_vid_only=allow_vid_only,
    )
    return present
class MainWindow_controller(QtWidgets.QMainWindow):
    def closeEvent(self, event):
        log_checkpoint("UI", "CLOSE", "Main window close requested", is_running=self.is_running)
        self.timerCheckAttachedRecDev.stop()

        # if accendentically close app while running
        if self.is_running:
            self.on_timerStopCapture()
    
        if self.need_close_saleae_while_exit:
            try:
                # only kill saleae if it was opened by this script
                close_saleae_thread(self)
            except Exception as exc:
                log_exception("UI", "CLOSE_SALEAE", exc)
                
        if self.need_close_ellisys_while_exit:
            try:
                close_ellisys_thread(self)
            except Exception as exc:
                log_exception("UI", "CLOSE_ELLISYS", exc)

    def __init__(self, periodic_device_check=False, periodic_device_check_interval=3.0):
        super().__init__() # in python3, super(Class, self).xxx = super().xxx
        log_checkpoint("UI", "INIT", "Main window controller init started")
        self.ui = Ui_Dg_Main()
        self.ui.setupUi(self)
        self.periodic_device_check = bool(periodic_device_check)
        if periodic_device_check_interval <= 0:
            periodic_device_check_interval = 3.0
        self.periodic_device_check_interval_ms = max(500, int(periodic_device_check_interval * 1000))

        self.cBset = ['cB_ICC1', 'cB_ICC2', 'cB_ISBU1', 'cB_ISBU2', 'cB_IVBUS',\
                    'cB_ECINT', 'cB_ECSDA', 'cB_ECCLK', 'cB_PDUART',\
                    'cB_ECINT_2', 'cB_ECSDA_2', 'cB_ECCLK_2', 'cB_PDUART_2',\
                    'cB_ECINT_3', 'cB_ECSDA_3', 'cB_ECCLK_3',\
                    'cB_AINT', 'cB_ARST', 'cB_ASDA', 'cB_ACLK', 'cB_MPWR', 'cB_MSDA', 'cB_MCLK',\
                    'cB_RINT', 'cB_RSDA', 'cB_RCLK', 'cB_BPWR', 'cB_BRST', 'cB_BSDA', 'cB_BCLK',\
                    'cB_OtherDevSel', 'cB_OtherPortSel', 'cB_DiffStepSel',\
                    'cB_Platform',\
#                    'cB_RecDev'\
                    ]
        self.lineEset = ['lineE_Project', 'lineE_PDver','lineE_ECver', 'lineE_Ticket', 'lineE_Port', 'lineE_FR']
        self.textEset = ['textE_Issue', 'textE_Device', 'textE_Replication', 'textE_Recovery', 'textE_OtherDev', 'textE_DiffStep']
#        self.cBvars = [self.icc1, self.icc2, self.isbu1, self.isbu2, self.ivbus,\
#                    self.aint, self.arst, self.asda, self.aclk, self.ahpd, self.mpwr, self.mrst, self.msda, self.mclk,\
#                    self.rint, self.rsda, self.rclk, self.bpwr, self.brst, self.bsda, self.bclk,\
#                    self.platform\
#                    ]
#        self.lineEvars = [self.pdver, self.ecver, self.pchver, self.hwver, self.ticket, self.project]

        self.is_running = False
        self.saleae_is_running = False
        self.need_close_saleae_while_exit = False
        self.apistr = ""
        self.savetofile = False

        #saleae parameters
        self.manager = 0
        self.sdevice = 0
        self.config = 0
        self.capture = 0
        self.capture_setting = 0
        self.enabled_ch = self.enabled_ch_i2c = self.enabled_ch_cc = []
                
        self.logsuffix = ''
        self.allrecords = ''
        self.sheetname = ''
        self.RecDevLst = ['']
        self.ellisys_configstr = ''
#        self.ellisysremote = ''
        self.need_close_ellisys_while_exit = False
        self.cy4500_app = None
        self.cy4500_main_window = None

        self.changerecdev = False

        self.setup_control()
        self.cB_SelectionChanged()       

        self.RecDevLst = self.updateRecDev()

#        self.ui.gB_INTEL.setVisible(False)
#        self.ui.gB_AMD.setVisible(True)

        if self.periodic_device_check:
            self.timerCheckAttachedRecDev.start(self.periodic_device_check_interval_ms)
            log_checkpoint(
                "USB",
                "TIMER_POLL",
                "Periodic recorder attachment check enabled",
                interval_ms=self.periodic_device_check_interval_ms,
            )
        else:
            log_checkpoint("USB", "TIMER_POLL", "Periodic recorder attachment check disabled")
        log_checkpoint("UI", "INIT", "Main window controller init completed", recorder_list=self.RecDevLst)
       
    def setup_control(self):
        for element_name in self.cBset:
            hdr = getattr(self.ui, element_name)
            hdr.currentIndexChanged.connect(self.on_stateChanged)

        for element_name in self.lineEset:
            hdr = getattr(self.ui, element_name)
            hdr.textChanged.connect(self.on_stateChanged)
        
        for element_name in self.textEset:
            hdr = getattr(self.ui, element_name)
            hdr.textChanged.connect(self.on_stateChanged)

        self.ui.cB_RecDev.currentIndexChanged.connect(self.on_RecDevstateChanged)

        self.ui.chkB_Analog.stateChanged.connect(self.on_stateChanged)
        self.ui.pB_Run.clicked.connect(self.on_pB_Run)
        self.ui.pB_Pass.clicked.connect(self.on_pB_Pass)
        self.ui.pB_Fail.clicked.connect(self.on_pB_Fail)

        self.timerStartCapture = QTimer()
        self.timerStartCapture.timeout.connect(self.on_timerStartCapture)
        self.timerStopCapture = QTimer()
        self.timerStopCapture.timeout.connect(self.on_timerStopCapture)
        self.timerSaveCapture = QTimer()
        self.timerSaveCapture.timeout.connect(self.on_timerSaveCapture)

        self.timerCheckAttachedRecDev = QTimer()
        self.timerCheckAttachedRecDev.timeout.connect(self.on_timerCheckAttachedRecDev)

    def updateRecDev(self):
        log_checkpoint("USB", "UI_POLL", "Refreshing attached recorder device list")
        target_devices = [
            (ELLISYS_VID, ELLISYS_PID, True),
            (SALEAE_VID, SALEAE_PID, True),
        ]
        usb_device_list = build_usb_device_list_fast_then_slow_cached(
            cache_ttl_seconds=4.0,
            target_devices=target_devices,
        )
        vid_to_pids = build_vid_to_pids_map(usb_device_list)

        self.ellisys_is_attached, _, _ = evaluate_usb_device_match(
            usb_device_list,
            ELLISYS_VID,
            ELLISYS_PID,
            allow_vid_only=True,
            vid_to_pids=vid_to_pids,
        )
        self.saleae_is_attached, _, _ = evaluate_usb_device_match(
            usb_device_list,
            SALEAE_VID,
            SALEAE_PID,
            allow_vid_only=True,
            vid_to_pids=vid_to_pids,
        )
        
        if self.ellisys_is_attached and self.saleae_is_attached:
            DevLst = [String_SALEAE, String_Ellisys]
        elif not self.ellisys_is_attached and self.saleae_is_attached:
            DevLst = [String_SALEAE]
        elif self.ellisys_is_attached and not self.saleae_is_attached:
            DevLst = [String_Ellisys]
        else:
            DevLst = ['']
            
        if self.RecDevLst != DevLst:
            log_checkpoint("USB", "UI_POLL", "Recorder device list changed", old=self.RecDevLst, new=DevLst)
            self.ui.cB_RecDev.clear()
            self.ui.cB_RecDev.addItems(DevLst)
        
        return DevLst

    def on_RecDevstateChanged(self):
        log_checkpoint("UI", "RECORDER", "Recorder combo changed", selection=self.ui.cB_RecDev.currentText())
        self.changerecdev = True
        self.on_stateChanged()
        self._launch_saleae_for_current_selection()
        self._launch_cy4500_for_current_selection()

    def _launch_saleae_for_current_selection(self):
        self.cB_SelectionChanged()
        if self.recorddevice != String_SALEAE:
            return

        try:
            if chk_LogApplicationRunning("Logic.exe"):
                log_checkpoint("UI", "SALEAE", "Saleae app already running in main UI flow")
                return

            log_checkpoint("UI", "SALEAE", "Launching Saleae app from recorder selection flow")
            search_and_run_saleae(self)
            log_checkpoint("UI", "SALEAE", "Saleae app launch command sent from main UI flow")
        except Exception as exc:
            log_exception("UI", "SALEAE_LAUNCH", exc)
            QMessageBox.warning(
                self,
                "Saleae Launch Error",
                f"Failed to launch Saleae:\n{str(exc)}"
            )

    def _launch_cy4500_for_current_selection(self):
        self.cB_SelectionChanged()
        if self.recorddevice != String_SALEAE:
            return

        try:
            log_checkpoint("UI", "CY4500", "Ensuring CY4500 launch/attach from recorder selection flow")
            _, main_window = CySniffer_LaunchAndAttach(self, launch_if_missing=True)
            if main_window is None:
                raise RuntimeError("CY4500 window is not available after launch/attach.")
            log_checkpoint("UI", "CY4500", "CY4500 launch/attach ready in main UI")
        except Exception as exc:
            log_exception("UI", "CY4500_LAUNCH", exc)
            QMessageBox.warning(
                self,
                "CY4500 Launch Error",
                f"Failed to launch/attach CY4500:\n{str(exc)}"
            )

    def on_main_window_shown(self):
        log_checkpoint("UI", "LAUNCH", "Post-show hook fired; launching recorder apps for current selection")
        self._launch_saleae_for_current_selection()
        self._launch_cy4500_for_current_selection()
    
    def on_stateChanged(self):
        self.cB_SelectionChanged()

        self.ui.textE_OtherDev.setEnabled(self.ui.cB_OtherDevSel.currentIndex())
        self.ui.textE_DiffStep.setEnabled(self.ui.cB_DiffStepSel.currentIndex())

        if self.otherdevsel and self.diffstepsel:
            ifcondition = ((self.otherdev != '') and (self.diffstep != ''))
        
        if not self.otherdevsel and self.diffstepsel:
            ifcondition = (self.diffstep != '')
        
        if self.otherdevsel and not self.diffstepsel:
            ifcondition = (self.otherdev != '')
                        
        if not self.otherdevsel and not self.diffstepsel:
            ifcondition = True

        if self.recorddevice == String_SALEAE:
            self.ui.gB_Generic.setVisible(True)
            self.ui.gB_INTEL.setVisible(self.ui.cB_Platform.currentIndex())
            self.ui.gB_AMD.setVisible(not self.ui.cB_Platform.currentIndex())

            self.ui.gB_Ellisys.setVisible(False)
            self.ui.label_ellisys.setVisible(False)
        elif self.recorddevice == String_Ellisys:
            self.ui.gB_Generic.setVisible(False)
            self.ui.gB_INTEL.setVisible(False)
            self.ui.gB_AMD.setVisible(False)

            self.ui.gB_Ellisys.setVisible(True)
            self.ui.label_ellisys.setVisible(True)

        if((self.project != '') and (self.pdver != '') and (self.ecver != '') and (self.port != '') and (self.failrate != '')\
                        and (self.issue != '') and (self.device != '') and (self.replication != '') and (self.recovery != '')\
                        and ifcondition):
            if self.recorddevice == String_SALEAE:
                if self.ui.cB_Platform.currentText() == 'INTEL':      # INTEL platform
                    if len(set([self.icc1, self.icc2, self.isbu1, self.isbu2, self.ivbus,\
                                self.ecint, self.ecsda, self.ecclk, self.pduart,\
                                self.rint, self.rsda, self.rclk, self.bpwr, self.brst, self.bsda, self.bclk\
                                ])) == 16:
                        self.ui.pB_Run.setEnabled(True)
                    else:
                        self.ui.pB_Run.setEnabled(False)
                elif self.ui.cB_Platform.currentText() == 'AMD':      # AMD platform
                    if len(set([self.icc1, self.icc2, self.isbu1, self.isbu2, self.ivbus,\
                                self.ecint, self.ecsda, self.ecclk, self.pduart,\
                                self.aint, self.arst, self.asda, self.aclk, self.mpwr, self.msda, self.mclk\
                                ])) == 16:
                        self.ui.pB_Run.setEnabled(True)
                    else:
                        self.ui.pB_Run.setEnabled(False)
            elif self.recorddevice == String_Ellisys:
                if len(set([self.ecint_ellisys, self.ecsda_ellisys, self.ecclk_ellisys, self.pduart_ellisys,\
                            self.ecint2_ellisys, self.ecsda2_ellisys, self.ecclk2_ellisys,\
                            ])) == 7:
                    self.ui.pB_Run.setEnabled(True)
                else:
                    self.ui.pB_Run.setEnabled(False)
        else:
            self.ui.pB_Run.setEnabled(False)
        
    def cB_SelectionChanged(self):
        self.recorddevice = self.ui.cB_RecDev.currentText()
    
        self.platform = self.ui.cB_Platform.currentText()
        self.project = self.ui.lineE_Project.text()
        self.pdver = self.ui.lineE_PDver.text()
        self.ecver = self.ui.lineE_ECver.text()
        self.ticket = self.ui.lineE_Ticket.text()
        self.port = self.ui.lineE_Port.text()
        self.failrate = self.ui.lineE_FR.text()
        
        self.issue = self.ui.textE_Issue.toPlainText()
        self.device = self.ui.textE_Device.toPlainText()
        self.replication = self.ui.textE_Replication.toPlainText()
        self.recovery = self.ui.textE_Recovery.toPlainText()
        self.otherdevsel = self.ui.cB_OtherDevSel.currentIndex()
        self.otherdev = self.ui.textE_OtherDev.toPlainText()
        self.otherportsel = self.ui.cB_OtherPortSel.currentIndex()
        self.diffstepsel = self.ui.cB_DiffStepSel.currentIndex()
        self.diffstep = self.ui.textE_DiffStep.toPlainText()
        
        self.icc1 = self.ui.cB_ICC1.currentIndex()
        self.icc2 = self.ui.cB_ICC2.currentIndex()
        self.isbu1 = self.ui.cB_ISBU1.currentIndex()
        self.isbu2 = self.ui.cB_ISBU2.currentIndex()
        self.ivbus = self.ui.cB_IVBUS.currentIndex()
        self.ecint = self.ui.cB_ECINT.currentIndex()
        self.ecsda = self.ui.cB_ECSDA.currentIndex()
        self.ecclk = self.ui.cB_ECCLK.currentIndex()
        self.pduart = self.ui.cB_PDUART.currentIndex()

        self.aint = self.ui.cB_AINT.currentIndex()
        self.arst = self.ui.cB_ARST.currentIndex()
        self.asda = self.ui.cB_ASDA.currentIndex()
        self.aclk = self.ui.cB_ACLK.currentIndex()
        self.mpwr = self.ui.cB_MPWR.currentIndex()
        self.msda = self.ui.cB_MSDA.currentIndex()
        self.mclk = self.ui.cB_MCLK.currentIndex()
               
        self.rint = self.ui.cB_RINT.currentIndex()
        self.rsda = self.ui.cB_RSDA.currentIndex()
        self.rclk = self.ui.cB_RCLK.currentIndex()
        self.bpwr = self.ui.cB_BPWR.currentIndex()
        self.brst = self.ui.cB_BRST.currentIndex()
        self.bsda = self.ui.cB_BSDA.currentIndex()
        self.bclk = self.ui.cB_BCLK.currentIndex()
    
        self.analogmode = self.ui.chkB_Analog.isChecked()

        # Ellisys
        self.ecint_ellisys = self.ui.cB_ECINT_2.currentIndex()
        self.ecsda_ellisys = self.ui.cB_ECSDA_2.currentIndex()
        self.ecclk_ellisys = self.ui.cB_ECCLK_2.currentIndex()
        self.pduart_ellisys = self.ui.cB_PDUART_2.currentIndex()
        self.ecint2_ellisys = self.ui.cB_ECINT_3.currentIndex()
        self.ecsda2_ellisys = self.ui.cB_ECSDA_3.currentIndex()
        self.ecclk2_ellisys = self.ui.cB_ECCLK_3.currentIndex()
        
        # don't use a new sheet if only record device is changed
        if self.changerecdev:
            self.changerecdev = False
        else:
            self.sheetname = ''

    def on_pB_Run(self):
        self.is_running = not self.is_running
        log_checkpoint("UI", "RUN_BUTTON", "Run button toggled", is_running=self.is_running)

        if self.is_running:
#            self.logsuffix += self.project + '_' + self.platform + '_PD' + self.pdver + '_EC' + self.ecver + '_Ticket' + self.ticket
            
            self.ui.pB_Run.setText("Starting...")
            self.ui.pB_Run.setEnabled(False)
            self.ui.gB_Generic.setEnabled(False)
            self.ui.gB_Ellisys.setEnabled(False)
            self.ui.gB_Info.setEnabled(False)
            self.ui.gB_AMD.setEnabled(False)
            self.ui.gB_INTEL.setEnabled(False)
            self.ui.chkB_Analog.setEnabled(False)
            self.ui.cB_RecDev.setEnabled(False)

            self.timerStartCapture.start(100)
        else:
            self.savetofile = False
            self.timerStopCapture.start(100)

    def on_pB_Pass(self):
        self.is_running = not self.is_running
        log_checkpoint("UI", "PASS_BUTTON", "Pass button clicked; preparing save flow")
        self.logsuffix += 'Pass_' + self.project + '_' + self.platform + '_PD' + self.pdver + '_EC' + self.ecver + '_Ticket' + self.ticket

        self.savetofile = True
        self.timerStopCapture.start(100)

    def on_pB_Fail(self):
        self.is_running = not self.is_running
        log_checkpoint("UI", "FAIL_BUTTON", "Fail button clicked; preparing save flow")
        self.logsuffix += 'Fail_' + self.project + '_' + self.platform + '_PD' + self.pdver + '_EC' + self.ecver + '_Ticket' + self.ticket

        self.savetofile = True
        self.timerStopCapture.start(100)
            
    def on_timerStartCapture(self):
        self.timerStartCapture.stop()
        log_checkpoint("UI", "TIMER_START", "Start capture timer fired")
        
        try:
            run_StartCapture(self)
        except Exception as exc:
            log_exception("UI", "START_CAPTURE", exc)
            self.is_running = False
            self.ui.pB_Run.setText("Start Recording")
            self.ui.pB_Run.setEnabled(True)
            self.ui.pB_Pass.setEnabled(False)
            self.ui.pB_Fail.setEnabled(False)
            self.ui.gB_Info.setEnabled(True)
            self.ui.gB_Generic.setEnabled(True)
            self.ui.gB_Ellisys.setEnabled(True)
            self.ui.gB_INTEL.setEnabled(True)
            self.ui.gB_AMD.setEnabled(True)
            self.ui.chkB_Analog.setEnabled(True)
            self.ui.cB_RecDev.setEnabled(True)
            QMessageBox.warning(
                self,
                "Start Capture Error",
                f"Failed to start capture:\n{str(exc)}"
            )
            return
        # if self.recorddevice == String_SALEAE:
            # # check if saleae is running or not
            # self.saleae_is_running = chk_LogApplicationRunning("Logic.exe")
            
            # if self.saleae_is_running:
                # self.apistr = 'connect'         # run automation.Manager.connect()
            # else:
                # search_and_run_saleae(self)
    # #            self.apistr = 'launch'          # run automation.Manager.launch()
                # self.apistr = 'connect'         # run automation.Manager.connect()
                # self.saleae_is_running = True

    # #        if not self.saleae_is_running:                  # saleae is not running
    # #            search_and_run_saleae(self)                 # execute saleae logic2 with --automation argument
                
            # # init saleae
            # self.manager, self.sdevice, self.config, self.capture_settings, \
            # self.enabled_ch, self.enabled_ch_i2c, self.enabled_ch_cc = Saleae_Setup(self)
            # self.capture = Saleae_StartCapture(self)

        # elif self.recorddevice == String_Ellisys:
            # self.ellisys_configstr = Ellisys_Setup(self)
# #            self.ellisysremote = Ellisys_StartCapture(self)
            # Ellisys_StartCapture(self)

        self.ui.pB_Run.setEnabled(True)
        self.ui.pB_Pass.setEnabled(True)
        self.ui.pB_Fail.setEnabled(True)
        self.ui.pB_Run.setText("Abort Recording")
        log_checkpoint("UI", "TIMER_START", "Capture started and UI updated")
        
    def on_timerStopCapture(self):
        self.timerStopCapture.stop()
        log_checkpoint("UI", "TIMER_STOP", "Stop capture timer fired")
        self.ui.pB_Run.setText("Stoping...")
        self.ui.pB_Run.setEnabled(False)
        self.ui.pB_Pass.setEnabled(False)
        self.ui.pB_Fail.setEnabled(False)
        self.timerSaveCapture.start(100)

    def on_timerSaveCapture(self):
        self.timerSaveCapture.stop()
        log_checkpoint("UI", "TIMER_SAVE", "Save capture timer fired", recorder=self.recorddevice, save=self.savetofile)
        
        try:
            run_StopCapture(self)
        except RuntimeError as e:
            # Handle save dialog errors gracefully (e.g., TC OS automation issues)
            print(f"[Error] Failed to save capture: {e}")
            log_exception("UI", "SAVE_RUNTIME", e)
            QMessageBox.warning(
                self,
                "Save Error",
                f"Failed to save the capture file:\n{str(e)}\n\nPlease save manually from the application or try again."
            )
        except Exception as e:
            # Catch any other unexpected errors
            print(f"[Error] Unexpected error during stop capture: {e}")
            log_exception("UI", "SAVE_UNEXPECTED", e)
            QMessageBox.warning(
                self,
                "Unexpected Error",
                f"An unexpected error occurred:\n{str(e)}"
            )

        # if self.recorddevice == String_SALEAE:
            # Saleae_StopCapture(self)      
        # elif self.recorddevice == String_Ellisys:
            # Ellisys_StopCapture(self)
            
        self.logsuffix = ''
        self.ui.pB_Run.setText("Start Recording")
        self.ui.pB_Run.setEnabled(True)
        self.ui.pB_Pass.setEnabled(False)
        self.ui.pB_Fail.setEnabled(False)
        self.ui.cB_RecDev.setEnabled(True)
        
        self.ui.gB_Info.setEnabled(True)
        self.ui.gB_Generic.setEnabled(True)
        self.ui.gB_Ellisys.setEnabled(True)
        self.ui.gB_INTEL.setEnabled(True)
        self.ui.gB_AMD.setEnabled(True)
        self.ui.chkB_Analog.setEnabled(True)
        log_checkpoint("UI", "TIMER_SAVE", "Save/stop flow completed and UI reset")
    
    def on_timerCheckAttachedRecDev(self):
        log_checkpoint("USB", "TIMER_POLL", "Periodic recorder attachment check")
        self.RecDevLst = self.updateRecDev()
        