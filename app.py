import streamlit as st
import concurrent.futures
import urllib.parse
import requests
import datetime
import random
import re
import secrets
import tempfile
import os
import streamlit.components.v1 as components
from audio_recorder_streamlit import audio_recorder
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer

# 1. Page Configuration - Must be at the very top
st.set_page_config(page_title="Feeder Echo", page_icon="🐦", layout="centered")


# Initialize session states
if 'selected_bird' not in st.session_state:
    st.session_state.selected_bird = ""

@st.cache_resource
def get_analyzer():
    # Initialize the BirdNET Analyzer. This downloads the model on first run.
    return Analyzer()

if 'home_search' not in st.session_state:
    st.session_state.home_search = ""
if 'recent_searches' not in st.session_state:
    st.session_state.recent_searches = []
if 'explore_family' not in st.session_state:
    st.session_state.explore_family = ""
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'text_size' not in st.session_state:
    st.session_state.text_size = "Large"
if 'theme' not in st.session_state:
    st.session_state.theme = "Night Mode"
if 'tour_seen' not in st.session_state:
    st.session_state.tour_seen = False

@st.cache_data(ttl=86400, max_entries=500, show_spinner=False)
def resolve_bird_name(query_name):
    if not query_name:
        return ""
    try:
        headers = {"User-Agent": "BirdCallr/1.0 (contact@birdcallr.app)"}
        url = f"https://en.wikipedia.org/w/api.php?action=query&redirects=1&format=json&titles={urllib.parse.quote(query_name)}"
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if "title" in page_data:
                    title = page_data["title"]
                    if " (bird)" in title:
                        title = title.replace(" (bird)", "")
                    return title.title()
    except Exception:
        pass
    return query_name.title()

def set_bird(bird_name):
    resolved_name = resolve_bird_name(bird_name)
    st.session_state.selected_bird = resolved_name
    if resolved_name:
        if resolved_name in st.session_state.recent_searches:
            st.session_state.recent_searches.remove(resolved_name)
        st.session_state.recent_searches.insert(0, resolved_name)
        if len(st.session_state.recent_searches) > 5:
            st.session_state.recent_searches.pop()

def toggle_favorite(bird_name):
    if bird_name in st.session_state.favorites:
        st.session_state.favorites.remove(bird_name)
    else:
        st.session_state.favorites.append(bird_name)

@st.cache_data(ttl=86400, max_entries=100, show_spinner=False)
def fetch_bird_image(species_name):
    try:
        headers = {"User-Agent": "BirdCallr/1.0 (contact@birdcallr.app)"}
        url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&redirects=1&format=json&piprop=original&titles={urllib.parse.quote(species_name)}"
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if "original" in page_data:
                    return page_data["original"]["source"]
    except Exception:
        pass
    return None

@st.cache_data(ttl=86400, max_entries=100, show_spinner=False)
def fetch_bird_summary(species_name):
    try:
        headers = {"User-Agent": "BirdCallr/1.0 (contact@birdcallr.app)"}
        url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&redirects=1&exintro=1&explaintext=1&titles={urllib.parse.quote(species_name)}&format=json"
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if "extract" in page_data:
                    return page_data["extract"]
    except Exception:
        pass
    return None

@st.cache_data(ttl=86400, max_entries=100, show_spinner=False)
def fetch_bird_taxonomy(species_name):
    try:
        headers = {"User-Agent": "BirdCallr/1.0 (contact@birdcallr.app)"}
        url = f"https://en.wikipedia.org/w/api.php?action=parse&page={urllib.parse.quote(species_name)}&prop=text&redirects=1&section=0&format=json"
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            html = data.get("parse", {}).get("text", {}).get("*", "")
            
            family_match = re.search(r'>Family:</th>\s*<td[^>]*>(?:<a[^>]*>)?([^<]{1,50})', html)
            status_match = re.search(r'Conservation status.{0,200}?<a[^>]*>([^<]{1,50})</a>', html, re.DOTALL)
            
            family = family_match.group(1).strip() if family_match else None
            status = status_match.group(1).strip() if status_match else None
            return {"family": family, "status": status}
    except Exception:
        pass
    return {"family": None, "status": None}

