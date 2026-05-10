import frappe
from frappe.model.document import Document


class OTPLoginSettings(Document):
	def validate(self):
		self.ensure_user_fields_exist()

	def ensure_user_fields_exist(self):
		"""Create custom fields on User doctype for any channel's user_field
		that doesn't already exist as a User field."""
		for channel in self.http_channels:
			fieldname = channel.user_field
			if not fieldname:
				continue
			# Skip standard fields
			if fieldname in ("email", "username", "phone", "mobile_no",
				"first_name", "last_name", "full_name", "name"):
				continue
			if frappe.db.exists("Custom Field", {"dt": "User", "fieldname": fieldname}):
				continue
			# Check if field already exists as a standard field
			meta = frappe.get_meta("User")
			if meta.get_field(fieldname):
				continue
			# Create the custom field
			frappe.get_doc({
				"doctype": "Custom Field",
				"dt": "User",
				"fieldname": fieldname,
				"label": fieldname.replace("_", " ").title(),
				"fieldtype": "Data",
				"insert_after": "mobile_no",
				"translatable": 0,
				"owner": "Administrator",
			}).insert(ignore_permissions=True)
			frappe.msgprint(
				frappe._("Added field '{0}' to User doctype for channel '{1}'").format(
					fieldname, channel.channel_name
				),
				alert=True,
			)

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
