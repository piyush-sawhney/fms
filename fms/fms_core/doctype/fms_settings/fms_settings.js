// FMS Settings Client Script
frappe.ui.form.on("FMS Settings", {
	refresh: function (frm) {
		// Nothing special needed
	},

	show_key: function (frm) {
		frappe.call({
			method: "fms.fms_core.doctype.fms_settings.fms_settings.show_encryption_key",
			callback: function (r) {
				if (r.exc) {
					frappe.msgprint(__("Error: {0}").format(r.exc));
				}
			},
		});
	},

	test_key: function (frm) {
		frappe.call({
			method: "fms.fms_core.doctype.fms_settings.fms_settings.test_encryption_key",
			callback: function (r) {
				console.log("Test result:", r);
				if (r.message) {
					frappe.msgprint(r.message.message);
				} else if (r.exc) {
					frappe.msgprint(__("Error: {0}").format(r.exc));
				}
			},
		});
	},

	generate_key: function (frm) {
		frappe.call({
			method: "fms.fms_core.doctype.fms_settings.fms_settings.generate_encryption_key",
			callback: function (r) {
				if (r.message && r.message.key) {
					frm.set_value("kyc_encryption_key", r.message.key);
					frm.refresh_field("kyc_encryption_key");
					setTimeout(function () {
						frm.save()
							.then(function () {
								frappe.msgprint(
									__("Key generated and saved! Click Debug to verify.")
								);
							})
							.catch(function (err) {
								frappe.msgprint(__("Save failed: ") + err);
							});
					}, 500);
				} else if (r.exc) {
					frappe.msgprint(__("Error: {0}").format(r.exc));
				}
			},
		});
	},

	debug_key: function (frm) {
		frappe.call({
			method: "fms.fms_core.doctype.fms_settings.fms_settings.debug_encryption_key",
			callback: function (r) {
				if (r.message) {
					let msg = "Key Length: " + r.message.key_length + "\n";
					msg += "Key Value: " + r.message.key_value;
					frappe.msgprint(msg);
				} else if (r.exc) {
					frappe.msgprint(__("Error: {0}").format(r.exc));
				}
			},
		});
	},
});
