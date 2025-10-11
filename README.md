# Self Haven

Self Haven is a lightweight, privacy-first web experience that helps teens
(13–18) soften body-image stress linked to social media. The interface offers
rotating daily inspiration, guided soundscapes, supportive journaling prompts,
micro mindfulness timers, sleep wind-down checklists, and a daily positivity
challenge. Teens and trusted adults can mark favorites, toggle dark mode, opt in
to gentle browser reminders, and clear all data at any time—no account required.

## Tech stack

- Static HTML + CSS + vanilla JavaScript (no frameworks)
- Client-side routing powered by a minimal hash router
- All preferences are saved to `localStorage`; no network calls are required

## Running locally

Open `index.html` in any modern browser. For local notifications to work, serve
the folder over `http://localhost` using your preferred static server:

```bash
python -m http.server 8000
```

Then visit `http://localhost:8000`.

## Key features

- **Daily rotation:** Quotes, affirmations, and a featured soundscape shift each
day so the home page always feels fresh.
- **Activities hub:** Tabs for soundscapes, journaling, mindfulness, sleep
support, and positivity challenges. All tools work offline and store state
locally.
- **Favorites:** Heart any activity to keep it in a dedicated favorites list.
- **Safety guardrails:** A gentle content filter surfaces encouraging messaging
when harsh language appears in journal entries.
- **Comfort controls:** Dark mode toggle, optional browser notifications, and a
single-click “clear saved data” button.
- **Optional sign-in stub:** Teens can store a pseudonymous email locally to
indicate an optional sign-in without sending data anywhere.

## Accessibility and performance

The interface uses semantic HTML, high-contrast typography, large touch targets,
and avoids flashing elements. CSS custom properties provide instant theme
switching, and JavaScript remains under 100 KB to keep the experience fast on
mobile devices.
