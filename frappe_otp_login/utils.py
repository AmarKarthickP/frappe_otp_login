import random

import frappe
from frappe import _


def generate_otp() -> str:
	return str(random.randint(100000, 999999))


def store_otp(identifier: str, otp: str, expiry: int = 300) -> None:
	frappe.cache.set_value(f"otp_login:{identifier}", otp, expires_in_sec=expiry)


def get_stored_otp(identifier: str) -> str | None:
	return frappe.cache.get_value(f"otp_login:{identifier}")


def delete_stored_otp(identifier: str) -> None:
	frappe.cache.delete_value(f"otp_login:{identifier}")


def check_rate_limit(identifier: str) -> bool:
	key = frappe.cache.make_key(f"otp_login_rate:{identifier}")
	count = frappe.cache.incrby(key, 1)
	if count == 1:
		frappe.cache.expire(key, 900)
	return count <= 5


def check_failure_count(identifier: str) -> bool:
	key = frappe.cache.make_key(f"otp_login_fail:{identifier}")
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


def send_otp_http(identifier: str, otp: str) -> None:
	"""Send OTP to all enabled HTTP channels."""
	from frappe_otp_login.otp_login.doctype.otp_login_settings.otp_login_settings import (
		OTPLoginSettings,
	)

	channels = OTPLoginSettings.get_enabled_channels()
	if not channels:
		frappe.throw(_("No HTTP channels are enabled in OTP Login Settings."))

	for channel in channels:
		try:
			send_http_request(channel, identifier, otp)
		except Exception:
			frappe.log_error(
				title=f"OTP Login: HTTP channel '{channel.channel_name}' failed",
				message=frappe.get_traceback(),
			)


def send_http_request(channel, identifier: str, otp: str) -> None:
	"""Send a single HTTP request for a channel using the requests library."""
	import requests

	site_name = (
		frappe.get_website_settings("app_name")
		or frappe.get_system_settings("app_name")
		or _("Frappe")
	)

	# Render message template
	template = channel.message_template or "Your OTP is {{ otp }}"
	try:
		body = frappe.render_template(template, {"otp": otp, "recipient": identifier, "site_name": site_name})
	except Exception:
		body = template.replace("{{ otp }}", otp).replace("{{ recipient }}", identifier).replace("{{ site_name }}", site_name)

	# Build headers
	headers = {}
	for p in channel.parameters:
		if p.is_header:
			headers[p.key] = p.value

	# Auth headers
	if channel.auth_type == "Bearer":
		headers["Authorization"] = f"Bearer {channel.get_password('auth_token') or ''}"
	elif channel.auth_type == "API Key":
		headers["X-API-Key"] = channel.get_password("auth_token") or ""
	elif channel.auth_type == "Basic":
		import base64
		user = channel.auth_username or ""
		pwd = channel.get_password("auth_password") or ""
		headers["Authorization"] = f"Basic {base64.b64encode(f'{user}:{pwd}'.encode()).decode()}"

	# Build query/body params
	params = {}
	if channel.method == "GET":
		params[channel.otp_param or "otp"] = otp
		params[channel.recipient_param or "recipient"] = identifier
		for p in channel.parameters:
			if not p.is_header:
				params[p.key] = p.value

		resp = requests.get(channel.url, params=params, headers=headers, timeout=10)
		resp.raise_for_status()

	elif channel.method == "POST":
		content_type = channel.content_type or "application/json"

		if content_type == "Raw (text/plain)":
			headers.setdefault("Content-Type", "text/plain")
			resp = requests.post(channel.url, data=body.encode("utf-8"), headers=headers, timeout=10)

		elif content_type == "application/x-www-form-urlencoded":
			headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
			form_data = {}
			form_data[channel.otp_param or "otp"] = otp
			form_data[channel.recipient_param or "recipient"] = identifier
			for p in channel.parameters:
				if not p.is_header:
					form_data[p.key] = p.value
			resp = requests.post(channel.url, data=form_data, headers=headers, timeout=10)

		else:  # application/json
			headers.setdefault("Content-Type", "application/json")
			json_data = {}
			json_data[channel.otp_param or "otp"] = otp
			json_data[channel.recipient_param or "recipient"] = identifier
			for p in channel.parameters:
				if not p.is_header:
					json_data[p.key] = p.value
			# If there's a message_template, use it as an additional field or override
			if channel.message_template:
				# If only template is set (no otp_param), use template as raw body
				if not channel.otp_param and not channel.recipient_param:
					headers["Content-Type"] = "text/plain"
					resp = requests.post(channel.url, data=body.encode("utf-8"), headers=headers, timeout=10)
				else:
					json_data["message"] = body
					resp = requests.post(channel.url, json=json_data, headers=headers, timeout=10)
			else:
				resp = requests.post(channel.url, json=json_data, headers=headers, timeout=10)

		resp.raise_for_status()
