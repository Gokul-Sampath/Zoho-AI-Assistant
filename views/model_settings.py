"""
Corporate ERP - AI Model Settings & Llama 3 Optimization View
Provides fine-grained inference parameter tuning, Llama 3 optimization profiles,
system prompt configuration, and real-time hardware diagnostics for Ollama.
"""

import os
import time
import streamlit as st
import ollama
import auth

# Page Header
st.title("⚙️ AI Engine Settings & Llama 3 Optimization")
st.caption("Fine-tune Ollama inference parameters, configure token limits, and inspect hardware diagnostics.")

# Initialize or retrieve shared parameter state
if "llama3_params" not in st.session_state:
    st.session_state.llama3_params = {
        "temperature": 0.2,
        "top_p": 0.9,
        "context_window": 4096,
        "repeat_penalty": 1.15,
        "num_predict": 1536,
        "selected_model": "llama3:8b"
    }

user = auth.get_current_user() or {}
is_admin = auth.is_admin()

# Status overview card
col_s1, col_s2, col_s3, col_s4 = st.columns(4)

# Test Ollama connection
ollama_online = False
installed_models = []
try:
    models_res = ollama.list()
    installed_models = [m.model for m in models_res.models]
    ollama_online = True
except Exception:
    pass

col_s1.metric("Ollama Engine", "Online" if ollama_online else "Offline", delta="Active" if ollama_online else "Error")
col_s2.metric("Active LLM", st.session_state.llama3_params.get("selected_model", "llama3:8b"))
col_s3.metric("Context Ceiling", f"{st.session_state.llama3_params.get('context_window', 4096):,} tokens")
col_s4.metric("User Access", user.get("badge", "Developer"))

st.markdown("---")

tab_tuning, tab_diagnostics, tab_presets = st.tabs(["🎛️ Hyperparameter Optimization", "🖥️ Hardware Diagnostics & Benchmark", "📑 Optimization Profiles"])

with tab_tuning:
    st.subheader("Llama 3 Runtime Parameters")
    st.caption("Configures temperature, sampling bounds, and memory context for optimal Deluge code generation.")

    if not is_admin:
        st.info("ℹ️ Your account has **Limited Access**. You may view optimization parameters, but changes require Administrator privileges.")

    c_m1, c_m2 = st.columns(2)
    with c_m1:
        default_model = st.session_state.llama3_params.get("selected_model", "llama3:8b")
        model_options = installed_models if installed_models else ["llama3:8b", "llama3:latest", "llama3"]
        model_idx = model_options.index(default_model) if default_model in model_options else 0
        
        chosen_model = st.selectbox(
            "Selected Ollama Model",
            options=model_options,
            index=model_idx,
            disabled=not is_admin,
            help="Select local model for Deluge Assistant inference."
        )

    with c_m2:
        context_window = st.select_slider(
            "Context Window (num_ctx)",
            options=[2048, 4096, 8192, 16384],
            value=st.session_state.llama3_params.get("context_window", 8192),
            disabled=not is_admin,
            help="Max tokens retained in working memory. 8192 is optimal for Deluge multi-page documentation."
        )

    st.markdown("##### Sampling & Determinism (Deluge Code Precision)")
    c_p1, c_p2 = st.columns(2)
    
    with c_p1:
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=float(st.session_state.llama3_params.get("temperature", 0.2)),
            step=0.05,
            disabled=not is_admin,
            help="Low temperature (0.1 - 0.3) ensures deterministic, syntactically rigid Deluge code without hallucinations."
        )
        top_p = st.slider(
            "Top-P (Nucleus Sampling)",
            min_value=0.1,
            max_value=1.0,
            value=float(st.session_state.llama3_params.get("top_p", 0.9)),
            step=0.05,
            disabled=not is_admin,
            help="Limits candidate tokens to cumulative probability mass."
        )

    with c_p2:
        repeat_penalty = st.slider(
            "Repetition Penalty",
            min_value=1.0,
            max_value=1.5,
            value=float(st.session_state.llama3_params.get("repeat_penalty", 1.15)),
            step=0.05,
            disabled=not is_admin,
            help="Penalizes repeated tokens. Critical to avoid infinite loops in generated syntax."
        )
        num_predict = st.slider(
            "Max Output Tokens (num_predict)",
            min_value=512,
            max_value=4096,
            value=int(st.session_state.llama3_params.get("num_predict", 2048)),
            step=256,
            disabled=not is_admin,
            help="Maximum length of code responses and technical guides."
        )

    if is_admin:
        if st.button("💾 Apply & Save Optimization Parameters", type="primary", use_container_width=True):
            st.session_state.llama3_params = {
                "temperature": temperature,
                "top_p": top_p,
                "context_window": context_window,
                "repeat_penalty": repeat_penalty,
                "num_predict": num_predict,
                "selected_model": chosen_model
            }
            st.success("✅ Parameters updated successfully! Applied to all subsequent Deluge AI queries.")


