@echo off
set "NODE_DIR=C:\Program Files\nodejs"
set "PATH=%NODE_DIR%;%PATH%"
cd /d "%~dp0"

echo 의존성 설치 중...
call "%NODE_DIR%\npm.cmd" install
if errorlevel 1 (
  echo npm install 실패. 아무 키나 누르면 종료합니다.
  pause >nul
  exit /b 1
)

echo 개발 서버 시작...
call "%NODE_DIR%\npm.cmd" run dev
pause