@st.cache_data(ttl=86400, max_entries=100, show_spinner=False)
def fetch_bird_calls(species_name, api_key, limit=5):
    if not api_key:
        return {"error": "Xeno-Canto now requires a free API key (v3). Please add XENO_CANTO_API_KEY to your Streamlit secrets."}
    try:
        # Xeno-canto v3 API requires tags for queries, e.g. en:"Blue Jay"
        query = urllib.parse.quote(f'en:"{species_name}"')
        url = f"https://xeno-canto.org/api/3/recordings?query={query}&key={api_key}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        recordings = data.get("recordings", [])
        if not recordings:
            return None
        
        categories = {
            "🎶 Song": ["song"],
            "🚨 Alarm / Warning Call": ["alarm", "warning", "scold"],
            "✈️ Flight Call": ["flight"],
            "🗣️ Standard Call": ["call", "contact call"]
        }
        
        curated = []
        used_ids = set()
        
        sorted_recordings = sorted(recordings, key=lambda x: str(x.get('q', 'Z')).upper())
        
        for cat_name, keywords in categories.items():
            for rec in sorted_recordings:
                if rec.get('id') in used_ids:
                    continue
                rec_type = str(rec.get('type', '')).lower()
                if any(kw in rec_type for kw in keywords):
                    rec['_curated_type'] = cat_name
                    curated.append(rec)
                    used_ids.add(rec.get('id'))
                    break
        
        for rec in sorted_recordings:
            if len(curated) >= limit:
                break
            if rec.get('id') not in used_ids:
                rec['_curated_type'] = "🎵 Other Recording"
                curated.append(rec)
                used_ids.add(rec.get('id'))
                
        return curated
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}

