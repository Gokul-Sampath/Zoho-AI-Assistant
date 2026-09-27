"""
Corporate ERP - Settings and Admin Panel
Consolidates Advanced Configuration Tools, CMD-Equivalent CLI Commands,
Model Management Settings (Llama 3 Optimization), and Deluge Document Injection.
"""

import os
import sys
import time
import subprocess
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

def get_model_dimension(model_name: str) -> int:
    clean = model_name.split(":")[0].strip().lower()
    return 768 if "nomic" in clean else (1024 if "large" in clean else 384)

def get_collection_dimension(client: chromadb.PersistentClient, collection_name: str):
    try:
        col = client.get_collection(name=collection_name)
        if col.count() > 0:
            sample = col.peek(1)
            embs = sample.get("embeddings")
            if embs is not None and len(embs) > 0:
                return len(embs[0])
    except Exception:
        pass
    return None

# Enforce Administrator (Full Access) permission
auth.require_admin_permission()

current_user = auth.get_current_user() or {}

# Header
st.title("⚙️ Settings & Administration Panel")
st.caption(f"Enterprise System Orchestration • Operator: **{current_user.get('name')}** ({current_user.get('badge')})")

st.markdown("---")

# Main Navigation Tabs
tab_models, tab_cmd, tab_config, tab_injection = st.tabs([
    "🧠 Model Management & Llama 3",
    "💻 CMD-Equivalent Commands & Terminal",
    "🛠️ Advanced Vector & Chunking Config",
    "💉 Deluge Document & Syntax Injection"
])


# ==============================================================================
# TAB 1: MODEL MANAGEMENT & LLAMA 3 OPTIMIZATION
# ==============================================================================
with tab_models:
    st.subheader("Ollama & Llama 3 Runtime Optimization")
    st.caption("Fine-tune inference parameters, sampling bounds, and memory context for Deluge code generation.")

    # Status Cards
    import ollama
    installed_models = []
    ollama_ok = False
    try:
        m_list = ollama.list()
        installed_models = [m.model for m in m_list.models]
        ollama_ok = True
    except Exception:
        pass

    m_c1, m_c2, m_c3, m_c4 = st.columns(4)
    m_c1.metric("Ollama Service", "Online" if ollama_ok else "Offline", delta="Local 11434" if ollama_ok else "Error")
    m_c2.metric("Active LLM", st.session_state.llama3_params.get("selected_model", "llama3:8b"))
    m_c3.metric("Context Window", f"{st.session_state.llama3_params.get('context_window', 4096):,} tokens")
    m_c4.metric("Inference Temp", str(st.session_state.llama3_params.get("temperature", 0.2)))

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    col_llm_cfg, col_telemetry = st.columns([1.2, 1], gap="large")

    with col_llm_cfg:
        st.markdown("##### 🎛️ Inference Hyperparameters")
        
        c_sel1, c_sel2 = st.columns(2)
        with c_sel1:
            opts = installed_models if installed_models else ["llama3:8b", "llama3:latest", "llama3"]
            cur_mod = st.session_state.llama3_params.get("selected_model", "llama3:8b")
            idx = opts.index(cur_mod) if cur_mod in opts else 0
            new_model = st.selectbox("LLM Model Name", options=opts, index=idx)

        with c_sel2:
            new_ctx = st.select_slider(
                "Context Window (num_ctx)",
                options=[2048, 4096, 8192, 16384],
                value=int(st.session_state.llama3_params.get("context_window", 4096)),
                help="Max tokens in working memory. 4096 is optimized for Llama 3 8B low-latency responses."
            )

        c_sl1, c_sl2 = st.columns(2)
        with c_sl1:
            new_temp = st.slider(
                "Temperature (Precision)",
                min_value=0.0,
                max_value=1.0,
                value=float(st.session_state.llama3_params.get("temperature", 0.2)),
                step=0.05,
                help="Low temperature (0.1 - 0.25) prevents hallucinations and ensures rigid Deluge syntax."
            )
            new_top_p = st.slider(
                "Top-P (Nucleus Sampling)",
                min_value=0.1,
                max_value=1.0,
                value=float(st.session_state.llama3_params.get("top_p", 0.9)),
                step=0.05
            )

        with c_sl2:
            new_rep = st.slider(
                "Repetition Penalty",
                min_value=1.0,
                max_value=1.5,
                value=float(st.session_state.llama3_params.get("repeat_penalty", 1.15)),
                step=0.05,
                help="Penalizes repetitive loops in generated code."
            )
            new_predict = st.slider(
                "Max Tokens (num_predict)",
                min_value=512,
                max_value=4096,
                value=int(st.session_state.llama3_params.get("num_predict", 2048)),
                step=256
            )

        if st.button("💾 Save & Apply Llama 3 Settings", type="primary", use_container_width=True):
            st.session_state.llama3_params = {
                "temperature": new_temp,
                "top_p": new_top_p,
                "context_window": new_ctx,
                "repeat_penalty": new_rep,
                "num_predict": new_predict,
                "selected_model": new_model
            }
            st.success("✅ Model parameters updated successfully!")

    with col_telemetry:
        st.markdown("##### ⚡ Latency & Hardware Benchmark")
        with st.container(border=True):
            st.markdown("""
            * **Architecture:** Llama-3-8B-Instruct (4-bit Q4_0)
            * **Embedding Engine:** `nomic-embed-text` (768-dim)
            * **Vector Database:** ChromaDB Persistent Client
            * **Data Egress:** 0% (Fully Offline & Local)
            """)

            if st.button("⏱️ Run Model Latency Test", use_container_width=True):
                with st.spinner("Executing inference benchmark on local Llama 3..."):
                    t0 = time.time()
                    try:
                        res = ollama.chat(
                            model=st.session_state.llama3_params.get("selected_model", "llama3"),
                            messages=[{"role": "user", "content": "Return single-line Deluge: info 'ERP Benchmark';"}],
                            options={"temperature": 0.2, "num_predict": 64}
                        )
                        latency_ms = round((time.time() - t0) * 1000, 1)
                        st.success(f"Benchmark Complete: **{latency_ms} ms** latency")
                        st.code(res["message"]["content"], language="deluge")
                    except Exception as e:
                        st.error(f"Benchmark error: {e}")


