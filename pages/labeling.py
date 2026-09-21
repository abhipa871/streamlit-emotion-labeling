import streamlit as st

from data_handler import (
    DatasetError,
    SupabaseError,
    complete_labeling_submission,
    label_to_text,
    load_emotion_dataset,
    sample_emotion_dataset,
    start_labeling_submission,
)
from shared_functions import go_back


if not st.session_state.get("user_id"):
    st.warning(
        "Enter a participant ID before starting the task.",
        icon=":material/info:",
    )
    if st.button(
        "Return to instructions",
        icon=":material/arrow_back:",
        width="content",
    ):
        st.switch_page("pages/instructions.py")
    st.stop()

st.session_state.setdefault("question_index", 0)
st.session_state.setdefault("selected_emotion", None)
st.session_state.setdefault("answers", [])
st.session_state.setdefault("responses_submitted", False)
st.session_state.setdefault("submission_id", None)
st.session_state.setdefault("emotion_choice_index", None)

if "samples" not in st.session_state:
    try:
        with st.spinner("Selecting five messages..."):
            dataset = load_emotion_dataset()
            st.session_state.samples = sample_emotion_dataset(
                dataset,
                num_samples=5,
            )
    except DatasetError as error:
        st.error(str(error), icon=":material/cloud_off:")
        if st.button("Try again", icon=":material/refresh:", width="content"):
            st.rerun()
        st.stop()

if not st.session_state.submission_id:
    try:
        submission_id, saved_samples = start_labeling_submission(
            st.session_state.user_id,
            st.session_state.samples,
        )
        st.session_state.submission_id = submission_id
        st.session_state.samples = saved_samples
    except SupabaseError as error:
        st.error(str(error), icon=":material/cloud_off:")
        st.stop()

index = st.session_state.question_index
samples = st.session_state.samples
total_questions = len(samples)

if index >= total_questions:
    st.switch_page("pages/finished_screen.py")

current_question = samples[index]

with st.container(
    horizontal=True,
    horizontal_alignment="distribute",
    vertical_alignment="center",
):
    st.badge(
        f"Message {index + 1} of {total_questions}",
        icon=":material/format_list_numbered:",
        color="gray",
    )
    st.caption(f"Participant ID: {st.session_state.user_id}")

st.progress((index + 1) / total_questions)
st.space("small")

st.header("What emotion does this message express?")
with st.container(border=True, gap="small", key="message_panel"):
    st.caption("MESSAGE")
    st.write(current_question["text"])

st.space("small")
st.subheader("Choose one emotion")

if st.session_state.emotion_choice_index != index:
    st.session_state.emotion_choice = st.session_state.selected_emotion
    st.session_state.emotion_choice_index = index

emotions = ["Anger", "Fear", "Joy", "Love", "Sadness", "Surprise"]
selected_emotion = st.pills(
    "Emotion",
    emotions,
    selection_mode="single",
    key="emotion_choice",
    label_visibility="collapsed",
    width="stretch",
    wrap=True,
)
st.session_state.selected_emotion = selected_emotion

st.space("medium")

with st.container(
    horizontal=True,
    horizontal_alignment="distribute",
    vertical_alignment="center",
    wrap=False,
):
    back_clicked = st.button(
        "Back",
        key="back_button",
        icon=":material/arrow_back:",
        width="content",
        disabled=index == 0,
    )

    is_last_question = index == total_questions - 1
    continue_clicked = st.button(
        "Submit labels" if is_last_question else "Save and continue",
        key="continue_button",
        icon=":material/check:" if is_last_question else ":material/arrow_forward:",
        type="primary",
        width="content",
        disabled=selected_emotion is None,
    )

if back_clicked:
    go_back()
    st.session_state.emotion_choice_index = None
    st.rerun()

if continue_clicked:
    answer = {
        "question_id": current_question["question_id"],
        "question": current_question["text"],
        "selected_emotion": selected_emotion,
        "true_label": current_question["label"],
        "true_label_name": label_to_text(current_question["label"]),
        "question_order": index + 1,
    }

    if len(st.session_state.answers) > index:
        st.session_state.answers[index] = answer
    else:
        st.session_state.answers.append(answer)

    if is_last_question:
        try:
            with st.spinner("Saving your labels..."):
                complete_labeling_submission(
                    st.session_state.submission_id,
                    st.session_state.answers,
                )
            st.session_state.responses_submitted = True
        except SupabaseError as error:
            st.error(str(error), icon=":material/cloud_off:")
            st.stop()

    st.session_state.question_index += 1
    st.session_state.selected_emotion = None
    st.session_state.emotion_choice_index = None
    st.rerun()
