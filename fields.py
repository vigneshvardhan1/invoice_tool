from pydantic import BaseModel, Field


class Fields(BaseModel):
    customer_name : str = Field( description="Person or company the invoice is billed to. From the 'Bill To' section.")
    bill_no: str = Field(
        description="Invoice number, printed after '#' near the top. Digits only."
    )
    date: str = Field(
        description="Invoice date exactly as printed, e.g. 'May 03 2012'."
    )
    total: float = Field(
        description="Grand total amount due. Digits only, no currency symbol, no commas."
    )

def reader_pdf(reader):
    text = ''.join('' or page.extract_text() for page in reader.pages)
    return text