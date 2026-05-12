import frappe
from frappe import _

from frappe_otp_login.utils import (
	check_failure_count,
	check_rate_limit,
	delete_stored_otp,
	find_user_by_identifier,
	generate_otp,
	get_stored_otp,
	get_stored_user,
	send_otp_email,
	send_otp_http,
	store_otp,
)


def has_app_permission():
	"""Permission check for desk icon visibility — System Manager only."""
	return "System Manager" in frappe.get_roles()


def _get_or_create_api_keys(user: str):
	"""Return existing API key/secret for user, or generate a new pair."""
	api_key = frappe.db.get_value("User", user, "api_key")
	api_secret = frappe.get_cached_value("User", user, "api_secret")
	if api_key and api_secret:
		return api_key, api_secret
	from frappe.core.doctype.user.user import generate_keys
	generate_keys(user)
	frappe.db.commit()
	api_key = frappe.db.get_value("User", user, "api_key")
	api_secret = frappe.db.get_value("User", user, "api_secret")
	return api_key, api_secret


@frappe.whitelist(allow_guest=True)
def get_available_channels():
	"""Return list of enabled OTP channels for the login page."""
	from frappe_otp_login.otp_login.doctype.otp_login_settings.otp_login_settings import (
		OTPLoginSettings,
	)

	settings = frappe.get_single("OTP Login Settings")
	if not settings.enabled:
		return {"channels": [], "resend_cooldown": 30}

	channels = []
	resend_cooldown = settings.get("resend_cooldown") or 30

	if settings.email_enabled:
		channels.append({
			"type": "email",
			"name": "Email",
			"label": "Email",
			"identifier_label": "Email Address",
			"user_field": settings.email_search_field or "email",
		})

	for c in settings.http_channels:
		if c.enabled:
			channels.append({
				"type": "http",
				"name": c.channel_name,
				"label": c.channel_name,
				"identifier_label": c.identifier_label or "Identifier",
				"user_field": c.user_field or "email",
			})

	return {"channels": channels, "resend_cooldown": resend_cooldown}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def send_otp(identifier: str, channel: str | None = None) -> dict:
	identifier = identifier.strip().lower()

	if not check_rate_limit(identifier):
		frappe.throw(_("Too many OTP requests. Please try again after 15 minutes."))

	settings = frappe.get_single("OTP Login Settings")

	# Determine which User field to match against
	from frappe_otp_login.otp_login.doctype.otp_login_settings.otp_login_settings import _prefixed

	user_field = None
	if channel and channel != "Email":
		for c in settings.http_channels:
			if c.channel_name == channel:
				user_field = _prefixed(c.user_field or "email")
				break
	elif channel == "Email" or (not channel and settings.email_enabled):
		user_field = settings.email_search_field or "email"

	user = find_user_by_identifier(identifier, user_field)
	if not user:
		return {"message": "OTP sent"}

	otp = generate_otp()
	store_otp(identifier, otp, user)

	sent = False

	if channel == "Email" or (not channel and settings.email_enabled):
		user_email = frappe.db.get_value("User", user, "email")
		if user_email:
			try:
				send_otp_email(user_email, otp)
				sent = True
			except Exception:
				frappe.log_error(title="OTP Login: Email send failed", message=frappe.get_traceback())

	if channel and channel != "Email":
		try:
			send_otp_http(identifier, otp, channel_name=channel)
			sent = True
		except Exception:
			frappe.log_error(title="OTP Login: HTTP send failed", message=frappe.get_traceback())
	elif not channel:
		try:
			send_otp_http(identifier, otp)
		except Exception:
			pass  # already logged in send_otp_http

	if not sent:
		frappe.throw(_("No OTP channel is enabled. Please contact the administrator."))

	return {"message": "OTP sent", "identifier": identifier}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def send_otp_via_channel(channel: str, identifier: str) -> dict:
	"""Send OTP via a specific channel. Channel name in the path."""
	return send_otp(identifier=identifier, channel=channel)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def verify_otp(identifier: str, otp: str) -> dict:
	identifier = identifier.strip().lower()
	otp = otp.strip()

	stored_otp = get_stored_otp(identifier)
	if not stored_otp:
		frappe.throw(_("OTP has expired. Please request a new one."))

	if not check_failure_count(identifier):
		delete_stored_otp(identifier)
		frappe.throw(_("Too many failed attempts. Please request a new OTP."))

	if stored_otp != otp:
		frappe.throw(_("Invalid OTP. Please try again."))

	user = get_stored_user(identifier)
	delete_stored_otp(identifier)

	if not user:
		frappe.throw(_("User not found."))

	from frappe.auth import LoginManager

	frappe.local.login_manager = LoginManager()
	frappe.local.login_manager.login_as(user)

	# Generate API key/secret for token-based auth
	api_key, api_secret = _get_or_create_api_keys(user)

	return {
		"message": "Logged In",
		"redirect_to": "/desk",
		"api_key": api_key,
		"api_secret": api_secret,
		"token": f"token {api_key}:{api_secret}",
	}
