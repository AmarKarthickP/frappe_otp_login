// OTP Login: Replace "Login with Email Link" button with our OTP login
(function() {
	function replace_button() {
		var link = document.querySelector('.btn-login-with-email-link');
		if (!link) return;

		link.textContent = 'Login with OTP';
		link.href = '/otp_login';
		link.removeAttribute('href');  // remove #hash to prevent Frappe's email-link handler
		link.setAttribute('onclick', 'window.location.href=\"/otp_login\"; return false;');

		// Also hide the Frappe email-link section since we're replacing it
		var section = document.querySelector('.for-login-with-email-link');
		if (section) section.style.display = 'none';
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', replace_button);
	} else {
		replace_button();
	}
	setTimeout(replace_button, 500);
})();
