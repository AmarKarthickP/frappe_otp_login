frappe.ui.form.on("OTP Login Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Fetch SMTP Settings"), () => {
			frm.call("fetch_smtp_settings").then(() => {
				frm.refresh();
				frappe.show_alert({ message: __("SMTP settings updated"), indicator: "green" });
			});
		});

		// Hide default Add Row and add custom button
		frm.fields_dict.http_channels.grid.wrapper.find(".grid-add-row").hide();
		frm.add_custom_button(__("Add HTTP Channel"), () => open_channel_dialog(frm), __("HTTP Channels"));

		// Add Edit button to each row
		add_edit_buttons(frm);

		// Refresh edit buttons when grid changes
		frm.fields_dict.http_channels.grid.grid_rows_updated = () => {
			add_edit_buttons(frm);
		};
	},

	email_enabled(frm) {
		frm.toggle_display("email_section", frm.doc.email_enabled);
		frm.toggle_display("email_search_field", frm.doc.email_enabled);
	},
});

function add_edit_buttons(frm) {
	let grid = frm.fields_dict.http_channels.grid;
	grid.wrapper.find(".grid-edit-row-btn").remove();

	grid.wrapper.find(".grid-row").each(function () {
		let $row = $(this);
		let row_name = $row.attr("data-name");

		if ($row.hasClass("grid-heading-row") || $row.hasClass("grid-footer-row")) return;
		if ($row.find(".grid-edit-row-btn").length) return;

		let $btn = $(`<button class="btn btn-xs btn-default grid-edit-row-btn"
			style="position:absolute; right: 8px; top: 4px; z-index:1;">
			${__("Edit")}</button>`);

		$btn.on("click", function (e) {
			e.stopPropagation();
			let row = frm.doc.http_channels.find(r => r.name === row_name);
			if (row) open_channel_dialog(frm, row);
		});

		$row.css("position", "relative").append($btn);
	});
}

function open_channel_dialog(frm, existing_row) {
	let is_edit = !!existing_row;
	let row_data = existing_row ? $.extend(true, {}, existing_row) : {};

	let fields = [
		{ fieldtype: "Section Break", label: __("Channel") },
		{ fieldtype: "Data", fieldname: "channel_name", label: __("Channel Name"), reqd: 1 },
		{ fieldtype: "Check", fieldname: "enabled", label: __("Enabled") },
		{ fieldtype: "Data", fieldname: "identifier_label", label: __("Identifier Label"),
			description: __("What to ask the user for on the login page (e.g., Phone Number, Subscribed Topic)") },
		{ fieldtype: "Section Break", label: __("User Matching") },
		{ fieldtype: "Data", fieldname: "user_field", label: __("Match User By"),
			description: __("Which field on the User document to match the identifier against") },
		{ fieldtype: "Section Break", label: __("HTTP Request") },
		{ fieldtype: "Select", fieldname: "method", label: __("Method"), options: "GET\nPOST", reqd: 1 },
		{ fieldtype: "Data", fieldname: "url", label: __("URL"), reqd: 1,
			description: __("Use {{ identifier }} as placeholder for the user's input") },
		{ fieldtype: "Section Break", label: __("How to Send the Identifier") },
		{ fieldtype: "Select", fieldname: "identifier_placement", label: __("Identifier Placement"),
			options: "URL Path\nQuery Parameter\nPOST Parameter\nMessage Template",
			description: __("How the identifier is passed to the HTTP endpoint") },
		{ fieldtype: "Data", fieldname: "recipient_param", label: __("Recipient Parameter Name"),
			depends_on: "eval:['Query Parameter','POST Parameter'].includes(doc.identifier_placement)",
			description: __("The key name for the identifier (e.g., mobiles, topic, to)") },
		{ fieldtype: "Column Break" },
		{ fieldtype: "Select", fieldname: "content_type", label: __("Content Type"),
			options: "application/json\napplication/x-www-form-urlencoded\nRaw (text/plain)" },
		{ fieldtype: "Data", fieldname: "otp_param", label: __("OTP Parameter Name"),
			description: __("The key name for the OTP code (e.g., message, code, otp)") },
		{ fieldtype: "Column Break" },
		{ fieldtype: "Small Text", fieldname: "message_template", label: __("Message"),
			description: __("Jinja template. Variables: {{ otp }}, {{ identifier }}, {{ site_name }}") },
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

	if (is_edit) {
		if (row_data.auth_token) row_data.auth_token = existing_row.auth_token;
		if (row_data.auth_password) row_data.auth_password = existing_row.auth_password;
	}

	let d = new frappe.ui.Dialog({
		title: is_edit ? __("Edit HTTP Channel") : __("Add HTTP Channel"),
		fields: fields,
		size: "large",
		primary_action_label: is_edit ? __("Update") : __("Add"),
		primary_action(values) {
			if (is_edit) {
				for (let key of Object.keys(values)) {
					frappe.model.set_value(existing_row.doctype, existing_row.name, key, values[key]);
				}
			} else {
				frm.add_child("http_channels", values);
			}
			frm.fields_dict.http_channels.grid.refresh();
			frm.dirty();
			d.hide();
			frm.save();
		},
	});

	// Dynamic message_template label based on content_type
	let msg_field = d.get_field("message_template");
	let ct_field = d.get_field("content_type");
	function update_msg_label() {
		let ct = d.get_value("content_type") || "application/json";
		if (ct === "Raw (text/plain)") msg_field.df.label = __("Message");
		else if (ct === "application/x-www-form-urlencoded") msg_field.df.label = __("Raw Form Data");
		else msg_field.df.label = __("JSON");
		msg_field.refresh();
	}
	ct_field.$input.on("change", update_msg_label);

	// Dynamic URL hint based on identifier_placement
	let place_field = d.get_field("identifier_placement");
	let url_field = d.get_field("url");
	function update_url_hint() {
		let p = d.get_value("identifier_placement") || "Query Parameter";
		if (p === "URL Path") {
			url_field.df.description = __("Use {{ identifier }} as placeholder. Example: https://ntfy.sh/{{ identifier }}");
		} else {
			url_field.df.description = __("API endpoint URL");
		}
		url_field.refresh();
	}
	place_field.$input.on("change", update_url_hint);

	if (is_edit) {
		d.set_values(row_data);
		update_msg_label();
		update_url_hint();
	}

	d.show();
}
