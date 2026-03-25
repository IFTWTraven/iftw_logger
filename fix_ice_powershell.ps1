# PowerShell script to diagnose and fix zeroc-ice issues
# Usage: Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process; .\fix_ice_powershell.ps1

param(
    [switch]$NoInstall = $false,
    [switch]$OnlyDiagnose = $false,
    [switch]$UseConda = $false
)

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

function Test-IceModule {
    $result = python -c "import Ice; print('OK')" 2>&1 | Select-String "OK"
    return $null -ne $result
}

# Main script
Write-Host ""
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  zeroc-ice Diagnostic & Fix Script    ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# Check Python availability
Write-Section "Python Environment Check"
$pythonCheck = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ERROR: Python not found in PATH" -ForegroundColor Red
    Write-Host "Please ensure Python is installed and added to PATH" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Python found: $pythonCheck" -ForegroundColor Green
$pythonExe = python -c "import sys; print(sys.executable)" 2>&1
Write-Host "  Executable: $pythonExe" -ForegroundColor Gray
$pythonVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>&1
Write-Host "  Version: $pythonVersion" -ForegroundColor Gray

# Check for Python 3.14+ incompatibility
$majorVersion = $pythonVersion.Split('.')[0]
$minorVersion = $pythonVersion.Split('.')[1]
if ([int]$majorVersion -eq 3 -and [int]$minorVersion -ge 14) {
    Write-Host ""
    Write-Host "⚠️  WARNING: Python $pythonVersion detected" -ForegroundColor Yellow
    Write-Host "   zeroc-ice does NOT have pre-built wheels for Python 3.14+ yet" -ForegroundColor Yellow
    Write-Host "   This will likely fail with 'DLL load failed' errors" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🔧 RECOMMENDED SOLUTION:" -ForegroundColor Yellow
    Write-Host "   Use Python 3.11.5 or 3.12 instead:" -ForegroundColor Yellow
    Write-Host "     • py -3.11 -m pip install --only-binary :all: zeroc-ice" -ForegroundColor Gray
    Write-Host "     • py -3.11 saleae2automation/main.py" -ForegroundColor Gray
    Write-Host "     • or use the same commands with py -3.12" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   If you want to continue with Python 3.14, enter YES to try:" -ForegroundColor Yellow
    $response = Read-Host "   Continue anyway? (YES/no)"
    if ($response -ne "YES") {
        Write-Host ""
        Write-Host "Please switch to Python 3.11.5 or 3.12 first." -ForegroundColor Green
        exit 0
    }
}

# Run diagnostic
Write-Section "Running Diagnostic"
if (Test-Path "diagnose_ice.py") {
    python diagnose_ice.py
} else {
    Write-Host "Warning: diagnose_ice.py not found in current directory" -ForegroundColor Yellow
}

# Check current Ice status
Write-Section "Ice Module Status"
if (Test-IceModule) {
    Write-Host "✓ Ice module is already installed and working!" -ForegroundColor Green
    Write-Host "  You can use Ellisys mode without any changes." -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ Ice module NOT available in current environment" -ForegroundColor Red
}

# If only diagnose requested, exit
if ($OnlyDiagnose) {
    Write-Host ""
    Write-Host "Diagnostic mode only. Run without -OnlyDiagnose to install." -ForegroundColor Yellow
    exit 0
}

# If no install requested, exit
if ($NoInstall) {
    Write-Host ""
    Write-Host "Installation disabled. Use -NoInstall:`$false to allow installation." -ForegroundColor Yellow
    exit 0
}

# Proceed with installation
Write-Section "Installing zeroc-ice"

if ($UseConda) {
    Write-Host "Installing via conda..." -ForegroundColor Yellow
    conda install -c conda-forge zeroc-ice
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Conda installation failed" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Attempting installation with pre-built wheels..." -ForegroundColor Yellow
    python -m pip install --upgrade --only-binary ":all:" zeroc-ice 2>&1 | Tee-Object -Variable output
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Pre-built installation failed. Attempting standard installation..." -ForegroundColor Yellow
        python -m pip install --upgrade zeroc-ice
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host ""
            Write-Host "❌ Installation failed with both methods" -ForegroundColor Red
            Write-Host ""
            Write-Host "Troubleshooting options:" -ForegroundColor Yellow
            Write-Host "  1. Try conda: .\fix_ice_powershell.ps1 -UseConda" -ForegroundColor Gray
            Write-Host "  2. Upgrade to Python 3.11/3.12 (better wheel support)" -ForegroundColor Gray
            Write-Host "  3. Install Visual Studio C++ Build Tools" -ForegroundColor Gray
            exit 1
        }
    }
}

# Verify installation
Write-Section "Verifying Installation"
if (Test-IceModule) {
    Write-Host "✓ SUCCESS! Ice module installed and working" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Green
    Write-Host "  1. Close and reopen saleae2automation" -ForegroundColor Gray
    Write-Host "  2. Try using Ellisys mode" -ForegroundColor Gray
    Write-Host "  3. If issues persist, run: python diagnose_ice.py" -ForegroundColor Gray
} else {
    Write-Host "❌ Verification failed - Ice still not importable" -ForegroundColor Red
    Write-Host "Possible reasons:" -ForegroundColor Yellow
    Write-Host "  - Installation didn't complete properly" -ForegroundColor Gray
    Write-Host "  - Python version incompatibility" -ForegroundColor Gray
    Write-Host "  - Requires restart of terminal or system" -ForegroundColor Gray
}

Write-Host ""
