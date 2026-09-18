# Run a command on the AutoDL RTX4090D box over the existing temporary key.
# Usage:  pwsh -f rcmd.ps1 -Cmd "nvidia-smi" [-TimeoutSec 120]
param(
  [Parameter(Mandatory=$true)][string]$Cmd,
  [int]$TimeoutSec = 120,
  [string]$User = "root",
  [string]$Host_ = "connect.cqa1.seetacloud.com",
  [int]$Port = 29127
)
$key = Join-Path $env:USERPROFILE ".ssh\monkeyocr_autodl_rsa"
$target = "$User@$Host_"
& ssh -p $Port -i $key -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=20 $target $Cmd 2>&1
exit $LASTEXITCODE
