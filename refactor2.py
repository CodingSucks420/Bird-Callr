import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add session states
session_state_replacement = """if 'selected_bird' not in st.session_state:
    st.session_state.selected_bird = ""
if 'recent_searches' not in st.session_state:
    st.session_state.recent_searches = []
if 'explore_family' not in st.session_state:
    st.session_state.explore_family = ""
if 'favorites' not in st.session_state:"""
code = re.sub(r"if 'selected_bird' not in st\.session_state:\n    st\.session_state\.selected_bird = \"\"\nif 'favorites' not in st\.session_state:", session_state_replacement, code)

# 2. Modify set_bird
set_bird_old = """def set_bird(bird_name):
    st.session_state.selected_bird = bird_name"""
set_bird_new = """def set_bird(bird_name):
    st.session_state.selected_bird = bird_name
    if bird_name:
        if bird_name in st.session_state.recent_searches:
            st.session_state.recent_searches.remove(bird_name)
        st.session_state.recent_searches.insert(0, bird_name)
        if len(st.session_state.recent_searches) > 5:
            st.session_state.recent_searches.pop()"""
code = code.replace(set_bird_old, set_bird_new)

# 3. Add Custom Audio Styling to CSS
css_injection = """
        audio::-webkit-media-controls-panel {
            background-color: rgba(255, 126, 95, 0.2) !important;
            backdrop-filter: blur(5px) !important;
        }
        audio::-webkit-media-controls-play-button, 
        audio::-webkit-media-controls-mute-button {
            filter: sepia(100%) hue-rotate(320deg) saturate(500%) brightness(120%) !important;
        }
        
        /* Premium Skeleton Loader */"""
code = code.replace("        /* Premium Skeleton Loader */", css_injection)

# 4. Add Recent Searches below Search Input
search_input_old = """    st.caption("💡 Tip: Tap the microphone on your keyboard to speak!")

    if search_query != st.session_state.selected_bird:
        set_bird(search_query)"""

search_input_new = """    st.caption("💡 Tip: Tap the microphone on your keyboard to speak!")
    
    if st.session_state.recent_searches:
        recent_selection = st.pills("Recent Searches", options=st.session_state.recent_searches, selection_mode="single")
        if recent_selection and recent_selection != st.session_state.selected_bird:
            set_bird(recent_selection)
            st.rerun()

    if search_query != st.session_state.selected_bird:
        set_bird(search_query)"""

# I need to find the correct lines for search input
# Actually, the code is:
#     if search_query != st.session_state.selected_bird:
#         st.session_state.selected_bird = search_query
# Let's fix that block.

search_block_old = """    st.caption("💡 Tip: Tap the microphone on your keyboard to speak!")

    if search_query != st.session_state.selected_bird:
        st.session_state.selected_bird = search_query"""

search_block_new = """    st.caption("💡 Tip: Tap the microphone on your keyboard to speak!")
    
    if st.session_state.recent_searches:
        recent_selection = st.pills("Recent Searches", options=st.session_state.recent_searches, selection_mode="single")
        if recent_selection and recent_selection != st.session_state.selected_bird:
            set_bird(recent_selection)
            st.rerun()

    if search_query != st.session_state.selected_bird:
        set_bird(search_query)"""
code = code.replace(search_block_old, search_block_new)

# 5. Taxonomy Badges and Empty States
taxonomy_old = """        # Taxonomy Badges
        if search_tax.get("family") or search_tax.get("status"):
            t_col1, t_col2 = st.columns(2)
            if search_tax.get("family"):
                t_col1.markdown(f"🧬 **Family:** {search_tax['family']}")
            if search_tax.get("status"):
                t_col2.markdown(f"🌍 **Status:** {search_tax['status']}")"""

taxonomy_new = """        # Taxonomy Badges
        if search_tax.get("family") or search_tax.get("status"):
            t_col1, t_col2 = st.columns(2)
            if search_tax.get("family"):
                fam = search_tax['family']
                if t_col1.button(f"🧬 Family: {fam}", key="fam_btn", help="Tap to discover other birds in this family!"):
                    st.session_state.explore_family = fam
                    st.session_state.selected_bird = ""
                    st.rerun()
            if search_tax.get("status"):
                t_col2.markdown(f"🌍 **Status:** {search_tax['status']}")"""
code = code.replace(taxonomy_old, taxonomy_new)


# 6. Smart Empty States
# Find: `    else:\n        st.write("Select a bird from the grid or search above to hear its calls.")`
empty_state_old = """    else:
        st.write("Select a bird from the grid or search above to hear its calls.")"""
empty_state_new = """    else:
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
                        if st.button(b, key=f"fam_grid_{b}", width="stretch"):
                            set_bird(b)
                            st.rerun()
            else:
                st.info(f"We don't have a curated grid for {fam} yet, but you can search for them above!")
        else:
            st.markdown("## 🔍 Discover Something New")
            title, fact, bird_hint = secrets.choice(TRIVIA)
            img = fetch_bird_image(bird_hint)
            
            st.info(f"**{title}**\\n{fact}")
            if img:
                st.image(img, width="stretch", clamp=True)
            if st.button(f"Listen to {bird_hint}", width="stretch"):
                set_bird(bird_hint)
                st.rerun()"""
code = code.replace(empty_state_old, empty_state_new)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Done!")
