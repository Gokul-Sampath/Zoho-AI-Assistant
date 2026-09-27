"""
Vector Setup for Zoho Deluge Documentation
Reads 'zoho_deluge_all_docs.md' from the data directory, chunks content into manageable segments,
generates embeddings using local Ollama 'all-minilm', and persists into ChromaDB.
"""

import os
import sys
import re
import time
import hashlib
import argparse
from typing import List, Dict, Any, Optional, Union

import chromadb
from chromadb.utils import embedding_functions

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_FILE = os.path.join(BASE_DIR, "data", "zoho_deluge_all_docs.md")
DEFAULT_CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
DEFAULT_COLLECTION = "zoho_deluge_docs"
DEFAULT_EMBED_MODEL = "nomic-embed-text"  # Fast 768-dim model with 8192 context window
OLLAMA_URL = "http://localhost:11434"

MODEL_DIMENSIONS = {
    "nomic-embed-text": 768,
    "all-minilm": 384,
    "bge-small-en": 384,
    "bge-large-en": 1024,
    "mxbai-embed-large": 1024,
}


def get_model_dimension(model_name: str) -> int:
    """Return expected embedding vector dimension for a model."""
    clean = model_name.split(":")[0].strip().lower()
    return MODEL_DIMENSIONS.get(clean, 768 if "nomic" in clean else 384)


def get_collection_dimension(client: chromadb.PersistentClient, collection_name: str) -> Optional[int]:
    """Detect stored embedding dimension in ChromaDB collection if records exist."""
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


def clean_markdown_page(body: str) -> str:
    """Strip repeated navigation trees and boilerplate badges to isolate core documentation."""
    # Strip footer links
    if "### Get Started Now" in body:
        body = body.split("### Get Started Now")[0].strip()
    if body.endswith("---"):
        body = body[:-3].strip()

    # If the page contains a secondary top-level header (# ...), start from there
    h1_matches = list(re.finditer(r"^#\s+(.+)$", body, re.MULTILINE))
    content = body
    if len(h1_matches) > 1:
        content = body[h1_matches[1].start():]

    # Filter out extraneous badges / buttons
    cleaned_lines = []
    for line in content.splitlines():
        line_clean = line.strip()
        if any(bad in line_clean for bad in [
            "Open in ChatGPT", "Open in Claude", "Copy as Markdown",
            "View as Markdown", "![ask ai]", "![chatgpt]", "![claude]",
            "Print and PDF", "#### Table of Contents"
        ]):
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def adaptive_chunk_markdown_content(
    body: str,
    target_size: int = 1000,
    max_size: int = 1600,
    overlap: int = 150
) -> List[Dict[str, Any]]:
    """
    Adaptively segment technical markdown documentation by semantic structure:
    - Protects code blocks (```...```) from arbitrary mid-block slicing.
    - Preserves markdown tables without splitting rows or headers.
    - Uses headings and paragraph breaks (\n\n) as primary natural boundaries.
    - Dynamically groups small related paragraphs and isolates code examples.
    """
    if not body.strip():
        return []

    # If the entire body is already within max_size, return as single chunk
    if len(body) <= max_size:
        c_type = "code" if "```" in body else ("table" if "|" in body else "text")
        return [{
            "text": body.strip(),
            "content_type": c_type,
            "char_count": len(body.strip())
        }]

    # Step 1: Parse content into semantic blocks (code, table, heading, paragraph)
    code_pattern = re.compile(r"(```[\s\S]*?```)", re.MULTILINE)
    raw_parts = code_pattern.split(body)
    blocks = []

    for part in raw_parts:
        part_clean = part.strip()
        if not part_clean:
            continue
        if part_clean.startswith("```") and part_clean.endswith("```"):
            blocks.append(("code", part_clean))
        else:
            paragraphs = part.split("\n\n")
            for para in paragraphs:
                p_str = para.strip()
                if not p_str:
                    continue
                if p_str.startswith("|") and "|" in p_str[1:]:
                    blocks.append(("table", p_str))
                elif p_str.startswith("#"):
                    blocks.append(("heading", p_str))
                else:
                    blocks.append(("text", p_str))

    # Step 2: Accumulate blocks adaptively
    chunks = []
    current_blocks = []
    current_len = 0
    has_code = False
    has_table = False

    for b_type, b_text in blocks:
        b_len = len(b_text)

        # Oversized block (e.g. huge code block or massive table)
        if b_len > max_size:
            if current_blocks:
                c_text = "\n\n".join(current_blocks)
                c_type = "code" if has_code else ("table" if has_table else "text")
                chunks.append({"text": c_text, "content_type": c_type, "char_count": len(c_text)})
                current_blocks = []
                current_len = 0
                has_code = False
                has_table = False

            lines = b_text.splitlines()
            sub_accum = []
            sub_len = 0
            for line in lines:
                if sub_len + len(line) + 1 > target_size and sub_accum:
                    s_text = "\n".join(sub_accum)
                    chunks.append({"text": s_text, "content_type": b_type, "char_count": len(s_text)})
                    sub_accum = sub_accum[-2:] if len(sub_accum) >= 2 else []
                    sub_len = sum(len(x) + 1 for x in sub_accum)
                sub_accum.append(line)
                sub_len += len(line) + 1
            if sub_accum:
                s_text = "\n".join(sub_accum)
                chunks.append({"text": s_text, "content_type": b_type, "char_count": len(s_text)})
            continue

        # Check if adding this block exceeds threshold at a natural boundary
        should_break = False
        if current_blocks:
            if current_len + b_len > max_size:
                should_break = True
            elif current_len >= target_size and b_type in ["heading", "code", "table"]:
                should_break = True

        if should_break:
            c_text = "\n\n".join(current_blocks)
            c_type = "code" if has_code else ("table" if has_table else "text")
            chunks.append({"text": c_text, "content_type": c_type, "char_count": len(c_text)})

            # Carry forward overlap if feasible
            overlap_block = []
            if current_blocks and len(current_blocks[-1]) <= overlap and not current_blocks[-1].startswith("```"):
                overlap_block = [current_blocks[-1]]
                current_len = len(current_blocks[-1])
            else:
                current_len = 0

            current_blocks = overlap_block + [b_text]
            current_len += b_len
            has_code = (b_type == "code")
            has_table = (b_type == "table")
        else:
            current_blocks.append(b_text)
            current_len += b_len
            if b_type == "code":
                has_code = True
            elif b_type == "table":
                has_table = True

    if current_blocks:
        c_text = "\n\n".join(current_blocks)
        c_type = "code" if has_code else ("table" if has_table else "text")
        chunks.append({"text": c_text, "content_type": c_type, "char_count": len(c_text)})

    return chunks


