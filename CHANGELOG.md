# Change history

## 3.1.0

Changes

1. **Open Source Enhancements**
   - Added `CONTRIBUTING.md` with detailed contributor guide
   - Added `SECURITY.md` with security policy and responsible disclosure process
   - Added `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1)
   - Added GitHub issue templates (bug report, feature request, question)
   - Added GitHub pull request template
   - Added GitHub Actions CI workflow replacing outdated Travis CI configuration
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