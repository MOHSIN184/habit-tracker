# Assessment Answers

## 1. Stack and design choices

- I used Python + Streamlit because it is the fastest way to ship a polished single-page internal tool with minimal setup.
- I chose a JSON-backed persistence layer on top of `st.session_state` so the app survives reloads without requiring a database.
- The weekly grid was implemented as a row-by-row tracker with 7 date columns to keep the mental model simple.

## 2. Visual and interaction decisions

- Today’s column is highlighted in a warm accent color so users can orient themselves quickly.
- Streak counters are shown beside each habit and use a color change when the streak is active.
- I kept styling clean and restrained rather than highly decorative so the interface reads like a practical assessment app.
- Add, rename, and delete actions are grouped separately from the grid to reduce accidental edits.

## 3. Responsive and accessibility considerations

- The layout is compact enough for a 360px mobile viewport while still working well on a 1440px desktop.
- Native Streamlit checkboxes and buttons provide keyboard navigation without custom scripting.
- Checkbox labels include the habit name and full date so screen readers can identify each control.
- The grid keeps dates visible and uses scroll-safe layout rules to avoid clipping on smaller screens.

## 4. AI usage and modifications

- AI was used to draft the initial implementation structure and documentation.
- I adjusted the code to keep the state model explicit, added atomic JSON saves, and wrote the streak calculation manually so the behavior is easy to audit.

## 5. Honest gap and improvement plan

- The app is not deployed in this submission, so there is no live URL to share.
- This workspace does not expose a `git` executable, so I could not create real commit history here; the README includes a suggested commit sequence instead.
- If I continued the project, I would add optional cloud persistence and a lightweight test suite for streak logic and week navigation.
