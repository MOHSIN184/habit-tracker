from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path

import streamlit as st


DATA_FILE = Path(__file__).with_name("habit_data.json")
APP_TITLE = "Habit Tracker"


def rerun() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
    st.experimental_rerun()


def today() -> date:
    return date.today()


def week_start_for(day: date) -> date:
    return day - timedelta(days=day.weekday())


def week_dates(start: date) -> list[date]:
    return [start + timedelta(days=offset) for offset in range(7)]


def iso_day(day: date) -> str:
    return day.isoformat()


def parse_day(value: str) -> date:
    return date.fromisoformat(value)


def default_state() -> dict:
    return {
        "habits": [],
        "checkmarks": {},
        "selected_week_start": iso_day(week_start_for(today())),
    }


def load_state() -> dict:
    if not DATA_FILE.exists():
        return default_state()

    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_state()

    habits: list[dict] = []
    seen_ids: set[str] = set()
    for item in raw.get("habits", []):
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        habit_id = str(item.get("id") or uuid.uuid4().hex)
        if habit_id in seen_ids:
            continue
        seen_ids.add(habit_id)
        habits.append({"id": habit_id, "name": name})

    checkmarks: dict[str, list[str]] = {}
    raw_checkmarks = raw.get("checkmarks", {})
    for habit in habits:
        saved_days = raw_checkmarks.get(habit["id"], [])
        cleaned_days = []
        for day_value in saved_days:
            try:
                cleaned_days.append(iso_day(parse_day(day_value)))
            except ValueError:
                continue
        if cleaned_days:
            checkmarks[habit["id"]] = sorted(set(cleaned_days))

    selected_week_start = iso_day(week_start_for(today()))
    stored_week = raw.get("selected_week_start")
    if isinstance(stored_week, str):
        try:
            selected_week_start = iso_day(parse_day(stored_week))
        except ValueError:
            pass

    return {
        "habits": habits,
        "checkmarks": checkmarks,
        "selected_week_start": selected_week_start,
    }


