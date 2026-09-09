import json
import streamlit as st

from agents.agent import BidComplianceAgent
from utils.document_parser import extract_uploaded_file
from rag.retriever import TenderRetriever
from reports.report_generator import generate_pdf_report


st.set_page_config(
    page_title="BidGuard AI",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 BidGuard AI")
st.caption("GenAI-powered Tender & Bid Compliance Platform")

with st.sidebar:
    st.header("Configuration")
    st.info(
        "Upload a tender and bidder documents. "
        "The AI extracts requirements, matches evidence, "
        "and produces a compliance report."
    )

    if st.button("Clear session"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


@st.cache_resource
def get_agent():
    return BidComplianceAgent()


agent = get_agent()

tab1, tab2 = st.tabs(["📋 Bid Analysis", "💬 Tender Q&A"])

with tab1:
    st.subheader("1. Upload Tender")
    tender_file = st.file_uploader(
        "Tender/NIT PDF or Excel",
        type=["pdf", "xlsx", "xls"],
        key="tender",
    )

    st.subheader("2. Upload Bidder Documents")
    bidder_files = st.file_uploader(
        "Upload company documents",
        type=["pdf", "xlsx", "xls", "txt"],
        accept_multiple_files=True,
        key="bidder",
    )

    if st.button("🚀 Analyze Bid", type="primary", use_container_width=True):
        if not tender_file:
            st.error("Please upload a tender document.")
            st.stop()

        if not bidder_files:
            st.warning(
                "Upload bidder documents for a real compliance comparison. "
                "You can still use the Tender Q&A tab."
            )
            st.stop()

        with st.spinner("Reading documents and analyzing compliance..."):
            tender_text = extract_uploaded_file(tender_file)

            bidder_text_parts = []
            for uploaded in bidder_files:
                text = extract_uploaded_file(uploaded)
                bidder_text_parts.append(
                    f"\n--- DOCUMENT: {uploaded.name} ---\n{text}"
                )

            bidder_text = "\n".join(bidder_text_parts)

            result = agent.analyze_bid(
                tender_text=tender_text,
                bidder_documents_text=bidder_text,
            )

            st.session_state["result"] = result
            st.session_state["tender_text"] = tender_text
            st.session_state["retriever"] = TenderRetriever(tender_text)

    result = st.session_state.get("result")

    if result:
        score = result["score"]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Compliance Score", f'{score["score"]}%')
        c2.metric("Compliant", score["compliant"])
        c3.metric("Partial", score["partial"])
        c4.metric("Missing / Failed", score["missing"] + score["non_compliant"])

        recommendation = score["recommendation"]
        if recommendation == "RECOMMENDED TO BID":
            st.success(f"### 🟢 {recommendation}")
        elif recommendation == "DO NOT BID":
            st.error(f"### 🔴 {recommendation}")
        else:
            st.warning(f"### 🟡 {recommendation}")

        st.subheader("Requirement-by-Requirement Analysis")

        rows = result["compliance"].get("compliance_results", [])
        for row in rows:
            status = row.get("status", "UNKNOWN")
            icon = {
                "COMPLIANT": "🟢",
                "PARTIAL": "🟡",
                "NON-COMPLIANT": "🔴",
                "MISSING": "⚪",
            }.get(status, "⚠️")

            with st.expander(
                f'{icon} {row.get("requirement_id", "")} — '
                f'{row.get("requirement", "")}'
            ):
                st.write(f'**Status:** {status}')
                st.write(f'**Evidence:** {row.get("evidence", "")}')
                st.write(
                    f'**Missing information:** '
                    f'{row.get("missing_information", "")}'
                )
                st.write(f'**Explanation:** {row.get("explanation", "")}')
                st.write(f'**Risk:** {row.get("risk", "")}')
                st.write(f'**Confidence:** {row.get("confidence", 0)}%')

        st.subheader("🤖 AI Recommendation")
        st.write(result["recommendation"])

        report_bytes = generate_pdf_report(result)
        st.download_button(
            "📄 Download Compliance Report",
            data=report_bytes,
            file_name="bid_compliance_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

with tab2:
    st.subheader("Ask the Tender")
    question = st.text_input(
        "Example: What documents are required for technical eligibility?"
    )

    if question:
        tender_text = st.session_state.get("tender_text")

        if not tender_text:
            st.info("Upload and analyze a tender first.")
        else:
            retriever = st.session_state.get("retriever")
            context = retriever.retrieve(question, top_k=5)

            with st.spinner("Searching tender and generating answer..."):
                answer = agent.ask(question, context)

            st.markdown("### Answer")
            st.write(answer)

            with st.expander("Retrieved tender context"):
                st.text(context)
