// OTP Login: Rename "Login with Email Link" → "Login with OTP"
(function() {
	function rename_button() {
		var link = document.querySelector('.btn-login-with-email-link');
		if (link) {
			link.textContent = 'Login with OTP';
		}
	}
	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', rename_button);
	} else {
		rename_button();
	}
	// Also try after a short delay in case it renders late
	setTimeout(rename_button, 500);
})();
