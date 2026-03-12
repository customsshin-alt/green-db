"""
급여명세서 합본 PDF를 페이지별로 분리하고,
각 페이지에서 사원명과 상단 "YYYY년 MM월분 급여명세서"를 추출하여
파일명: {사원명}_{YYYY년MM월급여명세서}.pdf 형식으로 생성합니다.
"""
import base64
import re
from io import BytesIO

import fitz  # PyMuPDF


def _sanitize_filename(name: str, max_len: int = 200) -> str:
    """파일명에 사용할 수 없는 문자 제거 (JSON/파일시스템 호환)"""
    if not name or not isinstance(name, str):
        return "unnamed"
    # 제어문자, \, /, :, *, ?, ", <, >, | 제거
    s = re.sub(r'[\x00-\x1f\\/:*?"<>|]', "", name.strip())
    return s[:max_len] if s else "unnamed"


def _normalize_title_for_filename(title: str) -> str:
    """'2021년 06월분 급여명세서' -> '2021년06월급여명세서' (공백 제거)"""
    if not title or not isinstance(title, str):
        return "급여명세서"
    return re.sub(r"\s+", "", title.strip()) or "급여명세서"


def _extract_employee_name(text: str) -> str:
    """페이지 텍스트에서 '사원명 : XXX' 또는 '사원명: XXX' 패턴으로 이름 추출 (세 글자 또는 전체 이름)"""
    if not text or not isinstance(text, str):
        return ""
    # 사원명 : 신성훈 / 사원명: 신성훈
    m = re.search(r"사원명\s*:\s*([^\s\n,]+)", text)
    if m:
        return m.group(1).strip()
    # 성명 오른쪽 이름 (폴백)
    m = re.search(r"성명\s*:\s*([^\s\n,]+)", text)
    if m:
        return m.group(1).strip()
    return ""


def _extract_payslip_title(text: str) -> str:
    """페이지 텍스트 상단에서 'YYYY년 MM월분 급여명세서' 패턴 추출"""
    if not text or not isinstance(text, str):
        return ""
    m = re.search(r"(\d{4}년\s*\d{1,2}월분?\s*급여명세서)", text)
    if m:
        return m.group(1).strip()
    return ""


def split_payslip_pdf(pdf_bytes: bytes) -> list[dict]:
    """
    급여명세서 합본 PDF를 1페이지씩 분리하고, 각 페이지에서 사원명·급여명세서 제목을 추출해
    파일명을 '{사원명}_{YYYY년MM월급여명세서}.pdf' 형식으로 만들어 반환합니다.

    Returns:
        list[dict]: [
            { "filename": str, "confirmedName": str, "contentBase64": str },
            ...
        ]
    """
    # stream: bytes 또는 BytesIO 모두 지원 (PyMuPDF 버전별 호환)
    if isinstance(pdf_bytes, (bytes, bytearray)):
        stream = BytesIO(pdf_bytes)
    else:
        stream = pdf_bytes
    if hasattr(stream, "seek"):
        stream.seek(0)
    doc = fitz.open(stream=stream, filetype="pdf")
    if len(doc) == 0:
        doc.close()
        return []
    results = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        raw_text = page.get_text()
        text = raw_text if isinstance(raw_text, str) else (str(raw_text) if raw_text is not None else "")

        name = _extract_employee_name(text)
        title = _extract_payslip_title(text)

        if not name:
            name = f"사원_{page_index + 1}"
        if not title:
            title = "급여명세서"

        title_part = _normalize_title_for_filename(title)
        base_name = _sanitize_filename(f"{name}_{title_part}")
        filename = f"{base_name}.pdf" if not base_name.endswith(".pdf") else base_name

        # 해당 페이지만 포함한 새 PDF 생성 (write()가 bytes 반환, 버전 호환)
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=page_index, to_page=page_index)
        try:
            pdf_content = new_doc.write()
        except (AttributeError, TypeError):
            out = BytesIO()
            new_doc.save(out)
            pdf_content = out.getvalue()
        new_doc.close()
        if not isinstance(pdf_content, (bytes, bytearray)):
            pdf_content = bytes(pdf_content) if pdf_content is not None else b""

        results.append({
            "filename": filename,
            "confirmedName": name,
            "contentBase64": base64.b64encode(pdf_content).decode("ascii"),
        })

    doc.close()
    return results
