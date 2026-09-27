"""
Corporate ERP - Deluge Document & Syntax Injection Module
Enables Administrators to ingest custom Zoho Deluge code snippets, internal API guides,
and technical syntax into ChromaDB using adaptive semantic chunking and nomic-embed-text embeddings.
"""

import os
import time
import hashlib
import streamlit as st
import chromadb
from chromadb.utils import embedding_functions

import auth
from vector_setup import (
    adaptive_chunk_markdown_content,
    DEFAULT_CHROMA_DIR,
    DEFAULT_COLLECTION,
    DEFAULT_EMBED_MODEL,
    OLLAMA_URL,
    query_vector_db
)

# Enforce Administrator (Full Access) permission
auth.require_admin_permission()

st.title("💉 Document Injection Tool for Deluge Syntax")
st.caption("Ingest enterprise Deluge scripts, custom API schemas, and proprietary Creator workflows into the semantic vector store.")

# Information banner
st.info(
    "🧩 **Adaptive Semantic Pipeline:** Code blocks (` ```deluge `) and markdown tables are preserved intact without mid-syntax slicing. "
    "Vectors are generated locally using **`nomic-embed-text`** (768-dim) and persisted directly into ChromaDB."
)

st.markdown("---")

col_input, col_preview = st.columns([1.1, 0.9], gap="large")

SAMPLE_DELUGE_SNIPPET = """# Custom Deluge Webhook - External Payment Dispatcher
Source: https://internal.erp/deluge/payment-webhook

This function receives payload from an external payment gateway, verifies signature, and updates Zoho Creator records.

### Implementation Syntax
```deluge
paymentPayload = input.payload.toMap();
transactionId = paymentPayload.get("txn_id");
paidAmount = paymentPayload.get("amount").toDecimal();
customerEmail = paymentPayload.get("email");

// Query Creator Invoice records
matchingInvoices = Invoices[Transaction_Reference == transactionId];
if (matchingInvoices.count() > 0)
{
    invoiceRecord = matchingInvoices.get(0);
    invoiceRecord.Payment_Status = "Paid";
    invoiceRecord.Amount_Received = paidAmount;
    invoiceRecord.Settled_Time = zoho.currenttime;
    info "Successfully updated invoice record: " + invoiceRecord.ID;
}
else
{
    info "No matching invoice found for txn: " + transactionId;
}
```

### Response Codes
| Status Code | Description | Next Action |
|---|---|---|
| 200 | Transaction Verified | Update Creator Record |
| 400 | Invalid Payload Signature | Reject Webhook |
| 404 | Invoice Not Found | Flag for Accounting Review |
"""

with col_input:
    st.subheader("📝 Deluge Document Input")
    
    doc_title = st.text_input(
        "Document Title",
        value="Custom Deluge Webhook - External Payment Dispatcher",
        help="Human-readable title for citations and retrieval metadata."
    )
    
    c_meta1, c_meta2 = st.columns(2)
    with c_meta1:
        doc_category = st.selectbox(
            "Deluge Category",
            options=["Workflows & Functions", "Integration Tasks", "API Handlers", "Custom Widgets & JS", "Database Operations"],
            index=0
        )
    with c_meta2:
        source_url = st.text_input(
            "Source URL / Reference ID",
            value="https://internal.erp/deluge/payment-webhook",
            help="Canonical reference URL stored in vector chunk metadata."
        )

    doc_content = st.text_area(
        "Markdown & Deluge Syntax Content",
        value=SAMPLE_DELUGE_SNIPPET,
        height=380,
        help="Include standard markdown with ```deluge code blocks and tables."
    )

    c_btn1, c_btn2 = st.columns([1, 1])
    with c_btn1:
        chunk_target_size = st.slider("Target Chunk Size (chars)", min_value=300, max_value=2000, value=800, step=100)
    with c_btn2:
        chunk_overlap = st.slider("Chunk Overlap (chars)", min_value=50, max_value=300, value=150, step=25)

# Generate live adaptive chunks
preview_chunks = []
if doc_content.strip():
    raw_blocks = adaptive_chunk_markdown_content(
        body=doc_content.strip(),
        target_size=chunk_target_size,
        max_size=int(chunk_target_size * 1.5),
        overlap=chunk_overlap
    )
    header_ctx = f"# {doc_title}\nSource: {source_url}\nCategory: {doc_category}\n\n"
    for idx, b in enumerate(raw_blocks):
        full_text = header_ctx + b["text"]
        c_hash = hashlib.sha256(full_text.encode("utf-8")).hexdigest()
        preview_chunks.append({
            "sub_index": idx,
            "text": full_text,
            "content_type": b["content_type"],
            "char_count": len(full_text),
            "hash": c_hash[:12]
        })

