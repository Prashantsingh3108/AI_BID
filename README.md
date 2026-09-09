# BidGuard AI

GenAI-powered Tender & Bid Compliance Platform.

## Features

- Upload tender PDF/Excel
- Upload bidder documents
- Extract tender requirements with Groq
- Extract bidder evidence with Groq
- Compare requirements with evidence
- Compliance statuses:
  - COMPLIANT
  - PARTIAL
  - NON-COMPLIANT
  - MISSING
- Compliance score
- Bid recommendation
- Tender Q&A using lightweight retrieval
- Downloadable PDF report

## Local setup

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install:

```bash
pip install -r requirements.txt
```

Create `.env` from `.env.example` and add your Groq API key.

Run:

```bash
streamlit run app.py
```

## Streamlit Cloud deployment

1. Push the project to GitHub.
2. Open Streamlit Community Cloud.
3. Select the GitHub repository.
4. Set the main file to `app.py`.
5. In App Settings -> Secrets, add:

```toml
GROQ_API_KEY = "your_key_here"
GROQ_MODEL = "llama-3.3-70b-versatile"
```

6. Deploy.

Do not commit `.env` or API keys to GitHub.

## Architecture

Tender/Bidder documents
-> parser
-> Groq requirement/evidence extraction
-> compliance engine
-> score
-> recommendation
-> PDF report

Tender Q&A:
Tender
-> local TF-IDF retrieval
-> relevant chunks
-> Groq
-> answer

## Production upgrades

- OCR for scanned PDFs
- semantic embeddings + FAISS/Qdrant
- database for users/bids
- document page/line citations
- deterministic numeric/date rules
- authentication
- background processing for large tenders
- audit logs
