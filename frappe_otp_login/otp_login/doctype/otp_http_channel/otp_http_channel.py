import frappe
from frappe import _
from frappe.model.document import Document


class OTPHTTPChannel(Document):
	def validate(self):
		self.validate_url()

	def validate_url(self):
		if not self.url:
			return
		url = self.url.strip()
		if not url.startswith(("http://", "https://")):
			frappe.throw(_("URL must start with http:// or https://"))
		if len(url) < 10:
			frappe.throw(_("URL is too short to be valid"))
		if " " in url:
			frappe.throw(_("URL must not contain spaces"))
