-- The shared beta codes (BETA-DESK, BETA-TEAM, BETA-OWNER) were visible on the public share page and in this repo.
-- Turn them off for new sign-ups. Salons that already joined with them are not affected.
-- New codes are one-time codes made privately in the Supabase SQL editor (never committed here).
update lp_invite_codes set uses_left = 0 where upper(code) in ('BETA-DESK', 'BETA-TEAM', 'BETA-OWNER');
