param([string]$Project,[ValidateSet('dflash144','base256','dflash128graph')][string]$Profile='dflash144')
Add-Type -AssemblyName System.Windows.Forms
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
try {
    if (-not $Project) {
        $picker=New-Object System.Windows.Forms.FolderBrowserDialog
        $picker.Description='Choose the project folder for Bonsai / Claude Code'
        if(Test-Path -LiteralPath "$root\last-project.txt"){$picker.SelectedPath=[IO.File]::ReadAllText("$root\last-project.txt").Trim()}
        if($picker.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK){exit}
        $Project=$picker.SelectedPath
    }
    [IO.File]::WriteAllText("$root\last-project.txt",$Project)
    & python "$root\claude_launch.py" --profile $Profile --project $Project
    if($LASTEXITCODE -ne 0){throw 'Claude Code did not complete normally. See C:\AI\bonsai\proxy.log and engine.log.'}
} catch {
    [System.Windows.Forms.MessageBox]::Show($_.Exception.Message,'Bonsai Claude Code') | Out-Null
}
