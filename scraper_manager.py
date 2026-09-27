"""
Scraper Manager for Zoho Deluge Documentation Dashboard
Handles execution history, dataset management, scheduling persistence, and background jobs.
"""

import os
import sys
import json
import time
import asyncio
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORY_FILE = os.path.join(BASE_DIR, "execution_history.json")
SCHEDULE_FILE = os.path.join(BASE_DIR, "schedule_config.json")

os.makedirs(DATA_DIR, exist_ok=True)


def init_history():
    """Initialize history file if not present, seeding with initial run if zoho_deluge_docs.md exists."""
    if not os.path.exists(HISTORY_FILE):
        seed = []
        sample_doc = os.path.join(BASE_DIR, "zoho_deluge_docs.md")
        if os.path.exists(sample_doc):
            stat = os.stat(sample_doc)
            seed.append({
                "id": "run-initial-01",
                "timestamp": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "trigger_type": "Manual (CLI)",
                "target_url": "https://www.zoho.com/deluge/help/",
                "output_file": "zoho_deluge_docs.md",
                "deep_crawl": False,
                "max_pages": 0,
                "status": "Success",
                "pages_crawled": 1,
                "file_size_kb": round(stat.st_size / 1024, 1),
                "duration_seconds": 2.27,
                "log": "Successfully extracted canonical Zoho Deluge documentation overview (103,914 chars)."
            })
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(seed, f, indent=2)


def get_history() -> List[Dict[str, Any]]:
    """Retrieve full execution history sorted latest first."""
    init_history()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return sorted(data, key=lambda x: x.get("timestamp", ""), reverse=True)
    except Exception:
        return []


