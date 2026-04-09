# Copyright (c) 2025, FMS and Contributors
# License: MIT
import re
from datetime import date

import frappe
from frappe import _
from frappe.contacts.address_and_contact import (
	delete_contact_and_address,
	load_address_and_contact,
)
from frappe.model.document import Document


class FMSPerson(Document):
	def onload(self):
		load_address_and_contact(self)

	def on_trash(self):
		delete_contact_and_address("FMS Person", self.name)

	def validate(self):
		self.validate_name_not_null()
		self.validate_date_of_birth_not_future()
		self.validate_kyc_dates_not_future()
		self.set_age()
		self.validate_pan()

	def validate_name_not_null(self):
		if not self.full_name:
			frappe.throw(_("Full Name is required"))

	def validate_date_of_birth_not_future(self):
		if self.date_of_birth:
			dob = self.date_of_birth
			if isinstance(dob, str):
				dob = frappe.utils.getdate(dob)
			if dob > frappe.utils.getdate(frappe.utils.today()):
				frappe.throw(_("Date of Birth cannot be in the future"))

	def validate_kyc_dates_not_future(self):
		if self.kyc_verified_on:
			if self.kyc_verified_on > frappe.utils.now_datetime():
				frappe.throw(_("KYC Verified On cannot be in the future"))

	def set_age(self):
		if self.date_of_birth:
			dob = self.date_of_birth
			if isinstance(dob, str):
				dob = frappe.utils.getdate(dob)
			today = date.today()
			self.age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

	def validate_pan(self):
		if self.pan:
			pan = self.pan.upper()
			pan_pattern = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")

			if len(pan) != 10:
				frappe.throw(_("PAN must be 10 characters"))

			if not pan_pattern.match(pan):
				frappe.throw(_("Invalid PAN format. Expected format: ABCDE1234F"))

			self.pan = pan

			existing = frappe.db.exists("FMS Person", {"pan": pan, "name": ("!=", self.name)})
			if existing:
				frappe.throw(_("PAN {0} is already linked to another Person").format(pan))
