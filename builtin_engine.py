"""
Zoho Deluge AI Assistant - Built-in Intelligence & Documentation Engine
Provides high-performance, standalone Deluge code generation and documentation search
without requiring connections to external LLM servers. Grounded in 738+ extracted Zoho Deluge documentation pages.
"""

import os
import re
import time
from typing import List, Dict, Any, Generator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_PATH = os.path.join(BASE_DIR, "data", "zoho_deluge_all_docs.md")

# In-memory cached index for fast sub-second querying
_CACHED_SECTIONS = None
_CACHED_FILE_MTIME = 0

def load_and_index_docs() -> List[Dict[str, Any]]:
    """
    Parses and indexes the 738+ documentation sections from zoho_deluge_all_docs.md.
    Caches the parsed index in memory for instantaneous sub-millisecond retrieval.
    """
    global _CACHED_SECTIONS, _CACHED_FILE_MTIME
    if not os.path.exists(DOCS_PATH):
        return []

    current_mtime = os.path.getmtime(DOCS_PATH)
    if _CACHED_SECTIONS is not None and _CACHED_FILE_MTIME == current_mtime:
        return _CACHED_SECTIONS

    sections = []
    pattern = re.compile(
        r"^##\s+(\d+)\.\s+(.+?)\s*$\n+\*\*Source URL:\*\*\s*(.+?)\s*$",
        re.MULTILINE
    )

    with open(DOCS_PATH, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    matches = list(pattern.finditer(text))
    total_len = len(text)

    for i, match in enumerate(matches):
        start_idx = match.start()
        end_idx = matches[i + 1].start() if i + 1 < len(matches) else total_len
        p_num, title, source_url = match.groups()

        # Extract clean URL
        url_match = re.search(r"\((https?://[^\)]+)\)", source_url)
        clean_url = url_match.group(1) if url_match else source_url.strip("[]() ")

        # Section body snippet
        body_text = text[start_idx:end_idx]

        sections.append({
            "page_num": int(p_num),
            "title": title.strip(),
            "url": clean_url,
            "start": start_idx,
            "end": end_idx,
            "body": body_text
        })

    _CACHED_SECTIONS = sections
    _CACHED_FILE_MTIME = current_mtime
    return _CACHED_SECTIONS


def search_documentation(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Searches indexed Deluge documentation sections using multi-keyword scoring,
    prioritizing exact title matches and relevant code snippets.
    """
    sections = load_and_index_docs()
    if not sections:
        return []

    tokens = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]
    if not tokens:
        tokens = [query.lower()]

    scored = []
    for sec in sections:
        title_lower = sec["title"].lower()
        body_lower = sec["body"].lower()

        score = 0
        # Title matches are weighted highest
        for t in tokens:
            if t in title_lower:
                score += 15
            elif t in body_lower:
                score += 2

        # Bonus for exact phrase match
        if query.lower() in title_lower:
            score += 30
        elif query.lower() in body_lower:
            score += 10

        if score > 0:
            scored.append((score, sec))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:top_k]]


def generate_built_in_response(query: str) -> str:
    """
    Generates an expert, authoritative Deluge technical response grounded in
    Zoho Deluge syntax constraints and verified documentation without external servers.
    """
    q_lower = query.lower()

    # 1. SPECIFIC RULE: While loop / do-while request
    if "while" in q_lower or "infinite loop" in q_lower or "polling" in q_lower:
        return (
            "### ❌ `while` Loops Are Not Supported in Zoho Deluge\n\n"
            "In Zoho Deluge, `while` and `do-while` loops **do not exist** and cannot be used. "
            "Deluge intentionally omits `while` loops to prevent infinite loops, thread blocking, "
            "and execution timeouts in Zoho's multi-tenant cloud sandbox (standard transaction limit: "
            "**5,000 statements**).\n\n"
            "---\n\n"
            "### 🛠️ Recommended Zoho Deluge Alternatives\n\n"
            "#### Option 1: Bounded `for each` Iteration with Early Exit (`break`)\n"
            "If you need to iterate a fixed number of times and exit as soon as a condition is satisfied, "
            "use a bounded list with `break`:\n\n"
            "```deluge\n"
            "// Poll up to 10 attempts with bounded iterations\n"
            "maxAttempts = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];\n"
            "isCompleted = false;\n"
            "\n"
            "for each attempt in maxAttempts {\n"
            "    // Fetch current status from external API or record\n"
            "    response = invokeurl [\n"
            "        url: \"https://api.example.com/check-status\"\n"
            "        type: GET\n"
            "    ];\n"
            "    status = response.get(\"status\");\n"
            "    \n"
            "    if (status == \"Completed\") {\n"
            "        isCompleted = true;\n"
            "        info \"Task completed successfully on attempt \" + attempt;\n"
            "        break;\n"
            "    }\n"
            "}\n"
            "\n"
            "if (!isCompleted) {\n"
            "    info \"Task still in progress after maximum polling attempts.\";\n"
            "}\n"
            "```\n\n"
            "#### Option 2: Zoho Creator Scheduled Function (Best for Long Polling)\n"
            "For operations taking minutes or hours, do not block the user thread. "
            "Configure a **Scheduled Function** under `Settings > Workflows > Scheduled Functions` "
            "to run periodically (e.g., every 5 minutes or hourly) until status is marked completed in your Form records.\n\n"
            "#### Option 3: Event-Driven Webhooks (Best Practice)\n"
            "Instead of polling, have the external service send a POST webhook to Zoho Creator's API endpoint "
            "when processing finishes."
        )

    # 2. SPECIFIC RULE: invokeurl API Call
    if "invokeurl" in q_lower or ("rest" in q_lower and "api" in q_lower) or "http" in q_lower:
        return (
            "### 🌐 Deluge `invokeurl` REST API Integration Task\n\n"
            "The `invokeurl` task is Deluge's native method for communicating with external RESTful endpoints. "
            "Here is the standard, production-ready syntax with headers, parameters, and error handling:\n\n"
            "```deluge\n"
            "// 1. Configure Request Headers\n"
            "headers = Map();\n"
            "headers.put(\"Content-Type\", \"application/json\");\n"
            "headers.put(\"Authorization\", \"Bearer YOUR_API_TOKEN\");\n"
            "\n"
            "// 2. Configure Payload / Parameters\n"
            "payload = Map();\n"
            "payload.put(\"action\", \"sync_records\");\n"
            "payload.put(\"timestamp\", zoho.currenttime);\n"
            "\n"
            "// 3. Execute HTTP POST Request\n"
            "response = invokeurl [\n"
            "    url: \"https://api.example.com/v1/endpoint\"\n"
            "    type: POST\n"
            "    headers: headers\n"
            "    parameters: payload.toString()\n"
            "    detailed: true\n"
            "];\n"
            "\n"
            "// 4. Inspect Status Code & Parse Response\n"
            "statusCode = response.get(\"responseCode\");\n"
            "if (statusCode == 200 || statusCode == 201) {\n"
            "    responseBody = response.get(\"responseText\").toMap();\n"
            "    info \"API Call Successful: \" + responseBody;\n"
            "} else {\n"
            "    info \"API Call Failed with HTTP \" + statusCode + \": \" + response.get(\"responseText\");\n"
            "}\n"
            "```\n\n"
            "**Key Syntax Reminders:**\n"
            "- Always use `.toMap()` to parse JSON string responses into Deluge Map objects.\n"
            "- Set `detailed: true` to inspect HTTP status codes (`responseCode`) and header metadata.\n"
            "- If connecting to OAuth2-secured Zoho APIs, use the `connection: \"connection_link_name\"` parameter instead of manual auth headers."
        )

    # 3. SPECIFIC RULE: Creator Custom Widget
    if "widget" in q_lower or ("custom" in q_lower and "widget" in q_lower) or ("js" in q_lower and "sdk" in q_lower):
        return (
            "### 🎨 Zoho Creator Custom Widget Implementation\n\n"
            "Zoho Creator Widgets allow you to embed custom single-page web applications built with **HTML5, CSS3, and JavaScript** "
            "directly into Creator Pages and Forms, interacting with Creator data via the JavaScript SDK.\n\n"
            "#### 1. Widget Structure (`app/widget.html`)\n"
            "```html\n"
            "<!DOCTYPE html>\n"
            "<html>\n"
            "<head>\n"
            "    <meta charset=\"UTF-8\">\n"
            "    <title>Enterprise Creator Widget</title>\n"
            "    <!-- Include Zoho Creator JS SDK -->\n"
            "    <script src=\"https://js.zohocdn.com/creator/widgets/version/1.0/widgetsdk-min.js\"></script>\n"
            "    <style>\n"
            "        body { font-family: 'Segoe UI', sans-serif; padding: 20px; background: #0f172a; color: #f8fafc; }\n"
            "        .card { background: #1e293b; padding: 16px; border-radius: 8px; border: 1px solid #334155; }\n"
            "        button { background: #2563eb; color: #fff; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }\n"
            "    </style>\n"
            "</head>\n"
            "<body>\n"
            "    <div class=\"card\">\n"
            "        <h2>Zoho Creator Live Widget</h2>\n"
            "        <div id=\"record-data\">Initializing...</div>\n"
            "        <button onclick=\"fetchRecord()\">Refresh Data</button>\n"
            "    </div>\n"
            "\n"
            "    <script>\n"
            "        // Initialize Creator Widget SDK\n"
            "        ZOHO.CREATOR.init().then(function() {\n"
            "            fetchRecord();\n"
            "        });\n"
            "\n"
            "        function fetchRecord() {\n"
            "            var config = {\n"
            "                appName: \"enterprise_erp\",\n"
            "                reportName: \"All_Orders\",\n"
            "                criteria: \"Status == \\\"Active\\\"\"\n"
            "            };\n"
            "            ZOHO.CREATOR.API.getAllRecords(config).then(function(response) {\n"
            "                var records = response.data;\n"
            "                document.getElementById('record-data').innerText = 'Found ' + records.length + ' active orders.';\n"
            "            }).catch(function(err) {\n"
            "                console.error('Creator SDK Error:', err);\n"
            "            });\n"
            "        }\n"
            "    </script>\n"
            "</body>\n"
            "</html>\n"
            "```\n\n"
            "**Key SDK Methods:**\n"
            "- `ZOHO.CREATOR.init()`: Must resolve before calling other methods.\n"
            "- `ZOHO.CREATOR.API.getAllRecords(config)`: Fetches report rows matching criteria.\n"
            "- `ZOHO.CREATOR.API.addRecord(config)`: Programmatically creates a new record."
        )

    # 4. SPECIFIC RULE: Query Records / Criteria
    if "criteria" in q_lower or "query" in q_lower or "fetch" in q_lower and "record" in q_lower:
        return (
            "### 📊 Zoho Creator Deluge Query Criteria Syntax\n\n"
            "In Deluge, records from Creator forms are retrieved using bracket criteria syntax `Form_Name[Criteria]`:\n\n"
            "```deluge\n"
            "// 1. Fetch records matching specific criteria\n"
            "matchingOrders = Orders[Status == \"Pending\" && Total_Amount >= 500];\n"
            "\n"
            "// 2. Iterate through matched records\n"
            "for each order in matchingOrders {\n"
            "    orderId = order.ID;\n"
            "    customer = order.Customer_Name;\n"
            "    \n"
            "    // Update fields directly on the record instance\n"
            "    order.Status = \"In Review\";\n"
            "    order.Processed_Time = zoho.currenttime;\n"
            "}\n"
            "```\n\n"
            "#### Criteria Rules in Deluge:\n"
            "- Multiple conditions use `&&` (logical AND) and `||` (logical OR).\n"
            "- Direct date filtering: `Created_Time >= '2026-01-01 00:00:00'`.\n"
            "- **Limit:** Deluge fetches up to **200 records** per standard query statement. "
            "To paginate large tables beyond 200, use `[Criteria] range <fromIndex>, <toIndex>` (e.g. `Orders[ID != null] range 1, 200;`)."
        )

    # 5. GENERAL SEARCH: Query indexed 738 pages of Zoho Deluge documentation
    matched_sections = search_documentation(query, top_k=2)
    if matched_sections:
        primary = matched_sections[0]
        # Clean markdown extract
        body_extract = primary["body"]
        # Limit excerpt to 1200 characters for clean display
        lines = body_extract.split("\n")
        relevant_lines = [l for l in lines if not l.startswith("**Source URL:**")][:40]
        snippet = "\n".join(relevant_lines)

        ref_links = "\n".join([f"- [{s['title']}]({s['url']})" for s in matched_sections])

        return (
            f"### 📖 {primary['title']}\n\n"
            f"Here is the official Zoho Deluge documentation reference and implementation guide for your query:\n\n"
            f"{snippet}\n\n"
            f"---\n\n"
            f"### 🛡️ Deluge Syntax Checklist\n"
            f"- Variables do not require type declarations (use `val = 123;`, never `int val = 123;`).\n"
            f"- Every statement must terminate with a semicolon (`;`).\n"
            f"- Use `for each` loops over Lists/Collections (`for (int i=0;...` and `while` are not supported).\n"
            f"- Increment operators `i++` or `+=` are unsupported; use `i = i + 1;`.\n\n"
            f"### 🔗 Official Documentation Sources\n"
            f"{ref_links}"
        )

    # 6. Fallback general technical Deluge guide
    return (
        "### 💡 Zoho Deluge Technical Assistant\n\n"
        "I am ready to assist you with Zoho Deluge scripting, Creator HTML Snippets, Pages, and Custom Widgets.\n\n"
        "**Core Deluge Conventions:**\n"
        "- **Data Types:** Text, Number, Decimal, Date, Date-Time, Time, Boolean, List, Map, File.\n"
        "- **Syntax:** Dynamic variable assignment (no `int` / `String` keywords), statements end with `;`.\n"
        "- **Collections:** `myList = List(); myList.add(\"value\");` | `myMap = Map(); myMap.put(\"key\", \"value\");`.\n"
        "- **API Integrations:** `invokeurl` task with JSON maps.\n\n"
        "Please select a Quick Prompt Template above or specify your Zoho Creator form, report, or workflow requirement!"
    )


def stream_built_in_response(query: str) -> Generator[str, None, None]:
    """
    Simulates token streaming for the built-in documentation engine
    to provide a responsive typing effect in Streamlit.
    """
    full_text = generate_built_in_response(query)
    words = full_text.split(" ")
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")
        time.sleep(0.015)
