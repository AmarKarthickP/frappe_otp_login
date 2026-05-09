// OTP Login: Rename "Login with Email Link" → "Login with OTP"
frappe.ready(() => {
	const el = document.querySelector('.login-with-email-link');
	if (el) {
		const heading = el.querySelector('h6');
		if (heading) heading.textContent = 'Login with OTP';
		const link = el.querySelector('a');
		if (link) link.textContent = 'Login with OTP';
	}
});
