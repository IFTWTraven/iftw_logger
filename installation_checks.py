import os
from log_utils import log_checkpoint


def validate_installed_applications(saleae_present, ellisys_present, cy4500_present, cy4500epr_present):
    log_checkpoint(
        "INSTALL",
        "VALIDATE",
        "Validating required external applications",
        saleae_present=saleae_present,
        ellisys_present=ellisys_present,
        cy4500_present=cy4500_present,
        cy4500epr_present=cy4500epr_present,
    )
    # When Saleae capture path is selected, CY4500 utility and Logic2 must both exist.
    if saleae_present and (cy4500_present or cy4500epr_present):
        cy4500_path = r"C:\Infineon\Tools"
        cy4500_bin = os.path.join(cy4500_path, "EZ-PD Protocol Analyzer Utility", "EZ_PD_Protocol_Analyzer_Utility.exe")
        log_checkpoint("INSTALL", "CHECK_CY4500", "Checking CY4500 utility path", path=cy4500_bin)
        if not os.path.exists(cy4500_bin):
            log_checkpoint("INSTALL", "CHECK_CY4500", "CY4500 utility not found")
            return (
                False,
                "Not Install",
                "EZ-PD Protocol Analyzer Utility install not found. Go to https://www.infineon.com/ to download the installer.",
            )

        saleae_root = os.environ.get("programw6432") or ""
        saleae_bin = os.path.join(saleae_root, "Logic", "Logic.exe")
        log_checkpoint("INSTALL", "CHECK_SALEAE", "Checking Saleae Logic2 path", path=saleae_bin)
        if not os.path.exists(saleae_bin):
            log_checkpoint("INSTALL", "CHECK_SALEAE", "Saleae Logic2 not found")
            return (
                False,
                "Not Install",
                "Saleae Logic2 install not found. Go to https://www.saleae.com/downloads/ to download the installer.",
            )

    if ellisys_present:
        ellisys_root = os.environ.get("ProgramFiles(x86)") or ""
        ellisys_bin = os.path.join(
            ellisys_root,
            "Ellisys\\Ellisys Type-C Tracker Analyzer",
            "Ellisys.TypeCTrackerAnalyzer.exe",
        )
        log_checkpoint("INSTALL", "CHECK_ELLISYS", "Checking Ellisys analyzer path", path=ellisys_bin)
        if not os.path.exists(ellisys_bin):
            log_checkpoint("INSTALL", "CHECK_ELLISYS", "Ellisys analyzer not found")
            return (
                False,
                "Not Install",
                "Ellisys Type-C Tracker Analyzer install not found.\r\nGo to https://www.ellisys.com/better_analysis/ctra_latest.htm to download the installer.",
            )

        user_documents = os.path.join(os.path.expanduser("~"), "Documents")
        ellisys_remote_root = os.path.join(
            user_documents,
            "Ellisys",
            "Ellisys Type-C Analyzer",
            "RemoteControl",
        )
        ellisys_remote1 = os.path.join(
            ellisys_remote_root,
            "EllisysAnalyzerRemoteControlPlugin.dll",
        )
        ellisys_remote2 = os.path.join(
            ellisys_remote_root,
            "Ice.dll",
        )
        log_checkpoint("INSTALL", "CHECK_ELLISYS_PLUGIN", "Checking Ellisys RemoteControl plugin under Documents", path=ellisys_remote_root)
        if not os.path.exists(ellisys_remote1) or not os.path.exists(ellisys_remote2):
            log_checkpoint("INSTALL", "CHECK_ELLISYS_PLUGIN", "Ellisys RemoteControl plugin missing in Documents")
            return (
                False,
                "Not Install",
                "Ellisys Type-C Tracker Analyzer RemoteControl plugin does not exist under user Documents.",
            )

    log_checkpoint("INSTALL", "VALIDATE", "Installation validation passed")
    return True, "", ""
