// FMS Person Client Script
frappe.ui.form.on("FMS Person", {
	refresh: function (frm) {
		if (!frm.doc.__islocal) {
			frappe.contacts.render_address_and_contact(frm);
			frm.set_df_property("status", "description", get_status_description(frm.doc.status));
		}
	},

	onload: function (frm) {
		frm.trigger("calculate_age");
	},

	date_of_birth: function (frm) {
		frm.trigger("calculate_age");
	},

	first_name: function (frm) {
		frm.trigger("update_full_name");
	},

	middle_name: function (frm) {
		frm.trigger("update_full_name");
	},

	last_name: function (frm) {
		frm.trigger("update_full_name");
	},

	calculate_age: function (frm) {
		if (frm.doc.date_of_birth) {
			const dob = new Date(frm.doc.date_of_birth);
			const today = new Date();
			let age = today.getFullYear() - dob.getFullYear();
			const m = today.getMonth() - dob.getMonth();
			if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) {
				age--;
			}
			frm.set_value("age", age);
		}
	},

	update_full_name: function (frm) {
		const parts = [];
		if (frm.doc.first_name) parts.push(frm.doc.first_name);
		if (frm.doc.middle_name) parts.push(frm.doc.middle_name);
		if (frm.doc.last_name) parts.push(frm.doc.last_name);
		frm.set_value("full_name", parts.join(" ").trim());
	},

	after_save: function (frm) {
		frappe.show_alert({
			message: __("Person saved successfully"),
			indicator: "green",
		});
	},
});

function get_status_description(status) {
	const descriptions = {
		Active: __("Active - Person is an active client"),
		Inactive: __("Inactive - Person is temporarily inactive"),
		Deceased: __("Deceased - Person has passed away"),
	};
	return descriptions[status] || "";
}
