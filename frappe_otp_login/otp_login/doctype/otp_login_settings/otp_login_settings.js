frappe.ui.form.on("OTP Login Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Fetch SMTP Settings"), () => {
			frm.call("fetch_smtp_settings").then(() => {
				frm.refresh();
				frappe.show_alert({ message: __("SMTP settings updated"), indicator: "green" });
			});
		});

		// Show/hide HTTP channels based on default_channel
		frm.set_query("http_channels", "http_channels", () => {
			return {};
		});
	},

	default_channel(frm) {
		frm.toggle_display("http_channels_section", frm.doc.default_channel === "HTTP");
		frm.toggle_display("http_channels", frm.doc.default_channel === "HTTP");
	},
});
