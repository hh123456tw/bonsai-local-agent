param([string]$Project,[ValidateSet('dflash144','base256')][string]$Profile='dflash144')
Add-Type -AssemblyName System.Windows.Forms
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
try {
    if (-not $Project) {
        $picker=New-Object System.Windows.Forms.FolderBrowserDialog
        $picker.Description='Choose the project folder for Bonsai OpenCode'
        if(Test-Path -LiteralPath "$root\last-project.txt"){$picker.SelectedPath=[IO.File]::ReadAllText("$root\last-project.txt").Trim()}
        if($picker.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK){exit}
        $Project=$picker.SelectedPath
    }
    [IO.File]::WriteAllText("$root\last-project.txt",$Project)
    Write-Host 'Starting Bonsai. Loading the model may take a minute...'
    & python "$root\bonsai_ensure.py" --profile $Profile
    if($LASTEXITCODE -ne 0){throw 'Model startup failed. See C:\AI\bonsai\engine.log'}
    $env:XDG_CONFIG_HOME="$root\config"
    $profiles=Get-Content -LiteralPath "$root\profiles.json" -Raw -Encoding UTF8 | ConvertFrom-Json
    $env:OPENCODE_CONFIG=Join-Path $root $profiles.$Profile.opencode_config
    Set-Location -LiteralPath $Project
    & "$env:APPDATA\npm\opencode.cmd" --standalone
} catch {
    [System.Windows.Forms.MessageBox]::Show($_.Exception.Message,'Bonsai OpenCode') | Out-Null
}
