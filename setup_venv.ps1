# 가상 환경 생성 및 의존성 설치 (PowerShell)
# 사용법: .\setup_venv.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

# 1. 가상 환경이 없으면 생성
if (-not (Test-Path ".venv")) {
    Write-Host "가상 환경 생성 중... (.venv)" -ForegroundColor Cyan
    python -m venv .venv
}

# 2. 가상 환경 활성화 후 패키지 설치
Write-Host "가상 환경 활성화 및 패키지 설치 중..." -ForegroundColor Cyan
& ".\.venv\Scripts\Activate.ps1"

# 기본 패키지 먼저 설치 (항상 성공해야 함)
pip install -r requirements-base.txt

# PaddlePaddle / PaddleOCR 시도 (Python 3.9~3.13 권장, 3.14는 미지원)
$pyVer = (python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null)
if ($pyVer -match "3\.1[4-9]") {
    Write-Host "Python $pyVer 감지: PaddlePaddle은 3.9~3.13만 지원합니다. 기본 패키지만 설치했습니다." -ForegroundColor Yellow
    Write-Host "원산지 증명서(CO) OCR을 쓰려면 Python 3.11/3.12로 별도 venv를 만든 뒤 paddlepaddle, paddleocr를 설치하세요." -ForegroundColor Yellow
} else {
    pip install paddlepaddle paddleocr 2>$null
    if ($LASTEXITCODE -ne 0) {
        pip install -r requirements.txt 2>$null
    }
}

Write-Host "완료. 가상환경 활성화: .\.venv\Scripts\Activate.ps1" -ForegroundColor Green
