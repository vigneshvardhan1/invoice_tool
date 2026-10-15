import json
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent

results = BASE / 'out' / 'result.json'
excel = BASE / 'out' / 'invoices.xlsx'

rows = json.load(open(results, encoding = 'utf-8'))



columns = ['file', 'customer_name', 'bill_no', 'date', 'total', 'error']

df = pd.DataFrame(rows, columns = columns)
df.to_excel(excel , index = False)

print("Excel file created at")
print(df.to_string(index = False))