# ==============================================================================
# TAB 2: CMD-EQUIVALENT COMMANDS & INTERACTIVE TERMINAL RUNNER
# ==============================================================================
with tab_cmd:
    st.subheader("💻 Command-Line Interface (CMD) Orchestrator")
    st.caption("Execute terminal operations directly from the ERP console with live execution output.")

    # Command Presets Grid
    st.markdown("##### Quick-Run Command Catalog")
    
    col_c1, col_c2 = st.columns(2)

    with col_c1:
        with st.container(border=True):
            st.markdown("###### 🔄 Delta Vector Synchronization")
            st.caption("Compares local documentation files against ChromaDB and embeds only changed sections.")
            st.code("python vector_setup.py --sync", language="powershell")
            if st.button("▶️ Execute Delta Sync", key="cmd_sync", use_container_width=True):
                st.session_state.active_cmd = "python vector_setup.py --sync"

        with st.container(border=True):
            st.markdown("###### 🔍 Dry-Run Differential Inspection")
            st.caption("Previews documentation diffs and change counts without writing to ChromaDB.")
            st.code("python vector_setup.py --sync --dry-run", language="powershell")
            if st.button("▶️ Run Dry-Run Preview", key="cmd_dry", use_container_width=True):
                st.session_state.active_cmd = "python vector_setup.py --sync --dry-run"

    with col_c2:
        with st.container(border=True):
            st.markdown("###### 🕷️ Execute Documentation Scraper")
            st.caption("Triggers headless Crawl4AI to fetch all canonical Deluge documentation pages.")
            st.code("python crawl_zoho_docs.py", language="powershell")
            if st.button("▶️ Launch Crawler Script", key="cmd_crawl", use_container_width=True):
                st.session_state.active_cmd = "python crawl_zoho_docs.py"

        with st.container(border=True):
            st.markdown("###### 📦 Standalone PyInstaller Compilation")
            st.caption("Packages the application, Python runtime, and Streamlit assets into an executable.")
            st.code("python build_executable.py --dry-run", language="powershell")
            if st.button("▶️ Test PyInstaller Build", key="cmd_build", use_container_width=True):
                st.session_state.active_cmd = "python build_executable.py --dry-run"

    st.markdown("---")
    
    # Interactive Console Runner
    st.markdown("##### 🖥️ Interactive Console Runner")
    st.caption("Select a pre-configured command or enter a custom python instruction to execute.")

    selected_cmd_input = st.text_input(
        "Command to Execute",
        value=st.session_state.get("active_cmd", "python vector_setup.py --sync --dry-run --limit 10"),
        help="Command will be run in the local workspace directory."
    )

    c_run1, c_run2 = st.columns([1, 4])
    with c_run1:
        execute_trigger = st.button("⚡ Run Command", type="primary", use_container_width=True)

    if execute_trigger and selected_cmd_input.strip():
        with st.spinner(f"Executing `{selected_cmd_input}`..."):
            t_cmd_start = time.time()
            try:
                proc = subprocess.run(
                    selected_cmd_input,
                    shell=True,
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=180
                )
                duration = round(time.time() - t_cmd_start, 2)
                
                if proc.returncode == 0:
                    st.success(f"✅ Command completed successfully in {duration}s (Exit Code: 0)")
                else:
                    st.error(f"❌ Command exited with error code {proc.returncode} in {duration}s")

                st.markdown("**Console Output (stdout):**")
                st.code(proc.stdout if proc.stdout else "[No output emitted on stdout]", language="text")
                
                if proc.stderr:
                    st.markdown("**Error Stream (stderr):**")
                    st.code(proc.stderr, language="text")

            except subprocess.TimeoutExpired:
                st.error("Command timed out after 180 seconds.")
            except Exception as e:
                st.error(f"Execution failed: {e}")


