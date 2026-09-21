import streamlit as st

from shared_functions import render_accessibility_controls


st.set_page_config(
    page_title="Emotion labeling",
    page_icon=":material/label:",
    layout="centered",
)

render_accessibility_controls()

pages = [
    st.Page("pages/instructions.py", title="Instructions"),
    st.Page("pages/labeling.py", title="Labeling"),
    st.Page("pages/finished_screen.py", title="Finished Screen"),
]
page = st.navigation(pages, position="hidden")
page.run()
