#!/usr/bin/env pwsh
# Launch Review Studio with optional workspace / project
param(
  [string]$Workspace = "",
  [string]$Project = "",
  [int]$Port = 8787,
  [int]$ScanDepth = 2
)

$server = Join-Path $PSScriptRoot "server\main.py"
$args = @("--port", $Port, "--scan-depth", $ScanDepth)
if ($Workspace) { $args += @("--workspace", $Workspace) }
if ($Project) { $args += @("--project", $Project) }
python $server @args
