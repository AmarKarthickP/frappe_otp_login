app_name = "frappe_otp_login"
app_title = "OTP Login"
app_publisher = "Clearent"
app_description = "Passwordless OTP login via email and HTTP"
app_email = "dev@clearent.in"
app_license = "GPL-3.0-or-later"

after_install = "frappe_otp_login.setup.after_install"
before_uninstall = "frappe_otp_login.setup.before_uninstall"

web_include_js = ["/assets/frappe_otp_login/js/login_button.js"]

add_to_apps_screen = [
	{
		"name": "otp_login",
		"logo": "/assets/frappe_otp_login/images/logo.svg",
		"title": "OTP Login",
		"route": "/app/otp-login-settings",
		"has_permission": "frappe_otp_login.api.has_app_permission"
	}
]
