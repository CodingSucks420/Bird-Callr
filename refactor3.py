import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Fix st.html space issue by moving the manifest link
code = code.replace("<!-- PWA Manifest Injection -->\n    <link rel=\"manifest\" href=\"app/static/manifest.json\">", "")
code = code.replace("    <!-- PWA Manifest Injection -->\n    <link rel=\"manifest\" href=\"app/static/manifest.json\">\n", "")

js_old = """        // 1. Theme Color Meta Tag"""
js_new = """        // 1. Theme Color Meta Tag & Manifest
        if (!document.querySelector('link[rel="manifest"]')) {
            document.head.insertAdjacentHTML('beforeend', '<link rel="manifest" href="app/static/manifest.json">');
        }"""
code = code.replace(js_old, js_new)

# 2. Fix the Pill colors
pill_css = """
        div[data-testid="stSegmentedControl"] button {
            background-color: {glass_bg} !important;
            border: 1px solid {glass_border} !important;
            color: {text_color} !important;
            border-radius: 20px !important;
        }
        div[data-testid="stSegmentedControl"] button[aria-selected="true"] {
            background: {btn_gradient} !important;
            color: white !important;
            border: none !important;
        }
        
        /* Premium Skeleton Loader */"""
code = code.replace("        /* Premium Skeleton Loader */", pill_css)

# 3. Fix Xeno-canto API
api_key_state = """if 'explore_family' not in st.session_state:
    st.session_state.explore_family = ""
if 'xc_api_key' not in st.session_state:
    st.session_state.xc_api_key = ""
if 'favorites' not in st.session_state:"""
code = re.sub(r"if 'explore_family' not in st\.session_state:\n    st\.session_state\.explore_family = \"\"\nif 'favorites' not in st\.session_state:", api_key_state, code)

settings_old = """    st.session_state.birdnet_api_url = st.text_input(
        "BirdNET AI Server URL",
        value=st.session_state.birdnet_api_url,
        help="Paste a free community BirdNET endpoint or your own self-hosted API URL here."
    )
    
    st.markdown("---")"""

settings_new = """    st.session_state.birdnet_api_url = st.text_input(
        "BirdNET AI Server URL",
        value=st.session_state.birdnet_api_url,
        help="Paste a free community BirdNET endpoint or your own self-hosted API URL here."
    )
    
    st.session_state.xc_api_key = st.text_input(
        "Xeno-Canto API Key (Required for audio)",
        value=st.session_state.xc_api_key,
        type="password",
        help="Xeno-Canto API v3 now requires a free API key. Get one at xeno-canto.org/account"
    )
    
    st.markdown("---")"""
code = code.replace(settings_old, settings_new)


fetch_api_old = """@st.cache_data(ttl=86400, max_entries=100, show_spinner=False)
def fetch_bird_calls(species_name, limit=5):
    try:
        query = urllib.parse.quote(species_name)
        url = f"https://xeno-canto.org/api/2/recordings?query={query}"
        response = requests.get(url, timeout=10)"""

fetch_api_new = """@st.cache_data(ttl=86400, max_entries=100, show_spinner=False)
def fetch_bird_calls(species_name, api_key, limit=5):
    if not api_key:
        return {"error": "Xeno-Canto now requires a free API key (v3). Please enter yours in the Settings tab."}
    try:
        query = urllib.parse.quote(species_name)
        url = f"https://xeno-canto.org/api/3/recordings?query={query}&key={api_key}"
        response = requests.get(url, timeout=10)"""
code = code.replace(fetch_api_old, fetch_api_new)


api_call_old = """recordings = fetch_bird_calls(st.session_state.selected_bird, 5)"""
api_call_new = """recordings = fetch_bird_calls(st.session_state.selected_bird, st.session_state.xc_api_key, 5)"""
code = code.replace(api_call_old, api_call_new)


with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Done!")
