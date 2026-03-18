# Acceptance Checklist

1. **Valid registration + email confirmation before activation**  
   - Implemented in `/register` and `/confirm/<token>` with email validation, token confirmation, and delivered confirmation emails.
2. **New users inactive until admin approval**  
   - `User.status` defaults to `INACTIVE`; admin approval required after confirmation.
3. **Unique PIN assigned and stored hashed only**  
   - Admin approval generates a unique PIN (`generate_unique_pin`) and stores only `pin_hash`.
4. **PIN verification server-side only**  
   - `process_access_attempt(user_id, entered_code, current_time)` performs verification on the server.
5. **All access attempts logged with user/timestamp/result**  
   - Every branch in `process_access_attempt` writes an `AccessLog` row.
6. **Admin sees all logs in UI**  
   - `/admin/logs` shows the full log list with filters.
7. **Users only see their own history**  
   - `/my-history` only queries `current_user.user_id`; cross-user checks return 403.
8. **HTTPS deployment requirement documented**  
   - Documented in `README.md` under the HTTPS requirement section.
9. **Admin can activate/deactivate remotely**  
   - `/admin/users/<id>/approve` and `/admin/users/<id>/deactivate`.
10. **Temporary admin role expiry**  
    - `role_expires_at` + `has_admin_access` logic.
11. **Time-restricted access windows**  
    - `AccessWindow` model + `/admin/windows` assignment UI.
12. **Outside window => deny + log**  
    - Implemented in `process_access_attempt` with reason `OUTSIDE_ACCESS_WINDOW`.
13. **Multiple failed PIN attempts recorded + visible to admin**  
    - `failed_pin_attempts`, `last_failed_at`, and per-attempt deny logs are visible in admin pages.
14. **SQL injection and unauthorized attempts handled safely**  
    - SQLAlchemy ORM, Flask-WTF validation, RBAC checks, and safe error pages.
15. **Works on modern desktop browsers**  
    - Standard responsive HTML/CSS/JS with no legacy browser dependencies.

## Manual test flow
1. Register a new user.
2. Open **Dev Mailbox** and confirm the user received a confirmation email.
3. Confirm the user email via the emailed link.
4. Seed/login as admin.
5. Approve the user.
6. Open **Dev Mailbox** again and verify the approval email includes the generated PIN.
7. Set an access window and test PIN entry inside/outside the permitted time.
8. Verify user history and admin all-log filtering.
