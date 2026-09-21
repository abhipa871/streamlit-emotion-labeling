# Emotion labeling app

A Streamlit app where a participant labels five randomly sampled messages from
the Hugging Face dataset [`dair-ai/emotion`](https://huggingface.co/datasets/dair-ai/emotion)
with one of six emotions. Every label is stored in Supabase under an anonymous
participant ID, so the database can answer *which participant labeled which
message with which label*.

## Files

| File | Purpose |
| --- | --- |
| `app.py` | Entry point: page config, accessibility controls, hidden navigation |
| `pages/instructions.py` | Task instructions and the participant ID form |
| `pages/labeling.py` | The five labeling questions |
| `pages/finished_screen.py` | Confirmation and a summary of the choices |
| `data_handler.py` | Dataset loading and all Supabase calls |
| `models.py` | Participant ID validation (`pydantic`) |
| `shared_functions.py` | Color-blind palette toggle, back-navigation helper |
| `supabase_setup.sql` | Tables, RLS, and the three RPCs the app calls |
| `check_supabase.py` | Command-line check that the database is reachable |
| `.streamlit/config.toml` | Theme |
| `.streamlit/secrets.toml.example` | Template for the Supabase credentials |

## 1. Supabase

The project this app points at (`icltrnnmwefegtleivaz`) is **already set up and
verified**: all four tables exist, the three RPCs answer with the publishable
key, and a full test submission was written and confirmed. The publishable key
has no `select`, `insert`, `update`, or `delete` privilege on any of the four
tables, so it can only reach the database through the RPCs.

`supabase_setup.sql` is therefore a rebuild script, not a required step. Run it
when you point the app at a **new** Supabase project, or to re-assert the grants
on this one. Note that it **drops and recreates** the three functions, so on a
project where they already work you only need it if something broke. To add just
the reporting view from section 5, run that section on its own.

To run it: Supabase → **SQL Editor** → **New query** → paste → **Run**, then
confirm with `select public.emotion_labeling_healthcheck();` → `true`.

The script enables Row Level Security on all four tables with no policies, so
the publishable (anon) key cannot read or write them directly. Participants
reach the database only through three `SECURITY DEFINER` functions, which are
granted to the `anon` role:

| RPC | Called from |
| --- | --- |
| `emotion_labeling_healthcheck()` | `pages/instructions.py`, before starting |
| `start_labeling_submission(p_user_id, p_questions)` | `pages/labeling.py`, on first load |
| `complete_labeling_submission(p_submission_id, p_responses)` | `pages/labeling.py`, on the last question |

This is why the app uses RPCs instead of `.table(...).insert(...)`: one call
spans `participants`, `submissions`, `questions`, and `responses`, and stays
atomic under RLS.

## 2. Run it locally

```powershell
pip install -r requirements.txt
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
# then edit .streamlit\secrets.toml with the real project URL and publishable key
python -m streamlit run app.py
```

Check the database connection without opening the browser:

```powershell
python check_supabase.py           # configuration + health check
python check_supabase.py --write   # also saves and verifies a test submission
```

`.streamlit/secrets.toml` is gitignored and must never be committed.

## 3. Deploy to Streamlit Community Cloud

1. Push this folder to a GitHub repository (public or private).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **Create app** →
   **Deploy a public app from GitHub**.
3. Fill in:
   - **Repository**: your repo
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **Python version** (under *Advanced settings*): **3.12** or **3.13**
4. Still under *Advanced settings*, paste into **Secrets**:

   ```toml
   [supabase]
   url = "https://YOUR_PROJECT_REF.supabase.co"
   publishable_key = "YOUR_SUPABASE_PUBLISHABLE_OR_ANON_KEY"
   schema = "public"
   ```

5. Click **Deploy**. The first build installs the requirements and the first
   visit downloads the dataset parquet (~27 MB, cached for 12 hours).

Anyone with the app URL can now label messages; no Supabase account or login is
needed on their side. The theme in `.streamlit/config.toml` is picked up
automatically.

Secrets can be edited later from the app's ⋮ menu → **Settings** → **Secrets**;
saving them restarts the app.

## 4. Read the collected data

In the Supabase SQL editor. The `labeling_results` view comes from section 5 of
`supabase_setup.sql`; until you run that section, use the join it contains.

```sql
-- one row per label, with the dataset's own label for comparison
select * from public.labeling_results order by submitted_at desc;

-- how many completed submissions per anonymous participant
select user_id, count(*) as submissions
from public.labeling_results
where completed
group by user_id
order by submissions desc;
```

## Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| "Supabase is not configured…" | Secrets missing or malformed. Check the `[supabase]` section in the app's **Secrets** box (or `.streamlit/secrets.toml` locally). |
| "The Supabase labeling schema is not available." | `supabase_setup.sql` has not been run on this project, or it was run on a different project than the URL points to. |
| "Supabase could not process the request…" | The RPCs exist but were rejected — usually missing `grant execute … to anon`. Re-run section 3 and 4 of `supabase_setup.sql`. |
| "Could not connect to Supabase." | The project is paused (free Supabase projects pause after inactivity) or the URL is wrong. Resume it from the Supabase dashboard. |
| "Could not download the emotion dataset…" | Transient Hugging Face outage. The loader already retries three times; press **Try again**. |
| App build fails on Community Cloud | Check the build log for a package that has no wheel for the selected Python version, and switch the app to Python 3.12. |

## Notes on the environment

- Python 3.11–3.13 are supported; Community Cloud does not offer 3.14 yet.
- The app reads the dataset straight from its parquet file with `pandas`, and
  keeps a random pool of 20,000 messages in cache, so the heavy `datasets`
  package is not needed at runtime and memory stays well inside Community
  Cloud's 1 GB limit.
