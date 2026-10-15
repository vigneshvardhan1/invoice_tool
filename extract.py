import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from pypdf import PdfReader

from fields import Fields, reader_pdf

load_dotenv()

in_folder = Path(__file__).parent / 'in'

pdfs = sorted(in_folder.glob('*.pdf'))

model = init_chat_model(
    model = 'openai/gpt-oss-120b',
    api_key=os.getenv("GROQ_API_KEY"),
model_provider = 'groq'

)
prompt =  """Extract invoice fields from this bill text.

Return exactly these fields:
- bill_no: the invoice number (the # near the top)
- date: the bill date
- customer_name: the person or company the bill is for
- total: the grand total amount as a number, no currency symbol, no commas

Bill text:
{text}
"""

results = []
for pdf in pdfs :
    try:
        reader =  PdfReader(pdf)
        response = reader_pdf(reader)
        result = model.with_structured_output(Fields).invoke(prompt.format(text = response))
        results.append({'file':pdf.name , **result.model_dump()})
    except Exception as e:
        results.append({"file": pdf.name, "error": str(e)})


out = Path(__file__).parent / 'out'

with open(out /'result.json' , 'w',encoding = 'utf-8') as f:
    json.dump(results, f, indent = 2)