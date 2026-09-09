import io
from typing import Any

import pandas as pd
from pypdf import PdfReader


def extract_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []

    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(f"\n--- PAGE {i} ---\n{text}")

    return "\n".join(pages).strip()


def extract_excel(file_bytes: bytes) -> str:
    workbook = pd.ExcelFile(io.BytesIO(file_bytes))
    sections = []

    for sheet in workbook.sheet_names:
        df = workbook.parse(sheet)
        sections.append(f"\n--- SHEET: {sheet} ---\n")
        sections.append(df.fillna("").to_csv(index=False))

    return "\n".join(sections).strip()


def extract_uploaded_file(uploaded_file: Any) -> str:
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()

    if name.endswith(".pdf"):
        return extract_pdf(data)

    if name.endswith((".xlsx", ".xls")):
        return extract_excel(data)

    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore")

    raise ValueError(f"Unsupported file type: {uploaded_file.name}")
