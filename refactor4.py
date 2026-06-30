import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Fix fetch_bird_image extracting 'thumbnail' instead of 'original'
img_old = """                if "thumbnail" in page_data:
                    return page_data["thumbnail"]["source"]"""
img_new = """                if "original" in page_data:
                    return page_data["original"]["source"]"""
code = code.replace(img_old, img_new)

# 2. Add home_search init state
init_old = """if 'selected_bird' not in st.session_state:
    st.session_state.selected_bird = \"\"
if 'recent_searches' not in st.session_state:"""
init_new = """if 'selected_bird' not in st.session_state:
    st.session_state.selected_bird = \"\"
if 'home_search' not in st.session_state:
    st.session_state.home_search = \"\"
if 'recent_searches' not in st.session_state:"""
code = code.replace(init_old, init_new)

# 3. Update set_bird to sync home_search
set_bird_old = """def set_bird(bird_name):
    st.session_state.selected_bird = bird_name
    if bird_name:"""
set_bird_new = """def set_bird(bird_name):
    st.session_state.selected_bird = bird_name
    st.session_state.home_search = bird_name
    if bird_name:"""
code = code.replace(set_bird_old, set_bird_new)

# 4. Update text_input and remove conflict block
search_old = """    search_query = st.text_input(
        "Enter a bird name to find its call:", 
        value=st.session_state.selected_bird,
        placeholder="e.g., Woodpecker",
        key="home_search"
    )
    st.caption("💡 Tip: Tap the microphone on your keyboard to speak!")
    
    if st.session_state.recent_searches:
        recent_selection = st.pills("Recent Searches", options=st.session_state.recent_searches, selection_mode="single")
        if recent_selection and recent_selection != st.session_state.selected_bird:
            set_bird(recent_selection)
            st.rerun()

    if search_query != st.session_state.selected_bird:
        set_bird(search_query)"""

search_new = """    st.text_input(
        "Enter a bird name to find its call:", 
        placeholder="e.g., Woodpecker",
        key="home_search",
        on_change=lambda: set_bird(st.session_state.home_search)
    )
    st.caption("💡 Tip: Tap the microphone on your keyboard to speak!")
    
    if st.session_state.recent_searches:
        recent_selection = st.pills("Recent Searches", options=st.session_state.recent_searches, selection_mode="single")
        if recent_selection and recent_selection != st.session_state.selected_bird:
            set_bird(recent_selection)
            st.rerun()"""
            
code = code.replace(search_old, search_new)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Done!")
