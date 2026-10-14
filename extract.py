import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from pypdf import PdfReader

from fields import Fields

load_dotenv()

in_folder = Path('in')

pdfs = sorted(in_folder.glob('*.pdf'))
pdf1 = pdfs[0]

reader =  PdfReader(pdf1)
text = ''.join( page.extract_text() or '' for page in reader.pages)

model = init_chat_model(
    model = 'openai/gpt-oss-120b',
    api_key=os.getenv("GROQ_API_KEY"),
    model_provider = 'groq'

)

prompt =  f"""Extract invoice fields from this bill text.

Return exactly these fields:
- bill_no: the invoice number (the # near the top)
- date: the bill date
- customer_name: the person or company the bill is for
- total: the grand total amount as a number, no currency symbol, no commas

Bill text:
{text}
"""

response = model.with_structured_output(Fields).invoke(prompt)

print("FILENAME:", pdf1.name)
print(response)