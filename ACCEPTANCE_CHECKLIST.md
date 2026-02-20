# Acceptance Checklist

1. **Email-confirmed registration**: Implemented in `/register` + `/confirm/<token>`. Test: `tests/test_auth_and_admin.py::test_email_confirm_toggles_state`.
2. **Inactive until admin approval**: `User.status` defaults to `INACTIVE`; approval route updates to `ACTIVE`.
3. **Unique PIN hashed only**: Admin approval generates random 6-digit PIN and stores only hash (`pin_hash`).
4. **Server-side PIN verification**: `process_access_attempt` validates PIN hash server-side.
5. **All attempts logged**: `process_access_attempt` writes `AccessLog` on every branch.
6. **Admin view all logs**: `/admin/logs` page lists all logs with filters.
7. **User view own logs only**: `/my-history` filtered by current user; cross-user route forbidden.
8. **HTTPS note**: README includes production HTTPS requirement.
9. **Remote activate/deactivate**: Admin actions in `/admin/users`.
10. **Temporary admin role**: `role_expires_at` + `has_admin_access` enforcement.
11. **Time-restricted windows**: `AccessWindow` table and `/admin/windows` assignment UI.
12. **Outside-window deny+log**: `process_access_attempt` returns deny/log when outside existing windows.
13. **Failed attempts recorded**: `failed_pin_attempts`, `last_failed_at`, and per-attempt deny logs visible on admin/users + logs pages.
14. **SQLi/auth safety**: SQLAlchemy ORM + validators + safe error handlers.
15. **Modern browser support**: Standard server-rendered HTML/CSS tested in Flask app (Chrome/Firefox/Edge compatible).

## Manual smoke test
1. Register a user.
2. Confirm email via dev link.
3. Login as admin (`flask --app app seed-admin` if needed).
4. Approve user and note generated PIN.
5. Set access window and test PIN in/outside window.
6. Validate logs in `/admin/logs` and user-only history in `/my-history`.
