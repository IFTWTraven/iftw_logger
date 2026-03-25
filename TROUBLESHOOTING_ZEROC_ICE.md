# Troubleshooting: "zeroc-ice is not installed" Popup Error

## Problem
When running `saleae2automation` on another PC and trying to use **Ellisys mode**, you see:
- **Popup Error**: "zeroc-ice is not installed"
- **But**: zeroc-ice IS installed on the system (pre-compiled .exe works fine)

## Root Cause
This is a classic **multi-environment issue**:
- **Pre-compiled `.exe`**: Finds zeroc-ice system-wide (system PATH, system libraries)
- **Python script**: Looks for `Ice` module in the **current Python environment** (venv, conda env, system Python)
- **Result**: `import Ice` fails because the Python environment doesn't have the package installed

This commonly happens because:
1. ❌ Multiple Python installations on the PC (different versions)
2. ❌ Using a Python virtual environment without Ice installed
3. ❌ zeroc-ice installed with different Python version than the one running the app
4. ❌ **🔴 Python 3.14+ detected** (NO pre-built wheels available yet - see section below)
5. ❌ Python version doesn't have pre-built wheels (older versions like 3.9 struggle)

---

## ⚠️ SPECIAL CASE: Python 3.14+ Incompatibility

**If you see "DLL load failed while importing IcePy" error and have Python 3.14+:**

**Root Cause**: 
- zeroc-ice does NOT yet have pre-built wheels for Python 3.14+
- Even if installed, the DLL compiled for older Python versions won't load
- This is a **known limitation** that will be fixed in future zeroc-ice releases

**Solution** (RECOMMENDED):
```powershell
# Use Python 3.11.5 or 3.12 instead
py -3.12 --version  # Check if available
py -3.12 -m pip install --only-binary :all: zeroc-ice
py -3.12 saleae2automation/main.py
```

**Why this works:**
- Python 3.11.5 and 3.12 are the recommended versions for this project
- The binary wheels are compiled specifically for each Python ABI
- Python 3.14's newer ABI doesn't have wheels yet

---

## Solution: Quick Fix (Choose One)

### **Option 1: Install Ice in Current Python (Recommended)**

Run this in PowerShell/Command Prompt:

```powershell
# Check which Python is running
python --version
python -c "import sys; print(sys.executable)"

# Install zeroc-ice with pre-built wheels (avoids C++ compiler)
python -m pip install --upgrade --only-binary :all: zeroc-ice

# Verify it worked
python -c "import Ice; print('Success: Ice imported')"
```

**If "--only-binary" fails**, try standard installation:
```powershell
python -m pip install --upgrade zeroc-ice
```

### **Option 2: Use Conda (Often Works Better)**

```powershell
# Install via conda (usually has better pre-built support)
conda install -c conda-forge zeroc-ice

# Verify
python -c "import Ice; print('Success: Ice imported')"
```

### **Option 3: Use Windows Batch Helper**

In the `saleae2automation` folder, run:
```powershell
.\fix_ice_windows.bat
```

This script will:
1. ✅ Check which Python is being used
2. ✅ Run diagnostics
3. ✅ Attempt to install zeroc-ice automatically

---

## Detailed Diagnostics

### Step 1: Run the Diagnostic Script

In the `saleae2automation` folder:
```powershell
python diagnose_ice.py
```

This will show:
- Which Python executable is running
- Python version (important! 3.11/3.12 have best support)
- Where `site-packages` is located
- Whether Ice is installed in that environment
- A list of installed packages

### Step 2: Check if Multiple Pythons Exist

If you have multiple Python installations:
```powershell
# Find all Python installations
where python
python -c "import sys; print(sys.executable)"

# If using a specific Python version:
python.exe --version
py -3.11 --version  # if you have Python 3.11
py -3.12 --version  # if you have Python 3.12
```

### Step 3: Verify Installation

