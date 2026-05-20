param(
  [string]$Configuration = "Debug"
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoDir = Resolve-Path (Join-Path $ProjectDir "..\..")
$OutDir = Join-Path $ProjectDir "bin\csc\$Configuration"
$ProgramDir = $env:TFLEX_PROGRAM_DIR
if (-not $ProgramDir) { $ProgramDir = "C:\Program Files\T-FLEX CAD 17\Program" }
$Csc = $env:CSC_EXE
if (-not $Csc) { $Csc = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe" }
if (-not (Test-Path -LiteralPath $Csc)) { throw "csc.exe not found: $Csc" }
if (-not (Test-Path -LiteralPath $ProgramDir)) { throw "T-FLEX Program dir not found: $ProgramDir" }

New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
$Refs = @("TFlexAPI.dll", "TFlexAPI3D.dll", "TFlexAPIData.dll", "TFlexCommandAPI.dll") | ForEach-Object { Join-Path $ProgramDir $_ }
foreach ($ref in $Refs) { if (-not (Test-Path -LiteralPath $ref)) { throw "Reference not found: $ref" } }

& $Csc /nologo /platform:x64 /target:exe "/out:$(Join-Path $OutDir 'TFlexRunner.exe')" `
  (Join-Path $ProjectDir "Program.cs") `
  (Join-Path $ProjectDir "ResultWriter.cs") `
  ($Refs | ForEach-Object { "/reference:$_" })
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

foreach ($ref in $Refs) { Copy-Item -LiteralPath $ref -Destination $OutDir -Force }
Write-Output (Join-Path $OutDir 'TFlexRunner.exe')
