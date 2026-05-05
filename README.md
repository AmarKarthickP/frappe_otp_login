# Frappe OTP Login

Passwordless OTP login for [Frappe Framework](https://frappe.io/framework) v17+.

Users log in with just their email, username, or phone number + a one-time verification code. No password required. This is not 2FA — it replaces password-based authentication entirely.

## Features

- **Email OTP login** — send a 6-digit code to the user's inbox, verify, session created
- **Flexible identifier** — look up users by email, username, or phone number
- **Rate limiting** — max 5 OTP requests per identifier per 15 minutes
- **Brute-force protection** — max 5 failed verification attempts per OTP
- **Custom login page** — clean two-step form at `/otp_login`, styled to match Frappe's UI
- **Anti-enumeration** — returns success even if the user doesn't exist

## Roadmap

- [x] Phase 1: Email OTP login
- [ ] Phase 2: SMS OTP via configurable gateway providers (ntfy.sh, MSG91, any DLT-compliant gateway)

## Install

```bash
bench get-app frappe_otp_login
bench --site your-site.localhost install-app frappe_otp_login
```

To install from source (development):

```bash
bench get-app frappe_otp_login --link /path/to/frappe_otp_login
bench --site your-site.localhost install-app frappe_otp_login
```

## Usage

1. Visit `/otp_login` on your site
2. Enter your email address, username, or phone number
3. Check your inbox for a 6-digit verification code
4. Enter the code — you're logged in and redirected to `/desk`

## How It Works

### Login Flow

```
User visits /otp_login
    │
    ├─ Step 1: Enter email / username / phone
    │      │
    │      ▼
    │   POST /api/method/frappe_otp_login.api.send_otp
    │      ├─ Look up User doc
    │      ├─ Generate random 6-digit OTP
    │      ├─ Store in Redis (5 min expiry)
    │      └─ Send via frappe.sendmail()
    │
    ├─ Step 2: Enter OTP code
    │      │
    │      ▼
    │   POST /api/method/frappe_otp_login.api.verify_otp
    │      ├─ Compare with stored OTP
    │      ├─ Delete OTP (prevent replay)
    │      ├─ Create session via LoginManager.login_as()
    │      └─ Redirect to /desk
```

### API Endpoints

Both endpoints are guest-accessible (`@frappe.whitelist(allow_guest=True)`).

| Endpoint | Method | Parameters | Description |
|---|---|---|---|
| `frappe_otp_login.api.send_otp` | POST | `identifier` | Sends a 6-digit OTP to the user's email |
| `frappe_otp_login.api.verify_otp` | POST | `identifier`, `otp` | Verifies the OTP and creates a session |

## Security

- OTPs expire after **5 minutes** and are deleted after successful verification
- **Rate limited**: 5 OTP requests per identifier per 15 minutes
- **Failure limit**: 5 wrong attempts locks the OTP (user must request a new one)
- **No user enumeration**: `send_otp` returns success even if the identifier doesn't match any user

## License

GPL-3.0-or-later
