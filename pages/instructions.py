import streamlit as st
from pydantic import ValidationError

from data_handler import SupabaseError, verify_supabase_schema
from models import UserIdentifier


st.title("Emotion labeling", icon=":material/label:")
st.subheader("Instructions")
st.write(
    "Welcome to the Emotion Labeling App! In this app, you will be presented "
    "with a series of text samples. Your task is to label each sample with the "
    "emotion that best describes it. The available emotions are:"
)
st.markdown(
    "- Anger\n"
    "- Fear\n"
    "- Joy\n"
    "- Love\n"
    "- Sadness\n"
    "- Surprise"
)
st.write(
    'Please read each text sample carefully and select the emotion that you feel '
    'is most appropriate. Once you have made your selection, click the "Save and '
    'continue" button to proceed to the next sample. You can also go back to '
    "previous samples if you wish to change your answers."
)
st.write("Thank you for participating in this labeling task!")

st.space("medium")

with st.container(border=True, gap="small"):
    st.subheader("Create your participant ID", icon=":material/person:")
    st.write(
        "Please enter a unique identifier. Do not use your name or any personal "
        "information. This identifier will be used to track your progress and "
        "ensure that your responses are recorded accurately."
    )
    st.caption(
        'The "who" does not have to be your real identity. Use an anonymous ID '
        "that lets the app group labels submitted by the same person."
    )

    with st.form("participant_id_form", border=False, enter_to_submit=True):
        user_id = st.text_input(
            "Participant ID",
            key="user_id_input",
            help=(
                "Use at least 8 characters with no spaces, including a number "
                "and a symbol."
            ),
            max_chars=100,
            placeholder="Example: blue-sky-27",
            autocomplete="off",
        )
        st.caption(
            "Using the same ID keeps all of your labels grouped together."
        )
        submitted = st.form_submit_button(
            "Start labeling",
            type="primary",
            icon=":material/arrow_forward:",
            width="stretch",
        )

if submitted:
    try:
        participant = UserIdentifier(user_id=user_id)
        with st.spinner("Preparing your questions..."):
            verify_supabase_schema()
    except ValidationError:
        st.error(
            "Use at least 8 characters with no spaces, including a number "
            "and a symbol. For example: blue-sky-27",
            icon=":material/error:",
        )
    except SupabaseError as error:
        st.error(str(error), icon=":material/cloud_off:")
    else:
        st.session_state.update(
            {
                "user_id": participant.user_id,
                "question_index": 0,
                "selected_emotion": None,
                "emotion_choice_index": None,
                "answers": [],
                "responses_submitted": False,
                "submission_id": None,
            }
        )
        st.session_state.pop("samples", None)
        st.switch_page("pages/labeling.py")
