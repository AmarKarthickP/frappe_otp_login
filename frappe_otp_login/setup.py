import frappe


def after_install():
	"""Create OTP Login Settings singleton if it doesn't exist."""
	if not frappe.db.exists("OTP Login Settings", "OTP Login Settings"):
		settings = frappe.new_doc("OTP Login Settings")
		settings.enabled = 1
		settings.email_enabled = 1
		settings.insert(ignore_permissions=True)
		frappe.db.commit()


def before_uninstall():
	"""Cleanup before bench uninstall-app removes the app.

	Frappe automatically drops all doctype tables and removes Module Def
	records. We only need to handle things the framework doesn't know about.
	"""
	clear_otp_redis_keys()
	delete_desktop_icon()


def clear_otp_redis_keys():
	"""Remove OTP codes, rate-limit counters, and failure counters from Redis.

	Uses raw Redis SCAN to find keys with the site-prefixed otp_login pattern.
	Safe to call even if Redis is empty — SCAN returns nothing.

	Note: frappe.cache.delete_value() doesn't support wildcards. We use the
	raw redis-py client for pattern-based deletion.
	"""
	try:
		prefix = frappe.cache.make_key("otp_login")
		cursor = 0
		deleted = 0
		while True:
			cursor, keys = frappe.cache.scan(cursor, match=f"{prefix}*", count=100)
			if keys:
				frappe.cache.delete(*keys)
				deleted += len(keys)
			if cursor == 0:
				break
		if deleted:
			print(f"Cleared {deleted} OTP Redis keys")
	except Exception:
		# Redis might not be available during uninstall — non-fatal
		pass


def delete_desktop_icon():
	"""Remove the Desktop Icon that may have been created for this app.

	Frappe *usually* handles this automatically during uninstall, but if the
	icon was created manually or the auto-cleanup path is missed, this ensures
	it's gone.
	"""
	try:
		frappe.db.delete("Desktop Icon", {"app": "frappe_otp_login"})
		frappe.db.commit()
	except Exception:
		pass