def save_state() -> None:
    payload = {
        "habits": st.session_state.app_state["habits"],
        "checkmarks": st.session_state.app_state["checkmarks"],
        "selected_week_start": st.session_state.app_state["selected_week_start"],
        "saved_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    temp_file = DATA_FILE.with_suffix(".tmp")
    temp_file.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    temp_file.replace(DATA_FILE)


def state() -> dict:
    return st.session_state.app_state


def habit_by_id(habit_id: str) -> dict | None:
    for habit in state()["habits"]:
        if habit["id"] == habit_id:
            return habit
    return None


def habit_names_lower(exclude_id: str | None = None) -> set[str]:
    names = set()
    for habit in state()["habits"]:
        if exclude_id and habit["id"] == exclude_id:
            continue
        names.add(habit["name"].strip().lower())
    return names


def clean_habit_name(value: str) -> str:
    return " ".join(value.split()).strip()


def sync_selected_week_start(new_start: date) -> None:
    state()["selected_week_start"] = iso_day(new_start)
    save_state()


def add_habit(name: str) -> tuple[bool, str]:
    clean_name = clean_habit_name(name)
    if not clean_name:
        return False, "Enter a habit name first."
    if clean_name.lower() in habit_names_lower():
        return False, "That habit already exists."

    habit_id = uuid.uuid4().hex
    state()["habits"].append({"id": habit_id, "name": clean_name})
    state()["checkmarks"].setdefault(habit_id, [])
    save_state()
    return True, f"Added '{clean_name}'."


def rename_habit(habit_id: str, new_name: str) -> tuple[bool, str]:
    clean_name = clean_habit_name(new_name)
    if not clean_name:
        return False, "Enter a new habit name."
    if clean_name.lower() in habit_names_lower(exclude_id=habit_id):
        return False, "Another habit already uses that name."

    habit = habit_by_id(habit_id)
    if habit is None:
        return False, "Habit not found."

    habit["name"] = clean_name
    save_state()
    return True, f"Renamed to '{clean_name}'."


def delete_habit(habit_id: str) -> tuple[bool, str]:
    habit = habit_by_id(habit_id)
    if habit is None:
        return False, "Habit not found."

    state()["habits"] = [item for item in state()["habits"] if item["id"] != habit_id]
    state()["checkmarks"].pop(habit_id, None)

    # Remove any lingering widget state for the deleted habit in this session.
    prefix = f"habit-check::{habit_id}::"
    for key in list(st.session_state.keys()):
        if isinstance(key, str) and key.startswith(prefix):
            del st.session_state[key]

    save_state()
    return True, f"Deleted '{habit['name']}'."


def toggle_check(habit_id: str, day_value: str, widget_key: str) -> None:
    checked = bool(st.session_state.get(widget_key))
    saved_days = state()["checkmarks"].setdefault(habit_id, [])

    if checked and day_value not in saved_days:
        saved_days.append(day_value)
    elif not checked and day_value in saved_days:
        saved_days.remove(day_value)

    saved_days.sort()
    if not saved_days:
        state()["checkmarks"].pop(habit_id, None)
    save_state()


def is_checked(habit_id: str, day_value: str) -> bool:
    return day_value in state()["checkmarks"].get(habit_id, [])


def current_streak(habit_id: str) -> int:
    """Count consecutive completed days ending today.

    This is intentionally simple and predictable: if today is not checked,
    the current streak is 0. If today is checked, we walk backward one day at a
    time until the chain breaks.
    """

    completed = {parse_day(day_value) for day_value in state()["checkmarks"].get(habit_id, [])}
    streak = 0
    cursor = today()

    while cursor in completed:
        streak += 1
        cursor -= timedelta(days=1)

    return streak


def selected_week() -> date:
    try:
        return parse_day(state()["selected_week_start"])
    except ValueError:
        return week_start_for(today())


def set_week(new_start: date) -> None:
    sync_selected_week_start(new_start)
    st.session_state.view_week_start = new_start


def go_previous_week() -> None:
    set_week(selected_week() - timedelta(days=7))
    rerun()


def go_next_week() -> None:
    set_week(selected_week() + timedelta(days=7))
    rerun()


def go_to_current_week() -> None:
    set_week(week_start_for(today()))
    rerun()


def set_initial_session_state() -> None:
    if "app_state" not in st.session_state:
        st.session_state.app_state = load_state()

    if "view_week_start" not in st.session_state:
        try:
            st.session_state.view_week_start = parse_day(st.session_state.app_state["selected_week_start"])
        except ValueError:
            st.session_state.view_week_start = week_start_for(today())


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            :root {
                color-scheme: light;
            }

            .block-container {
                padding-top: 1.15rem;
                padding-bottom: 2rem;
                max-width: 1200px;
            }

            .app-shell {
                display: flex;
                flex-direction: column;
                gap: 0.85rem;
            }

            .title-wrap h1 {
                margin-bottom: 0.15rem;
            }

            .subtitle {
                color: #57606a;
                font-size: 0.98rem;
                line-height: 1.45;
            }

            .meta-row {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
                margin-top: 0.35rem;
            }

            .meta-pill {
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
                border-radius: 999px;
                padding: 0.3rem 0.65rem;
                background: #eef2f7;
                color: #1f2937;
                font-size: 0.82rem;
                font-weight: 600;
            }

            .section-label {
                display: inline-flex;
                align-items: center;
                gap: 0.45rem;
                font-size: 0.8rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: #64748b;
                margin: 0.15rem 0 0.55rem 0;
            }

            .day-card {
                border: 1px solid #d8dee6;
                border-radius: 14px;
                background: #f8fafc;
                padding: 0.55rem 0.35rem;
                text-align: center;
                min-height: 74px;
            }

            .day-card.today {
                background: #fff4d2;
                border-color: #e7b94d;
                box-shadow: inset 0 0 0 1px rgba(231, 185, 77, 0.16);
            }

            .day-name {
                font-size: 0.75rem;
                letter-spacing: 0.05em;
                text-transform: uppercase;
                color: #5b6572;
                font-weight: 700;
            }

            .day-date {
                font-size: 0.95rem;
                font-weight: 700;
                color: #111827;
                margin-top: 0.1rem;
            }

            .today-badge {
                margin-top: 0.28rem;
                display: inline-flex;
                align-items: center;
                border-radius: 999px;
                padding: 0.18rem 0.48rem;
                background: rgba(217, 119, 6, 0.16);
                color: #92400e;
                font-size: 0.72rem;
                font-weight: 700;
            }

            .habit-card {
                border: 1px solid #d8dee6;
                border-radius: 14px;
                background: white;
                padding: 0.75rem 0.8rem;
                min-height: 74px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }

            .habit-name {
                font-size: 1rem;
                font-weight: 700;
                color: #111827;
                line-height: 1.3;
                word-break: break-word;
            }

            .habit-subline {
                display: flex;
                flex-wrap: wrap;
                gap: 0.4rem;
                margin-top: 0.35rem;
            }

            .streak-pill {
                display: inline-flex;
                align-items: center;
                gap: 0.3rem;
                border-radius: 999px;
                padding: 0.22rem 0.55rem;
                background: #edf7ed;
                color: #14532d;
                font-size: 0.78rem;
                font-weight: 700;
            }

            .streak-pill.zero {
                background: #f1f5f9;
                color: #475569;
            }

            .empty-state {
                border: 1px dashed #c8d0d9;
                border-radius: 18px;
                background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
                padding: 1rem;
            }

            .empty-state h3 {
                margin-bottom: 0.25rem;
            }

            .grid-wrap {
                overflow-x: auto;
                padding-bottom: 0.25rem;
            }

            .keyboard-note {
                color: #64748b;
                font-size: 0.82rem;
            }

            @media (max-width: 640px) {
                .block-container {
                    padding-left: 0.75rem;
                    padding-right: 0.75rem;
                }

                .day-card,
                .habit-card {
                    min-height: 68px;
                    padding: 0.5rem 0.4rem;
                }

                .day-date {
                    font-size: 0.88rem;
                }

                .habit-name {
                    font-size: 0.95rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_top_bar() -> None:
    week_start = selected_week()
    current_start = week_start_for(today())
    week_end = week_start + timedelta(days=6)

    left, middle, right, status = st.columns([1, 1, 1, 2.2], vertical_alignment="center")
    with left:
        st.button("Previous week", on_click=go_previous_week, use_container_width=True)
    with middle:
        if week_start == current_start:
            heading = "This week"
        else:
            heading = f"{week_start.strftime('%b %d, %Y')} - {week_end.strftime('%b %d, %Y')}"
        st.button("Back to this week", disabled=week_start == current_start, on_click=go_to_current_week if week_start != current_start else None, use_container_width=True)
    with right:
        st.button("Next week", on_click=go_next_week, use_container_width=True)
    with status:
        st.markdown(
            f"<div class='meta-pill'>Week view: {escape(heading)}</div>",
            unsafe_allow_html=True,
        )


def render_habit_form() -> None:
    st.markdown("<div class='section-label'>Add Habit</div>", unsafe_allow_html=True)
    with st.form("add_habit_form", clear_on_submit=True):
        habit_name = st.text_input(
            "New habit name",
            placeholder="e.g. Read for 20 minutes",
            label_visibility="visible",
        )
        submitted = st.form_submit_button("Add habit", use_container_width=False)

    if submitted:
        success, message = add_habit(habit_name)
        if success:
            st.success(message)
            rerun()
        else:
            st.warning(message)


def render_manage_section() -> None:
    habits = state()["habits"]
    if not habits:
        return

    with st.expander("Manage Habit", expanded=len(habits) <= 3):
        rename_col, delete_col = st.columns(2)

        with rename_col:
            st.markdown("<div class='section-label'>Rename habit</div>", unsafe_allow_html=True)
            with st.form("rename_habit_form"):
                target_id = st.selectbox(
                    "Habit to rename",
                    options=[item["id"] for item in habits],
                    format_func=lambda habit_id: habit_by_id(habit_id)["name"] if habit_by_id(habit_id) else "Unknown habit",
                )
                current_name = habit_by_id(target_id)["name"] if habit_by_id(target_id) else ""
                new_name = st.text_input("New habit name", value=current_name)
                rename_submitted = st.form_submit_button("Rename")

            if rename_submitted:
                success, message = rename_habit(target_id, new_name)
                if success:
                    st.success(message)
                    rerun()
                else:
                    st.warning(message)

        with delete_col:
            st.markdown("<div class='section-label'>Delete habit</div>", unsafe_allow_html=True)
            with st.form("delete_habit_form"):
                target_id = st.selectbox(
                    "Habit to delete",
                    options=[item["id"] for item in habits],
                    format_func=lambda habit_id: habit_by_id(habit_id)["name"] if habit_by_id(habit_id) else "Unknown habit",
                    key="delete_habit_select",
                )
                confirm_delete = st.checkbox("I understand this removes the habit and its history.")
                delete_submitted = st.form_submit_button("Delete", type="primary")

            if delete_submitted:
                if not confirm_delete:
                    st.warning("Please confirm deletion first.")
                else:
                    success, message = delete_habit(target_id)
                    if success:
                        st.success(message)
                        rerun()
                    else:
                        st.warning(message)


def render_empty_state() -> None:
    st.markdown(
        """
        <div class='empty-state'>
            <h3>No habits yet</h3>
            <p>Start by adding one habit below. Once you create habits, the weekly tracking grid will appear here.</p>
            <p class='keyboard-note'>Tip: checkbox controls are keyboard accessible and saved automatically.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_grid() -> None:
    habits = state()["habits"]
    if not habits:
        render_empty_state()
        return

    week_start = selected_week()
    days = week_dates(week_start)
    today_value = iso_day(today())

    st.markdown("<div class='section-label'>Weekly Grid</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='keyboard-note'>Use the checkboxes to mark a habit done for a day. Today is highlighted in gold.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='grid-wrap'>", unsafe_allow_html=True)

    header_columns = st.columns([2.6] + [1] * 7, gap="small")
    with header_columns[0]:
        st.markdown("<div class='habit-card'><div class='habit-name'>Habit</div></div>", unsafe_allow_html=True)

    for index, day in enumerate(days, start=1):
        with header_columns[index]:
            is_today = iso_day(day) == today_value
            badge_html = "<div class='today-badge'>Today</div>" if is_today else ""
            st.markdown(
                (
                    f"<div class='day-card {'today' if is_today else ''}'>"
                    f"<div class='day-name'>{escape(day.strftime('%a'))}</div>"
                    f"<div class='day-date'>{escape(day.strftime('%b %d'))}</div>"
                    f"{badge_html}"
                    f"</div>"
                ),
                unsafe_allow_html=True,
            )

    for habit in habits:
        streak = current_streak(habit["id"])
        row_columns = st.columns([2.6] + [1] * 7, gap="small")

        with row_columns[0]:
            streak_class = "streak-pill zero" if streak == 0 else "streak-pill"
            streak_text = "No current streak" if streak == 0 else f"{streak} day streak"
            st.markdown(
                (
                    "<div class='habit-card'>"
                    f"<div class='habit-name'>{escape(habit['name'])}</div>"
                    "<div class='habit-subline'>"
                    f"<span class='{streak_class}'>{escape(streak_text)}</span>"
                    "</div>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

        for index, day in enumerate(days, start=1):
            day_value = iso_day(day)
            widget_key = f"habit-check::{habit['id']}::{day_value}"
            help_text = f"{habit['name']} on {day.strftime('%A, %B %d, %Y')}"

            with row_columns[index]:
                st.checkbox(
                    help_text,
                    value=is_checked(habit["id"], day_value),
                    key=widget_key,
                    on_change=toggle_check,
                    args=(habit["id"], day_value, widget_key),
                    label_visibility="collapsed",
                    help=help_text,
                )

    st.markdown("</div>", unsafe_allow_html=True)


def render_summary() -> None:
    habits = state()["habits"]
    week_start = selected_week()
    week_days = week_dates(week_start)
    checked_count = 0
    for habit in habits:
        for day in week_days:
            if is_checked(habit["id"], iso_day(day)):
                checked_count += 1

    c1, c2, c3 = st.columns(3)
    c1.metric("Habits", len(habits))
    c2.metric("Completed this week", checked_count)
    c3.metric("Week range", f"{week_start.strftime('%b %d')} - {(week_start + timedelta(days=6)).strftime('%b %d')}")


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="✅", layout="wide")
    set_initial_session_state()
    inject_styles()

    st.markdown("<div class='app-shell'>", unsafe_allow_html=True)
    st.markdown(f"<div class='title-wrap'><h1>{APP_TITLE}</h1></div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='subtitle'>Track habits across the week, keep your streaks visible, and navigate between weeks without losing progress.</div>",
        unsafe_allow_html=True,
    )

    current_count = len(state()["habits"])
    current_start = week_start_for(today())
    viewed_start = selected_week()
    meta_items = [f"{current_count} habits"]
    if viewed_start == current_start:
        meta_items.append("viewing this week")
    else:
        meta_items.append(f"viewing {viewed_start.strftime('%b %d')}")
    st.markdown(
        "<div class='meta-row'>" + "".join(f"<span class='meta-pill'>{escape(item)}</span>" for item in meta_items) + "</div>",
        unsafe_allow_html=True,
    )

    render_top_bar()
    render_summary()
    render_grid()
    render_habit_form()
    render_manage_section()

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
