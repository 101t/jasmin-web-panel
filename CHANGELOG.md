# Change history

## 3.1.0 (2026-10-15)

Docker images now follow the application version: `tarekaec/jasmin_web_panel:3.1.0` (also `3.1`, `3` and
`latest`), built for amd64 and arm64. `edge` follows the master branch.

### Upgrade notes
- Run the migrations (the Docker image does it on start): stored Jasmin user passwords are encrypted.
  They are encrypted with `SECRET_KEY`; set `FIELD_ENCRYPTION_KEY` before rotating `SECRET_KEY`.
- With Docker Compose, Jasmin's configuration now lives in the `jasmin_config` volume; see
  "Upgrading" in the Docker guide if you kept one in `./jasmin_config`.
- API clients: gateway connection problems are now HTTP 503.

### Fixed: UI and gateway
- MT/MO routes with several connectors or filters (RandomRoundrobin, Failover) can be created from the panel: only the last selected value used to reach Jasmin (#107).
- Unchecking a user authorization (HTTP send, SMPP send, …) now revokes it; it used to be saved as allowed.
- Editing a user no longer copies the password typed for the previously edited user, no longer resends unchanged values (a stale balance or SMS count overwrote what was consumed meanwhile), and saves the `ND` / empty quota as unlimited.
- Errors returned by jcli are shown with Jasmin's message instead of being ignored, reported as success, or ending in a 10 second timeout and an HTML error page. A rejected line aborts the jcli session, so the next command is not misread.
- jcli output containing `> ` (route type descriptions, filters such as `<U (uid=u1)>`) no longer desynchronises the connection.
- Adding a group, user, filter or connector with an existing id is refused: jcli silently replaced the object, resetting a user's quotas and authorizations.
- The MO router offers Jasmin users (delivered as `smpps(username)`) instead of SMPP client connectors, and both routers only offer filters that Jasmin accepts for that direction.
- Filter, route, HTTP connector and SMPP connector listings are parsed correctly (routes/description columns, regex filters containing commas, empty values).
- The `/api/users/` and `/api/groups/` endpoints work (they relied on a middleware that was never enabled); every API error now has the `{"error": ...}` shape and its proper status code.
- Values containing line breaks are rejected instead of being sent to jcli as extra commands.
- The submit log date filter only accepts its two date columns.
- An expired session during an AJAX action sends the user to the sign-in page instead of failing silently.
- Accounts created with `manage.py createsuperuser` can sign in (they were refused as "email not verified").
- `DEBUG=False` (and `DEBUG: 0` in docker-compose) actually disables debug mode; `bool("False")` used to enable it. Same for `SUBMIT_LOG`.

### Fixed: deployment
- Static files are served by the panel (WhiteNoise), so the Docker image keeps its styling with `DEBUG=False`.
- `docker compose up` with the shipped `sample.env` works: database credentials match, Jasmin starts (its configuration now lives in the `jasmin_config` named volume instead of an empty bind mount), and Send SMS reaches the `jasmin` service.
- The Docker image builds on arm64 without editing the Dockerfile; Gunicorn no longer runs with `--reload`.
- Sign-in, sign-up and reset pages no longer request a missing `auth/global.js`.

### Security
- Jasmin user passwords kept for Send SMS are encrypted at rest (Fernet) instead of stored in plain text.
- jQuery 3.4.1 → 3.7.1 (CVE-2020-11022, CVE-2020-11023), jquery-validation 1.19.1 → 1.19.5
  (CVE-2021-21252, CVE-2022-31147), Bootstrap JS 4.3.1 → 4.6.2.

### Changed
- Gateway connection problems are reported as HTTP 503 (were 500, or 403 for a wrong jcli password).
- The users page loads with one jcli command instead of one per user; details load when editing.
- `sample.env` defaults to `DEBUG=False` and a placeholder `SECRET_KEY`; production warns when a published sample key is used.
- New `HTTPS_ONLY` setting for secure cookies and HTTPS redirects behind TLS.
- The user "service" menu can unbind or ban a user from the SMPP server; the edit form offers the `schedule_delivery_time` and `hex_content` authorizations.
- Clearer forms: validation matches Jasmin's id rules, uid/username are read-only when editing, loading and error states in every table, labelled status badges and accessible action buttons.

### Added
- Search box on every list page.
- Interface messages built by JavaScript are translatable; form validation messages in Turkish.
- Release workflow: Docker images published to Docker Hub on every master push (`edge`) and release tag,
  and GitHub releases created from this changelog.
- Integration tests against a live Jasmin gateway (`make test_integration`), parser and view tests, CI jobs for them and for the documentation build, Dependabot.
- `LICENSE` file (MIT, as stated in the README).
- Documentation: REST API reference, gateway management guide, troubleshooting, complete configuration reference.

### Removed
- Travis CI configuration (replaced by GitHub Actions).

### Fixed: documentation site
- The documentation site was not updated by the publishing workflow (it pushed a `gh-pages` branch while
  GitHub Pages deploys from Actions artifacts); it now deploys on every master push.

### Also in this release

1. **Open Source Enhancements**
   - Added `CONTRIBUTING.md` with detailed contributor guide
   - Added `SECURITY.md` with security policy and responsible disclosure process
   - Added `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1)
   - Added GitHub issue templates (bug report, feature request, question)
   - Added GitHub pull request template
   - Added GitHub Actions CI workflow alongside existing Travis CI configuration
2. **Testing Infrastructure**
   - Added `pytest` and `pytest-django` as dev dependencies
   - Added initial test suite covering core utilities, models, web views, and REST API
   - Tests run without requiring Redis or a live Jasmin gateway (use LocMemCache in tests)
3. **API Security**
   - Added configurable rate limiting to the REST API (`API_THROTTLE_ANON`, `API_THROTTLE_USER`)
   - Rate limits configurable via environment variables
4. **Bug Fixes**
   - Fixed `UserAgentMiddleware` crash when `HTTP_USER_AGENT` header is absent
   - Fixed `user_agent.py` module-level cache initialization to use lazy evaluation, respecting runtime settings overrides (benefits testing and deployments that reconfigure the cache)

## 3.0.1
Changes
1. JavaScript fixes
2. Adding Send Message to test Jasmin Gateway

## 3.0.0
Changes
1. Adding live health checker for jasmin sms gateway
2. bug fixes, code improvements

## 2.0.2
Changes

1. Adding FailOverRouter supports to MT / MO Router

## 2.0.1
Changes

1. Adding **[Submit Log](https://github.com/101t/jasmin-submit-logs)** report (DLR report)

## 2.0.0
Changes

1. UI Improved, jQuery Fixed, jQuery Validation added.
2. Backend fixing, upgrade to python3 and fresh Django version.
3. Telnet connector fixing.
4. Deployment made easier.
5. Fixing common connection issues.
6. Simple dashboard initialized.
7. User Profile, Change Password, Add Avatar.
8. Activity Log, to log your usage.

## 1.0.0
Changes

1. first standard release of jasmin web panel
2. the idea of project