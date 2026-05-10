import frappe
from frappe.model.document import Document


class OTPLoginSettings(Document):
	def validate(self):
		self.ensure_user_fields_exist()
		self.cleanup_deleted_channel_fields()

	def ensure_user_fields_exist(self):
		"""Create custom fields on User doctype for any channel's user_field
		that doesn't already exist as a User field."""
		for channel in self.http_channels:
			fieldname = channel.user_field
			if not fieldname:
				continue
			if _is_standard_user_field(fieldname):
				continue
			if frappe.db.exists("Custom Field", {"dt": "User", "fieldname": fieldname}):
				continue
			_create_user_field(fieldname)
			frappe.msgprint(
				frappe._("Added field '{0}' to User doctype for channel '{1}'").format(
					fieldname, channel.channel_name
				),
				alert=True,
			)

	def cleanup_deleted_channel_fields(self):
		"""Remove custom User fields for channels that were deleted."""
		if not self.is_new():
			old_doc = self.get_doc_before_save()
			if not old_doc:
				return
			old_fields = {c.user_field for c in old_doc.http_channels if c.user_field}
		else:
			old_fields = set()

		new_fields = {c.user_field for c in self.http_channels if c.user_field}

		removed = old_fields - new_fields
		for fieldname in removed:
			if _is_standard_user_field(fieldname):
				continue
			# Only delete if no other channel still uses this field
			if fieldname in new_fields:
				continue
			_delete_user_field(fieldname)
			frappe.msgprint(
				frappe._("Removed field '{0}' from User doctype").format(fieldname),
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


def _is_standard_user_field(fieldname):
	"""Standard User fields should not be deleted."""
	standard = frappe.get_meta("User").get_field(fieldname)
	return bool(standard)


def _create_user_field(fieldname):
	frappe.get_doc({
		"doctype": "Custom Field",
		"dt": "User",
		"fieldname": fieldname,
		"label": fieldname.replace("_", " ").title(),
		"fieldtype": "Data",
		"insert_after": "mobile_no",
		"translatable": 0,
	}).insert(ignore_permissions=True)


def _delete_user_field(fieldname):
	frappe.db.delete("Custom Field", {"dt": "User", "fieldname": fieldname})