def save_history_entry(entry: Dict[str, Any]):
    """Append or update a history entry."""
    history = get_history()
    # Check if existing id
    idx = next((i for i, item in enumerate(history) if item.get("id") == entry.get("id")), -1)
    if idx >= 0:
        history[idx] = entry
    else:
        history.insert(0, entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def get_schedule_config() -> Dict[str, Any]:
    """Load schedule configuration."""
    default_config = {
        "enabled": False,
        "frequency": "Daily",  # Hourly, Daily, Weekly, Custom
        "time_of_day": "02:00",
        "custom_interval_hours": 12,
        "deep_crawl": True,
        "max_pages": 0,  # 0 for all pages
        "target_url": "https://www.zoho.com/deluge/help/",
        "output_filename": "zoho_deluge_scheduled.md",
        "last_run": None,
        "next_run": None
    }
    if not os.path.exists(SCHEDULE_FILE):
        save_schedule_config(default_config)
        return default_config
    try:
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            for k, v in default_config.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    except Exception:
        return default_config


def calculate_next_run(cfg: Dict[str, Any]) -> Optional[str]:
    """Calculate the next scheduled run timestamp based on current configuration."""
    if not cfg.get("enabled"):
        return None
    
    now = datetime.now()
    freq = cfg.get("frequency", "Daily")

    if freq == "Hourly":
        next_dt = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    elif freq == "Daily":
        t_str = cfg.get("time_of_day", "02:00")
        try:
            hour, minute = map(int, t_str.split(":"))
        except ValueError:
            hour, minute = 2, 0
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        next_dt = candidate
    elif freq == "Weekly":
        t_str = cfg.get("time_of_day", "02:00")
        try:
            hour, minute = map(int, t_str.split(":"))
        except ValueError:
            hour, minute = 2, 0
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        # Next Monday
        days_ahead = (7 - candidate.weekday()) % 7
        if days_ahead == 0 and candidate <= now:
            days_ahead = 7
        candidate += timedelta(days=days_ahead)
        next_dt = candidate
    else:  # Custom
        hours = max(1, cfg.get("custom_interval_hours", 12))
        next_dt = now + timedelta(hours=hours)

    return next_dt.strftime("%Y-%m-%d %H:%M:%S")


def save_schedule_config(cfg: Dict[str, Any]):
    """Save schedule configuration with updated next_run estimation."""
    if cfg.get("enabled"):
        cfg["next_run"] = calculate_next_run(cfg)
    else:
        cfg["next_run"] = None
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def get_available_datasets() -> List[Dict[str, Any]]:
    """Find all generated markdown documentation files and calculate metadata."""
    datasets = []
    # Search in root and in data/
    candidates = []
    for f in os.listdir(BASE_DIR):
        if f.endswith(".md") and not f.startswith("."):
            candidates.append(os.path.join(BASE_DIR, f))
    if os.path.exists(DATA_DIR):
        for f in os.listdir(DATA_DIR):
            if f.endswith(".md"):
                candidates.append(os.path.join(DATA_DIR, f))

    for path in set(candidates):
        try:
            stat = os.stat(path)
            size_kb = round(stat.st_size / 1024, 1)
            modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            filename = os.path.basename(path)
            
            # Quick analysis of content
            line_count = 0
            word_count = 0
            headings = []
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line_count += 1
                    word_count += len(line.split())
                    if line.startswith("#"):
                        h = line.strip()
                        if len(headings) < 50:
                            headings.append(h)

            est_tokens = int(word_count * 1.3)

            datasets.append({
                "filename": filename,
                "path": path,
                "size_kb": size_kb,
                "modified": modified,
                "lines": line_count,
                "words": word_count,
                "estimated_tokens": est_tokens,
                "headings": headings
            })
        except Exception:
            pass

    return sorted(datasets, key=lambda x: x["modified"], reverse=True)


def calculate_metrics() -> Dict[str, Any]:
    """Compute overall dashboard statistics."""
    history = get_history()
    datasets = get_available_datasets()
    schedules = get_schedule_config()

    total_runs = len(history)
    successful_runs = sum(1 for h in history if h.get("status") == "Success")
    success_rate = round((successful_runs / total_runs * 100), 1) if total_runs > 0 else 0.0
    
    total_pages_crawled = sum(h.get("pages_crawled", 0) for h in history if h.get("status") == "Success")
    total_dataset_size_kb = sum(d["size_kb"] for d in datasets)
    total_words = sum(d["words"] for d in datasets)

    last_run_time = history[0]["timestamp"] if history else "Never"

    return {
        "total_runs": total_runs,
        "successful_runs": successful_runs,
        "success_rate": success_rate,
        "total_pages_crawled": total_pages_crawled,
        "total_datasets": len(datasets),
        "total_dataset_size_kb": total_dataset_size_kb,
        "total_words": total_words,
        "last_run_time": last_run_time,
        "schedule_active": schedules.get("enabled", False),
        "next_scheduled_run": schedules.get("next_run") or "None"
    }


# Import crawler functionality
from crawl_zoho_docs import crawl_zoho_documentation, DEFAULT_TARGET_URL, CANONICAL_DELUGE_URL


async def execute_crawl_job(
    target_url: str,
    output_filename: str,
    deep_crawl: bool = False,
    max_pages: int = 0,
    request_delay: float = 0.5,
    trigger_type: str = "Manual",
    status_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """Execute a crawling job with telemetry and record to history."""
    run_id = f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    start_time = datetime.now()
    output_path = os.path.join(BASE_DIR, output_filename)

    if status_callback:
        status_callback(f"Initializing crawler for {target_url}...")

    entry = {
        "id": run_id,
        "timestamp": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "trigger_type": trigger_type,
        "target_url": target_url,
        "output_file": output_filename,
        "deep_crawl": deep_crawl,
        "max_pages": max_pages,
        "status": "Running",
        "pages_crawled": 0,
        "file_size_kb": 0.0,
        "duration_seconds": 0.0,
        "log": f"Started extraction job {run_id}"
    }
    save_history_entry(entry)

    try:
        t0 = time.time()
        success = await crawl_zoho_documentation(
            start_url=target_url,
            output_file=output_path,
            deep_crawl=deep_crawl,
            max_pages=max_pages,
            request_delay=request_delay
        )
        duration = round(time.time() - t0, 2)
        
        if success and os.path.exists(output_path):
            file_size_kb = round(os.path.getsize(output_path) / 1024, 1)
            # Count how many sections were generated
            pages_count = 1
            with open(output_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if line.startswith("## ") and "." in line[:6]:
                        pages_count += 1
            
            entry["status"] = "Success"
            entry["pages_crawled"] = max(1, pages_count - 1)
            entry["file_size_kb"] = file_size_kb
            entry["duration_seconds"] = duration
            entry["log"] = f"Extraction completed successfully in {duration}s. Saved {file_size_kb} KB to {output_filename}."
        else:
            entry["status"] = "Failed"
            entry["duration_seconds"] = duration
            entry["log"] = f"Extraction failed or returned empty payload after {duration}s."

    except Exception as e:
        duration = round((datetime.now() - start_time).total_seconds(), 2)
        entry["status"] = "Failed"
        entry["duration_seconds"] = duration
        entry["log"] = f"Error during extraction: {str(e)}"

    save_history_entry(entry)
    return entry


def sync_vector_database(dataset_path: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
    """
    Incrementally sync ChromaDB vector database with the latest documentation dataset.
    Only new or modified chunks will be embedded and updated.
    """
    from vector_setup import compare_and_update_chromadb, DEFAULT_DATA_FILE
    target = dataset_path or (
        os.path.join(DATA_DIR, "zoho_deluge_all_docs.md")
        if os.path.exists(os.path.join(DATA_DIR, "zoho_deluge_all_docs.md"))
        else DEFAULT_DATA_FILE
    )
    return compare_and_update_chromadb(new_data=target, dry_run=dry_run, verbose=False)
