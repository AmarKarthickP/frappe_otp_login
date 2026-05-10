# Frappe OTP Login

Passwordless OTP login for [Frappe Framework](https://frappe.io/framework) v16+.

Users log in with just their email, username, or phone number + a one-time verification code. No password required. This is not 2FA — it replaces password-based authentication entirely.

## Features

- **Email OTP** — send a 6-digit code via Frappe's built-in email (SMTP)
- **HTTP channel OTP** — send codes via any HTTP API (SMS gateways, ntfy.sh, custom providers)
- **Channel selection UX** — users pick how to receive the OTP when multiple channels are enabled
- **Email as a peer channel** — enable/disable email independently, just like any HTTP channel
- **Flexible identifier** — lookup by email, username, phone, or mobile number
- **Per-channel identifier label** — configure what each channel asks for ("Email Address", "Phone Number", "Subscribed Topic")
- **Rate limiting** — max 5 OTP requests per identifier per 15 minutes
- **Brute-force protection** — max 5 failed verification attempts per OTP
- **Anti-enumeration** — returns success even if the user doesn't exist
- **Desk configuration page** — modal dialogs for channel setup, SMTP status display
- **Clean uninstall** — removes Redis keys and Desktop Icon on `bench uninstall-app`

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
3. Choose a channel (Email or configured HTTP channels)
4. Check your inbox/device for a 6-digit verification code
5. Enter the code — you're logged in and redirected to `/desk`

## How It Works

### Login Flow

```
User visits /otp_login
    │
    ├─ Step 1: Enter email / username / phone
    │      │
    │      ▼
    │   POST /api/method/frappe_otp_login.api.send_otp
    │      ├─ Look up User doc (by email, username, phone, mobile_no)
    │      ├─ Generate random 6-digit OTP
    │      ├─ Store in Redis (5 min expiry)
    │      ├─ Send via frappe.sendmail() (Email channel)
    │      └─ Send via HTTP request (HTTP channels)
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
| `frappe_otp_login.api.get_available_channels` | GET | — | Returns list of enabled OTP channels |
| `frappe_otp_login.api.send_otp` | POST | `identifier`, `channel` (optional) | Sends a 6-digit OTP |
| `frappe_otp_login.api.verify_otp` | POST | `identifier`, `otp` | Verifies the OTP and creates a session |

## HTTP Channels

The app supports configurable HTTP channels for OTP delivery via external APIs (SMS gateways, notification services, etc.).

### Channel Configuration

Each channel is configured via a modal dialog in **OTP Login Settings** with:

| Field | Description |
|---|---|
| Channel Name | Display name (e.g., "MSG91", "ntfy.sh") |
| Enabled | Toggle to enable/disable this channel |
| Identifier Label | What the input field asks for ("Email Address", "Phone Number", "Subscribed Topic") |
| Method | GET or POST |
| URL | API endpoint URL (must start with `http://` or `https://`) |
| Content Type | `application/json`, `application/x-www-form-urlencoded`, or `Raw (text/plain)` |
| Auth Type | None, Bearer, Basic, or API Key |
| Auth Token | Bearer token or API key value (stored encrypted) |
| Auth Username / Password | Credentials for Basic auth (stored encrypted) |
| OTP Parameter Name | Field name for the OTP code in the request |
| Recipient Parameter Name | Field name for the recipient identifier |
| Message Template | Jinja template with `{{ otp }}`, `{{ recipient }}`, `{{ site_name }}` |
| Parameters | Extra key-value pairs (query params, form fields, headers) |

### Preset Channels

On first install, two preset channels are created:

- **ntfy.sh** — Raw text POST to a ntfy topic (disabled by default)
- **Generic Indian SMS Provider** — GET with query params, pre-configured for DLT-compliant gateways (disabled by default)

## Security

- OTPs expire after **5 minutes** and are deleted after successful verification
- **Rate limited**: 5 OTP requests per identifier per 15 minutes
- **Failure limit**: 5 wrong attempts locks the OTP (user must request a new one)
- **No user enumeration**: `send_otp` returns success even if the identifier doesn't match any user
- **Passwordless session**: Uses `LoginManager.login_as()` — same session mechanism as Frappe's built-in login

## Configuration

1. Open the desk and navigate to the **OTP Login** workspace (lock icon in sidebar)
2. Click **OTP Login Settings** shortcut
3. **Email OTP**: toggle `Email OTP` to enable/disable email delivery. Click **Fetch SMTP Settings** to verify your outgoing email is configured
4. **HTTP Channels**: click **Add HTTP Channel** to open the configuration modal. Double-click any row to edit, or use the **Edit** button on each row
5. Set `Identifier Label` on each channel — this controls what the login page asks the user to enter

The grid shows a 4-column summary: Channel Name, Enabled, Method, URL. All other fields are in the modal.

## Uninstall

```bash
bench --site your-site.localhost uninstall-app frappe_otp_login
```

The `before_uninstall` hook cleans up:
- All OTP codes, rate-limit counters, and failure counters from Redis
- The Desktop Icon record for the app

Frappe automatically drops all doctype tables, removes Module Def records, and deletes the workspace.

## How It Differs from Built-in 2FA

| | Frappe Built-in 2FA | Frappe OTP Login |
|---|---|---|
| **Purpose** | Second factor after password | Password replacement |
| **Password required?** | Yes | No |
| **Flow** | Password → OTP → Login | OTP → Login |
| **OTP types** | TOTP, HOTP (SMS/Email) | Random 6-digit (Email/HTTP) |
| **Channel config** | SMS Settings doctype | Built-in HTTP Channel child table |
| **Login page** | Standard /login with extra step | Custom /otp_login page |
| **User lookup** | Pre-authenticated user | By email, username, or phone |

---

# Frappe Built-in 2FA System (Reference)

This section documents Frappe's built-in 2FA system — useful as reference for understanding the framework's OTP infrastructure and login flow internals.

## Architecture

Frappe ships a built-in 2FA system supporting three methods: **OTP App** (TOTP), **Email**, and **SMS**.

### Source Files

| File | Purpose |
|---|---|
| `frappe/frappe/twofactor.py` | All OTP logic: generation, sending, verification, QR codes |
| `frappe/frappe/auth.py` | `LoginManager` integrates 2FA into the login flow |
| `frappe/frappe/templates/includes/login/login.js` | Frontend OTP form rendering per method |
| `frappe/frappe/core/doctype/sms_settings/sms_settings.py` | Generic HTTP SMS gateway sender |
| `frappe/frappe/core/doctype/system_settings/system_settings.json` | 2FA config fields |
| `frappe/frappe/hooks.py` (line 308) | `otp_methods = ["OTP App", "Email", "SMS"]` |

## End-to-End Login Flow

```
User submits usr + pwd
        │
        ▼
LoginManager.login()  ──►  auth.py
        │
        ▼
should_run_2fa(user) ?
        │
    No ─┴─ Yes
    │       │
    │       ▼
    │   authenticate_for_2factor(user)          twofactor.py:80
    │       │
    │       ├─ get_otpsecret_for_(user)         twofactor.py:133
    │       │     (retrieves or creates HOTP secret, encrypted)
    │       │
    │       ├─ token = TOTP(otp_secret).now()   (current time-based token)
    │       │
    │       ├─ cache_2fa_data(user, token, ...) twofactor.py:94
    │       │     (stores user, pwd, token, secret in Redis with tmp_id)
    │       │
    │       ├─ get_verification_obj(user, ...)  twofactor.py:191
    │       │     ├─ SMS  → process_2fa_for_sms()  → send_token_via_sms()
    │       │     ├─ Email → process_2fa_for_email() → send_token_via_email()
    │       │     └─ OTP App → process_2fa_for_otp_app() (or email QR on first use)
    │       │
    │       └─ sets frappe.local.response["verification"] + "tmp_id"
    │
    ▼
Frontend (login.js:264) reads data.verification.method
        │
        ├─ "SMS"   → continue_sms()   → shows "code sent to +91******789"
        ├─ "Email" → continue_email() → shows "code sent to your email"
        └─ "OTP App" → continue_otp_app() → shows "enter code from app"
        │
        ▼
User enters OTP + tmp_id → POST /api/method/login
        │
        ▼
confirm_otp_token(login_manager, otp, tmp_id)   twofactor.py:149
        │
        ├─ HOTP verify (if cached hotp_token exists — for SMS/Email)
        │     hotp.verify(otp, int(hotp_token))
        │
        └─ TOTP verify (fallback — for OTP App)
              totp.verify(otp)
        │
    Valid ─┴─ Invalid
      │        │
      ▼        ▼
  post_login()   login_manager.fail("Incorrect Verification code")
  (session created)
```

## Token Types

- **HOTP** (counter-based): Used for **SMS** and **Email** delivery. Counter is cached in Redis (`tmp_id + "_token"`). After successful verification, the cached token is deleted to prevent replay.
- **TOTP** (time-based): Used for **OTP App**. Standard 6-digit codes with a 30-second window.

## Configuration

### System Settings Fields

| Field | Type | Purpose |
|---|---|---|
| `enable_two_factor_auth` | Check | Master switch for 2FA |
| `two_factor_method` | Select: OTP App / Email / SMS | Default delivery method |
| `otp_issuer_name` | Data | Name shown in emails and authenticator apps |
| `otp_sms_template` | Small Text | Custom SMS template with `{{otp}}` placeholder |
| `bypass_2fa_for_retricted_ip_users` | Check | Skip 2FA for users with restricted IPs |
| `bypass_restrict_ip_check_if_2fa_enabled` | Check | Bypass IP restriction when 2FA is active |
| `lifespan_qrcode_image` | Int | QR code link expiry in seconds (default: 240) |

### Enabling 2FA for Roles

2FA activates per-role. Enable `two_factor_auth` on the relevant Role(s) — typically the "All" role to apply site-wide.

```bash
bench --site mysite.localhost console
>>> role = frappe.get_doc("Role", "All")
>>> role.two_factor_auth = 1
>>> role.save()
```

Or via the Frappe UI: **Role list → All → Edit → Two Factor Auth = checked**.

### Important: Administrator is exempt

`two_factor_is_enabled_for_()` at `twofactor.py:114` hard-codes `if user == "Administrator": return False`.

## Email OTP

**No external service needed** — uses Frappe's built-in email (`frappe.sendmail()`).

### Setup

1. System Settings → Enable Two Factor Auth = **checked**
2. Two Factor Method = **Email**
3. OTP Issuer Name = your company name
4. Ensure outgoing email is configured (Email Account / SMTP)

### How it works

- `send_token_via_email()` at `twofactor.py:353`
- Generates HOTP code: `pyotp.HOTP(otp_secret).at(int(token))`
- Email subject: `"Login Verification Code from {issuer}"`
- Email body: `"Enter this code to complete your login: **{otp}**"`
- Sent synchronously with `delayed=False`, retries 3 times
- Token cached for **300 seconds** in Redis

## SMS OTP

Requires an SMS gateway configured in **SMS Settings** doctype.

### Setup

1. System Settings → Two Factor Method = **SMS**
2. Go to **SMS Settings** (search in global search)
3. Configure:
   - **SMS Gateway URL**: your provider's API endpoint
   - **Message Parameter**: parameter name for the message body (e.g., `message`, `text`)
   - **Receiver Parameter**: parameter name for recipient number (e.g., `number`, `to`)
   - **Use POST**: check if gateway requires POST
   - **Parameters** (child table): add any extra gateway params (API key, sender ID, etc.)
     - Set `Header = 1` on params that should be sent as HTTP headers (e.g., `Authorization`)
4. Optional: set `otp_sms_template` in System Settings (default: `"Your verification code is {{otp}}"`)
5. Users must have `mobile_no` or `phone` set on their User doc

### How it works

- `send_token_via_sms()` at `twofactor.py:303`
- Checks for custom hook `send_token_via_sms` first, falls back to SMS Settings
- Phone from User doc: `mobile_no` preferred, fallback to `phone`
- SMS sent **asynchronously** via `enqueue()` in the "short" background queue
- Masked phone shown in UI: `+91******789`
- Token cached for **300 seconds**

### Example SMS Settings for common providers

**MSG91:**
- Gateway URL: `https://api.msg91.com/api/v5/flow/`
- Message Parameter: `message`
- Receiver Parameter: `mobile`
- Use POST: checked
- Parameters: `flow_id` = your flow ID, `authkey` header = your API key

**Twilio:**
- Gateway URL: `https://api.twilio.com/2010-04-01/Accounts/{ACCOUNT_SID}/Messages.json`
- Message Parameter: `Body`
- Receiver Parameter: `To`
- Use POST: checked
- Parameters: `From` = your Twilio number, `Authorization` header = `Basic {base64(sid:token)}`

## Custom SMS Provider (Hook)

Override SMS delivery in your custom app without touching core:

```python
# your_app/hooks.py
send_token_via_sms = "your_app.utils.send_custom_sms"
```

```python
# your_app/utils.py
import pyotp

def send_custom_sms(otpsecret, token=None, phone_no=None):
    """Custom SMS handler. Called by frappe.twofactor.send_token_via_sms()."""
    otp = pyotp.HOTP(otpsecret).at(int(token))

    # Your provider API call here
    # e.g., requests.post("https://your-sms-gateway.com/send", json={
    #     "to": phone_no,
    #     "message": f"Your verification code is {otp}"
    # })

    return True  # True = success, False = failure
```

The hook is checked at `twofactor.py:306-308` — if defined, it completely replaces the default SMS Settings logic.

## OTP App (TOTP / Authenticator App)

### Setup

1. System Settings → Two Factor Method = **OTP App**
2. OTP Issuer Name = your company name
3. On first login, Frappe sends an email with a QR code link
4. User scans the QR code with Google Authenticator, Authy, 1Password, etc.
5. Subsequent logins require the 6-digit code from the app

### How it works

- `process_2fa_for_otp_app()` at `twofactor.py:221`
- First login: `process_2fa_for_email()` sends QR code link (TOTP URI) via email
- QR code page hosted at `/qrcode?k={key}`, expires in 240s (configurable)
- TOTP URI format: `otpauth://totp/{issuer}:{user}?secret={secret}&issuer={issuer}`
- Token verified via `pyotp.TOTP(otp_secret).verify(otp)` at `twofactor.py:179`
- Token cached for **180 seconds**

### Resetting a user's OTP secret

```python
# Via whitelisted API
frappe.twofactor.reset_otp_secret("user@example.com")
```

Or via Frappe UI: User profile → Reset OTP Secret. Clears the secret and notifies the user by email. Next login triggers QR code re-registration.

## Security Details

| Feature | Detail |
|---|---|
| Secret storage | Encrypted with `frappe.utils.password.encrypt()`, key = `{user}.otpsecret` |
| Cache expiry | 300s (SMS/Email), 180s (OTP App) |
| Replay prevention | HOTP counter deleted from cache after successful verify |
| Attempt tracking | `get_login_attempt_tracker()` in `auth.py` tracks failures |
| IP bypass | Restricted-IP users can be exempted from 2FA |
| QR code cleanup | Auto-deleted after first successful OTP App login |

## Redis Cache Keys (Built-in 2FA)

All stored under the `tmp_id` (8-char random hash):

| Key | Content | TTL |
|---|---|---|
| `{tmp_id}_token` | HOTP counter (SMS/Email only) | 300s |
| `{tmp_id}_usr` | Username | 300s/180s |
| `{tmp_id}_pwd` | Password | 300s/180s |
| `{tmp_id}_otp_secret` | Decrypted OTP secret | 300s/180s |

## Whitelisted API Methods (Built-in 2FA)

| Method | Description |
|---|---|
| `frappe.twofactor.reset_otp_secret(user: str)` | Reset OTP secret. System Manager can reset any user; regular users can only reset their own. |

## Design History

Originally planned as `frappe_sms` with separate DocTypes for SMS Provider, SMS Template, and SMS Settings. During implementation, the design was simplified to a single **OTP Login Settings** doctype with a generic **OTP HTTP Channel** child table — one channel type that handles Email, SMS, and any HTTP-based OTP delivery in a unified way. The SMS-specific stubs (`sms_provider`, `sms_template`, `sms_settings`) remain in the codebase as placeholders for future DLT-compliant SMS template management.

### From Plan to Implementation

| Plan (`frappe_sms`) | Actual (`frappe_otp_login`) |
|---|---|
| SMS Provider doctype | OTP HTTP Channel (generic) |
| SMS Provider Param | OTP HTTP Channel Parameter |
| SMS Template doctype | `message_template` field on channel |
| SMS Settings (singleton) | OTP Login Settings (singleton) |
| Separate email vs SMS flows | Unified `send_otp()` with channel routing |

## License

GPL-3.0-or-later
