import streamlit as st

st.title("Labels submitted", icon=":material/check_circle:")

if st.session_state.get("responses_submitted"):
    st.success(
        "All five labels were saved. Thank you for your participation!",
        icon=":material/cloud_done:",
    )
else:
    st.warning(
        "This submission has not been confirmed by the database.",
        icon=":material/warning:",
    )

answers = st.session_state.get("answers", [])

with st.container(border=True, gap="small"):
    st.subheader("Your choices")
    for index, answer in enumerate(answers, start=1):
        with st.container(
            horizontal=True,
            horizontal_alignment="distribute",
            vertical_alignment="center",
        ):
            st.write(f"Message {index}")
            st.badge(answer["selected_emotion"], color="gray")

st.space("medium")

if st.button(
    "Label another set",
    icon=":material/restart_alt:",
    type="primary",
    width="content",
    key="restart_button",
):
    st.session_state.question_index = 0
    st.session_state.selected_emotion = None
    st.session_state.emotion_choice_index = None
    st.session_state.answers = []
    st.session_state.responses_submitted = False
    st.session_state.submission_id = None
    st.session_state.pop("samples", None)
    st.switch_page("pages/instructions.py")

st.stop()
