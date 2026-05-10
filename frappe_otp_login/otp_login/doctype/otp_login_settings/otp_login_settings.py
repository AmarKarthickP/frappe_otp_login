import frappe
from frappe.model.document import Document

PREFIX = "otp_"
STANDARD_USER_FIELDS = {"email", "username", "phone", "mobile_no", "first_name", "last_name", "full_name", "name"}


def _is_standard(fieldname: str) -> bool:
	return fieldname in STANDARD_USER_FIELDS


def _prefixed(fieldname: str) -> str:
	"""Add prefix only for custom fields, leave standard fields as-is."""
	if _is_standard(fieldname):
		return fieldname
	if fieldname.startswith(PREFIX):
		return fieldname
	return PREFIX + fieldname


class OTPLoginSettings(Document):
	def validate(self):
		self.ensure_user_fields_exist()
		self.cleanup_orphaned_user_fields()

	def ensure_user_fields_exist(self):
		for channel in self.http_channels:
			fieldname = channel.user_field
			if not fieldname:
				continue
			if _is_standard(fieldname):
				continue
			pf = _prefixed(fieldname)
			if frappe.db.exists("Custom Field", {"dt": "User", "fieldname": pf}):
				continue
			_create_user_field(pf)
			frappe.msgprint(
				frappe._("Added field '{0}' to User for channel '{1}'").format(pf, channel.channel_name),
				alert=True,
			)

	def cleanup_orphaned_user_fields(self):
		active_prefixed = {_prefixed(c.user_field) for c in self.http_channels if c.user_field}
		custom_fields = frappe.get_all(
			"Custom Field",
			filters={"dt": "User", "fieldname": ("like", PREFIX + "%")},
			fields=["fieldname"],
		)
		for cf in custom_fields:
			fn = cf.fieldname
			if fn not in active_prefixed:
				_delete_user_field(fn)
				frappe.msgprint(
					frappe._("Removed field '{0}' from User").format(fn),
					alert=True,
				)

	@frappe.whitelist()
	def fetch_smtp_settings(self):
		if default := frappe.db.get_value(
			"Email Account",
			{"default_outgoing": 1, "enable_outgoing": 1},
			["name", "smtp_server", "smtp_port", "email_id"],
		):
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
		settings = frappe.get_single("OTP Login Settings")
		if not settings.enabled:
			return []
		return [c for c in settings.http_channels if c.enabled]


def _create_user_field(fieldname):
	frappe.get_doc({
		"doctype": "Custom Field",
		"dt": "User",
		"fieldname": fieldname,
		"label": fieldname.replace("_", " ").title(),
		"fieldtype": "Data",
		"unique": 1,
		"insert_after": "mobile_no",
		"translatable": 0,
	}).insert(ignore_permissions=True)


def _delete_user_field(fieldname):
	frappe.db.delete("Custom Field", {"dt": "User", "fieldname": fieldname})
