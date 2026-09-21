# Claude Code Handoff: Streamlit + Supabase Emotion Labeling App

## Project

Local path:

`C:\Users\patel\Downloads\Streamlit`

Run command:

```powershell
python -m streamlit run app.py --server.port 8501 --server.headless true
```

Local URL:

`http://localhost:8501`

## Current Problem

The Streamlit app currently shows:

```text
Supabase is not configured. Add the project URL and publishable key to Streamlit secrets.
```

Root cause: the local `.streamlit` folder is missing, including `.streamlit/secrets.toml`.

The app code is present, but Streamlit cannot connect to Supabase until the project URL and publishable key are restored.

## Assignment Requirements

The app must satisfy the A1-2 instruction and instructor clarification:

- User labels 5 randomly selected tweets/messages.
- App records who labeled which tweet with which label.
- "Who" does not need to be a real identity.
- Use an anonymous participant/user ID.
- Same person's responses should be grouped under the same ID.
- No need to implement repeat-user duplicate prevention or multiple-completion edge cases.
- Store data in Supabase.

Instructor clarification to preserve in spirit:

```text
the "who" does not have to be their real identity. The goal is to be able to know which labels are submitted by the same person. E.g., you can assign an ID or create a sign-up process
```

## Current App Structure

Files:

- `app.py`
- `data_handler.py`
- `models.py`
- `shared_functions.py`
- `pages/instructions.py`
- `pages/labeling.py`
- `pages/finished_screen.py`
- `requirements.txt`
- `.gitignore`

Deleted intentionally per user request:

- `supabase_handler.py`
- `supabase_schema.sql`

Do not recreate those unless necessary.

## Current Code Behavior

`app.py`:

- Sets Streamlit page config.
- Calls `render_accessibility_controls()`.
- Uses hidden `st.navigation` for:
  - `pages/instructions.py`
  - `pages/labeling.py`
  - `pages/finished_screen.py`

`shared_functions.py`:

- Defines `render_accessibility_controls()`.
- Adds top-right `Color-blind palette` toggle.
- Defines `go_back()`.

`models.py`:

- Defines `UserIdentifier`.
- Requires:
  - minimum 8 characters
  - no spaces
  - at least one digit
  - at least one special character

`pages/instructions.py`:

- Shows the assignment instructions.
- Includes instructor clarification that the "who" does not have to be real identity.
- Takes participant ID in a form.
- Calls `verify_supabase_schema()` before moving to labeling.

`pages/labeling.py`:

- Loads Hugging Face dataset `dair-ai/emotion`.
- Samples 5 items.
- Calls `start_labeling_submission(user_id, samples)`.
- Shows each message and `st.pills` options:
  - Anger
  - Fear
  - Joy
  - Love
  - Sadness
  - Surprise
- On the last question, calls `complete_labeling_submission(submission_id, answers)`.

`data_handler.py`:

- Contains all dataset and Supabase logic.
- Uses official Supabase Python client:
  - `create_client(...)`
  - `client.rpc(...).execute()`
- Does not use manual REST endpoint calls.
- Defines:
  - `SupabaseError`
  - `load_emotion_dataset`
  - `label_to_text`
  - `sample_emotion_dataset`
  - `get_supabase_client`
  - `verify_supabase_schema`
  - `start_labeling_submission`
  - `complete_labeling_submission`

## Supabase Schema Known From Previous Inspection

Live Supabase tables exist:

### `participants`

- `participant_id uuid primary key default gen_random_uuid()`
- `user_id text unique`
- `created_at timestamptz default now()`

### `questions`

- `question_id bigint identity primary key`
- `question_text text`
- `correct_emotion text`
- `created_at timestamptz default now()`

### `submissions`

- `submission_id uuid primary key default gen_random_uuid()`
- `participant_id uuid references participants(participant_id)`
- `started_at timestamptz default now()`
- `submitted_at timestamptz`
- `completed boolean default false`

### `responses`

- `response_id bigint identity primary key`
- `submission_id uuid references submissions(submission_id)`
- `question_id bigint references questions(question_id)`
- `selected_emotion text`
- `created_at timestamptz default now()`

The relationship satisfies:

```text
participants.user_id -> submissions -> responses -> questions
```

So the database can answer:

```text
which anonymous user labeled which tweet with which label
```

## Supabase RPCs Expected By App

The app expects these RPC functions:

- `emotion_labeling_healthcheck`
- `start_labeling_submission`
- `complete_labeling_submission`

These worked before the local secrets disappeared.

## Needed Fix

Recreate `.streamlit/secrets.toml`.

Expected shape:

```toml
[supabase]
url = "https://YOUR_PROJECT_REF.supabase.co"
publishable_key = "YOUR_SUPABASE_PUBLISHABLE_OR_ANON_KEY"
schema = "public"
```

The app also supports environment variables:

```powershell
$env:SUPABASE_URL="https://YOUR_PROJECT_REF.supabase.co"
$env:SUPABASE_PUBLISHABLE_KEY="YOUR_KEY"
$env:SUPABASE_SCHEMA="public"
```

Project-local `.streamlit/secrets.toml` is preferred.

Also recreate `.streamlit/config.toml` if desired:

```toml
[theme]
base = "light"
primaryColor = "#0F766E"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F4F7F6"
codeBackgroundColor = "#F3F4F6"
textColor = "#17211F"
linkColor = "#0F766E"
borderColor = "#D8E0DE"
showWidgetBorder = true
baseRadius = "6px"
buttonRadius = "6px"
font = "'Inter':https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
baseFontSize = 15
headingFontSizes = ["34px", "27px", "21px", "17px", "15px", "13px"]
headingFontWeights = [650, 650, 600, 600, 600, 600]
linkUnderline = false

grayColor = "#66736F"
blueColor = "#2563EB"
greenColor = "#16825D"
redColor = "#C2413B"
yellowColor = "#B7791F"
orangeColor = "#C65D21"
violetColor = "#7656A8"
```

## Verification Commands

From:

`C:\Users\patel\Downloads\Streamlit`

Run:

```powershell
python -m py_compile app.py data_handler.py models.py shared_functions.py pages\instructions.py pages\labeling.py pages\finished_screen.py
```

Run:

```powershell
python -c "from streamlit.testing.v1 import AppTest; at=AppTest.from_file('app.py', default_timeout=20).run(); print('exceptions', len(at.exception)); print('titles', [t.value for t in at.title]); print('toggles', len(at.toggle))"
```

Expected:

```text
exceptions 0
titles ['Emotion labeling']
toggles 1
```

Relaunch:

```powershell
$connections = Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
if ($connections) {
  $connections | Select-Object -ExpandProperty OwningProcess | Sort-Object -Unique | ForEach-Object {
    Stop-Process -Id $_ -Force
  }
}

python -m streamlit run app.py --server.port 8501 --server.headless true
```

Health check:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8501/_stcore/health
```

Expected content:

```text
ok
```

## Notes

- Do not expose or print the Supabase key in chat/output.
- `.streamlit/secrets.toml` should remain gitignored.
- `.gitignore` currently includes:
  - `.streamlit/secrets.toml`
  - `__pycache__/`
  - `*.py[cod]`
- If using Supabase MCP, get the project URL and publishable key from the connected project and write them into `.streamlit/secrets.toml`.
- The app intentionally uses RPC instead of direct `.table("responses").insert(...)` because:
  - The actual `responses` table stores `submission_id`, not `participant_id`.
  - The save operation spans participants, submissions, questions, and responses.
  - RPC keeps the multi-table operation atomic and works with RLS.
