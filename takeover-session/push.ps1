# Upload a local file to the AutoDL box as raw BYTES (encoding-proof) by splitting
# the base64 payload into chunks and appending them over several ssh calls, so it
# works regardless of PowerShell version, code page, or command-line length limits.
#   pwsh -f push.ps1 -Local .\remote\x.py -Remote /root/autodl-tmp/monkeyocr-repro/scripts/x.py
param(
  [Parameter(Mandatory=$true)][string]$Local,
  [Parameter(Mandatory=$true)][string]$Remote,
  [string]$User = "root",
  [string]$HostName = "connect.cqa1.seetacloud.com",
  [int]$Port = 29127,
  [int]$Chunk = 4000
)
$ErrorActionPreference = "Stop"
$key = Join-Path $env:USERPROFILE ".ssh\monkeyocr_autodl_rsa"
$target = "$User@$HostName"
$b64 = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $Local).Path))
$dir = $Remote.Substring(0, $Remote.LastIndexOf('/'))

& ssh -p $Port -i $key -o BatchMode=yes -o StrictHostKeyChecking=no $target "mkdir -p '$dir'; : > '$Remote'.b64" | Out-Null
for ($i = 0; $i -lt $b64.Length; $i += $Chunk) {
  $len = [Math]::Min($Chunk, $b64.Length - $i)
  & ssh -p $Port -i $key -o BatchMode=yes -o StrictHostKeyChecking=no $target "printf '%s' '$($b64.Substring($i, $len))' >> '$Remote'.b64" | Out-Null
}
& ssh -p $Port -i $key -o BatchMode=yes -o StrictHostKeyChecking=no $target "base64 -d '$Remote'.b64 > '$Remote' && rm -f '$Remote'.b64 && wc -c '$Remote'"