with tab_diagnostics:
    st.subheader("Local Inference Engine Diagnostics")
    st.caption("Real-time telemetry from Ollama local daemon (`http://localhost:11434`).")

    col_d1, col_d2 = st.columns([1.5, 1])

    with col_d1:
        st.markdown("##### Installed Local Models")
        if installed_models:
            for m in installed_models:
                is_active = m == st.session_state.llama3_params.get("selected_model")
                badge = "🟢 ACTIVE" if is_active else "AVAILABLE"
                st.markdown(f"* **`{m}`** — `{badge}`")
        else:
            st.warning("No models found in Ollama repository.")

        st.markdown("##### Performance Benchmark")
        test_prompt = "Return single-line Deluge code: info 'ERP Benchmark';"
        if st.button("⚡ Run Latency & Throughput Benchmark"):
            with st.spinner("Executing inference benchmark on local Llama 3 instance..."):
                t_start = time.time()
                try:
                    res = ollama.chat(
                        model=st.session_state.llama3_params.get("selected_model", "llama3"),
                        messages=[{"role": "user", "content": test_prompt}],
                        options={
                            "temperature": st.session_state.llama3_params.get("temperature", 0.2),
                            "num_predict": 128
                        }
                    )
                    t_latency = round((time.time() - t_start) * 1000, 1)
                    st.success(f"Benchmark Complete! Total latency: **{t_latency} ms**")
                    st.code(res["message"]["content"], language="deluge")
                except Exception as e:
                    st.error(f"Benchmark failed: {e}")

    with col_d2:
        with st.container(border=True):
            st.markdown("##### 🛡️ Architecture & Offload")
            st.markdown("""
            * **Model Base:** Meta Llama-3-8B-Instruct
            * **Quantization:** Q4_0 (4-bit integer weights)
            * **Embeddings:** `nomic-embed-text` (768-dim)
            * **Context Memory:** Dynamic KV-cache paging
            * **Vector Engine:** ChromaDB 1.5.x
            * **Hosting:** 100% Local / Zero egress
            """)


with tab_presets:
    st.subheader("Enterprise Profile Presets")
    st.caption("Apply pre-configured optimization profiles based on your workflow needs.")

    c_pre1, c_pre2, c_pre3 = st.columns(3)

    with c_pre1:
        with st.container(border=True):
            st.markdown("##### 🎯 Rigid Deluge Code")
            st.caption("Strict syntax compliance. Zero creativity or hallucination. Ideal for production workflows.")
            st.markdown("• Temp: `0.1`  \n• Top-P: `0.85`  \n• Context: `8192`")
            if is_admin and st.button("Apply Code Profile", use_container_width=True):
                st.session_state.llama3_params["temperature"] = 0.1
                st.session_state.llama3_params["top_p"] = 0.85
                st.session_state.llama3_params["repeat_penalty"] = 1.2
                st.success("Applied 'Rigid Deluge Code' profile!")
                st.rerun()

    with c_pre2:
        with st.container(border=True):
            st.markdown("##### 💡 Architectural Advice")
            st.caption("Balanced configuration for designing Zoho Creator multi-app solutions and database schemas.")
            st.markdown("• Temp: `0.3`  \n• Top-P: `0.9`  \n• Context: `8192`")
            if is_admin and st.button("Apply Architecture Profile", use_container_width=True):
                st.session_state.llama3_params["temperature"] = 0.3
                st.session_state.llama3_params["top_p"] = 0.9
                st.session_state.llama3_params["repeat_penalty"] = 1.15
                st.success("Applied 'Architectural Advice' profile!")
                st.rerun()

    with c_pre3:
        with st.container(border=True):
            st.markdown("##### ⚡ High-Speed Drafting")
            st.caption("Rapid iterative prototyping with low token prediction ceilings for maximum throughput.")
            st.markdown("• Temp: `0.2`  \n• Predict: `1024`  \n• Context: `4096`")
            if is_admin and st.button("Apply Speed Profile", use_container_width=True):
                st.session_state.llama3_params["temperature"] = 0.2
                st.session_state.llama3_params["num_predict"] = 1024
                st.session_state.llama3_params["context_window"] = 4096
                st.success("Applied 'High-Speed Drafting' profile!")
                st.rerun()
