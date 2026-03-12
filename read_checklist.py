# -*- coding: utf-8 -*-
import pandas as pd
import sys
import os

os.chdir(r'c:\Projects\test')
path = r'c:\Users\alstn\OneDrive\바탕 화면\사전진단체크리스트.xlsx'
if not os.path.isfile(path):
    # try copied path
    for f in os.listdir('.'):
        if '체크리스트' in f or 'checklist' in f.lower():
            path = f
            break
    else:
        path = None
if path and os.path.isfile(path):
    xl = pd.ExcelFile(path)
    print('Sheets:', xl.sheet_names)
    for name in xl.sheet_names:
        df = pd.read_excel(path, sheet_name=name, header=None)
        print('\n--- Sheet:', name, '---')
        print(df.to_string())
else:
    print('File not found')
    sys.exit(1)
