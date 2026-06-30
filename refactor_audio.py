import re

with open("app.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update fetch_bird_calls
old_fetch = """        recordings = data.get("recordings", [])
        if not recordings:
            return None
        
        sorted_recordings = sorted(recordings, key=lambda x: str(x.get('q', 'Z')).upper())
        return sorted_recordings[:limit]"""

new_fetch = """        recordings = data.get("recordings", [])
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
                
        return curated"""

code = code.replace(old_fetch, new_fetch)

# 2. Update UI rendering
old_ui = """        if isinstance(recordings, dict) and "error" in recordings:
            st.warning(recordings["error"])
        elif not recordings:
            st.warning(f"No recordings found for '{st.session_state.selected_bird}'. Try a different name.")
        else:
            for idx, rec in enumerate(recordings):
                st.markdown(f"### Recording {idx + 1}")
                rec_type = rec.get("type", "Unknown type").capitalize()
                loc = rec.get("loc", "Unknown location")
                country = rec.get("cnt", "Unknown country")
                audio_url = rec.get("file", "")
                
                if audio_url.startswith("//"):
                    audio_url = "https:" + audio_url
                    
                st.caption(f"Type: {rec_type} | Location: {loc}, {country}")
                if audio_url:
                    st.audio(audio_url)
                else:
                    st.warning("Audio file unavailable for this recording.")"""

new_ui = """        if isinstance(recordings, dict) and "error" in recordings:
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
                    st.warning("Audio file unavailable for this recording.")"""

code = code.replace(old_ui, new_ui)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(code)