def query_birdnet_api(audio_bytes):
    try:
        import subprocess
        analyzer = get_analyzer()
        
        # Save raw audio_bytes to a temporary file (format unknown, could be webm/mp4 from iOS)
        with tempfile.NamedTemporaryFile(delete=False) as temp_in:
            temp_in.write(audio_bytes)
            temp_in_path = temp_in.name
            
        temp_out_path = temp_in_path + "_converted.wav"
        
        try:
            # Forcefully transcode any audio format to a clean 48kHz WAV using ffmpeg
            subprocess.run([
                "ffmpeg", "-y", "-i", temp_in_path, 
                "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", temp_out_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if not os.path.exists(temp_out_path):
                return {"error": "Failed to process audio format from device."}
                
            recording = Recording(analyzer, temp_out_path, min_conf=0.1)
            recording.analyze()
            
            if recording.detections:
                sorted_matches = sorted(recording.detections, key=lambda x: x['confidence'], reverse=True)[:3]
                matches_list = []
                for m in sorted_matches:
                    matches_list.append({
                        "species": m['common_name'],
                        "confidence": m['confidence'],
                        "scientific_name": m['scientific_name']
                    })
                return {"matches": matches_list}
            else:
                return {"error": "No bird sounds detected with enough confidence."}
        finally:
            if os.path.exists(temp_in_path):
                os.remove(temp_in_path)
            if os.path.exists(temp_out_path):
                os.remove(temp_out_path)
                
    except Exception as e:
        return {"error": str(e)}



# ----------------------------------------
# FIRST TIME GUIDED TOUR (Modal)
# ----------------------------------------
@st.dialog("Welcome to Bird Callr! 🦜")
def welcome_tour():
    st.markdown("""
Here is a quick guide on how to use your new aviary companion:

1. 🦜 **Tap a bird** on the Home screen to instantly hear its call.

2. 🎙️ **Use the microphone** to identify a bird singing in your yard.

3. ⭐ **Save your favorites** for easy access later.
""")
    if st.button("Let's Go!", use_container_width=True):
        st.session_state.tour_seen = True
        st.rerun()

if not st.session_state.tour_seen:
    st.session_state.tour_seen = True
    welcome_tour()


# ----------------------------------------
# 3-TAB MOBILE LAYOUT
# ----------------------------------------
tab_home, tab_fav, tab_set = st.tabs(["🏠 Home", "⭐ Favorites", "⚙️ Settings"])

# ----------------------------------------
# SETTINGS TAB
# ----------------------------------------
with tab_set:

    st.markdown("## Accessibility & Display")
    st.radio(
        "Text Size", 
        ["Normal", "Large", "Extra Large"],
        key="text_size"
    )
    st.radio(
        "Theme", 
        ["Day Mode", "Night Mode"],
        key="theme"
    )

# Dynamic CSS generation for Rich Aesthetics & Mobile PWA optimizations
if st.session_state.text_size == "Normal":
    base_size = "18px"; h1_size = "3.0rem"; btn_size = "1.2rem"
elif st.session_state.text_size == "Large":
    base_size = "22px"; h1_size = "4.0rem"; btn_size = "1.5rem"
else:
    base_size = "26px"; h1_size = "5.0rem"; btn_size = "1.8rem"

# Dynamic Bird Auras Mapping
BIRD_AURAS_DAY = {
    "Northern Cardinal": ("#fee2e2", "#fecaca"), 
    "Blue Jay": ("#e0f2fe", "#bae6fd"),          
    "American Goldfinch": ("#fef9c3", "#fef08a"),
    "American Robin": ("#ffedd5", "#fed7aa"),    
    "Tufted Titmouse": ("#f3f4f6", "#e5e7eb"),   
    "Mourning Dove": ("#f5f5f4", "#e7e5e4"),     
    "Carolina Wren": ("#ffedd5", "#fdba74"),     
    "Black-capped Chickadee": ("#f3f4f6", "#d1d5db"),
    "Downy Woodpecker": ("#f8fafc", "#f1f5f9")   
}
BIRD_AURAS_NIGHT = {
    "Northern Cardinal": ("#450a0a", "#7f1d1d"), 
    "Blue Jay": ("#082f49", "#0c4a6e"),          
    "American Goldfinch": ("#422006", "#713f12"),
    "American Robin": ("#431407", "#7c2d12"),    
    "Tufted Titmouse": ("#1f2937", "#374151"),   
    "Mourning Dove": ("#292524", "#44403c"),     
    "Carolina Wren": ("#431407", "#7c2d12"),     
    "Black-capped Chickadee": ("#111827", "#1f2937"),
    "Downy Woodpecker": ("#0f172a", "#1e293b")   
}

if st.session_state.theme == "Day Mode":
    aura = BIRD_AURAS_DAY.get(st.session_state.selected_bird, ("#e0f2fe", "#bae6fd"))
    bg_gradient = f"linear-gradient(135deg, {aura[0]} 0%, {aura[1]} 100%)"
    glass_bg = "rgba(255, 255, 255, 0.9)"
    glass_border = "rgba(255, 255, 255, 0.8)"
    text_color = "#000000"
    sub_color = "#1e293b"
    shadow = "rgba(0, 0, 0, 0.1)"
    skeleton_bg = "rgba(255,255,255,0.8)"
else:
    aura = BIRD_AURAS_NIGHT.get(st.session_state.selected_bird, ("#0f172a", "#1e1b4b"))
    bg_gradient = f"linear-gradient(135deg, {aura[0]} 0%, {aura[1]} 100%)"
    glass_bg = "rgba(15, 23, 42, 0.9)"
    glass_border = "rgba(255, 255, 255, 0.3)"
    text_color = "#ffffff"
    sub_color = "#f8fafc"
    shadow = "rgba(0, 0, 0, 0.5)"
    skeleton_bg = "rgba(0,0,0,0.5)"

btn_gradient = "linear-gradient(135deg, #ff7e5f 0%, #feb47b 100%)"

# Inject Custom CSS, PWA Manifest Link, and Mobile Optimizations
st.html(f"""<style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&display=swap');
        
        html, body {{ touch-action: manipulation !important; }}
        .block-container {{
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            max-width: 100% !important;
        }}
        
        .stApp {{
            background: {bg_gradient} !important;
            background-attachment: fixed !important;
            transition: background 0.8s ease-in-out !important;
        }}
        
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden; pointer-events: none;}}
        
        html, body, [class*="css"], p, div, span {{
            font-family: 'Outfit', sans-serif !important;
            font-size: {base_size};
            color: {text_color};
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Outfit', sans-serif !important;
            color: {text_color} !important;
            font-weight: 700 !important;
        }}
        h1 {{ font-size: {h1_size} !important; font-weight: 800 !important; }}
        
        [data-baseweb="tab-panel"] {{
            background: {glass_bg} !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border-radius: 16px !important;
            border: 1px solid {glass_border} !important;
            padding: 20px !important;
            box-shadow: 0 8px 32px 0 {shadow} !important;
            animation: fadeIn 0.8s ease-in-out;
        }}

        .stTextInput input {{
            font-size: {btn_size} !important;
            padding: 12px 24px !important;
            border-radius: 50px !important;
            background: {glass_bg} !important;
            color: {text_color} !important;
            border: 1px solid {glass_border} !important;
            box-shadow: inset 0 2px 4px {shadow} !important;
            transition: all 0.3s ease;
        }}
        .stTextInput input:focus {{
            border-color: #ff7e5f !important;
            box-shadow: 0 0 0 2px rgba(255, 126, 95, 0.3) !important;
        }}
        
        .stButton>button {{
            width: 100%;
            height: 3.5em;
            font-size: {btn_size} !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
            border: none !important;
            background: {btn_gradient} !important;
            color: #ffffff !important;
            box-shadow: 0 4px 15px {shadow} !important;
            transition: all 0.3s ease !important;
        }}
    /* Clean Tab Navigation */
    button[data-baseweb="tab"] {{
        background-color: transparent !important;
        border: none !important;
        border-radius: 20px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}
    button[data-baseweb="tab"] p {{
        margin: 0 !important;
    }}
    button[data-baseweb="tab"]:hover {{
        background-color: rgba(255, 126, 95, 0.1) !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        background: linear-gradient(135deg, rgba(255,126,95,0.2) 0%, rgba(254,180,123,0.2) 100%) !important;
        border: 1px solid rgba(255, 126, 95, 0.5) !important;
    }}
        .stButton>button:hover {{
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 8px 25px rgba(255, 126, 95, 0.4) !important;
            color: #ffffff !important;
        }}
        .stButton>button:active {{
            transform: translateY(1px) scale(0.98);
        }}
        
        [data-baseweb="tab-list"] {{
            gap: 10px;
            margin-bottom: 1rem;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        audio {{
            width: 100%;
            border-radius: 50px;
            margin-top: 10px;
            transition: box-shadow 0.2s ease-in-out;
        }}
        

        audio::-webkit-media-controls-panel {{
            background-color: rgba(255, 126, 95, 0.2) !important;
            backdrop-filter: blur(5px) !important;
        }}
        audio::-webkit-media-controls-play-button, 
        audio::-webkit-media-controls-mute-button {{
            filter: sepia(100%) hue-rotate(320deg) saturate(500%) brightness(120%) !important;
        }}
        

        div[data-testid="stSegmentedControl"] button {{
            background-color: {glass_bg} !important;
            border: 1px solid {glass_border} !important;
            color: {text_color} !important;
            border-radius: 20px !important;
        }}
        div[data-testid="stSegmentedControl"] button[aria-selected="true"] {{
            background: {btn_gradient} !important;
            color: white !important;
            border: none !important;
        }}
        
        /* Premium Skeleton Loader */
        .skeleton {{
            animation: skeleton-loading 1.2s ease-in-out infinite alternate;
            border-radius: 16px;
            width: 100%;
        }}
        @keyframes skeleton-loading {{
            0% {{ background-color: {skeleton_bg}; opacity: 0.3; }}
            100% {{ background-color: {skeleton_bg}; opacity: 0.7; }}
        }}
        
        /* AI Radar Pulse Animation */
        .radar-pulse {{
            width: 60px; height: 60px;
            background: #ff7e5f;
            border-radius: 50%;
            margin: 20px auto;
            animation: radar 1.5s infinite ease-out;
        }}
        @keyframes radar {{
            0% {{ transform: scale(0.5); opacity: 1; }}
            100% {{ transform: scale(2.5); opacity: 0; }}
        }}
        
        @media (max-width: 768px) {{
            .stButton>button {{
                width: 100% !important;
                margin-bottom: 10px !important;
            }}
        }}
        /* Mobile Optimizations */
        @media (max-width: 768px) {{
            html, body, [class*="css"], p, div, span {{
                font-size: calc({base_size} * 0.8) !important;
            }}
            h1 {{ font-size: calc({h1_size} * 0.8) !important; }}
            .stButton>button {{ font-size: calc({btn_size} * 0.8) !important; }}
            [data-baseweb="dialog"] {{ width: 95vw !important; max-width: 95vw !important; padding: 10px !important; }}
        }}
    </style>
""")


# ----------------------------------------
# HOME TAB
# ----------------------------------------
with tab_home:
    try:
        st.image("logo.png", use_container_width=True)
    except Exception:
        pass

    st.title("Bird Callr")
    st.markdown("### **An Aviary Audio Companion**")
    st.markdown("---")
    
    st.markdown("## 🎙️ Identify by Sound")
    st.write("Hear a bird? Tap the microphone to record its call and instantly identify it!")
    
    audio_bytes = audio_recorder(text="Tap to Start / Tap to Stop", recording_color="#ff7e5f", neutral_color="#cbd5e1", icon_name="microphone", icon_size="4x", sample_rate=44100)
    
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        
        if "last_audio" not in st.session_state or st.session_state.last_audio != audio_bytes:
            anim_ph = st.empty()
            anim_ph.markdown("<div style='text-align:center;'><div class='radar-pulse'></div><p style='color:#ff7e5f; font-weight:bold;'>AI is listening...</p></div>", unsafe_allow_html=True)
            
            st.session_state.last_audio_result = query_birdnet_api(audio_bytes)
            st.session_state.last_audio = audio_bytes
            
            anim_ph.empty()
            
        result = st.session_state.last_audio_result
        
        if "error" in result:
            st.warning(f"Analysis failed: {result['error']}")
            if st.button("Try a Simulated Match Instead"):
                set_bird("Northern Cardinal")
                st.rerun()
        else:
            matches = result.get('matches', [])
            if matches:
                top_match = matches[0]
                species = top_match['species']
                conf = top_match['confidence']
                
                st.success(f"Top Match: **{species}** ({(conf*100):.1f}%)")
                
                if len(matches) > 1:
                    other_text = ", ".join([f"{m['species']} ({(m['confidence']*100):.1f}%)" for m in matches[1:3]])
                    st.info(f"Other possibilities: {other_text}")
                    
                if st.button(f"Load {species} Audio Results", use_container_width=True):
                    set_bird(species)
                    st.rerun()

    st.markdown("---")

    st.markdown("## 🌟 Bird of the Day")
    bird_list = ["Tufted Titmouse", "Mourning Dove", "Carolina Wren", "Black-capped Chickadee", "Downy Woodpecker", "Blue Jay", "Northern Cardinal", "American Goldfinch"]
    rng = random.Random(datetime.date.today().toordinal())
    bird_of_the_day = rng.choice(bird_list)

    st.write(f"Today's featured bird is the **{bird_of_the_day}**!")

    botd_img = fetch_bird_image(bird_of_the_day)
    if botd_img:
        st.image(botd_img, use_container_width=True, clamp=True)

    if st.button(f"Listen to the {bird_of_the_day}", key="botd_btn"):
        set_bird(bird_of_the_day)
        st.rerun()

    st.markdown("---")
    
    st.markdown("## 🎲 Discover")
    BIRD_LIST_EXPANDED = [
        "Northern Cardinal", "American Robin", "Blue Jay", "American Goldfinch", 
        "Tufted Titmouse", "Mourning Dove", "Carolina Wren", "Black-capped Chickadee", 
        "Downy Woodpecker", "Red-tailed Hawk", "Bald Eagle", "Ruby-throated Hummingbird", 
        "European Starling", "House Sparrow", "Northern Mockingbird", "Common Grackle",
        "Red-winged Blackbird", "Mallard", "Canada Goose", "American Crow",
        "White-breasted Nuthatch", "Eastern Bluebird", "Song Sparrow", "Dark-eyed Junco"
    ]
    
    if st.button("Surprise Me!", key="surprise_btn", use_container_width=True):
        set_bird(secrets.choice(BIRD_LIST_EXPANDED))
        st.rerun()
        
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("## Quick Select")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Northern Cardinal"):
            set_bird("Northern Cardinal")
            st.rerun()
        if st.button("American Robin"):
            set_bird("American Robin")
            st.rerun()
    with col2:
        if st.button("Blue Jay"):
            set_bird("Blue Jay")
            st.rerun()
        if st.button("American Goldfinch"):
            set_bird("American Goldfinch")
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("## Search")
    
    search_container = st.container()
    recent_container = st.container()
    
    with recent_container:
        if st.session_state.recent_searches:
            recent_selection = st.pills("Recent Searches", options=st.session_state.recent_searches, selection_mode="single")
            if recent_selection and recent_selection != st.session_state.selected_bird:
                set_bird(recent_selection)
                st.rerun()

    with search_container:
        st.text_input(
            "Enter a bird name to find its call:", 
            placeholder="e.g., Woodpecker",
            key="home_search",
            on_change=lambda: set_bird(st.session_state.home_search)
        )
        st.caption("💡 Tip: Tap the microphone on your keyboard to speak!")

    st.markdown("---")

    if st.session_state.selected_bird:
        st.markdown("## Audio Results")
        
        # -----------------------------------------------------
        # CONCURRENT API FETCHING & SKELETON LOADER
        # -----------------------------------------------------
        skel_ph = st.empty()
        skel_ph.markdown("<div class='skeleton' style='height: 350px;'></div>", unsafe_allow_html=True)
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_img = executor.submit(fetch_bird_image, st.session_state.selected_bird)
            future_summary = executor.submit(fetch_bird_summary, st.session_state.selected_bird)
            future_tax = executor.submit(fetch_bird_taxonomy, st.session_state.selected_bird)
            api_key = st.secrets.get("XENO_CANTO_API_KEY", "")
            future_recordings = executor.submit(fetch_bird_calls, st.session_state.selected_bird, api_key, 5)
            
            search_img = future_img.result()
            search_summary = future_summary.result()
            search_tax = future_tax.result()
            recordings = future_recordings.result()
            
        skel_ph.empty() # Remove skeleton once concurrent fetching is complete
        # -----------------------------------------------------

        if search_img:
            st.image(search_img, use_container_width=True)
            
        # Taxonomy Badges
        if search_tax.get("family") or search_tax.get("status"):
            t_col1, t_col2 = st.columns(2)
            if search_tax.get("family"):
                fam = search_tax['family']
                if t_col1.button(f"🧬 Family: {fam}", key="fam_btn", help="Tap to discover other birds in this family!"):
                    st.session_state.explore_family = fam
                    st.session_state.selected_bird = ""
                    st.rerun()
            if search_tax.get("status"):
                t_col2.markdown(f"🌍 **Status:** {search_tax['status']}")
                
        if search_summary:
            st.info(search_summary)
            
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.write(f"Listening to: **{st.session_state.selected_bird}**")
        with col_b:
            is_fav = st.session_state.selected_bird in st.session_state.favorites
            fav_label = "❌ Remove Favorite" if is_fav else "⭐ Add to Favorites"
            if st.button(fav_label, key="fav_toggle_home"):
                toggle_favorite(st.session_state.selected_bird)
                st.rerun()
        
        if isinstance(recordings, dict) and "error" in recordings:
            st.warning(recordings["error"])
        elif not recordings:
            st.warning(f"No recordings found for '{st.session_state.selected_bird}'. Try a different name.")
        else:
            for idx, rec in enumerate(recordings):
                curated_type = rec.get("_curated_type", f"Recording {idx + 1}")
                st.markdown(f"### {curated_type}")
                
                rec_type = rec.get("type", "Unknown type").capitalize()
                loc = rec.get("loc", "Unknown location")
                country = rec.get("cnt", "Unknown country")
                audio_url = rec.get("file", "")
                
                if audio_url.startswith("//"):
                    audio_url = "https:" + audio_url
                    
                st.caption(f"Original Type: {rec_type} | Location: {loc}, {country}")
                if audio_url:
                    st.audio(audio_url)
                else:
                    st.warning("Audio file unavailable for this recording.")
    BIRD_FAMILIES = {
        "Cardinalidae": ["Northern Cardinal", "Rose-breasted Grosbeak", "Indigo Bunting", "Dickcissel"],
        "Corvidae": ["Blue Jay", "American Crow", "Common Raven", "Steller's Jay"],
        "Fringillidae": ["American Goldfinch", "House Finch", "Purple Finch", "Pine Siskin"],
        "Turdidae": ["American Robin", "Eastern Bluebird", "Wood Thrush", "Hermit Thrush"],
        "Paridae": ["Tufted Titmouse", "Black-capped Chickadee", "Carolina Chickadee", "Mountain Chickadee"],
        "Columbidae": ["Mourning Dove", "Rock Pigeon", "Eurasian Collared-Dove", "White-winged Dove"],
        "Troglodytidae": ["Carolina Wren", "House Wren", "Winter Wren", "Marsh Wren"],
        "Picidae": ["Downy Woodpecker", "Hairy Woodpecker", "Red-bellied Woodpecker", "Northern Flicker"]
    }
    
    TRIVIA = [
        ("Did you know?", "The Northern Cardinal is the state bird of seven U.S. states, more than any other species!", "Northern Cardinal"),
        ("Fun Fact", "Blue Jays are known to mimic the calls of hawks, especially the Red-shouldered Hawk, to see if predators are around.", "Blue Jay"),
        ("Did you know?", "A woodpecker's tongue can wrap all the way around its brain to cushion it from heavy impacts!", "Downy Woodpecker"),
        ("Fun Fact", "Hummingbirds are the only birds that can fly backwards and hover in mid-air.", "Ruby-throated Hummingbird")
    ]
    
    if st.session_state.explore_family:
        fam = st.session_state.explore_family
        st.markdown(f"## 🧬 Exploring Family: {fam}")
        if st.button("⬅️ Back"):
            st.session_state.explore_family = ""
            st.rerun()
            
        family_birds = BIRD_FAMILIES.get(fam, [])
        if family_birds:
            st.write(f"Discover other fascinating species in the {fam} family:")
            cols = st.columns(2)
            for i, b in enumerate(family_birds):
                with cols[i % 2]:
                    if st.button(b, key=f"fam_grid_{b}", use_container_width=True):
                        set_bird(b)
                        st.rerun()
        else:
            st.info(f"We don't have a curated grid for {fam} yet, but you can search for them above!")
    else:
        st.markdown("## 🔍 Discover Something New")
        if "current_trivia" not in st.session_state:
            st.session_state.current_trivia = secrets.choice(TRIVIA)
        
        title, fact, bird_hint = st.session_state.current_trivia
        img = fetch_bird_image(bird_hint)
        
        st.info(f"**{title}**\n{fact}")
        if img:
            st.image(img, use_container_width=True, clamp=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Listen to {bird_hint}", use_container_width=True):
                set_bird(bird_hint)
                st.rerun()
        with col2:
            if st.button("🔄 Next Fact", use_container_width=True):
                st.session_state.current_trivia = secrets.choice(TRIVIA)
                st.rerun()


# ----------------------------------------
# FAVORITES TAB
# ----------------------------------------
with tab_fav:
    st.markdown("## ⭐ Your Favorites")
    if st.session_state.favorites:
        st.write("Tap a favorite to instantly load its calls on the Home screen.")
        for fav in st.session_state.favorites:
            if st.button(f"Listen to {fav}", key=f"fav_tab_btn_{fav}"):
                set_bird(fav)
                st.success(f"{fav} selected! Switch to the 🏠 Home tab to hear it.")
    else:
        st.write("You don't have any favorites yet! Go to the Home tab and add some.")


# ----------------------------------------
# INJECT ANDROID OPTIMIZATIONS
# ----------------------------------------
st.html("""
    <script>
        // 1. Theme Color Meta Tag & Manifest
        if (!document.querySelector('link[rel="manifest"]')) {
            document.head.insertAdjacentHTML('beforeend', '<link rel="manifest" href="app/static/manifest.json">');
        }
        if (!document.querySelector('meta[name="theme-color"]')) {
            document.head.insertAdjacentHTML('beforeend', '<meta name="theme-color" content="#ff7e5f">');
        }

        // 2. Service Worker & CPU Optimizations
        if (!window.optimizationsAttached) {
            
            // Service Worker Registration
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('app/static/sw.js').catch(function(error) {
                    console.log('ServiceWorker registration failed: ', error);
                });
            }

            // Haptics (Event Delegation - Zero CPU Polling)
            document.addEventListener('click', (e) => {
                if (e.target.closest('button') && navigator.vibrate) {
                    navigator.vibrate(25);
                }
            });
            
            // Audio Player Pulsing & Cleanup (Capture Phase - Zero CPU Polling)
            document.addEventListener('play', (e) => {
                if (e.target.tagName === 'AUDIO') {
                    e.target.style.boxShadow = '0 0 25px 5px rgba(255, 126, 95, 0.7)';
                    e.target.setAttribute('controlsList', 'nodownload noplaybackrate');
                }
            }, true);
            
            document.addEventListener('pause', (e) => {
                if (e.target.tagName === 'AUDIO') {
                    e.target.style.boxShadow = 'none';
                }
            }, true);

            // Swipe Navigation Logic
            let touchstartX = 0;
            let touchendX = 0;
            
            document.addEventListener('touchstart', e => {
                touchstartX = e.changedTouches[0].screenX;
            }, { passive: true });

            document.addEventListener('touchend', e => {
                touchendX = e.changedTouches[0].screenX;
                handleSwipe();
            }, { passive: true });

            function handleSwipe() {
                const threshold = 75; 
                if (touchendX < touchstartX - threshold) { navigateTab(1); }
                if (touchendX > touchstartX + threshold) { navigateTab(-1); }
            }
            
            function navigateTab(direction) {
                const tabButtons = Array.from(document.querySelectorAll('[data-baseweb="tab"]'));
                if (tabButtons.length === 0) return;
                
                let currentIndex = tabButtons.findIndex(btn => btn.getAttribute('aria-selected') === 'true');
                if (currentIndex === -1) currentIndex = 0;
                
                let nextIndex = currentIndex + direction;
                if (nextIndex >= 0 && nextIndex < tabButtons.length) {
                    tabButtons[nextIndex].click();
                }
            }
            
            // Prevent multiple audio elements from playing simultaneously
            document.addEventListener('play', function(e){
                if(e.target.tagName === 'AUDIO'){
                    const audios = document.getElementsByTagName('audio');
                    for(let i = 0, len = audios.length; i < len; i++){
                        if(audios[i] !== e.target){
                            audios[i].pause();
                        }
                    }
                }
            }, true);

            window.optimizationsAttached = true;
        }
    </script>
""", unsafe_allow_javascript=True)