with col_preview:
    st.subheader(f"🧩 Semantic Slicing Preview ({len(preview_chunks)} Chunks)")
    
    if not preview_chunks:
        st.warning("Enter Deluge content on the left to preview adaptive segmentation.")
    else:
        # Metrics summary
        p1, p2, p3 = st.columns(3)
        code_count = sum(1 for c in preview_chunks if c["content_type"] == "code")
        table_count = sum(1 for c in preview_chunks if c["content_type"] == "table")
        text_count = sum(1 for c in preview_chunks if c["content_type"] == "text")
        
        p1.metric("Code Chunks", code_count)
        p2.metric("Table Chunks", table_count)
        p3.metric("Text Chunks", text_count)

        with st.container(height=420):
            for c in preview_chunks:
                type_color = "#10b981" if c["content_type"] == "code" else ("#6366f1" if c["content_type"] == "table" else "#64748b")
                st.markdown(
                    f"<div style='border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; margin-bottom: 10px;'>"
                    f"<b>Chunk #{c['sub_index'] + 1}</b> • "
                    f"<span style='background: {type_color}22; color: {type_color}; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-size: 0.8rem;'>{c['content_type'].upper()}</span> • "
                    f"<span style='color: #64748b; font-size: 0.85rem;'>{c['char_count']} chars (Hash: <code>{c['hash']}</code>)</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                with st.expander(f"Inspect Chunk #{c['sub_index'] + 1} Text"):
                    st.code(c["text"], language="markdown")

st.markdown("---")

# Injection Action Section
c_act1, c_act2 = st.columns([1.5, 2])

with c_act1:
    inject_btn = st.button("🚀 Ingest Document into ChromaDB Vector Store", type="primary", use_container_width=True)

if inject_btn:
    if not preview_chunks:
        st.error("No chunks available for injection. Please enter valid content.")
    else:
        with st.spinner("Generating 768-dim embeddings with nomic-embed-text & updating ChromaDB..."):
            try:
                t0 = time.time()
                embed_fn = embedding_functions.OllamaEmbeddingFunction(
                    url=OLLAMA_URL,
                    model_name=DEFAULT_EMBED_MODEL
                )
                client = chromadb.PersistentClient(path=DEFAULT_CHROMA_DIR)
                collection = client.get_or_create_collection(
                    name=DEFAULT_COLLECTION,
                    embedding_function=embed_fn
                )

                # Generate clean unique chunk IDs
                current_total = collection.count()
                ids = [f"custom_{int(time.time())}_{i:03d}" for i in range(len(preview_chunks))]
                docs = [c["text"] for c in preview_chunks]
                metas = [
                    {
                        "title": doc_title[:100],
                        "source_url": source_url,
                        "category": doc_category,
                        "content_type": c["content_type"],
                        "char_count": c["char_count"],
                        "injected_by": auth.get_current_user().get("name", "Admin"),
                        "injected_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    for c in preview_chunks
                ]

                collection.upsert(ids=ids, documents=docs, metadatas=metas)
                duration = round(time.time() - t0, 2)
                
                st.success(f"✅ Ingestion successful! Stored {len(preview_chunks)} chunks in {duration}s.")
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Injected Chunks", len(preview_chunks))
                m2.metric("ChromaDB Total", f"{collection.count():,}")
                m3.metric("Latency", f"{duration}s")

            except Exception as e:
                st.error(f"Error during vector injection: {e}")

# Verification Query Tool
st.markdown("#### 🔎 Immediate Retrieval Verification")
st.caption("Verify that your newly injected Deluge syntax is retrieved with high relevance.")

test_q = st.text_input("Test Query", value="How to handle webhook payment status in Deluge?", placeholder="Enter prompt to test retrieval...")
if st.button("⚡ Test Semantic Vector Search"):
    if test_q.strip():
        with st.spinner("Querying vector database..."):
            results = query_vector_db(query_text=test_q.strip(), top_k=2)
            if results:
                for idx, r in enumerate(results, start=1):
                    meta = r.get("metadata", {})
                    dist = r.get("distance")
                    st.markdown(f"**Match #{idx}:** `{meta.get('title')}` (URL: {meta.get('source_url')})")
                    if dist is not None:
                        st.caption(f"Vector Distance: `{dist:.4f}`")
                    st.code(r.get("document", ""), language="markdown")
            else:
                st.info("No matching records retrieved.")
