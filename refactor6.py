import re

with open("app.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Add imports at the top
imports = """import streamlit as st
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
"""
code = re.sub(r"import streamlit as st.*?from audio_recorder_streamlit import audio_recorder\n", imports, code, flags=re.DOTALL)

# 2. Add cached analyzer initialization
analyzer_init = """
# Initialize session states
if 'selected_bird' not in st.session_state:
    st.session_state.selected_bird = ""

@st.cache_resource
def get_analyzer():
    # Initialize the BirdNET Analyzer. This downloads the model on first run.
    return Analyzer()
"""
code = code.replace("""# Initialize session states\nif 'selected_bird' not in st.session_state:\n    st.session_state.selected_bird = \"\"""", analyzer_init)

# 3. Rewrite query_birdnet_api
new_query = """def query_birdnet_api(audio_bytes, api_url):
    try:
        # Instead of using an external API, process locally with birdnetlib
        analyzer = get_analyzer()
        
        # Save audio_bytes to a temporary wav file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio_path = temp_audio.name
            
        try:
            recording = Recording(analyzer, temp_audio_path, min_conf=0.1)
            recording.analyze()
            
            # Extract detections
            if recording.detections:
                # Get the highest confidence detection
                best_match = max(recording.detections, key=lambda x: x['confidence'])
                return {
                    "species": best_match['common_name'],
                    "confidence": best_match['confidence'],
                    "scientific_name": best_match['scientific_name']
                }
            else:
                return {"error": "No bird sounds detected with enough confidence."}
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
                
    except Exception as e:
        return {"error": str(e)}"""
code = re.sub(r"def query_birdnet_api\(audio_bytes, api_url\):.*?return \{\"error\": str\(e\)\}", new_query, code, flags=re.DOTALL)

# 4. Update the microphone logic to handle the new return format
old_mic = """        if "error" in result:
            if result["error"] == "Demo":
                st.info("💡 **Demo Mode Active:** Connect a real AI server in Settings to identify live audio!")
            else:
                st.warning(f"Could not reach the AI Server. Check your URL in the Settings tab. (Error: {result['error']})")
            
            if st.button("Simulate Match (Demo)"):
                st.success("Simulated Match: **Northern Cardinal** (98% Confidence)")
                set_bird("Northern Cardinal")
                st.rerun()
        else:
            st.success("Identification complete!")
            st.json(result)"""
new_mic = """        if "error" in result:
            st.warning(f"Analysis failed: {result['error']}")
            if st.button("Try a Simulated Match Instead"):
                st.success("Simulated Match: **Northern Cardinal** (98% Confidence)")
                set_bird("Northern Cardinal")
                st.rerun()
        else:
            species = result.get('species', 'Unknown')
            conf = result.get('confidence', 0)
            st.success(f"Identification complete! It's a **{species}**! ({(conf*100):.1f}% confidence)")
            set_bird(species)
            st.rerun()"""
code = code.replace(old_mic, new_mic)

# 5. Remove the placeholder logic
old_placeholder = """        if st.session_state.birdnet_api_url == "https://birdnet.cornell.edu/api/v1/identify":
            result = {"error": "Demo"}
        else:
            result = query_birdnet_api(audio_bytes, st.session_state.birdnet_api_url)"""
new_placeholder = """        result = query_birdnet_api(audio_bytes, st.session_state.birdnet_api_url)"""
code = code.replace(old_placeholder, new_placeholder)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(code)
