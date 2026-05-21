# Habit Tracker

Single-page Habit Tracker built with Python and Streamlit for the frontend assessment.

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Start the app with `streamlit run app.py`.

If you want a clean reset, delete `habit_data.json` and reload the app. The file is created automatically the first time you add or change data.

## Deploy

Streamlit Community Cloud is the simplest deployment path for this app.

1. Push the repository to GitHub.
2. Open https://share.streamlit.io and sign in.
3. Choose the repository, branch, and `app.py` as the entry point.
4. Add `streamlit` to the dependencies through `requirements.txt`.
5. Deploy and copy the public URL into the section below.

## Stack and design decisions

- Python + Streamlit keeps the app simple to run and easy to review.
- State is stored in `st.session_state` and mirrored to `habit_data.json` so habits and checkmarks survive reloads.
- The weekly grid uses a row-per-habit, column-per-day layout so the tracking model is obvious at a glance.
- Today is highlighted in the date header to make the current column easy to find.
- Streaks are shown next to each habit so progress is visible without opening another screen.

## Responsive and accessibility notes

- The layout uses wide-mode Streamlit with compact cards and restrained styling so it stays usable on desktop and mobile.
- Checkbox labels are descriptive and tied to the habit name plus the full date for screen readers.
- Buttons and checkboxes are keyboard accessible through native Streamlit controls.
- The grid keeps the 7-day structure intact across screen sizes and adds horizontal overflow protection for smaller widths.

## Deployed URL

Not deployed in this submission.

## Project structure

- `app.py` - Streamlit app entry point.
- `requirements.txt` - dependency list.
- `README.md` - run and design notes.
- `ANSWERS.md` - assessment responses.
- `.gitignore` - ignores local data and virtual environments.

## Suggested git history

If you want the repository history to show progress clearly, use commits like these:

1. `chore: scaffold habit tracker project`
2. `feat: add weekly habit grid and persistence`
3. `docs: add assessment answers and setup instructions`
