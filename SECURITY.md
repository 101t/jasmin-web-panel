# Security Policy

## Supported Versions

We actively maintain security fixes for the following versions:

| Version | Supported          |
|---------|--------------------|
| 3.x     | ✅ Active support  |
| 2.x     | ⚠️ Critical fixes only |
| < 2.0   | ❌ End of life     |

---

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

If you discover a security vulnerability, please report it responsibly by emailing:

📧 **[tarek.it.eng@gmail.com](mailto:tarek.it.eng@gmail.com)**

Include the following in your report:

- **Description** of the vulnerability
- **Steps to reproduce** (proof of concept if possible)
- **Affected versions**
- **Potential impact**
- **Suggested fix** (optional)

### What to Expect

| Timeline | Action |
|----------|--------|
| Within **48 hours** | Acknowledgement of your report |
| Within **7 days** | Initial assessment and severity rating |
| Within **30 days** | Patch release or workaround guidance |
| After fix is released | Credit in the release notes (if desired) |

We ask that you keep the vulnerability confidential until we have released a fix.

---

## Security Best Practices

When deploying Jasmin Web Panel, follow these guidelines:

### Environment Variables

- **Never commit `.env` files** to version control.
- Set a strong, unique `SECRET_KEY` (at least 50 random characters).
- Always set `DEBUG=False` in production.
- Restrict `ALLOWED_HOSTS` to your actual domain(s).

### Credentials

- **Change default credentials** (`admin` / `secret`) immediately after first login.
- Use strong passwords for all accounts.
- Rotate Jasmin telnet credentials (`TELNET_USERNAME`, `TELNET_PW`) regularly.

### Network Security

- Run behind a reverse proxy (Nginx/Caddy) with TLS/SSL enabled.
- Restrict access to the Jasmin telnet port (default: 8990) to trusted hosts only.
- Use firewall rules to limit exposure of administrative ports.

### Database

- Use a dedicated database user with minimum required privileges.
- Enable SSL for database connections in production.

### Updates

- Keep the application and all dependencies up to date.
- Monitor [GitHub Security Advisories](https://github.com/101t/jasmin-web-panel/security/advisories) for this repository.

---

## Known Security Considerations

- The Jasmin telnet protocol transmits credentials in plaintext. Ensure the telnet interface is only accessible over a trusted internal network.
- The `SECRET_KEY` in `sample.env` is for development only. **Always override it in production.**

---

Thank you for helping keep Jasmin Web Panel secure! 🔒
