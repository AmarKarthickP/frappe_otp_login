import frappe


def after_install():
	"""Create OTP Login Settings singleton with preset HTTP channels."""
	if not frappe.db.exists("OTP Login Settings", "OTP Login Settings"):
		settings = frappe.new_doc("OTP Login Settings")
		settings.enabled = 1
		settings.default_channel = "Email"

		# Preset: ntfy.sh
		ntfy = settings.append("http_channels")
		ntfy.channel_name = "ntfy.sh"
		ntfy.enabled = 0
		ntfy.method = "POST"
		ntfy.url = "https://ntfy.sh/your-topic"
		ntfy.auth_type = "None"
		ntfy.content_type = "Raw (text/plain)"
		ntfy.message_template = "Your OTP code is {{ otp }}"

		# Preset: Generic Indian SMS Provider (GET)
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
		for param in [
			("authkey", "YOUR_AUTH_KEY"),
			("sender", "SENDERID"),
			("route", "Transactional"),
			("country", "91"),
			("DLT_TE_ID", "YOUR_DLT_ID"),
		]:
			p = sms.append("parameters")
			p.key = param[0]
			p.value = param[1]
			p.is_header = 0

		settings.insert(ignore_permissions=True)
		frappe.db.commit()


def before_uninstall():
	pass
