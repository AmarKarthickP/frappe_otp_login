import frappe


def after_install():
	"""Create OTP Login Settings singleton if it doesn't exist."""
	if not frappe.db.exists("OTP Login Settings", "OTP Login Settings"):
		settings = frappe.new_doc("OTP Login Settings")
		settings.enabled = 1
		settings.default_channel = "Email"
		settings.insert(ignore_permissions=True)
		frappe.db.commit()


def before_uninstall():
	pass