# ==============================================================================
# TAB 3: ADVANCED VECTOR & CHUNKING CONFIGURATION
# ==============================================================================
with tab_config:
    st.subheader("🛠️ Vector Store & Chunking Architecture")
    st.caption("Manage ChromaDB collections, verify embedding dimensions, and configure adaptive chunking thresholds.")

    # Read Collection Dimensions
    client = chromadb.PersistentClient(path=DEFAULT_CHROMA_DIR)
    current_dim = get_collection_dimension(client, DEFAULT_COLLECTION)
    expected_dim = get_model_dimension(DEFAULT_EMBED_MODEL)

    col_v1, col_v2 = st.columns(2, gap="large")

    with col_v1:
        st.markdown("##### ChromaDB Collection Status")
        with st.container(border=True):
            st.markdown(f"• **Collection Name:** `{DEFAULT_COLLECTION}`")
            st.markdown(f"• **Persistent Path:** `{DEFAULT_CHROMA_DIR}`")
            st.markdown(f"• **Active Model:** `{DEFAULT_EMBED_MODEL}`")
            st.markdown(f"• **Target Dimension:** `{expected_dim}` dimensions")
            st.markdown(f"• **Stored Dimension:** `{current_dim if current_dim else 'Uninitialized'}` dimensions")

            try:
                col_obj = client.get_collection(name=DEFAULT_COLLECTION)
                count = col_obj.count()
                st.markdown(f"• **Total Indexed Chunks:** `{count:,}` records")
            except Exception:
                st.markdown("• **Total Indexed Chunks:** `0` records")

        st.markdown("##### Collection Maintenance")
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            if st.button("🗑️ Reset & Re-create Collection", use_container_width=True):
                try:
                    client.delete_collection(name=DEFAULT_COLLECTION)
                    st.success(f"Collection '{DEFAULT_COLLECTION}' reset.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Reset error: {e}")

        with c_p2:
            if st.button("🧹 Vacuum Cache", use_container_width=True):
                st.cache_data.clear()
                st.success("Application memory cache cleared.")

    with col_v2:
        st.markdown("##### Adaptive Semantic Chunking Rules")
        with st.container(border=True):
            st.markdown("""
            * **Code Block Isolation:** Multi-line Deluge code snippets (` ```deluge...``` `) are detected and kept intact. They are never sliced in the middle.
            * **Markdown Table Integrity:** Parameter tables (`| Parameter | Type | ... |`) are preserved without row fragmentation.
            * **Heading Boundaries:** `#`, `##`, `###` headings serve as semantic boundary breakpoints.
            * **Target Chunk Size:** `1,000` characters (Target) • `1,600` characters (Ceiling).
            * **Overlap Buffer:** `150` characters.
            """)

        st.markdown("##### Quick Vector Search Diagnostics")
        diag_query = st.text_input("Semantic Query Test", value="How to send email in Zoho Deluge")
        if st.button("🔎 Test Vector Retrieval", use_container_width=True):
            results = query_vector_db(query_text=diag_query, top_k=2)
            if results:
                for idx, r in enumerate(results, 1):
                    meta = r.get("metadata", {})
                    st.markdown(f"**Result #{idx}:** `{meta.get('title')}` (URL: {meta.get('source_url')})")
                    st.code(r.get("document", "")[:300] + "...", language="markdown")
            else:
                st.warning("No matches returned.")


