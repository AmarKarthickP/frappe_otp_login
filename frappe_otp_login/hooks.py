app_name = "frappe_otp_login"
app_title = "Frappe OTP Login"
app_publisher = "Clearent"
app_description = "Passwordless OTP login via email and HTTP"
app_email = "dev@clearent.in"
app_license = "GPL-3.0-or-later"

after_install = "frappe_otp_login.setup.after_install"
before_uninstall = "frappe_otp_login.setup.before_uninstall"

add_to_apps_screen = [
	{
		"name": "otp_login",
		"logo": "",
		"title": "OTP Login",
		"route": "/app/otp-login-settings",
		"has_permission": "frappe_otp_login.otp_login.doctype.otp_login_settings.otp_login_settings.has_otp_settings_permission"
	}
]
