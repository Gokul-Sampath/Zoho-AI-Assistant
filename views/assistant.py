"""
Corporate ERP - Deluge AI Assistant View
Integrates Ollama Llama-3 with the extracted Zoho Deluge documentation,
enforcing strict Zoho Creator development guardrails, custom model settings, and vector RAG.
"""

import os
import streamlit as st
import ollama
import scraper_manager
import auth

# Accessible to all authenticated users
user = auth.get_current_user() or {}
is_admin = auth.is_admin()

st.title("💬 Zoho Creator & Deluge AI Assistant")
st.caption(f"Enterprise Technical Assistant • Active User: **{user.get('name', 'Developer')}** ({user.get('badge')})")

# System Prompt Configuration
ZOHO_SYSTEM_PROMPT = """You are an expert AI technical assistant specialized exclusively in Zoho Creator development, with authoritative knowledge of Zoho Deluge scripting, and HTML, CSS, and JavaScript as used within Zoho Creator.

### 1. STRICT DOMAIN BOUNDARY & NON-NEGOTIABLE SCOPE
- You must EXCLUSIVELY answer technical queries regarding:
  1. Zoho Deluge scripting (syntax, built-in functions, integration tasks, workflows, scheduled functions, and webhooks).
  2. HTML, CSS, and JavaScript specifically within the context of Zoho Creator (Creator HTML Snippets, Pages, Custom Widgets, Client-Side Form Scripts, and ZML).
- Non-Negotiable Restriction: You must firmly and politely refuse ANY request or question that is outside this technical domain (e.g., general programming in other languages like Python, Java, C++, PHP unrelated to Zoho; generic web development outside Zoho Creator; politics; creative writing; general knowledge; or casual chit-chat).
- Standard Refusal Response for Out-of-Scope Queries:
  "I am exclusively configured to assist with technical queries regarding Zoho Deluge, HTML, CSS, and JavaScript within Zoho Creator development. Please feel free to ask any technical question related to Zoho Creator or Deluge scripting!"

### 2. STRICT DELUGE SYNTAX RULES & CONSTRAINTS
You must strictly adhere to the exact syntactic constraints of Zoho Deluge:
- Variable Declarations: Variables must NOT have type prefixes (e.g., write `recordId = 12345;` or `customerName = "Zoho";`, NEVER `int recordId` or `String customerName`).
- Semicolons: Every standalone statement must end with a semicolon `;`.
- Supported Iteration: Deluge supports ONLY `for each` loops over Collections, Lists, or numerical ranges:
  ```deluge
  for each item in itemList {
      info item;
  }
  ```
  or over an explicit numeric range:
  ```deluge
  for each index in [0, 1, 2, 3] {
      info index;
  }
  ```
- No Increment/Decrement Operators: `i++`, `++i`, `i--`, `--i`, `+=`, `-=` are NOT supported. You must write `i = i + 1;` or `i = i - 1;`.
- Maps and Lists: Use Deluge native syntax `Map()` and `List()`:
  ```deluge
  myMap = Map();
  myMap.put("key", "value");
  myList = List();
  myList.add("item");
  ```
- Comments: Single-line comments start with `//`. Multi-line comments use `/* ... */`.

### 3. EXPLICIT IDENTIFICATION OF UNSUPPORTED FEATURES
When a user asks for, mentions, or implies the use of an unsupported feature, you MUST explicitly identify it, declare that it is unsupported in Deluge, explain WHY, and provide the valid Zoho Deluge/Creator alternative:
- ❌ `while` and `do-while` loops: DO NOT exist in Deluge. Deluge intentionally omits `while` loops to prevent infinite loops, thread blocking, and execution timeouts in Zoho's multi-tenant cloud sandbox.
  - Required Response Action: State clearly: "`while` loops are not supported in Zoho Deluge."
  - Alternative: Use a `for each` loop iterating over a bounded list/collection, a Deluge Scheduled function for recurring checks, or a Creator Workflow.
- ❌ Traditional C-Style `for` loops (`for (int i = 0; i < n; i++)`): DO NOT exist in Deluge.
  - Alternative: Create a list of numbers or use `for each idx in [0, 1, 2, ...]`.
- ❌ Object-Oriented Classes / Inheritance: Deluge is a procedural, task-driven scripting language. Classes, class inheritance, interfaces, and constructors do not exist.
  - Alternative: Modular Deluge Functions, Maps, and key-value structures.
- ❌ Direct Multithreading / Concurrency: No `threading`, `async/await`, `Promise`, or worker threads within a Deluge execution block.
  - Alternative: Asynchronous tasks, webhook callbacks, or Deluge Schedulers.
- ❌ Low-Level Disk / Socket IO: No raw file descriptors, sockets, or local file system access.
  - Alternative: `invokeurl` for network HTTP/REST APIs, Creator File Upload fields, or Zoho WorkDrive/Drive APIs.
- ❌ Raw SQL Queries: SQL syntax like `SELECT * FROM ...` is unsupported in Deluge.
  - Alternative: Deluge query criteria syntax (`Form_Name[Criteria]`) or Zoho Creator REST API / COQL.

### 4. IMPOSSIBLE METHODS & ARCHITECTURAL LIMITATIONS
If a user requests a method, architecture, or behavior that is impossible within Zoho Deluge or Zoho Creator:
1. Immediately and unambiguously declare: "This method/approach is impossible in Zoho Deluge / Zoho Creator."
2. Explain the exact technical constraint or platform limitation (e.g., Deluge server-side sandbox boundary, statement count execution limit of 5,000 statements per transaction, absence of client-side DOM access from backend Deluge workflows).
3. Provide the supported, idiomatic Zoho Creator architecture:
   - Client-side DOM manipulation from a backend Deluge workflow: Explain that Deluge executes server-side and has zero direct access to the client browser DOM. Recommend Zoho Creator Pages with custom HTML/CSS/JavaScript or Creator Custom Widgets using the Zoho Creator JS SDK (`ZOHO.CREATOR.init()`).
   - Indefinite polling or continuous daemon processes: Explain execution timeout and statement limits. Recommend Deluge Scheduled Functions, Webhooks, or Creator Form Actions.
   - Importing external npm / Python / Java packages directly into Deluge: Explain sandbox isolation. Recommend hosting custom logic on Zoho Catalyst Serverless Functions and calling them via `invokeurl`.

### 5. HTML, CSS, AND JAVASCRIPT IN ZOHO CREATOR
When explaining or providing HTML, CSS, and JavaScript:
- Restrict usage specifically to Zoho Creator implementation contexts:
  - Zoho Creator Pages & HTML Snippets.
  - Creator Custom Widgets using the official Zoho Creator JS SDK (`ZOHO.CREATOR.API`).
  - Creator Client-Side Form Scripts (e.g. On Load, On User Input, Field Actions).
- Provide clean, secure, and modern markup and styles scoped to avoid interfering with Zoho Creator's internal container stylesheets.

### 6. OUTPUT & CODE FORMATTING
- Format all Deluge code blocks with ```deluge ... ```.
- Format HTML, CSS, and JS with ```html ... ```, ```css ... ```, and ```javascript ... ```.
- Keep all explanations technically rigorous, concise, and focused on production-ready Zoho Creator implementations."""

