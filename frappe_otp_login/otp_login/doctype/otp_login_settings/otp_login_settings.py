import frappe
from frappe.model.document import Document


class OTPLoginSettings(Document):
	def validate(self):
		pass

	@frappe.whitelist()
	def fetch_smtp_settings(self):
		"""Fetch SMTP settings from the default outgoing Email Account."""
		default = frappe.db.get_value(
			"Email Account",
			{"default_outgoing": 1, "enable_outgoing": 1},
			["name", "smtp_server", "smtp_port", "email_id"],
		)
		if default:
			self.email_status = "Configured"
			self.smtp_server = default[1] or "Not set"
			self.smtp_port = str(default[2]) if default[2] else "Not set"
			self.smtp_sender = default[3] or "Not set"
		else:
			self.email_status = "Not configured"
			self.smtp_server = "N/A"
			self.smtp_port = "N/A"
			self.smtp_sender = "N/A"

	@staticmethod
	def get_enabled_channels():
		"""Return list of enabled HTTP channels for API use."""
		settings = frappe.get_single("OTP Login Settings")
		if not settings.enabled:
			return []
		return [c for c in settings.http_channels if c.enabled]


def has_otp_settings_permission():
	"""Permission check for the desk icon — System Manager only."""
	return "System Manager" in frappe.get_roles()
