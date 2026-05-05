import frappe


def after_install():
	frappe.db.commit()


def before_uninstall():
	pass
