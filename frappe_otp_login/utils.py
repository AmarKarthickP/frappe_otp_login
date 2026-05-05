import random

import frappe
from frappe import _


def generate_otp() -> str:
	return str(random.randint(100000, 999999))


def store_otp(identifier: str, otp: str, expiry: int = 300) -> None:
	frappe.cache.set(f"otp_login:{identifier}", otp, expires_in_sec=expiry)


def get_stored_otp(identifier: str) -> str | None:
	return frappe.cache.get(f"otp_login:{identifier}")


def delete_stored_otp(identifier: str) -> None:
	frappe.cache.delete(f"otp_login:{identifier}")


def check_rate_limit(identifier: str) -> bool:
	key = f"otp_login_rate:{identifier}"
	count = frappe.cache.incrby(key, 1)
	if count == 1:
		frappe.cache.expire(key, 900)
	return count <= 5


def check_failure_count(identifier: str) -> bool:
	key = f"otp_login_fail:{identifier}"
	count = frappe.cache.incrby(key, 1)
	if count == 1:
		frappe.cache.expire(key, 300)
	return count <= 5


def find_user_by_identifier(identifier: str) -> str | None:
	identifier = identifier.strip().lower()

	user = frappe.db.get_value("User", {"email": identifier}, "name")
	if user:
		return user

	user = frappe.db.get_value("User", {"username": identifier}, "name")
	if user:
		return user

	user = frappe.db.get_value("User", {"phone": identifier}, "name")
	if user:
		return user

	user = frappe.db.get_value("User", {"mobile_no": identifier}, "name")
	if user:
		return user

	return None


def send_otp_email(email: str, otp: str) -> None:
	site_name = (
		frappe.get_website_settings("app_name")
		or frappe.get_system_settings("app_name")
		or _("Frappe")
	)
	subject = _("Login Verification Code from {0}").format(site_name)

	frappe.sendmail(
		subject=subject,
		recipients=email,
		template="otp_login_code",
		args={"otp": otp, "site_name": site_name},
		now=True,
	)
