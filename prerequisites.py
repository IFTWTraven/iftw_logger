import importlib.util
import subprocess
import sys
from log_utils import log_checkpoint


REQUIRED_PACKAGES = [
    ("PyQt5", "PyQt5"),
    ("psutil", "psutil"),
    ("win32api", "pywin32"),
    ("pywinauto", "pywinauto"),
    ("openpyxl", "openpyxl"),
    ("saleae", "logic2-automation"),
]

OPTIONAL_PACKAGES = [
    ("Ice", ["zeroc-ice==3.7.10", "zeroc-ice"]),
]


def _is_module_available(module_name):
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ModuleNotFoundError, ValueError):
        return False


def _install_package(package_name, only_binary=False):
    command = [sys.executable, "-m", "pip", "install"]
    if only_binary:
        command.extend(["--only-binary", ":all:"])
    command.append(package_name)
    print(f"[Prerequisite] Installing {package_name} ...")
    log_checkpoint("PREREQ", "INSTALL", "Installing package", package=package_name, only_binary=only_binary)
    result = subprocess.run(command, check=False)
    log_checkpoint("PREREQ", "INSTALL", "Install command finished", package=package_name, returncode=result.returncode)
    return result.returncode == 0


def ensure_prerequisites():
    log_checkpoint("PREREQ", "CHECK", "Checking required Python modules")
    missing = [(mod, pkg) for mod, pkg in REQUIRED_PACKAGES if not _is_module_available(mod)]
    if not missing:
        log_checkpoint("PREREQ", "CHECK", "All required modules available")
        return True

    print("[Prerequisite] Missing packages detected.")
    failures = []
    for module_name, package_name in missing:
        if _is_module_available(module_name):
            continue
        if not _install_package(package_name):
            failures.append(package_name)

    if failures:
        print("[Prerequisite] Failed to install:", ", ".join(failures))
        print("[Prerequisite] Please install them manually and rerun main.py.")
        log_checkpoint("PREREQ", "CHECK", "Required package installation failed", failures=",".join(failures))
        return False

    for module_name, package_candidates in OPTIONAL_PACKAGES:
        if _is_module_available(module_name):
            continue

        installed = False
        for candidate in package_candidates:
            # Prefer prebuilt wheels to avoid Visual C++ build tool requirements.
            if _install_package(candidate, only_binary=True):
                installed = True
                break
            if _install_package(candidate, only_binary=False):
                installed = True
                break

        if not installed:
            print(f"[Prerequisite] Optional dependency '{module_name}' is not available.")
            print("[Prerequisite] Ellisys automation will be unavailable.")
            print("[Prerequisite] Alternatives:")
            print("  1) Use Python 3.11/3.12 and reinstall dependencies")
            print("  2) Use conda: conda install -c conda-forge zeroc-ice")
            print("  3) Install Visual Studio C++ Build Tools (MSVC v14+)")
            log_checkpoint("PREREQ", "OPTIONAL", "Optional dependency unavailable", module=module_name)

    log_checkpoint("PREREQ", "CHECK", "Prerequisite checks completed")
    return True
