# Invoice PDF → Excel

Extracts invoice fields from PDF files using an LLM, validates every extracted
field against the source document, and writes an Excel sheet.

## What it extracts

`bill_no`, `date`, `customer_name`, `total`

## Why the validation matters

LLM extraction is not guaranteed to be right. The failure mode that matters is
a **wrong number in an accountant's spreadsheet** — it surfaces days later,
during a reconciliation, and nobody knows which invoice caused it.

So each extracted field is checked against the source PDF text. `total` must
match a dollar amount on the page; `date` and `customer_name` must appear
verbatim; `bill_no` must match a whole line. If a check fails, the extraction
is retried up to 3 times. Only then is the row written, flagged with the reason.

The deterministic check is hard-coded — no LLM, no cost, and it cannot be wrong.
The retry is what LangGraph is for.

## Setup

    uv venv
    uv pip install --link-mode=copy -r requirements.txt

Copy `.env.example` to `.env` and add your key:

    GROQ_API_KEY=your_key_here

## Usage

    python graph.py                        # reads ./in
    python graph.py path\to\invoices       # reads any folder

Outputs to `out/`:

- `invoices.xlsx` — one row per invoice
- `result.json` — same data, machine-readable
- `graph.png`  — pipeline diagram

## How it works

    START → read_pdf → extract_fields → validate → finalize → END
                                       ↑          │
                                       └── retry ─┘  (max 3, back to extract_fields)

Built with LangGraph. Nodes are plain functions; `route()` decides whether a
failure retries or gets written out flagged.

Retry goes back to `extract_fields`, not `validate`. The validator is
deterministic — same text, same verdict — so retrying it would fail identically
forever. The retry exists to give the *model* another attempt.

## Project layout

    graph.py          LangGraph pipeline + CLI entry point
    fields.py         Pydantic schema + PDF text reader
    requirements.txt
    in/               input PDFs
    out/              generated results

The diagram in `out/graph.png` is regenerated on every run. After editing the
graph, rebuild it with:

    graph.get_graph().draw_mermaid_png(output_file_path=BASE / 'out' / 'graph.png')

## Limitations

- Scanned/image-only PDFs are not supported (no OCR)
- `bill_no` is matched against a whole line (optionally after `#`), which fits
  the sample layout — an invoice number rendered mid-sentence would be flagged
- One invoice per PDF

## Stack

Python · LangChain · LangGraph · Groq (`openai/gpt-oss-120b`) · pypdf · pandas
Two things in that README are doing real work, not decoration:
"Limitations" — listing what breaks makes the rest believable. A client who knows you flagged the scanned-PDF gap trusts your numbers. One who discovers it in production doesn't come back.
"Why the validation matters" — that's the paragraph that justifies your rate to them. Anyone can call an LLM. The part worth paying for is that a wrong number can't reach their books.