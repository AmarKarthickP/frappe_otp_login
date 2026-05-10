// OTP Login: Rename "Login with Email Link" → "Login with OTP"
frappe.ready(() => {
	const link = document.querySelector('.btn-login-with-email-link');
	if (link) {
		link.textContent = 'Login with OTP';
	}
});