# Retrieve active Llama-3 parameters from session state
llama_params = st.session_state.get("llama3_params", {
    "temperature": 0.2,
    "top_p": 0.9,
    "context_window": 8192,
    "repeat_penalty": 1.15,
    "num_predict": 2048,
    "selected_model": "llama3:latest"
})

# Sidebar settings specific to AI Assistant
with st.sidebar:
    st.subheader("🤖 Active Model Profile")
    st.markdown(f"**Model:** `{llama_params.get('selected_model', 'llama3:latest')}`")
    st.caption(f"Temp: `{llama_params.get('temperature', 0.2)}` • Context: `{llama_params.get('context_window', 8192)}` • Top-P: `{llama_params.get('top_p', 0.9)}`")

    # RAG Context injection toggle
    datasets = scraper_manager.get_available_datasets()
    use_vector_rag = st.toggle("🧠 ChromaDB Vector RAG", value=True, help="Inject semantic matches using nomic-embed-text")
    use_docs = st.toggle("📖 Full Documentation Fallback", value=False)
    selected_doc = None
    if use_docs and datasets:
        selected_doc = st.selectbox(
            "Reference Document",
            options=[d["filename"] for d in datasets],
            index=0
        )

    st.markdown("---")
    st.markdown("##### 🛡️ Active Guardrails")
    st.caption("• **Scope:** Zoho Deluge & Creator HTML/CSS/JS only\n• **Syntax Rules:** Deluge sandbox constraints strictly enforced\n• **Unsupported Features:** Explicitly flagged (e.g., `while` loops)\n• **Impossible Methods:** Formally identified with alternatives")

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.assistant_messages = []
        st.rerun()

# Initialize chat session
if "assistant_messages" not in st.session_state:
    st.session_state.assistant_messages = []

# Quick Prompt Pills
st.markdown("##### ⚡ Quick Prompt Templates")
pill1, pill2, pill3, pill4 = st.columns(4)

prefill_prompt = None
with pill1:
    if st.button("🌐 invokeurl API Call", use_container_width=True):
        prefill_prompt = "How do I invoke an external REST API with POST method, custom headers, and JSON body in Deluge?"
