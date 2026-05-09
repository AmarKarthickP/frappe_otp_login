import frappe


def execute():
	"""Create preset HTTP channels if none exist."""
	settings = frappe.get_single("OTP Login Settings")

	if settings.http_channels:
		return

	# ntfy.sh — Raw text POST
	ntfy = settings.append("http_channels")
	ntfy.channel_name = "ntfy.sh"
	ntfy.enabled = 0
	ntfy.method = "POST"
	ntfy.url = "https://ntfy.sh/your-topic"
	ntfy.auth_type = "None"
	ntfy.content_type = "Raw (text/plain)"
	ntfy.message_template = "Your OTP code is {{ otp }}"

	# Generic Indian SMS Provider — GET with query params
	sms = settings.append("http_channels")
	sms.channel_name = "Generic Indian SMS Provider"
	sms.enabled = 0
	sms.method = "GET"
	sms.url = "https://api.example.com/sendotp"
	sms.auth_type = "None"
	sms.content_type = "application/x-www-form-urlencoded"
	sms.recipient_param = "mobiles"
	sms.otp_param = "message"
	sms.message_template = "{{ otp }} is your OTP for {{ site_name }}"

	sms_params = [
		("authkey", "YOUR_AUTH_KEY"),
		("sender", "SENDERID"),
		("route", "Transactional"),
		("country", "91"),
		("DLT_TE_ID", "YOUR_DLT_ID"),
	]
	for key, val in sms_params:
		p = sms.append("parameters")
		p.key = key
		p.value = val
		p.is_header = 0

	settings.save()
	frappe.db.commit()