def chunk_documentation(
    file_path: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
    max_chunks: int = 0
) -> List[Dict[str, Any]]:
    """Parse the Deluge markdown file and slice into adaptively-sized semantic chunks."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Documentation file not found: {file_path}")

    print(f"📖 Reading dataset from: {file_path}")
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"📦 File size: {file_size_mb:.2f} MB")

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    section_pattern = re.compile(
        r"^##\s+(\d+)\.\s+(.+?)\s*$\n+\*\*Source URL:\*\*\s*(.+?)\s*$",
        re.MULTILINE
    )
    matches = list(section_pattern.finditer(text))
    print(f"📑 Identified {len(matches)} distinct documentation page sections.")

    chunks = []
    global_chunk_idx = 0

    for i, match in enumerate(matches):
        page_num, title, source_url = match.groups()
        start_idx = match.end()
        end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        raw_body = text[start_idx:end_idx].strip()
        clean_body = clean_markdown_page(raw_body)

        if not clean_body:
            continue

        url_match = re.search(r"\((https?://[^\)]+)\)", source_url)
        clean_url = url_match.group(1) if url_match else source_url.strip("[]() ")
        header_context = f"# {title}\nSource: {clean_url}\n\n"

        # Apply adaptive semantic chunking
        adaptive_blocks = adaptive_chunk_markdown_content(
            body=clean_body,
            target_size=chunk_size,
            max_size=int(chunk_size * 1.5),
            overlap=chunk_overlap
        )

        for sub_idx, ab in enumerate(adaptive_blocks):
            chunk_text = header_context + ab["text"]
            content_hash = hashlib.sha256(chunk_text.strip().encode("utf-8")).hexdigest()

            chunks.append({
                "id": f"chunk_{global_chunk_idx:06d}",
                "text": chunk_text,
                "metadata": {
                    "page_number": int(page_num),
                    "title": title[:100],
                    "source_url": clean_url,
                    "sub_chunk_index": sub_idx,
                    "content_hash": content_hash,
                    "content_type": ab["content_type"],
                    "char_count": len(chunk_text)
                }
            })
            global_chunk_idx += 1
            if 0 < max_chunks <= len(chunks):
                break

        if 0 < max_chunks <= len(chunks):
            break

    print(f"✂️  Generated {len(chunks)} adaptive semantic chunks (target: {chunk_size} chars).")
    return chunks


def chunk_scraped_pages(
    pages: List[Dict[str, Any]],
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
    max_chunks: int = 0
) -> List[Dict[str, Any]]:
    """Chunk a list of scraped page dicts adaptively: [{'url': ..., 'title': ..., 'markdown': ...}]."""
    chunks = []
    global_idx = 0
    for page_idx, page in enumerate(pages, start=1):
        url = page.get("url", "")
        title = page.get("title", "Untitled")
        raw_body = page.get("markdown", "")
        clean_body = clean_markdown_page(raw_body)
        if not clean_body:
            continue

        url_match = re.search(r"\((https?://[^\)]+)\)", url)
        clean_url = url_match.group(1) if url_match else url.strip("[]() ")
        header_context = f"# {title}\nSource: {clean_url}\n\n"

        adaptive_blocks = adaptive_chunk_markdown_content(
            body=clean_body,
            target_size=chunk_size,
            max_size=int(chunk_size * 1.5),
            overlap=chunk_overlap
        )

        for sub_idx, ab in enumerate(adaptive_blocks):
            chunk_text = header_context + ab["text"]
            c_hash = hashlib.sha256(chunk_text.strip().encode("utf-8")).hexdigest()
            chunks.append({
                "id": f"chunk_{global_idx:06d}",
                "text": chunk_text,
                "metadata": {
                    "page_number": page_idx,
                    "title": title[:100],
                    "source_url": clean_url,
                    "sub_chunk_index": sub_idx,
                    "content_hash": c_hash,
                    "content_type": ab["content_type"],
                    "char_count": len(chunk_text)
                }
            })
            global_idx += 1
            if 0 < max_chunks <= len(chunks):
                break

        if 0 < max_chunks <= len(chunks):
            break

    return chunks


def compare_and_update_chromadb(
    new_data: Any = DEFAULT_DATA_FILE,
    db_dir: str = DEFAULT_CHROMA_DIR,
    collection_name: str = DEFAULT_COLLECTION,
    model_name: str = DEFAULT_EMBED_MODEL,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    batch_size: int = 16,
    limit: int = 0,
    delete_missing: bool = False,
    dry_run: bool = False,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Compare local data with new scraper fetches and update ONLY the changed/new content in ChromaDB.
    
    Args:
        new_data: Path to markdown file, raw markdown string, or list of scraped page dicts.
        db_dir: Persistent ChromaDB directory.
        collection_name: Target ChromaDB collection name.
        model_name: Local Ollama embedding model.
        chunk_size: Target characters per chunk.
        chunk_overlap: Overlap characters between chunks.
        batch_size: Batch size for embeddings and upsert operations.
        limit: Max chunks to process (0 = all).
        delete_missing: If True, delete obsolete chunks from ChromaDB for touched URLs.
        dry_run: If True, simulate changes without writing to ChromaDB.
        verbose: Print progress to console.
    
    Returns:
        Dict summarizing comparison statistics (evaluated, unchanged, added, modified, deleted, duration).
    """
    t_start = time.time()
    if verbose:
        print("\n" + "=" * 70)
        print("🔄 Incremental Sync: Comparing Scraper Data with ChromaDB")
        print(f"💾 Persistent DB  : {db_dir}")
        print(f"🏷️  Collection     : {collection_name}")
        print(f"🧠 Local Model    : {model_name} (Ollama @ {OLLAMA_URL})")
        print(f"🔍 Dry Run Mode   : {'Enabled (Preview Only)' if dry_run else 'Disabled (Live Updates)'}")
        print("=" * 70 + "\n")

    # Step 1: Chunk incoming scraper data
    if isinstance(new_data, list):
        if verbose:
            print(f"📦 Processing {len(new_data)} in-memory scraped pages...")
        new_chunks = chunk_scraped_pages(
            new_data,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            max_chunks=limit
        )
    elif isinstance(new_data, str) and os.path.exists(new_data):
        if verbose:
            print(f"📖 Reading newly scraped file: {new_data}")
        new_chunks = chunk_documentation(
            file_path=new_data,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            max_chunks=limit
        )
    elif isinstance(new_data, str):
        # Raw markdown text string
        import tempfile
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as tmp:
            tmp.write(new_data)
            tmp_path = tmp.name
        try:
            new_chunks = chunk_documentation(
                file_path=tmp_path,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                max_chunks=limit
            )
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    else:
        raise ValueError(f"Unsupported new_data type: {type(new_data)}")

    if not new_chunks:
        if verbose:
            print("⚠️ No chunks generated from new scraper data.")
        return {
            "status": "empty",
            "total_evaluated": 0,
            "added": 0,
            "modified": 0,
            "unchanged": 0,
            "deleted": 0,
            "updated_total": 0,
            "duration_seconds": round(time.time() - t_start, 2)
        }

    # Step 2: Connect to ChromaDB
    embed_fn = embedding_functions.OllamaEmbeddingFunction(
        url=OLLAMA_URL,
        model_name=model_name
    )
    os.makedirs(db_dir, exist_ok=True)
    client = chromadb.PersistentClient(path=db_dir)

    target_dim = get_model_dimension(model_name)
    existing_dim = get_collection_dimension(client, collection_name)

    if existing_dim is not None and existing_dim != target_dim:
        if verbose:
            print(f"⚠️ Model dimension mismatch detected!")
            print(f"   Existing collection '{collection_name}' has dimension {existing_dim}.")
            print(f"   Target model '{model_name}' produces dimension {target_dim}.")
        if not dry_run:
            if verbose:
                print(f"🔄 Automatically re-creating collection '{collection_name}' for {target_dim}-dim embeddings...")
            client.delete_collection(name=collection_name)
            collection = client.create_collection(
                name=collection_name,
                embedding_function=embed_fn,
                metadata={
                    "description": "Zoho Deluge technical documentation embeddings",
                    "embedding_model": model_name,
                    "dimension": target_dim
                }
            )
        else:
            if verbose:
                print(f"ℹ️ [Dry Run] Live sync will re-create collection '{collection_name}' with {target_dim} dimensions.")
            collection = client.get_collection(name=collection_name, embedding_function=embed_fn)
    else:
        collection = client.get_or_create_collection(
            name=collection_name,
            embedding_function=embed_fn,
            metadata={
                "description": "Zoho Deluge technical documentation embeddings",
                "embedding_model": model_name,
                "dimension": target_dim
            }
        )

    # Step 3: Fetch existing ChromaDB chunks with safe pagination
    total_existing = collection.count()
    if verbose:
        print(f"🔍 Loading existing database index ({total_existing:,} records in ChromaDB)...")

    # Map: (source_url, sub_chunk_index) -> {"id": chunk_id, "hash": content_hash}
    existing_map = {}
    read_batch = 2000
    for offset in range(0, total_existing, read_batch):
        res = collection.get(
            limit=read_batch,
            offset=offset,
            include=["metadatas", "documents"]
        )
        for cid, meta, doc in zip(res["ids"], res["metadatas"], res["documents"]):
            s_url = meta.get("source_url")
            s_idx = meta.get("sub_chunk_index", 0)
            c_hash = meta.get("content_hash")
            if not c_hash and doc:
                c_hash = hashlib.sha256(doc.strip().encode("utf-8")).hexdigest()
            existing_map[(s_url, s_idx)] = {
                "id": cid,
                "hash": c_hash
            }

    if verbose:
        print(f"📊 Indexed {len(existing_map):,} existing chunks for differential comparison.")

    # Step 4: Compare incoming scraper chunks against existing ChromaDB records
    chunks_to_add = []
    chunks_to_modify = []
    unchanged_count = 0
    new_keys_seen = set()

    # Track highest existing chunk numeric id to assign clean IDs for newly added chunks
    max_numeric_id = 0
    for info in existing_map.values():
        cid = info["id"]
        if cid.startswith("chunk_"):
            try:
                num = int(cid.split("_")[1])
                if num > max_numeric_id:
                    max_numeric_id = num
            except ValueError:
                pass

    next_id_counter = max_numeric_id + 1

    for chunk in new_chunks:
        meta = chunk["metadata"]
        key = (meta.get("source_url"), meta.get("sub_chunk_index", 0))
        new_keys_seen.add(key)
        new_hash = meta.get("content_hash")

        if key in existing_map:
            existing_entry = existing_map[key]
            existing_hash = existing_entry["hash"]

            if new_hash != existing_hash:
                # Content has changed -> Re-use existing ID to update in-place
                chunk["id"] = existing_entry["id"]
                chunks_to_modify.append(chunk)
            else:
                # Content is identical -> Skip embedding!
                unchanged_count += 1
        else:
            # Completely new chunk
            chunk["id"] = f"chunk_{next_id_counter:06d}"
            next_id_counter += 1
            chunks_to_add.append(chunk)

    # Optional: Detect deleted chunks for the URLs present in new_data
    chunks_to_delete_ids = []
    if delete_missing:
        touched_urls = {c["metadata"].get("source_url") for c in new_chunks}
        for (url, sub_idx), info in existing_map.items():
            if url in touched_urls and (url, sub_idx) not in new_keys_seen:
                chunks_to_delete_ids.append(info["id"])

    # Step 5: Display Diff Analysis
    total_evaluated = len(new_chunks)
    total_to_update = len(chunks_to_add) + len(chunks_to_modify)

    if verbose:
        print("\n" + "-" * 50)
        print("📋 Comparison Results:")
        print(f"   • Total Evaluated : {total_evaluated:,} chunks")
        print(f"   • Unchanged       : {unchanged_count:,} chunks (SKIPPED - 0 compute)")
        print(f"   • Modified        : {len(chunks_to_modify):,} chunks (To Update)")
        print(f"   • Newly Added     : {len(chunks_to_add):,} chunks (To Insert)")
        if delete_missing:
            print(f"   • Obsolete        : {len(chunks_to_delete_ids):,} chunks (To Delete)")
        print(f"   ⚡ Net Updates    : {total_to_update:,} chunks requiring embeddings")
        print("-" * 50 + "\n")

    # Step 6: Execute Updates in ChromaDB
    if dry_run:
        if verbose:
            print("🛑 Dry run complete. No changes were written to ChromaDB.")
    else:
        # Delete obsolete records if requested
        if chunks_to_delete_ids:
            if verbose:
                print(f"🗑️ Deleting {len(chunks_to_delete_ids)} obsolete chunks from ChromaDB...")
            for i in range(0, len(chunks_to_delete_ids), batch_size):
                collection.delete(ids=chunks_to_delete_ids[i:i + batch_size])

        # Upsert only changed and new chunks
        updates_payload = chunks_to_modify + chunks_to_add
        if updates_payload:
            if verbose:
                print(f"📥 Generating local embeddings & upserting {len(updates_payload):,} changed chunks...")
            t_upsert = time.time()
            for i in range(0, len(updates_payload), batch_size):
                batch = updates_payload[i:i + batch_size]
                collection.upsert(
                    ids=[c["id"] for c in batch],
                    documents=[c["text"] for c in batch],
                    metadatas=[c["metadata"] for c in batch]
                )
                done = min(i + batch_size, len(updates_payload))
                elapsed = time.time() - t_upsert
                rate = done / elapsed if elapsed > 0 else 0
                if verbose:
                    pct = (done / len(updates_payload)) * 100
                    print(f"\r progress: [{done}/{len(updates_payload)}] {pct:.1f}% ({rate:.1f} chunks/sec)", end="", flush=True)
            if verbose:
                print(f"\n✅ Upserted {len(updates_payload):,} chunks in {time.time() - t_upsert:.2f}s!")
        else:
            if verbose:
                print("✨ Everything is already up-to-date! No embeddings or database updates were needed.")

    total_duration = round(time.time() - t_start, 2)
    return {
        "status": "success",
        "total_evaluated": total_evaluated,
        "unchanged": unchanged_count,
        "modified": len(chunks_to_modify),
        "added": len(chunks_to_add),
        "deleted": len(chunks_to_delete_ids),
        "updated_total": total_to_update,
        "duration_seconds": total_duration,
        "collection_count_after": collection.count()
    }


