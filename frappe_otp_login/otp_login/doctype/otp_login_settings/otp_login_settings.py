import frappe
from frappe.model.document import Document


class OTPLoginSettings(Document):
	def validate(self):
		self.ensure_user_fields_exist()
		self.cleanup_orphaned_user_fields()

	def ensure_user_fields_exist(self):
		"""Create custom fields on User doctype for any channel's user_field."""
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

	def cleanup_orphaned_user_fields(self):
		"""Remove custom User fields that are no longer referenced by any channel.
		Also removes fields from old channel edits (when user_field is changed)."""
		# Collect all currently-referenced user_fields
		active_fields = {c.user_field for c in self.http_channels if c.user_field}

		# Find all non-standard custom fields on User
		custom_fields = frappe.get_all(
			"Custom Field",
			filters={"dt": "User"},
			fields=["fieldname"],
		)

		for cf in custom_fields:
			fn = cf.fieldname
			if _is_standard_user_field(fn):
				continue
			if fn not in active_fields:
				_delete_user_field(fn)
				frappe.msgprint(
					frappe._("Removed field '{0}' from User doctype").format(fn),
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
	"""Return True if fieldname is a built-in User field (not a custom one we created)."""
	# Built-in fields are in the JSON schema, custom fields are in tabCustom Field
	return not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": fieldname})


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
	_add_field_to_form_layout(fieldname)


def _add_field_to_form_layout(fieldname):
	"""Ensure the custom field appears on the User form."""
	try:
		if frappe.db.exists("Customize Form", {"doc_type": "User"}):
			cf = frappe.get_doc("Customize Form", {"doc_type": "User"})
		else:
			cf = frappe.new_doc("Customize Form")
			cf.doc_type = "User"
		already = any(f.fieldname == fieldname for f in cf.fields)
		if not already:
			cf.append("fields", {"fieldname": fieldname})
			cf.save(ignore_permissions=True)
			frappe.db.commit()
	except Exception:
		pass  # Customize Form table may not exist; field is still usable via API


def _delete_user_field(fieldname):
	frappe.db.delete("Custom Field", {"dt": "User", "fieldname": fieldname})
	_remove_field_from_form_layout(fieldname)


def _remove_field_from_form_layout(fieldname):
	try:
		if frappe.db.exists("Customize Form", {"doc_type": "User"}):
			cf = frappe.get_doc("Customize Form", {"doc_type": "User"})
			cf.fields = [f for f in cf.fields if f.fieldname != fieldname]
			cf.save(ignore_permissions=True)
			frappe.db.commit()
	except Exception:
		pass
