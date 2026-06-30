import re
with open('app.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace use_container_width
c = c.replace('use_container_width=True', 'width="stretch"')

# Replace components.html
c = c.replace('components.html("""', 'st.html("""')
c = c.replace('""", height=0, width=0)', '""", unsafe_allow_javascript=True)')
c = c.replace('window.parent.document', 'document')
c = c.replace('window.parent.optimizationsAttached', 'window.optimizationsAttached')
c = c.replace('window.parent.swipeAttached', 'window.swipeAttached')

# Replace ThreadPoolExecutor
p = r'(\s*)ctx = get_script_run_ctx\(\)\n\s*def wrap\(func, \*args\):\n\s*add_script_run_ctx\(ctx=ctx\)\n\s*return func\(\*args\)\n\s*with ThreadPoolExecutor\(max_workers=4\) as executor:\n\s*future_img = executor\.submit\(wrap, fetch_bird_image, st\.session_state\.selected_bird\)\n\s*future_sum = executor\.submit\(wrap, fetch_bird_summary, st\.session_state\.selected_bird\)\n\s*future_tax = executor\.submit\(wrap, fetch_bird_taxonomy, st\.session_state\.selected_bird\)\n\s*future_aud = executor\.submit\(wrap, fetch_bird_calls, st\.session_state\.selected_bird, 5\)\n\s*search_img = future_img\.result\(\)\n\s*search_summary = future_sum\.result\(\)\n\s*search_tax = future_tax\.result\(\)\n\s*recordings = future_aud\.result\(\)'

r = r'''\1search_img = fetch_bird_image(st.session_state.selected_bird)
\1search_summary = fetch_bird_summary(st.session_state.selected_bird)
\1search_tax = fetch_bird_taxonomy(st.session_state.selected_bird)
\1recordings = fetch_bird_calls(st.session_state.selected_bird, 5)'''
c = re.sub(p, r, c)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(c)
print("Done!")