# Backwards compatibility alias
update_changed_content_in_chromadb = compare_and_update_chromadb


def setup_vector_database(
    file_path: str = DEFAULT_DATA_FILE,
    db_dir: str = DEFAULT_CHROMA_DIR,
    collection_name: str = DEFAULT_COLLECTION,
    model_name: str = DEFAULT_EMBED_MODEL,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    batch_size: int = 16,
    limit: int = 0,
    reset: bool = False
):
    """Chunk documentation, generate local embeddings, and store in persistent ChromaDB."""
    print("\n" + "=" * 70)
    print("🚀 Initializing ChromaDB Vector Store with Local Embeddings")
    print(f"📁 Source Dataset : {file_path}")
    print(f"💾 Persistent DB  : {db_dir}")
    print(f"🏷️  Collection     : {collection_name}")
    print(f"🧠 Local Model    : {model_name} (Ollama @ {OLLAMA_URL})")
    print("=" * 70 + "\n")

    # Step 1: Chunk documents
    chunks = chunk_documentation(
        file_path=file_path,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        max_chunks=limit
    )

    if not chunks:
        print("⚠️ No chunks generated. Aborting vector setup.")
        return None

    # Step 2: Initialize local Ollama embedding function
    print(f"\n🔌 Connecting to local Ollama embedding service (`{model_name}`)...")
    embed_fn = embedding_functions.OllamaEmbeddingFunction(
        url=OLLAMA_URL,
        model_name=model_name
    )

    # Step 3: Initialize Persistent ChromaDB Client
    os.makedirs(db_dir, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=db_dir)

    target_dim = get_model_dimension(model_name)
    existing_dim = get_collection_dimension(chroma_client, collection_name)

    if reset or (existing_dim is not None and existing_dim != target_dim):
        try:
            chroma_client.delete_collection(name=collection_name)
            if existing_dim and existing_dim != target_dim:
                print(f"🔄 Dimension change detected ({existing_dim} -> {target_dim}): Re-created collection '{collection_name}' for model '{model_name}'.")
            else:
                print(f"🗑️  Reset: Deleted existing collection '{collection_name}'")
        except Exception:
            pass

    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        embedding_function=embed_fn,
        metadata={
            "description": "Zoho Deluge technical documentation embeddings",
            "embedding_model": model_name,
            "dimension": target_dim
        }
    )

    total_chunks = len(chunks)
    print(f"📥 Storing {total_chunks} chunks in collection '{collection_name}' (batch size: {batch_size})...\n")

    t_start = time.time()
    for i in range(0, total_chunks, batch_size):
        batch = chunks[i:i + batch_size]
        ids = [c["id"] for c in batch]
        documents = [c["text"] for c in batch]
        metadatas = [c["metadata"] for c in batch]

        try:
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
        except Exception as e:
            print(f"\n❌ Error inserting batch {i}..{i+len(batch)}: {e}")
            raise e

        processed = min(i + batch_size, total_chunks)
        elapsed = time.time() - t_start
        speed = processed / elapsed if elapsed > 0 else 0
        pct = (processed / total_chunks) * 100
        print(f"\r progress: [{processed}/{total_chunks}] {pct:.1f}% ({speed:.1f} chunks/sec)", end="", flush=True)

    print(f"\n\n✅ Successfully indexed {total_chunks} chunks into ChromaDB in {time.time() - t_start:.2f}s!")
    print(f"📍 Database location: {os.path.abspath(db_dir)}")
    return collection


