import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.services.pdf_split import split_payslip_pdf

app = FastAPI(title="PDF Split & Email API", version="0.1.0")


def _run_split(content: bytes):
    """스레드에서 실행할 동기 함수 (Python 3.8 호환)"""
    return split_payslip_pdf(content)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/split")
async def split_pdf(file: UploadFile = File(...)):
    """급여명세서 합본 PDF를 업로드하면 페이지별로 분리하고, 각 페이지에서 사원명·급여명세서 제목을 추출해 파일명을 생성합니다."""
    try:
        if not file or not getattr(file, "filename", None):
            raise HTTPException(status_code=400, detail="PDF 파일을 선택해 주세요.")
        fname = (file.filename or "").strip()
        if not fname.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")
        content = await file.read()
        if not content or len(content) == 0:
            raise HTTPException(status_code=400, detail="파일 내용이 비어 있습니다.")
        # CPU 바운드 작업을 스레드 풀에서 실행 (Python 3.7+ 호환)
        loop = asyncio.get_running_loop()
        items = await loop.run_in_executor(None, _run_split, content)
        return {"items": items}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        err_msg = str(e).replace("\n", " ").strip()
        raise HTTPException(status_code=500, detail=f"서버 오류: {type(e).__name__}: {err_msg}")
