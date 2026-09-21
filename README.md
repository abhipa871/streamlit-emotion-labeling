# Emotion labeling app

A Streamlit app where a participant labels five random messages from the
[`dair-ai/emotion`](https://huggingface.co/datasets/dair-ai/emotion) dataset as
anger, fear, joy, love, sadness, or surprise. Each label is saved to Supabase
under an anonymous participant ID, so the same person's labels stay grouped.

## Run locally

```powershell
pip install -r requirements.txt
python -m streamlit run app.py
```

First create `.streamlit/secrets.toml` (gitignored — never commit it):

```toml
[supabase]
url = "https://YOUR_PROJECT_REF.supabase.co"
publishable_key = "YOUR_SUPABASE_PUBLISHABLE_KEY"
schema = "public"
```

The app opens at http://localhost:8501.

## Deploy to Streamlit Community Cloud

1. [share.streamlit.io](https://share.streamlit.io) → **Create app** → deploy from GitHub.
2. Branch `main`, main file `app.py`, Python **3.12** or **3.13**.
3. Under **Advanced settings → Secrets**, paste the same TOML as above.
4. **Deploy.**

Participants just need the app URL — no login, no Supabase account.

## Database

```
participants → submissions → responses → questions
```

The publishable key has no direct access to these tables. The app writes through
three Postgres functions: `emotion_labeling_healthcheck`,
`start_labeling_submission`, and `complete_labeling_submission`.

`supabase_setup.sql` creates all of it — run it in the Supabase SQL editor when
pointing the app at a new project.

To see the collected labels:

```sql
select p.user_id, q.question_text, r.selected_emotion, q.correct_emotion
from public.responses r
join public.submissions s  on s.submission_id = r.submission_id
join public.participants p on p.participant_id = s.participant_id
join public.questions q    on q.question_id = r.question_id
order by s.submitted_at desc;
```

## Files

| File | Purpose |
| --- | --- |
| `app.py` | Entry point and navigation |
| `pages/` | Instructions, labeling, finished screen |
| `data_handler.py` | Dataset loading and Supabase calls |
| `models.py` | Participant ID validation |
| `shared_functions.py` | Color-blind palette toggle, back navigation |
| `supabase_setup.sql` | Database schema and functions |
| `.streamlit/config.toml` | Theme |