def query_vector_db(
    query_text: str,
    top_k: int = 3,
    db_dir: str = DEFAULT_CHROMA_DIR,
    collection_name: str = DEFAULT_COLLECTION,
    model_name: str = DEFAULT_EMBED_MODEL
) -> List[Dict[str, Any]]:
    """Query ChromaDB for relevant Zoho Deluge documentation chunks with automatic dimension matching."""
    if not os.path.exists(db_dir):
        print(f"❌ ChromaDB directory not found at {db_dir}. Please run vector_setup.py first.")
        return []

    client = chromadb.PersistentClient(path=db_dir)
    target_dim = get_model_dimension(model_name)
    existing_dim = get_collection_dimension(client, collection_name)

    active_model = model_name
    if existing_dim is not None and existing_dim != target_dim:
        # Collection was indexed with a different model dimension
        if existing_dim == 384:
            active_model = "all-minilm"
        elif existing_dim == 768:
            active_model = "nomic-embed-text"

    embed_fn = embedding_functions.OllamaEmbeddingFunction(
        url=OLLAMA_URL,
        model_name=active_model
    )

    try:
        collection = client.get_collection(name=collection_name, embedding_function=embed_fn)
        results = collection.query(
            query_texts=[query_text],
            n_results=top_k
        )
    except Exception as e:
        print(f"Vector search query warning: {e}")
        return []

    formatted = []
    if results and "documents" in results and results["documents"]:
        for idx in range(len(results["documents"][0])):
            doc = results["documents"][0][idx]
            meta = results["metadatas"][0][idx] if "metadatas" in results else {}
            dist = results["distances"][0][idx] if "distances" in results else None
            formatted.append({
                "document": doc,
                "metadata": meta,
                "distance": dist
            })

    return formatted


