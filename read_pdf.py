from pathlib import Path

from pypdf import PdfReader

in_folder = Path('in')

pdfs = sorted(in_folder.glob('*.pdf'))

pdf1 = pdfs[1]

reader = PdfReader(pdf1)
text = ''.join(page.extract_text() for page in reader.pages)

print(f"FILE: {pdf1.name}")
print(text)