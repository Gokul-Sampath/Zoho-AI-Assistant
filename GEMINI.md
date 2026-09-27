# Antigravity Configuration & Project Operational Guidelines

## Operational Mode: Built-in Capabilities & Local Documentation Grounding

1. **Autonomous Built-in Execution**:
   - Operate exclusively using Antigravity's built-in tools and capabilities (local filesystem inspection, ripgrep search, local Python environment, and cached workspace indexing).
   - **No External Servers**: Do not attempt to establish connections to external servers, remote Ollama hosts, external APIs, or network tunnels. All logic and knowledge retrieval must be handled locally and within the repository.

2. **Grounded in Local Documentation**:
   - All code generation, API references, parameter signatures, and technical assistance must be strictly grounded in the official extracted documentation located at:
     `data/zoho_deluge_all_docs.md` (738+ verified Zoho Deluge documentation sections).
   - Utilize `builtin_engine.py` for indexing, searching, and streaming responses directly from the local knowledge base.

3. **Strict Zoho Deluge Syntax & Platform Guardrails**:
   - **Unsupported Features**:
     - ❌ `while` and `do-while` loops: Strictly unsupported in Deluge. Always explain the cloud transaction limit (5,000 statements) and provide valid alternatives (`for each` over bounded lists with `break`, Zoho Creator Scheduled Functions, or Webhooks).
     - ❌ `++`, `--`, `+=`, `-=`: Unsupported operators. Always use `i = i + 1;` or `i = i - 1;`.
     - ❌ Variable type prefixes: Variables must not declare types (e.g. `customerName = "Zoho";`, never `String customerName = "Zoho";`).
     - ❌ Semicolons: Every standalone statement must terminate with a semicolon (`;`).
     - ❌ Classes / OOP: Deluge is procedural; use Functions and `Map()` / `List()`.
     - ❌ Raw SQL: Use Deluge Criteria (`Form_Name[Criteria]`) or Zoho Creator COQL.
   - **Creator HTML/CSS/JS**:
     - Scoped strictly to Zoho Creator Pages, HTML Snippets, and Custom Widgets using the official `ZOHO.CREATOR` JavaScript SDK.

4. **Performance & Reliability**:
   - Deliver instantaneous, low-latency responses.
   - Maintain zero memory thrashing and memory-safe lazy loading across all ERP views.
   - Ensure the repository remains completely functional in offline and standalone mode on Streamlit Community Cloud.
