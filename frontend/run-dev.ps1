# Node.js 전체 경로로 개발 서버 실행 (PATH 미반영 시 사용)
$nodeDir = "C:\Program Files\nodejs"
$env:Path = "$nodeDir;$env:Path"
Set-Location $PSScriptRoot
& "$nodeDir\npm.cmd" run dev
