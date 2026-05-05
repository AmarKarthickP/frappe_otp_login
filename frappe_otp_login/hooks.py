app_name = "frappe_otp_login"
app_title = "Frappe OTP Login"
app_publisher = "Clearent"
app_description = "Passwordless OTP login via email and SMS"
app_email = "dev@clearent.in"
app_license = "GPL-3.0-or-later"

after_install = "frappe_otp_login.setup.after_install"
before_uninstall = "frappe_otp_login.setup.before_uninstall"
