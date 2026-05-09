import frappe
from frappe import _

from frappe_otp_login.utils import (


def has_app_permission():
	"""Permission check for desk icon visibility — System Manager only."""
	return "System Manager" in frappe.get_roles()

	check_failure_count,
	check_rate_limit,
	delete_stored_otp,
	find_user_by_identifier,
	generate_otp,
	get_stored_otp,
	send_otp_email,
	send_otp_http,
	store_otp,
)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def send_otp(identifier: str) -> dict:
	identifier = identifier.strip().lower()

	if not check_rate_limit(identifier):
		frappe.throw(_("Too many OTP requests. Please try again after 15 minutes."))

	user = find_user_by_identifier(identifier)
	if not user:
		return {"message": "OTP sent"}

	otp = generate_otp()
	store_otp(identifier, otp)

	channel = frappe.db.get_single_value("OTP Login Settings", "default_channel") or "Email"

	if channel == "HTTP":
		try:
			send_otp_http(identifier, otp)
		except Exception:
			frappe.log_error(title="OTP Login: HTTP send failed", message=frappe.get_traceback())
			frappe.throw(_("Failed to send OTP. Please try again."))
	else:
		user_email = frappe.db.get_value("User", user, "email")
		if not user_email:
			frappe.throw(_("User has no email address configured."))

		try:
			send_otp_email(user_email, otp)
		except Exception:
			frappe.log_error(title="OTP Login: Failed to send email", message=frappe.get_traceback())
			frappe.throw(_("Failed to send OTP email. Please try again."))

	return {"message": "OTP sent", "identifier": identifier}


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

	delete_stored_otp(identifier)

	user = find_user_by_identifier(identifier)
	if not user:
		frappe.throw(_("User not found."))

	from frappe.auth import LoginManager

	frappe.local.login_manager = LoginManager()
	frappe.local.login_manager.login_as(user)

	return {"message": "Logged In", "redirect_to": "/desk"}
