// FMS Person Client Script
frappe.ui.form.on("FMS Person", {
	refresh: function (frm) {
		if (!frm.doc.__islocal) {
			frappe.contacts.render_address_and_contact(frm);
		}
	},

	onload: function (frm) {
		frm.trigger("calculate_age");
	},

	date_of_birth: function (frm) {
		frm.trigger("calculate_age");
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

	after_save: function (frm) {
		frappe.show_alert({
			message: __("Person saved successfully"),
			indicator: "green",
		});
	},
});