with pill2:
    if st.button("🔄 While Loop Alternative", use_container_width=True):
        prefill_prompt = "How can I write a while loop in Deluge to poll until status is completed?"
with pill3:
    if st.button("🎨 Creator Custom Widget", use_container_width=True):
        prefill_prompt = "How do I create a Zoho Creator Custom Widget using HTML, CSS, and the Zoho Creator JavaScript SDK?"
with pill4:
    if st.button("📊 Query Records Criteria", use_container_width=True):
        prefill_prompt = "Show me the syntax to fetch and update records using Deluge criteria in Zoho Creator."

# Display conversation history
for msg in st.session_state.assistant_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User prompt
user_input = st.chat_input("Ask a technical question on Deluge, HTML, CSS, or JS in Zoho Creator...")
active_prompt = prefill_prompt or user_input

if active_prompt:
    st.session_state.assistant_messages.append({"role": "user", "content": active_prompt})
    with st.chat_message("user"):
        st.markdown(active_prompt)

    # Prepare messages payload with strict system prompt
    system_text = ZOHO_SYSTEM_PROMPT
    
    # Retrieve relevant context using ChromaDB vector database if enabled
    vector_context = ""
    if use_vector_rag:
        try:
            from vector_setup import query_vector_db, DEFAULT_CHROMA_DIR
            if os.path.exists(DEFAULT_CHROMA_DIR):
                matches = query_vector_db(query_text=active_prompt, top_k=3)
                if matches:
                    snippets = []
                    for m in matches:
                        title = m.get("metadata", {}).get("title", "Reference")
                        url = m.get("metadata", {}).get("source_url", "")
                        snippets.append(f"### {title} ({url})\n{m['document']}")
                    vector_context = "\n\n---\n\n".join(snippets)
        except Exception:
            pass

    if vector_context:
        system_text += f"\n\n### RETRIEVED ZOHO DELUGE DOCUMENTATION CONTEXT\nUse the following verified Zoho Deluge documentation excerpts to ensure maximum accuracy:\n\n{vector_context}\n\nStrictly adhere to the Deluge syntax rules, unsupported feature constraints, and domain boundary outlined above."
    elif use_docs and selected_doc:
        doc_obj = next((d for d in datasets if d["filename"] == selected_doc), None)
        if doc_obj and os.path.exists(doc_obj["path"]):
            with open(doc_obj["path"], "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
                context_snippet = content[:5000]
                system_text += f"\n\n### REFERENCE ZOHO DELUGE DOCUMENTATION\n```markdown\n{context_snippet}\n```\n\nStrictly adhere to the Deluge syntax rules, unsupported feature constraints, and domain boundary outlined above."

    payload = [{"role": "system", "content": system_text}]
    payload.extend(st.session_state.assistant_messages)

    with st.chat_message("assistant"):
        try:
            model_to_use = llama_params.get("selected_model", "llama3:8b")
            host_to_use = llama_params.get("ollama_host", "http://localhost:11434")
            try:
                if hasattr(st, "secrets") and "OLLAMA_HOST" in st.secrets:
                    host_to_use = st.secrets["OLLAMA_HOST"]
            except Exception:
                pass

            options_payload = {
                "temperature": float(llama_params.get("temperature", 0.2)),
                "top_p": float(llama_params.get("top_p", 0.9)),
                "repeat_penalty": float(llama_params.get("repeat_penalty", 1.15)),
                "num_predict": int(llama_params.get("num_predict", 1536)),
                "num_ctx": int(llama_params.get("context_window", 4096)),
            }

            client = ollama.Client(host=host_to_use)
            try:
                response_stream = client.chat(
                    model=model_to_use,
                    messages=payload,
                    options=options_payload,
                    stream=True
                )
            except ollama.ResponseError as err:
                if "not found" in str(err).lower() and model_to_use == "llama3:8b":
                    response_stream = client.chat(
                        model="llama3",
                        messages=payload,
                        options=options_payload,
                        stream=True
                    )
                else:
                    raise err

            def stream_gen():
                for chunk in response_stream:
                    yield chunk["message"]["content"]

            full_reply = st.write_stream(stream_gen())
            st.session_state.assistant_messages.append({"role": "assistant", "content": full_reply})

        except ollama.ResponseError as e:
            st.error(f"Ollama Error ({e.status_code}): {e.error}")
        except Exception as e:
            st.error(f"Failed to connect to Ollama at `{host_to_use}`: {str(e)}.\n\n"
                     f"• If running locally: Ensure `ollama run llama3:8b` is active.\n"
                     f"• If hosting on Streamlit Community Cloud: Add your remote Ollama endpoint to `st.secrets` (`OLLAMA_HOST`).")
