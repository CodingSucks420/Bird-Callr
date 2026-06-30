import re

with open("app.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Remove Obsolete AI Settings
# a. Remove from session state initialization
code = code.replace("""if 'birdnet_api_url' not in st.session_state:\n    st.session_state.birdnet_api_url = "https://birdnet.cornell.edu/api/v1/identify"\n""", "")

# b. Remove from Settings Tab
settings_ai = """    st.markdown("## AI Identification Settings")
    st.session_state.birdnet_api_url = st.text_input(
        "BirdNET AI Server URL",
        value=st.session_state.birdnet_api_url,
        help="Paste a free community BirdNET endpoint or your own self-hosted API URL here."
    )
    
    st.session_state.xc_api_key = st.text_input(
        "Xeno-Canto API Key (Required for audio)",
        value=st.session_state.xc_api_key,
        type="password",
        help="Xeno-Canto API v3 now requires a free API key. Get one at xeno-canto.org/account"
    )"""
new_settings_ai = """    st.markdown("## Integrations")
    st.text_input(
        "Xeno-Canto API Key (Required for audio)",
        key="xc_api_key",
        type="password",
        help="Xeno-Canto API v3 now requires a free API key. Get one at xeno-canto.org/account"
    )"""
code = code.replace(settings_ai, new_settings_ai)

# c. Update query_birdnet_api signature and usage
code = code.replace("""def query_birdnet_api(audio_bytes, api_url):""", """def query_birdnet_api(audio_bytes):""")
code = code.replace("""result = query_birdnet_api(audio_bytes, st.session_state.birdnet_api_url)""", """result = query_birdnet_api(audio_bytes)""")


# 2. Fix Settings UI State Bug (Theme and Text Size)
old_settings_display = """    st.session_state.text_size = st.radio(
        "Text Size", 
        ["Normal", "Large", "Extra Large"],
        index=["Normal", "Large", "Extra Large"].index(st.session_state.text_size)
    )
    st.session_state.theme = st.radio(
        "Theme", 
        ["Day Mode", "Night Mode"],
        index=["Day Mode", "Night Mode"].index(st.session_state.theme)
    )"""
new_settings_display = """    st.radio(
        "Text Size", 
        ["Normal", "Large", "Extra Large"],
        key="text_size"
    )
    st.radio(
        "Theme", 
        ["Day Mode", "Night Mode"],
        key="theme"
    )"""
code = code.replace(old_settings_display, new_settings_display)


# 3. Implement True Concurrency
# We need to import concurrent.futures at the top
code = code.replace("import streamlit as st\n", "import streamlit as st\nimport concurrent.futures\n")

old_concurrency = """        # -----------------------------------------------------
        # CONCURRENT API FETCHING & SKELETON LOADER
        # -----------------------------------------------------
        skel_ph = st.empty()
        skel_ph.markdown("<div class='skeleton' style='height: 350px;'></div>", unsafe_allow_html=True)
        
        search_img = fetch_bird_image(st.session_state.selected_bird)

        
        search_summary = fetch_bird_summary(st.session_state.selected_bird)

        
        search_tax = fetch_bird_taxonomy(st.session_state.selected_bird)

        
        recordings = fetch_bird_calls(st.session_state.selected_bird, st.session_state.xc_api_key, 5)
            
        skel_ph.empty() # Remove skeleton once concurrent fetching is complete
        # -----------------------------------------------------"""

new_concurrency = """        # -----------------------------------------------------
        # CONCURRENT API FETCHING & SKELETON LOADER
        # -----------------------------------------------------
        skel_ph = st.empty()
        skel_ph.markdown("<div class='skeleton' style='height: 350px;'></div>", unsafe_allow_html=True)
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_img = executor.submit(fetch_bird_image, st.session_state.selected_bird)
            future_summary = executor.submit(fetch_bird_summary, st.session_state.selected_bird)
            future_tax = executor.submit(fetch_bird_taxonomy, st.session_state.selected_bird)
            future_recordings = executor.submit(fetch_bird_calls, st.session_state.selected_bird, st.session_state.xc_api_key, 5)
            
            search_img = future_img.result()
            search_summary = future_summary.result()
            search_tax = future_tax.result()
            recordings = future_recordings.result()
            
        skel_ph.empty() # Remove skeleton once concurrent fetching is complete
        # -----------------------------------------------------"""
code = code.replace(old_concurrency, new_concurrency)

# 4. Fix Keyword Arguments (width="stretch")
code = code.replace("""width="stretch\"""", """use_container_width=True""")


with open("app.py", "w", encoding="utf-8") as f:
    f.write(code)
