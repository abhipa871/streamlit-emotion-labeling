import streamlit as st


COLOR_BLIND_PALETTE_CSS = """
<style>
button[kind="primary"] {
    background-color: #0072B2 !important;
    border-color: #0072B2 !important;
}

button[kind="primary"]:hover {
    background-color: #005A8D !important;
    border-color: #005A8D !important;
}

[data-testid="stProgressBar"] > div > div > div > div {
    background-color: #0072B2 !important;
}

.st-key-emotion_choice button[aria-pressed="true"] {
    background-color: #0072B2 !important;
    border-color: #0072B2 !important;
    box-shadow: 0 0 0 3px #E69F00 !important;
    color: #FFFFFF !important;
}

.st-key-emotion_choice button:focus-visible {
    outline: 3px solid #E69F00 !important;
    outline-offset: 2px;
}
</style>
"""


def render_accessibility_controls():
    with st.container(
        horizontal=True,
        horizontal_alignment="right",
        vertical_alignment="center",
    ):
        color_blind_mode = st.toggle(
            "Color-blind palette",
            key="color_blind_mode",
            help=(
                "Use a blue and orange high-contrast palette designed to remain "
                "distinct across common forms of color-vision deficiency."
            ),
            width="content",
            persist_state="session",
        )

    if color_blind_mode:
        st.html(COLOR_BLIND_PALETTE_CSS)


def go_back():
    if st.session_state.question_index <= 0:
        return

    previous_index = st.session_state.question_index - 1
    previous_answer = None

    if len(st.session_state.answers) > previous_index:
        previous_answer = st.session_state.answers[previous_index]
        st.session_state.answers = st.session_state.answers[:previous_index]

    st.session_state.question_index = previous_index
    st.session_state.selected_emotion = (
        previous_answer["selected_emotion"]
        if previous_answer
        else None
    )
