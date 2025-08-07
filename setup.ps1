$ErrorActionPreference = "Stop"

try {
    Write-Host "[*] Starting VENV" -ForegroundColor Cyan
    py -m venv .venv

    & .\.venv\Scripts\Activate.ps1

    Write-Host "[*] Upgrading PIP" -ForegroundColor Cyan
    py -m pip install --upgrade pip

    Write-Host "[*] Installing deps" -ForegroundColor Cyan
    pip install -r ./requirements.txt

    Write-Host "[+] Environment ready!" -ForegroundColor Green
}
catch {
    <#Do this if a terminating exception happens#>
    Write-Host "[-] An error occurred: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

