import re

with open("app.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update Settings UI
old_settings = """    st.markdown("## Integrations")
    st.text_input(
        "Xeno-Canto API Key (Required for audio)",
        key="xc_api_key",
        type="password",
        help="Xeno-Canto API v3 now requires a free API key. Get one at xeno-canto.org/account"
    )
    
    st.markdown("---")"""
code = code.replace(old_settings, "")

# 2. Update session state for xc_api_key
old_session = """if 'xc_api_key' not in st.session_state:\n    st.session_state.xc_api_key = \"\"\n"""
code = code.replace(old_session, "")

# 3. Update the call to fetch_bird_calls
old_call = """            future_recordings = executor.submit(fetch_bird_calls, st.session_state.selected_bird, st.session_state.xc_api_key, 5)"""
new_call = """            api_key = st.secrets.get("XENO_CANTO_API_KEY", "")
            future_recordings = executor.submit(fetch_bird_calls, st.session_state.selected_bird, api_key, 5)"""
code = code.replace(old_call, new_call)

# 4. Update fetch_bird_calls error message
old_err = """    if not api_key:
        return {"error": "Xeno-Canto now requires a free API key (v3). Please enter yours in the Settings tab."}"""
new_err = """    if not api_key:
        return {"error": "Xeno-Canto now requires a free API key (v3). Please add XENO_CANTO_API_KEY to your Streamlit secrets."}"""
code = code.replace(old_err, new_err)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(code)
