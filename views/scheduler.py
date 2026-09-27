"""
Corporate ERP - Task Scheduler & Automation Module
Orchestrates automated recurring documentation scraping, delta sync jobs, and cron cadences.
"""

import streamlit as st
import scraper_manager
import auth

# Enforce Administrator (Full Access) permission
auth.require_admin_permission()

current_user = auth.get_current_user() or {}

st.title("⏱️ Automation & Task Scheduling")
st.caption("Configure recurring background jobs, automation cadences, and automated sync policies.")

cfg = scraper_manager.get_schedule_config()

# Scheduler Status Banner
if cfg.get("enabled"):
    st.markdown(
        f"<div style='border: 1px solid #86efac; background: #f0fdf4; border-radius: 8px; padding: 14px 18px; margin-bottom: 16px;'>"
        f"<div style='display: flex; justify-content: space-between; align-items: center;'>"
        f"<div><span style='font-size: 1.1rem; font-weight: 700; color: #166534;'>🟢 AUTOMATION ENGINE ACTIVE</span><br>"
        f"<span style='color: #15803d; font-size: 0.9rem;'>Cadence: <b>{cfg.get('frequency')}</b> (at <b>{cfg.get('time_of_day', '02:00')}</b>) &nbsp;•&nbsp; Destination: <code>{cfg.get('output_filename')}</code></span></div>"
        f"<span style='background: #22c55e; color: white; padding: 4px 12px; border-radius: 9999px; font-weight: 600; font-size: 0.8rem;'>SCHEDULED</span>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True
    )
else:
    st.markdown(
        f"<div style='border: 1px solid #fed7aa; background: #fff7ed; border-radius: 8px; padding: 14px 18px; margin-bottom: 16px;'>"
        f"<span style='font-size: 1.1rem; font-weight: 700; color: #9a3412;'>⏸️ AUTOMATION ENGINE PAUSED</span><br>"
        f"<span style='color: #c2410c; font-size: 0.9rem;'>Scheduled crawls are currently inactive. Enable automation below to start recurring synchronization.</span>"
        f"</div>",
        unsafe_allow_html=True
    )

st.markdown("---")

col_form, col_info = st.columns([1.3, 1], gap="large")

with col_form:
    st.subheader("Configure Schedule Parameters")
    with st.form("detailed_schedule_form"):
        enable_toggle = st.toggle("Enable Automation Schedule", value=cfg.get("enabled", False))

        freq_options = ["Hourly", "Daily", "Weekly", "Custom Interval"]
        current_freq = cfg.get("frequency", "Daily")
        freq_idx = freq_options.index(current_freq) if current_freq in freq_options else 1

        selected_freq = st.selectbox("Schedule Cadence", options=freq_options, index=freq_idx)

        c1, c2 = st.columns(2)
        with c1:
            time_of_day = st.text_input(
                "Execution Time (HH:MM UTC)",
                value=cfg.get("time_of_day", "02:00"),
                help="Applies to Daily and Weekly schedules (e.g., 03:00)"
            )
        with c2:
            custom_interval = st.number_input(
                "Custom Interval (Hours)",
                min_value=1,
                max_value=168,
                value=int(cfg.get("custom_interval_hours", 12)),
                help="Applies when 'Custom Interval' is selected."
            )

        st.markdown("##### Crawler Directives for Scheduled Run")
        target_url = st.text_input("Canonical Root URL", value=cfg.get("target_url", "https://www.zoho.com/deluge/help/"))
        output_file = st.text_input("Destination Dataset File", value=cfg.get("output_filename", "zoho_deluge_scheduled.md"))
        deep_crawl = st.checkbox("Deep Crawl Linked Subpages", value=cfg.get("deep_crawl", True))
        max_pages = st.number_input(
            "Max Pages (0 = All Pages)",
            min_value=0,
            max_value=2000,
            value=int(cfg.get("max_pages", 0)),
            help="Set to 0 to crawl ALL ~740 pages on schedule."
        )

        submit_btn = st.form_submit_button("💾 Save & Activate Schedule", type="primary", use_container_width=True)

    if submit_btn:
        updated = {
            "enabled": enable_toggle,
            "frequency": selected_freq,
            "time_of_day": time_of_day,
            "custom_interval_hours": custom_interval,
            "deep_crawl": deep_crawl,
            "max_pages": max_pages,
            "target_url": target_url,
            "output_filename": output_file,
            "last_run": cfg.get("last_run")
        }
        scraper_manager.save_schedule_config(updated)
        st.success("✅ Schedule configuration updated successfully!")
        st.rerun()

with col_info:
    st.subheader("📋 Automation Policy & Guidelines")
    with st.container(border=True):
        st.markdown("""
        * **Off-Peak Execution**: Scheduled runs should be assigned between `01:00` and `04:00` UTC to prevent network contention.
        * **Politeness Throttling**: Automated crawler retains safe delays (0.5s) per request to respect Zoho rate limiters.
        * **Diff Sync Pipeline**: After scheduled scrapes complete, the delta sync pipeline updates modified vectors in ChromaDB automatically.
        * **Audit Retention**: Scheduled execution logs are preserved for 90 days in `execution_history.json`.
        """)

    st.markdown("##### Recent Scheduled Runs")
    history = scraper_manager.get_history()
    sched_runs = [h for h in history if "Schedule" in h.get("trigger_type", "")]
    if not sched_runs:
        st.info("No scheduled runs recorded yet. Active scheduled runs will appear here.")
    else:
        for r in sched_runs[:5]:
            st.write(f"• **{r['timestamp']}** — {r['status']} ({r['pages_crawled']} pages, {r['file_size_kb']} KB)")
