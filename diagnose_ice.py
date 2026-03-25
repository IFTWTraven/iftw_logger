#!/usr/bin/env python3
"""
Diagnostic script to debug zeroc-ice installation issues.
Helps identify why Ice import fails even when zeroc-ice is installed on the system.
"""

import sys
import subprocess
import importlib.util
import os

def print_section(title):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")

def check_python_info():
    print_section("Python Environment Information")
    print(f"Python Executable: {sys.executable}")
    print(f"Python Version: {sys.version}")
    print(f"Python Version Info: {sys.version_info}")
    print(f"Prefix (site-packages parent): {sys.prefix}")
    
    # Warning for Python 3.14+
    if sys.version_info >= (3, 14):
        print("\n⚠️  WARNING: Python 3.14+ detected")
        print("   zeroc-ice does NOT have pre-built wheels for Python 3.14+ yet")
        print("   RECOMMENDATION: Use Python 3.11.5 (or 3.12) instead")
    
    print(f"\nSite-packages locations:")
    for path in sys.path:
        if 'site-packages' in path or 'dist-packages' in path:
            print(f"  - {path}")

def check_ice_availability():
    print_section("Ice Module Availability Check")
    try:
        spec = importlib.util.find_spec("Ice")
        if spec is not None:
            print("✓ Ice module FOUND")
            if spec.origin:
                print(f"  Location: {spec.origin}")
            return True
        else:
            print("✗ Ice module NOT FOUND (find_spec returned None)")
            return False
    except (ModuleNotFoundError, ValueError) as e:
        print(f"✗ Ice module NOT FOUND: {e}")
        return False

def check_pip_list():
    print_section("Installed Python Packages (pip list)")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        # Filter for relevant packages
        lines = result.stdout.split('\n')
        print("Looking for zeroc-ice and related packages:")
        for line in lines:
            if 'ice' in line.lower() or 'zeroc' in line.lower():
                print(f"  {line}")
        if not any('ice' in line.lower() for line in lines):
            print("  (No zeroc-ice packages found)")
    else:
        print(f"Error running pip list: {result.stderr}")

def check_pip_show():
    print_section("Package Details (pip show zeroc-ice)")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", "zeroc-ice"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(result.stdout)
    else:
        print("zeroc-ice not installed in current Python environment")

def check_alternative_install_methods():
    print_section("Checking for Alternative Installation Methods")
    
    # Check conda
    try:
        result = subprocess.run(["conda", "list"], capture_output=True, text=True, timeout=5)
        if "zeroc-ice" in result.stdout or "ice" in result.stdout:
            print("✓ Found conda installation")
            for line in result.stdout.split('\n'):
                if 'ice' in line.lower() or 'zeroc' in line.lower():
                    print(f"  {line}")
        else:
            print("✗ zeroc-ice not found in conda packages")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("- conda not available")

def check_system_paths():
    print_section("System PATH and Environment Variables")
    print("PYTHONPATH:")
    pythonpath = os.environ.get("PYTHONPATH", "(not set)")
    if pythonpath != "(not set)":
        for path in pythonpath.split(os.pathsep):
            print(f"  - {path}")
    else:
        print("  (not set)")

def suggest_fixes():
    print_section("Suggested Fixes")
    
    # Special case for Python 3.14+
    if sys.version_info >= (3, 14):
        python_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
        print(f"""
⚠️  PYTHON {python_ver} DETECTED - NOT YET SUPPORTED FOR ZEROC-ICE
═══════════════════════════════════════════════════════════════════

❌ PROBLEM:
   zeroc-ice does NOT have pre-built wheels for Python {python_ver} yet.
   Installing it will fail with "DLL load failed" errors.

✅ SOLUTION - Switch to Python 3.11.5 (development baseline):

    Option A: Use Python 3.11
    ─────────────────────────
    py -3.11 -m pip install --only-binary :all: zeroc-ice
    py -3.11 saleae2automation/main.py

    Option B: Use Python 3.12
    ────────────────────────
    py -3.12 -m pip install --only-binary :all: zeroc-ice
    py -3.12 saleae2automation/main.py

    Option C: Use conda (may have broader compatibility)
   ──────────────────────────────────────────────────
   conda install -c conda-forge zeroc-ice

📚 WHY THIS HAPPENS:
   - Native Python packages like zeroc-ice have binary wheels per Python version
   - Each wheel is built for a specific ABI (Application Binary Interface)
   - Python 3.14 ABI is too new; wheels don't exist yet
   - Using older wheels causes DLL initialization failures

🔄 Wait for Python 3.14 Support:
   Check https://github.com/zeroc-ice/ice for latest updates
   Support should arrive in a future zeroc-ice release.
"""
        )
    else:
        print("""
1. INSTALL IN CURRENT PYTHON ENVIRONMENT (RECOMMENDED):
   python -m pip install --upgrade zeroc-ice
   Or with pre-built wheels (avoids C++ compiler requirement):
   python -m pip install --only-binary :all: zeroc-ice

2. USE CONDA (OFTEN WORKS BETTER FOR zeroc-ice):
   conda install -c conda-forge zeroc-ice

3. VERIFY INSTALLATION:
   python -c "import Ice; print('Ice import successful')"
   python -c "from Ellisys.Platform.NetworkRemoteControl.Analyzer import *"

4. CHECK FOR MULTIPLE PYTHON INSTALLATIONS:
   This PC might have multiple Python versions. Make sure you're using
   the same Python that has zeroc-ice installed.

5. IF USING A VIRTUAL ENVIRONMENT:
   Make sure it's activated before running the application:
   - venv: .\\venv\\Scripts\\activate
   - conda: conda activate <env_name>

6. PYTHON VERSION COMPATIBILITY:
   zeroc-ice has limited pre-built wheel support. Recommended versions:
    - Python 3.11.5 (project development baseline)
    - Python 3.12 (best support)
   - Python 3.10 and older (may require compilation)
   
    ⚠️  Python 3.14+ is NOT YET SUPPORTED - use 3.11.5 or 3.12 instead.
"""
        ))

def main():
    print("\n" + "="*60)
    print("ZEROC-ICE DIAGNOSTIC TOOL")
    print("="*60)
    
    # Run all checks
    check_python_info()
    ice_found = check_ice_availability()
    check_pip_list()
    check_pip_show()
    check_alternative_install_methods()
    check_system_paths()
    
    if not ice_found:
        suggest_fixes()
    else:
        print("\n✓ Ice module is properly installed. Check the import in your script.")
    
    print("\n" + "="*60)
    print("END OF DIAGNOSTIC REPORT")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
