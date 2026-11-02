$root=$PSScriptRoot
foreach($kind in @('proxy','engine')) {
    $file=Join-Path $root "$kind.pid"
    if(-not (Test-Path -LiteralPath $file)){continue}
    $taskPid=0
    if(-not [int]::TryParse([IO.File]::ReadAllText($file).Trim(),[ref]$taskPid)){continue}
    $p=Get-CimInstance Win32_Process -Filter "ProcessId = $taskPid" -ErrorAction SilentlyContinue
    if(-not $p){continue}
    $owned=($kind -eq 'engine' -and $p.ExecutablePath -eq "$root\ninfer-serve.exe") -or ($kind -eq 'proxy' -and $p.CommandLine -like "*$root\bonsai_proxy.py*")
    if($owned){Stop-Process -Id $taskPid -ErrorAction Stop;Write-Host "Stopped Bonsai $kind"}
}