# ==============================================================================
# TAB 4: DELUGE DOCUMENT & SYNTAX INJECTION
# ==============================================================================
with tab_injection:
    st.subheader("💉 Deluge Document & Syntax Injection Tool")
    st.caption("Ingest enterprise Deluge code snippets, custom API schemas, or internal workflows into ChromaDB.")

    col_inj_in, col_inj_prev = st.columns([1.1, 0.9], gap="large")

    SAMPLE_SNIPPET = """# Custom Deluge Webhook - External Payment Dispatcher
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

    with col_inj_in:
        inj_title = st.text_input("Document Title", value="Custom Deluge Webhook - External Payment Dispatcher")
        
        c_i1, c_i2 = st.columns(2)
        with c_i1:
            inj_cat = st.selectbox(
                "Category",
                options=["Workflows & Functions", "Integration Tasks", "API Handlers", "Custom Widgets & JS", "Database Operations"]
            )
        with c_i2:
            inj_url = st.text_input("Canonical Reference URL", value="https://internal.erp/deluge/payment-webhook")

        inj_body = st.text_area("Markdown & Deluge Syntax Content", value=SAMPLE_SNIPPET, height=300)
        inj_target_size = st.slider("Target Chunk Size", min_value=300, max_value=2000, value=800, step=100)

    # Adaptive chunk preview
    inj_chunks = []
    if inj_body.strip():
        raw_b = adaptive_chunk_markdown_content(body=inj_body.strip(), target_size=inj_target_size, max_size=int(inj_target_size * 1.5))
        h_ctx = f"# {inj_title}\nSource: {inj_url}\nCategory: {inj_cat}\n\n"
        for idx, b in enumerate(raw_b):
            full_t = h_ctx + b["text"]
            inj_chunks.append({
                "sub_index": idx,
                "text": full_t,
                "content_type": b["content_type"],
                "char_count": len(full_t)
            })

    with col_inj_prev:
        st.markdown(f"##### 🧩 Chunking Preview ({len(inj_chunks)} Chunks)")
        if inj_chunks:
            p1, p2, p3 = st.columns(3)
            p1.metric("Code", sum(1 for c in inj_chunks if c["content_type"] == "code"))
            p2.metric("Table", sum(1 for c in inj_chunks if c["content_type"] == "table"))
            p3.metric("Text", sum(1 for c in inj_chunks if c["content_type"] == "text"))

            with st.container(height=360):
                for c in inj_chunks:
                    st.markdown(f"**Chunk #{c['sub_index'] + 1}** ({c['content_type'].upper()} • {c['char_count']} chars)")
                    st.code(c["text"], language="markdown")

    if st.button("🚀 Ingest Document into ChromaDB Vector Store", type="primary", use_container_width=True):
        if not inj_chunks:
            st.error("No chunks available to ingest.")
        else:
            with st.spinner("Generating embeddings and upserting into ChromaDB..."):
                try:
                    embed_fn = embedding_functions.OllamaEmbeddingFunction(
                        url=OLLAMA_URL,
                        model_name=DEFAULT_EMBED_MODEL
                    )
                    c_client = chromadb.PersistentClient(path=DEFAULT_CHROMA_DIR)
                    c_col = c_client.get_or_create_collection(name=DEFAULT_COLLECTION, embedding_function=embed_fn)

                    ids = [f"custom_{int(time.time())}_{i:03d}" for i in range(len(inj_chunks))]
                    docs = [c["text"] for c in inj_chunks]
                    metas = [
                        {
                            "title": inj_title[:100],
                            "source_url": inj_url,
                            "category": inj_cat,
                            "content_type": c["content_type"],
                            "char_count": c["char_count"],
                            "injected_by": current_user.get("name", "Admin"),
                            "injected_at": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        for c in inj_chunks
                    ]

                    c_col.upsert(ids=ids, documents=docs, metadatas=metas)
                    st.success(f"✅ Ingestion successful! Stored {len(inj_chunks)} chunks in ChromaDB.")
                except Exception as e:
                    st.error(f"Ingestion error: {e}")
