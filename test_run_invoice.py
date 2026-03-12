# -*- coding: utf-8 -*-
"""
지정한 인보이스 PDF로 customs_pdf_extractor 테스트 실행
사용: python test_run_invoice.py
"""

from pathlib import Path

# 테스트할 PDF가 있는 폴더 (해당 폴더 내 CI/CO PDF 자동 검색)
TEST_PDF_DIR = r"c:\Users\alstn\Downloads\아태협정 - CROCS TRADING COMPANY PTE (SG)\1. MAEU262577784 (아태협정)"
OUTPUT_EXCEL = "Customs_Integrated_Data.xlsx"


def main():
    from customs_pdf_extractor import run_extraction_and_merge

    folder = Path(TEST_PDF_DIR)
    if not folder.is_dir():
        print(f"폴더가 없습니다: {folder}")
        return

    print(f"PDF 폴더: {folder}")
    run_extraction_and_merge(str(folder), OUTPUT_EXCEL)

    # 결과 미리보기 (Commercial Invoice 형식: 15행이 헤더, 16행~ 데이터)
    import pandas as pd
    out_path = Path(__file__).resolve().parent / OUTPUT_EXCEL
    if out_path.is_file():
        df = pd.read_excel(out_path, engine="openpyxl", header=14)  # 15행(0-based 14)을 헤더로
        print(f"\n[추출 결과 미리보기] 데이터 행 수: {len(df)}, 컬럼: {list(df.columns)}")
        print(df.head(10).to_string())


if __name__ == "__main__":
    main()