def main():
    parser = argparse.ArgumentParser(
        description="Build ChromaDB vector database from Zoho Deluge documentation."
    )
    parser.add_argument(
        "--file",
        default=DEFAULT_DATA_FILE,
        help=f"Path to input markdown file (default: {DEFAULT_DATA_FILE})"
    )
    parser.add_argument(
        "--db-dir",
        default=DEFAULT_CHROMA_DIR,
        help=f"ChromaDB persistent directory (default: {DEFAULT_CHROMA_DIR})"
    )
    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
        help=f"ChromaDB collection name (default: {DEFAULT_COLLECTION})"
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_EMBED_MODEL,
        help=f"Local Ollama embedding model (default: {DEFAULT_EMBED_MODEL})"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Chunk size in characters (default: 1000)"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Chunk overlap in characters (default: 200)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Batch size for embedding and ingestion (default: 16)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of chunks to index for quick testing (default: 0 = all)"
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Compare local data with new scraper fetches and update ONLY changed/new content in ChromaDB"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to ChromaDB"
    )
    parser.add_argument(
        "--delete-missing",
        action="store_true",
        help="Delete obsolete chunks from ChromaDB for touched documentation pages"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear existing collection before adding documents"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="",
        help="Optional test query to run against the database after setup"
    )

    args = parser.parse_args()

    if args.sync or (not args.reset and os.path.exists(args.db_dir)):
        # Run differential sync
        stats = compare_and_update_chromadb(
            new_data=args.file,
            db_dir=args.db_dir,
            collection_name=args.collection,
            model_name=args.model,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            batch_size=args.batch_size,
            limit=args.limit,
            delete_missing=args.delete_missing,
            dry_run=args.dry_run
        )
    else:
        # Full setup/reset
        collection = setup_vector_database(
            file_path=args.file,
            db_dir=args.db_dir,
            collection_name=args.collection,
            model_name=args.model,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            batch_size=args.batch_size,
            limit=args.limit,
            reset=args.reset
        )

    # Verification query
    test_query = args.query.strip() or "How to create and use a collection in Deluge"
    print(f"\n🔎 Testing Semantic Vector Query: '{test_query}'")
    matches = query_vector_db(
        query_text=test_query,
        top_k=2,
        db_dir=args.db_dir,
        collection_name=args.collection,
        model_name=args.model
    )

    for i, res in enumerate(matches, 1):
        meta = res["metadata"]
        print(f"\n--- Result #{i} ---")
        print(f"Title: {meta.get('title')}")
        print(f"URL: {meta.get('source_url')}")
        print(f"Preview:\n{res['document'][:250]}...")


if __name__ == "__main__":
    main()
