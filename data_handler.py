import io
import os
import re
import time

import httpx
import pandas as pd
import streamlit as st
from supabase import Client, PostgrestAPIError, SupabaseException, create_client
from supabase.client import ClientOptions


class SupabaseError(RuntimeError):
    pass


class DatasetError(RuntimeError):
    pass


SCHEMA_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# The `unsplit` configuration of the Hugging Face dataset `dair-ai/emotion`,
# read straight from its parquet file so the app does not need the heavy
# `datasets` package at runtime.
EMOTION_DATASET_URL = (
    "https://huggingface.co/datasets/dair-ai/emotion/resolve/main/"
    "unsplit/train-00000-of-00001.parquet"
)

# The full dataset holds 416,809 messages. Keeping a random pool of this size
# leaves plenty of variety while staying small enough for a shared 1 GB
# Streamlit Community Cloud app.
DATASET_POOL_SIZE = 20_000


# Transient connection resets happen, so every download gets a few tries.
DATASET_DOWNLOAD_ATTEMPTS = 3


def _download_emotion_dataset():
    last_error = None

    with httpx.Client(
        transport=httpx.HTTPTransport(retries=2),
        timeout=httpx.Timeout(90.0, connect=30.0),
        follow_redirects=True,
        headers={"User-Agent": "emotion-labeling-app"},
    ) as client:
        for attempt in range(DATASET_DOWNLOAD_ATTEMPTS):
            try:
                response = client.get(EMOTION_DATASET_URL)
                response.raise_for_status()
                return response.content
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt + 1 < DATASET_DOWNLOAD_ATTEMPTS:
                    time.sleep(1.5 * (attempt + 1))

    raise DatasetError(
        "Could not download the emotion dataset from Hugging Face. "
        "Please try again in a moment."
    ) from last_error


@st.cache_data(ttl="12h", show_spinner=False)
def load_emotion_dataset():
    content = _download_emotion_dataset()

    try:
        frame = pd.read_parquet(
            io.BytesIO(content),
            columns=["text", "label"],
        )
    except (ValueError, OSError) as exc:
        raise DatasetError("The emotion dataset could not be read.") from exc

    if frame.empty:
        raise DatasetError("The emotion dataset came back empty.")

    if len(frame) > DATASET_POOL_SIZE:
        frame = frame.sample(n=DATASET_POOL_SIZE)

    return frame.reset_index(drop=True)


def label_to_text(label):
    label_map = {
        0: "sadness",
        1: "joy",
        2: "love",
        3: "anger",
        4: "fear",
        5: "surprise",
    }
    return label_map.get(label, "unknown")


def sample_emotion_dataset(dataset, num_samples=5):
    if len(dataset) < num_samples:
        raise DatasetError("The emotion dataset does not have enough messages.")

    selection = dataset.sample(n=num_samples)
    return [
        {"text": str(row.text), "label": int(row.label)}
        for row in selection.itertuples()
    ]


def _get_setting(section_key, env_key, default=None):
    try:
        supabase_settings = st.secrets.get("supabase", {})
        value = supabase_settings.get(section_key)
        if value:
            return value

        value = st.secrets.get(env_key)
        if value:
            return value
    except (FileNotFoundError, KeyError, AttributeError):
        pass

    return os.getenv(env_key, default)


def _supabase_config():
    url = _get_setting("url", "SUPABASE_URL")
    api_key = (
        _get_setting("publishable_key", "SUPABASE_PUBLISHABLE_KEY")
        or _get_setting("anon_key", "SUPABASE_ANON_KEY")
    )
    schema = _get_setting("schema", "SUPABASE_SCHEMA", "public")

    if not url or not api_key:
        raise SupabaseError(
            "Supabase is not configured. Add the project URL and publishable "
            "key to Streamlit secrets."
        )

    if not SCHEMA_NAME_PATTERN.fullmatch(schema):
        raise SupabaseError("The configured Supabase schema name is invalid.")

    return url.rstrip("/"), api_key, schema


@st.cache_resource
def get_supabase_client() -> Client:
    url, api_key, schema = _supabase_config()

    try:
        return create_client(
            url,
            api_key,
            options=ClientOptions(
                schema=schema,
                postgrest_client_timeout=15,
                storage_client_timeout=15,
                function_client_timeout=15,
            ),
        )
    except (SupabaseException, ValueError) as exc:
        raise SupabaseError("Supabase could not be initialized.") from exc


def _rpc(function_name, payload):
    try:
        response = get_supabase_client().rpc(function_name, payload).execute()
    except httpx.RequestError as exc:
        raise SupabaseError(
            "Could not connect to Supabase. Please try again."
        ) from exc
    except (PostgrestAPIError, SupabaseException) as exc:
        raise SupabaseError(
            "Supabase could not process the request. Check that the database "
            "schema is configured correctly."
        ) from exc

    return response.data


def verify_supabase_schema():
    if _rpc("emotion_labeling_healthcheck", {}) is not True:
        raise SupabaseError("The Supabase labeling schema is not available.")


def start_labeling_submission(user_id, samples):
    questions = [
        {
            "question_text": sample["text"],
            "correct_emotion": label_to_text(sample["label"]),
        }
        for sample in samples
    ]
    result = _rpc(
        "start_labeling_submission",
        {"p_user_id": user_id, "p_questions": questions},
    )

    if not isinstance(result, dict):
        raise SupabaseError("Supabase did not return the new submission.")

    saved_questions = result.get("questions")
    if not result.get("submission_id") or not isinstance(saved_questions, list):
        raise SupabaseError("Supabase returned an incomplete submission.")
    if len(saved_questions) != len(samples):
        raise SupabaseError("Supabase did not register all five questions.")

    return result["submission_id"], [
        {**sample, "question_id": saved_question["question_id"]}
        for sample, saved_question in zip(samples, saved_questions)
    ]


def complete_labeling_submission(submission_id, answers):
    responses = [
        {
            "question_id": answer["question_id"],
            "selected_emotion": answer["selected_emotion"].lower(),
        }
        for answer in answers
    ]
    completed = _rpc(
        "complete_labeling_submission",
        {"p_submission_id": submission_id, "p_responses": responses},
    )

    if completed is not True:
        raise SupabaseError("Supabase did not confirm the completed submission.")
