import re

with open("app.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update session state for text_size to default to "Large"
code = code.replace("""if 'text_size' not in st.session_state:\n    st.session_state.text_size = "Large"\n""", """if 'text_size' not in st.session_state:\n    st.session_state.text_size = "Large"\n""")
# It's already "Large".

# 2. Update Font Scaling (Normal=18, Large=22, XL=26)
old_fonts = """if st.session_state.text_size == "Normal":
    base_size = "16px"; h1_size = "2.5rem"; btn_size = "1rem"
elif st.session_state.text_size == "Large":
    base_size = "18px"; h1_size = "3.5rem"; btn_size = "1.2rem"
else:
    base_size = "22px"; h1_size = "4.5rem"; btn_size = "1.5rem\""""

new_fonts = """if st.session_state.text_size == "Normal":
    base_size = "18px"; h1_size = "3.0rem"; btn_size = "1.2rem"
elif st.session_state.text_size == "Large":
    base_size = "22px"; h1_size = "4.0rem"; btn_size = "1.5rem"
else:
    base_size = "26px"; h1_size = "5.0rem"; btn_size = "1.8rem\""""
code = code.replace(old_fonts, new_fonts)

# 3. Update Contrast (Day and Night mode text/sub/glass_bg)
old_day = """    glass_bg = "rgba(255, 255, 255, 0.7)"
    glass_border = "rgba(255, 255, 255, 0.5)"
    text_color = "#0f172a"
    sub_color = "#334155"
    shadow = "rgba(0, 0, 0, 0.05)\""""
new_day = """    glass_bg = "rgba(255, 255, 255, 0.9)"
    glass_border = "rgba(255, 255, 255, 0.8)"
    text_color = "#000000"
    sub_color = "#1e293b"
    shadow = "rgba(0, 0, 0, 0.1)\""""
code = code.replace(old_day, new_day)

old_night = """    glass_bg = "rgba(30, 41, 59, 0.6)"
    glass_border = "rgba(255, 255, 255, 0.1)"
    text_color = "#f8fafc"
    sub_color = "#cbd5e1"
    shadow = "rgba(0, 0, 0, 0.3)\""""
new_night = """    glass_bg = "rgba(15, 23, 42, 0.9)"
    glass_border = "rgba(255, 255, 255, 0.3)"
    text_color = "#ffffff"
    sub_color = "#f8fafc"
    shadow = "rgba(0, 0, 0, 0.5)\""""
code = code.replace(old_night, new_night)

# 4. Massive Tap Targets
# Update button CSS
old_button_css = """        .stButton>button {
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
        }"""
new_button_css = """        .stButton>button {
            width: 100%;
            min-height: 70px !important;
            height: 4.5em;
            font-size: {btn_size} !important;
            font-weight: 800 !important;
            border-radius: 16px !important;
            border: 2px solid rgba(255, 126, 95, 0.5) !important;
            background: {btn_gradient} !important;
            color: #ffffff !important;
            box-shadow: 0 6px 20px {shadow} !important;
            transition: all 0.3s ease !important;
        }"""
code = code.replace(old_button_css, new_button_css)

# Update Tab CSS
old_tab_css = """    button[data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        border-radius: 20px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }"""
new_tab_css = """    button[data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        border-radius: 20px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 16px 24px !important;
    }"""
code = code.replace(old_tab_css, new_tab_css)

# Update Input padding
old_input_css = """        .stTextInput input {
            font-size: {btn_size} !important;
            padding: 12px 24px !important;
            border-radius: 50px !important;"""
new_input_css = """        .stTextInput input {
            font-size: {btn_size} !important;
            padding: 16px 24px !important;
            border-radius: 50px !important;
            min-height: 60px !important;"""
code = code.replace(old_input_css, new_input_css)


# 5. Microphone Size
# find icon_size="2x" and replace with "4x"
code = code.replace("""icon_size="2x\"""", """icon_size="4x\"""")

with open("app.py", "w", encoding="utf-8") as f:
    f.write(code)
