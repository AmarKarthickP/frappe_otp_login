frappe.ui.form.on("OTP Login Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Fetch SMTP Settings"), () => {
			frm.call("fetch_smtp_settings").then(() => {
				frm.refresh();
				frappe.show_alert({ message: __("SMTP settings updated"), indicator: "green" });
			});
		});

		// Replace default Add Row with custom modal
		frm.fields_dict.http_channels.grid.wrapper.find(".grid-add-row").hide();
		frm.add_custom_button(__("Add HTTP Channel"), () => open_channel_dialog(frm), __("HTTP Channels"));
	},

	email_enabled(frm) {
		frm.toggle_display("email_section", frm.doc.email_enabled);
	},
});

function open_channel_dialog(frm, existing_row) {
	let is_edit = !!existing_row;
	let row_data = existing_row ? frappe.model.copy_doc(existing_row) : {};

	let fields = [
		{ fieldtype: "Section Break", label: __("Channel") },
		{ fieldtype: "Data", fieldname: "channel_name", label: __("Channel Name"), reqd: 1 },
		{ fieldtype: "Check", fieldname: "enabled", label: __("Enabled") },
		{ fieldtype: "Data", fieldname: "identifier_label", label: __("Identifier Label") },
		{ fieldtype: "Section Break", label: __("Request") },
		{ fieldtype: "Select", fieldname: "method", label: __("Method"), options: "GET\nPOST", reqd: 1 },
		{ fieldtype: "Data", fieldname: "url", label: __("URL"), reqd: 1 },
		{ fieldtype: "Column Break" },
		{ fieldtype: "Select", fieldname: "content_type", label: __("Content Type"),
			options: "application/json\napplication/x-www-form-urlencoded\nRaw (text/plain)" },
		{ fieldtype: "Data", fieldname: "otp_param", label: __("OTP Parameter Name"),
			depends_on: "eval:doc.method=='POST'" },
		{ fieldtype: "Data", fieldname: "recipient_param", label: __("Recipient Parameter Name"),
			depends_on: "eval:doc.method=='POST'" },
		{ fieldtype: "Small Text", fieldname: "message_template", label: __("Message Template") },
		{ fieldtype: "Section Break", label: __("Authentication") },
		{ fieldtype: "Select", fieldname: "auth_type", label: __("Auth Type"),
			options: "None\nBearer\nBasic\nAPI Key" },
		{ fieldtype: "Column Break" },
		{ fieldtype: "Password", fieldname: "auth_token", label: __("Token / API Key"),
			depends_on: "eval:['Bearer','API Key'].includes(doc.auth_type)" },
		{ fieldtype: "Data", fieldname: "auth_username", label: __("Username"),
			depends_on: "eval:doc.auth_type=='Basic'" },
		{ fieldtype: "Password", fieldname: "auth_password", label: __("Password"),
			depends_on: "eval:doc.auth_type=='Basic'" },
		{ fieldtype: "Section Break", label: __("Extra Parameters") },
		{ fieldtype: "Table", fieldname: "parameters", label: __("Parameters"),
			options: "OTP HTTP Channel Parameter",
			fields: [
				{ fieldtype: "Data", fieldname: "key", label: __("Key"), in_list_view: 1, reqd: 1 },
				{ fieldtype: "Data", fieldname: "value", label: __("Value"), in_list_view: 1, reqd: 1 },
				{ fieldtype: "Check", fieldname: "is_header", label: __("Is Header"), in_list_view: 1 },
			],
			data: row_data.parameters || [] },
	];

	let d = new frappe.ui.Dialog({
		title: is_edit ? __("Edit HTTP Channel") : __("Add HTTP Channel"),
		fields: fields,
		size: "large",
		primary_action_label: is_edit ? __("Update") : __("Add"),
		primary_action(values) {
			if (is_edit) {
				// Update existing row
				Object.assign(existing_row, values);
				frm.fields_dict.http_channels.grid.refresh();
			} else {
				// Add new row
				let row = frm.add_child("http_channels", values);
				frm.fields_dict.http_channels.grid.refresh();
			}
			d.hide();
		},
	});

	// Pre-populate if editing
	if (is_edit) {
		d.set_values(row_data);
	}

	// Handle grid row clicks: open editor on double-click
	frm.fields_dict.http_channels.grid.wrapper.on("dblclick", ".grid-row", function () {
		let $row = $(this);
		let row_name = $row.attr("data-name");
		let row = frm.doc.http_channels.find(r => r.name === row_name);
		if (row) {
			open_channel_dialog(frm, row);
		}
	});

	d.show();
}
