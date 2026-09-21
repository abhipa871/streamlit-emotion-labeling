"""Verify that the deployed Supabase project is reachable with the app's key.

Usage:

    python check_supabase.py            # read-only health check
    python check_supabase.py --write    # also write and read back a test submission

The read-only check confirms the project URL and key resolve and that all four
tables exist. The --write check exercises the same RPC calls the app makes, so
it proves an outside participant can actually save labels. It inserts rows under
the participant ID printed at the end; the SQL to remove them is printed too.

No secret values are printed.
"""

import sys

from data_handler import (
    SupabaseError,
    complete_labeling_submission,
    start_labeling_submission,
    verify_supabase_schema,
    _supabase_config,
)

TEST_USER_ID = "zz-selftest-01!"
TEST_QUESTIONS = [
    {"text": f"self test message {index}", "label": index}
    for index in range(5)
]


def main():
    write_test = "--write" in sys.argv[1:]

    try:
        url, _, schema = _supabase_config()
    except SupabaseError as error:
        print(f"FAIL  configuration: {error}")
        return 1

    print(f"OK    configuration: {url} (schema: {schema})")

    try:
        verify_supabase_schema()
    except SupabaseError as error:
        print(f"FAIL  healthcheck: {error}")
        print("      Run supabase_setup.sql in the Supabase SQL editor.")
        return 1

    print("OK    healthcheck: participants, questions, submissions, responses")

    if not write_test:
        print("SKIP  write test (pass --write to run it)")
        return 0

    try:
        submission_id, samples = start_labeling_submission(
            TEST_USER_ID,
            TEST_QUESTIONS,
        )
    except SupabaseError as error:
        print(f"FAIL  start_labeling_submission: {error}")
        return 1

    print(f"OK    start_labeling_submission: {len(samples)} questions registered")

    answers = [
        {"question_id": sample["question_id"], "selected_emotion": "Joy"}
        for sample in samples
    ]

    try:
        complete_labeling_submission(submission_id, answers)
    except SupabaseError as error:
        print(f"FAIL  complete_labeling_submission: {error}")
        return 1

    print("OK    complete_labeling_submission: 5 labels saved")
    print(f"      submission_id: {submission_id}")
    print()
    print("Remove the test rows from the Supabase SQL editor with:")
    print(
        "  delete from public.responses where submission_id = "
        f"'{submission_id}';"
    )
    print(
        "  delete from public.submissions where submission_id = "
        f"'{submission_id}';"
    )
    print(
        "  delete from public.participants where user_id = "
        f"'{TEST_USER_ID}';"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
