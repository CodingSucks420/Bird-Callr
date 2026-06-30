import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Fix Wikipedia Redirects (add redirects=1)
code = code.replace("prop=pageimages&format=json", "prop=pageimages&redirects=1&format=json")
code = code.replace("prop=extracts&exintro=1", "prop=extracts&redirects=1&exintro=1")
code = code.replace("prop=text&section=0&format=json", "prop=text&redirects=1&section=0&format=json")


# 2. Fix State Exception by using containers to order execution while preserving visual order
old_search_block = """    st.markdown("## Search")
    st.text_input(
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

new_search_block = """    st.markdown("## Search")
    
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
        st.caption("💡 Tip: Tap the microphone on your keyboard to speak!")"""

code = code.replace(old_search_block, new_search_block)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Done!")
