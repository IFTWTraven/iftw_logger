# Zero-Ice Fix Toolkit for saleae2automation

## Problem Summary
**Symptom**: Popup error "zeroc-ice is not installed while running under python" 
- **But**: Pre-compiled `.exe` works fine
- **Root Cause**: Python environment != System-wide installation

### ⚠️ Special Case: Python 3.14+ NOT Supported Yet
If you see error: `DLL load failed while importing IcePy` with **Python 3.14+**:
- ✗ zeroc-ice doesn't have pre-built wheels for Python 3.14 yet
- ⚡ **Quick fix**: Use Python 3.11.5 or 3.12 instead
  ```powershell
  py -3.12 -m pip install --only-binary :all: zeroc-ice
  py -3.12 saleae2automation/main.py
  ```

---

## Available Tools

### 🔍 **1. diagnose_ice.py** - Comprehensive Diagnostic Tool
**What it does**: Generates a detailed report of your Python environment and zeroc-ice status

**How to use**:
```powershell
python diagnose_ice.py
```

**Output includes**:
- Python executable path and version
- Whether Ice module is available
- List of installed packages  
- pip show details
- System PATH and environment variables
- Suggested fixes tailored to your situation

**Best for**: Understanding exactly what's wrong and what needs to be fixed

---

### 🔧 **2. fix_ice_windows.bat** - Automated Windows Batch Fixer
**What it does**: Automatically run diagnostics and attempt to install zeroc-ice

**How to use**:
```powershell
.\fix_ice_windows.bat
```

**Features**:
- ✓ Shows which Python is being used
- ✓ Runs diagnostics automatically
- ✓ Tries pre-built wheels first (no C++ compiler needed)
- ✓ Falls back to standard installation if needed
- ✓ Verifies success at the end

**Best for**: Non-technical users or quick fixes

---

### 🚀 **3. fix_ice_powershell.ps1** - Advanced PowerShell Script
**What it does**: Intelligent PowerShell-based diagnostic and installation

**How to use** (PowerShell):
```powershell
# First time: allow script execution
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Then run:
.\fix_ice_powershell.ps1
```

**Options**:
```powershell
.\fix_ice_powershell.ps1 -OnlyDiagnose    # Just show diagnostics, don't install
.\fix_ice_powershell.ps1 -UseConda       # Try conda instead of pip
.\fix_ice_powershell.ps1 -NoInstall      # Don't install (default is to install)
```

**Features**:
- ✓ Colored output for easy reading
- ✓ Conditional logic for smarter decisions
- ✓ Try/fallback mechanism (wheels → standard)
- ✓ Option to use conda
- ✓ Step-by-step progress

**Best for**: Advanced users or troubleshooting

---

### 📖 **4. TROUBLESHOOTING_ZEROC_ICE.md** - Comprehensive Troubleshooting Guide
**What it contains**:
- Problem explanation with root cause
- Quick fix solutions (3 options)
- Detailed diagnostic steps
- Advanced solutions (C++ build tools, Python upgrades, etc.)
- Quick reference table
- FAQ

**How to use**: 
- Read when experiencing issues
- Share with users who need to fix on their PC
- Reference for alternative solutions

---

## Quick Start Guide for Users on Problematic PC

### **Fastest Way to Fix** (2 minutes)

1. **Run the batch script**:
   ```powershell
   cd C:\Users\ShihTraven\GitLab\gadgets\saleae2automation
   .\fix_ice_windows.bat
   ```
   
2. **Restart saleae2automation** and try Ellisys mode

---

### **If Batch Script Fails**

Try the PowerShell version:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\fix_ice_powershell.ps1 -UseConda
```

---

### **If You Want to Understand the Problem**

```powershell
python diagnose_ice.py
```
Then refer to `TROUBLESHOOTING_ZEROC_ICE.md` for solutions

---

## Manual Installation Commands

If you prefer to install manually or the scripts fail:

### **Option A: Pip with pre-built wheels** (Recommended)
```powershell
python -m pip install --upgrade --only-binary :all: zeroc-ice
```

### **Option B: Pip standard**
```powershell
python -m pip install --upgrade zeroc-ice
```

### **Option C: Conda**
```powershell
conda install -c conda-forge zeroc-ice
```

---

## Verification

After any installation attempt, verify:

```powershell
# Test Ice import
python -c "import Ice; print('✓ Ice import successful')"

# Test Ellisys analyzer import
python -c "from Ellisys.Platform.NetworkRemoteControl.Analyzer import *; print('✓ Ellisys import successful')"
```

---

## Troubleshooting the Troubleshooting

| Issue | Solution |
|-------|----------|
| "Python not found" | Install Python or add to PATH |
| "Pre-built wheels failed" | Try standard installation or conda |
| "Python version" shows 3.9 or older | Upgrade to Python 3.11 or 3.12 |
| Multiple Python versions exist | Check `python -c "import sys; print(sys.executable)"` |
| Conda not found | Either install Miniconda or use pip |
| Scripts won't run (PowerShell) | Run: `Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process` |

---

## For Different Python Versions

If you have multiple Python installations:

```powershell
# Find all Python versions
where python

# Use specific version
py -3.11 -m pip install zeroc-ice          # Python 3.11
py -3.12 -m pip install zeroc-ice          # Python 3.12
python3.11 -m pip install zeroc-ice        # Alternative syntax

# Run app with specific Python
py -3.11 saleae2automation/main.py
```

---

## Files Provided

```
saleae2automation/
├── diagnose_ice.py                    ← Run this to diagnose
├── fix_ice_windows.bat                ← Run this for auto-fix (Windows)
├── fix_ice_powershell.ps1             ← Advanced fix script (PowerShell)
├── TROUBLESHOOTING_ZEROC_ICE.md       ← Read this for detailed help
└── prerequisites.py                   ← (Already updated with better messages)
```

---

## Support Information

When reporting an issue, always include:
1. Output from: `python diagnose_ice.py` 
2. Output from: `python --version`
3. Which script you tried and what error you got
4. Whether .exe works but Python doesn't (confirms the diagnosis)

---

## Notes

- ⚠️ **Important**: The pre-compiled `.exe` working but Python not working is the key indicator that this is an environment mismatch, not a system installation issue.
- 💡 **Best Practice**: Use Python 3.11 or 3.12 for the best zeroc-ice pre-built wheel support.
- 🔄 **After Installation**: Restart the terminal and/or application to ensure Python reloads modules.
- 📝 **Logging**: App now logs which Python executable and version it's using, making it easier to diagnose future issues.
