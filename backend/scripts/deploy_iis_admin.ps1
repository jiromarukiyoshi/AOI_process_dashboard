$ErrorActionPreference = "Stop"

$logPath = "C:\tmp\aoi_iis_admin_deploy.log"
$siteName = "AOI_process_dashboard"
$appPoolName = "AOI_process_dashboard"
$physicalPath = "C:\web\AOI_process_dashboard\backend"
$pythonPath = "C:\web\AOI_process_dashboard\backend\venv\Scripts\python.exe"
$wfastcgiEnable = "C:\web\AOI_process_dashboard\backend\venv\Scripts\wfastcgi-enable.exe"
$appcmd = Join-Path $env:windir "system32\inetsrv\appcmd.exe"

Start-Transcript -Path $logPath -Force

try {
    Import-Module WebAdministration

    & $appcmd unlock config -section:system.webServer/handlers
    & $wfastcgiEnable

    if (-not (Test-Path "IIS:\AppPools\$appPoolName")) {
        New-WebAppPool -Name $appPoolName | Out-Null
    }
    Set-ItemProperty "IIS:\AppPools\$appPoolName" -Name managedRuntimeVersion -Value ""
    Set-ItemProperty "IIS:\AppPools\$appPoolName" -Name processModel.identityType -Value "ApplicationPoolIdentity"

    if (-not (Test-Path "IIS:\Sites\$siteName")) {
        New-Website -Name $siteName -Port 8008 -PhysicalPath $physicalPath -ApplicationPool $appPoolName -Force | Out-Null
    } else {
        Set-ItemProperty "IIS:\Sites\$siteName" -Name physicalPath -Value $physicalPath
        Set-ItemProperty "IIS:\Sites\$siteName" -Name applicationPool -Value $appPoolName
        $hasPort8008 = Get-WebBinding -Name $siteName -Protocol "http" |
            Where-Object { $_.bindingInformation -eq "*:8008:" }
        if (-not $hasPort8008) {
            New-WebBinding -Name $siteName -Protocol "http" -IPAddress "*" -Port 8008 | Out-Null
        }
    }

    Start-WebAppPool -Name $appPoolName
    Start-Website -Name $siteName

    Write-Host "AOI IIS deploy completed."
    Write-Host "Site: http://localhost:8008/"
    Write-Host "Python: $pythonPath"
    Write-Host "PhysicalPath: $physicalPath"
} finally {
    Stop-Transcript
}
