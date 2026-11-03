param([ValidateSet('dflash144','base256','dflash128graph','dflash96vision')][string]$Profile='dflash96vision')
$ErrorActionPreference='Stop'
try {
    Write-Host "Starting Bonsai server: $Profile"
    & python "$PSScriptRoot\bonsai_ensure.py" --profile $Profile
    if($LASTEXITCODE -ne 0){throw 'Bonsai startup failed. See C:\AI\bonsai\engine.log and proxy.log.'}
    Write-Host 'OpenAI API:    http://127.0.0.1:8081/v1'
    Write-Host 'Anthropic API: http://127.0.0.1:8081'
    Write-Host 'Server is running in the background. You can close this window.'
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
}
