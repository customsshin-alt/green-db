# 관세 인보이스(CI) / 원산지 증명서(CO) PDF 추출 및 통합

Commercial Invoice와 Certificate of Origin PDF에서 데이터를 추출하고, **Invoice No** 기준으로 결합하여 엑셀(`Customs_Integrated_Data.xlsx`)로 저장하는 Python 프로그램입니다.

### 추출 원칙 (프롬프트)

- **PDF 한 박스(셀) = 엑셀 한 셀.** 박스 안의 숫자·문자는 모두 한 셀에 넣고, 줄 단위로 나누지 않음.
- 박스가 여러 줄이면 셀 값 내부에 `\n`으로 유지하여 엑셀에서 한 셀에 여러 줄로 표시.
- 각 박스 안의 숫자·문자는 모두 추출하여 누락 없이 엑셀에 기록.

## 가상 환경 설정 및 의존성 설치

**PowerShell에서:**

```powershell
# 1. 가상 환경 생성 (최초 1회)
python -m venv .venv

# 2. 가상 환경 활성화
.\.venv\Scripts\Activate.ps1

# 3. 의존성 설치
pip install -r requirements-base.txt
```

또는 스크립트 한 번에 실행:

```powershell
.\setup_venv.ps1
```

- **CO(원산지 증명서) OCR**: 기본은 **Tesseract** 사용 (`pytesseract`). Python 3.14 포함 모든 버전에서 동작합니다.  
  Windows에서 [Tesseract 엔진](https://github.com/UB-Mannheim/tesseract/wiki)을 설치한 뒤, 설치 경로를 PATH에 추가하거나 `pytesseract.pytesseract.tesseract_cmd`에 설정하세요.  
- **선택**: PaddleOCR을 쓰려면 `pip install paddlepaddle paddleocr` (Python 3.9~3.13). 설치되어 있으면 Tesseract 대신 PaddleOCR이 사용됩니다.

## 사용 방법

1. CI/인보이스 PDF와 CO(원산지 증명서) PDF를 `pdf_files` 폴더에 넣거나, 스크립트와 같은 폴더에 넣습니다.
2. 파일명 규칙:
   - **인보이스**: 파일명에 `Invoice` 또는 `CI` 포함
   - **원산지 증명서**: 파일명에 `Certificate` 또는 `Origin` 포함
3. 터미널에서 실행:

```bash
python customs_pdf_extractor.py
```

4. 결과 파일 `Customs_Integrated_Data.xlsx`가 **Commercial Invoice 엑셀 형식**으로 현재 폴더에 생성됩니다.

## 웹 UI로 INVOICE 업로드

PDF를 브라우저에서 업로드하고 분석할 수 있는 웹 인터페이스를 사용할 수 있습니다.

1. 의존성에 Flask 포함: `pip install -r requirements.txt`
2. 웹 서버 실행:

```bash
python app.py
```

3. 브라우저에서 **http://localhost:5000** 접속
4. **INVOICE** 또는 **원산지증명서(CO)** 탭을 선택한 뒤, PDF를 드래그 앤 드롭하거나 클릭하여 선택 후 **업로드** 버튼 클릭
5. 업로드된 파일이 `inputs/invoices`, `inputs/co` 폴더에 저장됩니다
6. **분석 실행 및 엑셀 다운로드** 버튼으로 추출·통합 후 **Commercial Invoice 형식**의 `Customs_Integrated_Data.xlsx`를 다운로드합니다.

## 추출 항목

- **인보이스**: Invoice No, Invoice Date, Order No, Product Code, Description, HTS No, Qty, Unit Price, Total
- **원산지 증명서**: Reference No, Origin Criterion, Invoice No, Tariff Item Number (HS Code)

두 서류는 **Invoice No**로 outer merge 되며, 수량·단가 등 숫자 컬럼은 float로 변환됩니다.

## 분석기 출력 형식

결과 엑셀은 **Commercial Invoice** 레이아웃(`customs_pdf_extractor.write_excel_commercial_invoice_format`)으로 저장됩니다.

- **1~2행**: Invoice No, Invoice Date
- **3~14행**: 빈 행 (Seller/Buyer 등 추후 입력 가능)
- **15행**: 테이블 헤더 (Order No., Product Code, Description, Gender, Brand Description, Product Category, Quality, HTS No., Country of Origin, Qty, UOM, Unit Price, Value Add Price, Gross Unit Price, Total, Manufacturer 등)
- **16행~**: 추출·merge된 데이터 행 (추출 컬럼이 위 헤더 순서에 맞게 매핑됨)
