# Loopd-In

The digital logbook for salon teams: daily log, client incidents, supplies, team chat, time off, 1:1s with goal sheets,
employee handbook sign-off, write-ups, and applicant tracking, with phone notifications.

- **App:** https://lbooger43.github.io/loopd-in/
- **Demo salon (sample data, no sign-in):** https://lbooger43.github.io/loopd-in/demo/

## Plans

| Plan | Price (per location) | Adds |
| --- | --- | --- |
| Front Desk | $29/mo | Daily log, incidents, supplies, team chat, announcements, issue reports, notifications |
| Team | $59/mo | Time off, 1:1s and goal sheets, handbook sign-off, staff notes, manager log, write-ups |
| Owner | $99/mo | Applicant tracking, salon logo, setup call |

Free during the beta. Salons join with an invite code.

## How it's built

- One page app (`index.html`) on GitHub Pages, data in Supabase.
- Every salon's data lives in `lp_` tables tied to a salon; database rules make sure people only see their own salon (`db/`).
- Files (photos, handbook, signatures, logo) live in the private `lp-files` bucket, one folder per salon.
