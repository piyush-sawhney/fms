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

frappe.ui.form.on("FMS KYC Document Details", {
	upload: function (frm, cdt, cdn) {
		const row = locals[cdt][cdn];

		if (!row.document_number) {
			frappe.msgprint(__("Please enter Document Number before uploading"));
			return;
		}

		doUpload(frm, row);
	},

	download: function (frm, cdt, cdn) {
		const row = locals[cdt][cdn];

		if (!row.file_url) {
			frappe.msgprint(__("No file to download"));
			return;
		}

		frappe.call({
			method: "fms.fms_core.doctype.fms_person.fms_person.request_kyc_otp",
			args: {
				person_name: frm.doc.name,
				doc_name: row.document_number,
			},
			callback: function (r) {
				const d = new frappe.ui.Dialog({
					title: __("Enter OTP"),
					fields: [
						{
							fieldtype: "Data",
							fieldname: "otp",
							label: __("OTP"),
							description: r.message.message || __("Enter the OTP"),
						},
					],
					primary_action: function () {
						const otp = d.get_value("otp");
						d.hide();
						downloadDocument(frm, row, otp);
					},
					primary_action_label: __("Download"),
				});
				d.show();
			},
		});
	},
});

function doUpload(frm, row) {
	frappe.call({
		method: "fms.fms_core.doctype.fms_settings.fms_settings.has_encryption_key",
		callback: function (r) {
			if (!r.message) {
				frappe.msgprint(__("KYC Encryption Key not configured in FMS Settings"));
				return;
			}

			new frappe.ui.FileUploader({
				on_success: function (file) {
					let fileUrl = file.file_url;
					if (!fileUrl && file.file_name) {
						fileUrl = file.is_private
							? "/private/files/" + file.file_name
							: "/files/" + file.file_name;
					}

					if (!fileUrl) {
						frappe.msgprint(__("Upload failed. Could not get file URL."));
						return;
					}

					frappe.call({
						method: "fms.fms_core.doctype.fms_person.fms_person.upload_kyc_document",
						args: {
							person_name: frm.doc.name,
							doc_name: row.document_number,
							file_url: fileUrl,
						},
						callback: function (r) {
							if (r.message && r.message.success) {
								const grid = frm.get_field("kyc_documents");
								if (grid && grid.grid) {
									for (let i = 0; i < grid.grid.data.length; i++) {
										if (
											grid.grid.data[i].document_number ===
											row.document_number
										) {
											grid.grid.data[i].file_url = r.message.file_url;
											grid.grid.data[i].file_name = r.message.file_name;
											grid.grid.data[i].original_file_name =
												r.message.original_file_name || "";
										}
									}
									grid.grid.refresh();
								}

								frm.refresh_field("kyc_documents");
								frappe.show_alert({
									message: __("Document encrypted and saved"),
									indicator: "green",
								});
							} else {
								const errMsg =
									r.message && r.message.message
										? r.message.message
										: "Upload failed";
								frappe.msgprint(errMsg);
							}
						},
					});
				},
			});
		},
	});
}

function downloadDocument(frm, row, otp) {
	let filename = row.document_number + ".pdf";
	if (row.original_file_name) {
		filename = row.original_file_name;
	}

	const csrfToken = frappe.csrf_token || "";

	const url = `/api/method/fms.fms_core.doctype.fms_person.fms_person.download_kyc_document?person_name=${encodeURIComponent(
		frm.doc.name
	)}&doc_name=${encodeURIComponent(row.document_number)}&otp=${encodeURIComponent(otp)}`;

	fetch(url, {
		method: "GET",
		credentials: "include",
		headers: {
			"X-Frappe-CSRF-Token": csrfToken,
		},
	})
		.then((response) => {
			if (!response.ok) {
				throw new Error("Download failed with status: " + response.status);
			}
			return response.blob();
		})
		.then((blob) => {
			const downloadUrl = window.URL.createObjectURL(blob);
			const a = document.createElement("a");
			a.href = downloadUrl;
			a.download = filename;
			document.body.appendChild(a);
			a.click();
			window.URL.revokeObjectURL(downloadUrl);
			document.body.removeChild(a);
		})
		.catch((error) => {
			frappe.msgprint(__("Download failed: ") + error.message);
		});
}
