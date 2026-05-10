// OTP Login: Replace "Login with Email Link" button with link to /otp_login
(function() {
	function replace_button() {
		var wrapper = document.querySelector('.login-with-email-link');
		if (!wrapper) return;

		// Replace the entire button with our own that links to /otp_login
		wrapper.innerHTML = '<div class="login-button-wrapper">'
			+ '<a href="/otp_login" class="btn btn-block btn-default btn-sm btn-login-option">'
			+ 'Login with OTP</a></div>';

		// Hide the Frappe email-link section
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