```powershell
# Verify Ice is importable
python -c "import Ice; print('Ice imported successfully')"

# Verify Ellisys analyzer can be imported
python -c "from Ellisys.Platform.NetworkRemoteControl.Analyzer import *; print('Ellisys analyzer import successful')"
```

---

## Advanced Solutions

### **If Pre-built Wheels Fail (C++ Compiler Required)**

Install **Visual Studio C++ Build Tools**:
1. Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Run installer → select **"Desktop development with C++"**
3. Wait for installation to complete
4. Try installing zeroc-ice again:
   ```powershell
   python -m pip install --upgrade zeroc-ice
   ```

### **If Python 3.9 or Older**

zeroc-ice has limited support for older Python versions. **Recommended upgrade**:
```powershell
# Use Python 3.11 or 3.12
py -3.11 --version  # Check if 3.11 is installed
py -3.11 -m pip install zeroc-ice
py -3.11 saleae2automation/main.py  # Run app with Python 3.11
```

### **If Python 3.14+ Detected (With DLL Load Error)**

**This is a known incompatibility.** zeroc-ice doesn't have pre-built wheels for Python 3.14+ yet.

**Only recommended solution**:
```powershell
# Switch to Python 3.11.5 (development baseline)
py -3.11 -m pip install --only-binary :all: zeroc-ice
py -3.11 saleae2automation/main.py

# Alternative: Python 3.12
py -3.12 -m pip install --only-binary :all: zeroc-ice
py -3.12 saleae2automation/main.py
```

**Why?** Each Python version has a different binary ABI. Pre-built wheels are compiled per ABI. Python 3.14's ABI is too new - wheels don't exist yet. Using 3.11.5 or 3.12 solves this completely.

### **If Using Virtual Environment**

Ensure it's activated:
```powershell
# For venv
.\.venv\Scripts\Activate.ps1

# For conda
conda activate <env_name>

# Then install
python -m pip install --upgrade --only-binary :all: zeroc-ice
```

---

## How to Tell if It's Fixed

✅ **Restart the application and try Ellisys mode again**

Expected behavior:
- ✓ No popup error about Ice
- ✓ Ellisys controls become available
- ✓ Can start/stop Ellisys recording

---

## Still Not Working?

### 1. **Check the Log File**
The app logs diagnostics to a file. Find it by looking for the path printed at startup:
```
Application bootstrap started
Prerequisite check completed
```

### 2. **Send Diagnostic Report**
Run this and share output:
```powershell
python diagnose_ice.py > ice_diagnostic_report.txt
```

### 3. **Fallback: System-Level Install**

If Python can't find Ice but the .exe works, zeroc-ice might be installed system-wide. Try:
```powershell
# On some systems, Ice is installed to system paths
python -c "import sys; sys.path.insert(0, 'C:\\Program Files\\ZeroC\\Ice'); import Ice"
```

---

## Quick Reference

| Symptom | Fix |
|---------|-----|
| Popup: "zeroc-ice is not installed" | `python -m pip install --only-binary :all: zeroc-ice` |
| Error: "DLL load failed while importing IcePy" + Python 3.14+ | **Use Python 3.11.5 or 3.12**: `py -3.11 -m pip install --only-binary :all: zeroc-ice` |
| Python 3.14+ detected | ⚠️ Not yet supported - Switch to Python 3.11.5/3.12 |
| Python 3.9 or older | Upgrade to Python 3.11/3.12 |
| "ModuleNotFoundError: No module named 'Ice'" | Install Ice in current Python env |
| Multiple Python versions on PC | Ensure same Python that installed Ice runs the app |
| Pre-built wheels fail | Install Visual Studio C++ Build Tools |
| conda not available | Use pip instead or install Miniconda |

---

## Need More Help?

1. **Run diagnostics**: `python diagnose_ice.py`
2. **Run auto-fix**: `.\fix_ice_windows.bat`
3. **Check logs**: Look for checkpoint logs in the app output
4. **Compare PCs**: Run `diagnose_ice.py` on both the working and broken PC to compare environments
