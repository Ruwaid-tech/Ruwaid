# Acceptance Checklist

1. **Valid registration + email confirmation before activation**  
   - Implemented in `/register` and `/confirm/<token>` with email validation + token confirmation.
2. **New users inactive until admin approval**  
   - `User.status` defaults to `INACTIVE`; admin approval required.
3. **Unique PIN assigned and stored hashed only**  
   - Admin approval generates unique PIN (`generate_unique_pin`) and stores only `pin_hash`.
4. **PIN verification server-side only**  
   - `process_access_attempt(user_id, entered_code, current_time)` performs verification on server.
5. **All access attempts logged with user/timestamp/result**  
   - Every branch in `process_access_attempt` writes an `AccessLog` row.
6. **Admin sees all logs in UI**  
   - `/admin/logs` shows full log list with filters.
7. **Users only see their own history**  
   - `/my-history` only queries `current_user.user_id`; cross-user checks return 403.
8. **HTTPS deployment requirement documented**  
   - Documented in `README.md` under HTTPS requirement.
9. **Admin can activate/deactivate remotely**  
   - `/admin/users/<id>/approve` and `/admin/users/<id>/deactivate`.
10. **Temporary admin role expiry**  
    - `role_expires_at` + `has_admin_access` logic.
11. **Time-restricted access windows**  
    - `AccessWindow` model + `/admin/windows` assignment UI.
12. **Outside window => deny + log**  
    - Implemented in `process_access_attempt` branch with reason `OUTSIDE_ACCESS_WINDOW`.
13. **Multiple failed PIN attempts recorded + visible to admin**  
    - `failed_pin_attempts`, `last_failed_at`, and per-attempt deny logs.
14. **SQL injection and unauthorized attempts handled safely**  
    - SQLAlchemy ORM, Flask-WTF validation, RBAC checks, safe error pages.
15. **Works on modern desktop browsers**  
    - Standard responsive HTML/CSS/JS with no legacy browser dependencies.

## Manual test flow
1. Register a new user.
2. Confirm user email via generated link.
3. Seed/login admin.
4. Approve user and note one-time shown PIN.
5. Set access window.
6. Submit PIN inside/outside window from user dashboard.
7. Verify user history and admin all-log filtering.
