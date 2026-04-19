# Copyright (c) 2026, FMS and Contributors
# License: MIT
import re
from datetime import date

import frappe

STATUS_ACTIVE = "Active"
MAX_AGE = 140

from frappe import _
from frappe.contacts.address_and_contact import (
	delete_contact_and_address,
	load_address_and_contact,
)
from frappe.model.document import Document

from fms.fms_core import utils as fms_utils


class FMSPerson(Document):
	def onload(self):
		load_address_and_contact(self)

	def on_trash(self):
		delete_contact_and_address("FMS Person", self.name)

	def validate(self):
		self.validate_name_fields()
		self.validate_no_duplicate_contacts()
		self.validate_no_duplicate_emails()
		self.auto_set_primary_contact()
		self.auto_set_primary_email()
		self.validate_only_one_primary_contact()
		self.validate_only_one_primary_email()
		self.set_full_name()
		self.sync_primary_fields()
		self.validate_pan()
		self.validate_ckyc()
		self.set_age()
		self.validate_date_of_birth()

	def validate_no_duplicate_contacts(self):
		if self.contact_details:
			numbers = []
			for contact in self.contact_details:
				if contact.number:
					if contact.number in numbers:
						frappe.throw(
							_("Duplicate phone number {0} found").format(contact.number),
							title=_("Validation Error"),
						)
					numbers.append(contact.number)

	def validate_no_duplicate_emails(self):
		if self.email_addresses:
			emails = []
			for email in self.email_addresses:
				if email.email:
					if email.email in emails:
						frappe.throw(
							_("Duplicate email {0} found").format(email.email),
							title=_("Validation Error"),
						)
					emails.append(email.email)

	def validate_only_one_primary_contact(self):
		if self.contact_details:
			active_primary_count = sum(
				1 for c in self.contact_details if c.is_primary and c.is_active == STATUS_ACTIVE
			)
			if active_primary_count > 1:
				frappe.throw(
					_("Only one active contact can be marked as primary"),
					title=_("Validation Error"),
				)

	def validate_only_one_primary_email(self):
		if self.email_addresses:
			active_primary_count = sum(
				1 for e in self.email_addresses if e.is_primary and e.is_active == STATUS_ACTIVE
			)
			if active_primary_count > 1:
				frappe.throw(
					_("Only one active email can be marked as primary"),
					title=_("Validation Error"),
				)

	def auto_set_primary_contact(self):
		if self.contact_details:
			has_primary = any(c.is_primary for c in self.contact_details)
			if not has_primary:
				for contact in self.contact_details:
					if contact.is_active == "Active":
						contact.is_primary = 1
						contact.is_whatsapp = 1
						break

	def auto_set_primary_email(self):
		if self.email_addresses:
			has_primary = any(e.is_primary for e in self.email_addresses)
			if not has_primary:
				for email in self.email_addresses:
					if email.is_active == "Active":
						email.is_primary = 1
						break

	def validate_name_fields(self):
		if not self.first_name:
			if self.is_new():
				frappe.throw(_("First Name is required"))
			elif not self.get_db_value("first_name"):
				frappe.throw(_("First Name is required"))

	def set_full_name(self):
		parts = [self.first_name or ""]
		if self.middle_name:
			parts.append(self.middle_name)
		if self.last_name:
			parts.append(self.last_name)
		self.full_name = " ".join(parts).strip()

	def sync_primary_fields(self):
		primary_fields = fms_utils.sync_primary_fields(self.contact_details, self.email_addresses)
		self.primary_mobile = primary_fields["primary_mobile"]
		self.primary_whatsapp = primary_fields["primary_whatsapp"]
		self.primary_email = primary_fields["primary_email"]

	def validate_pan(self):
		if self.pan_number:
			pan = self.pan_number.upper()
			pan_pattern = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")

			if len(pan) != 10:
				frappe.throw(_("PAN Number must be 10 characters"))

			if not pan_pattern.match(pan):
				frappe.throw(_("Invalid PAN format. Expected format: ABCDE1234F"))

			self.pan_number = pan

			existing = frappe.db.exists("FMS Person", {"pan_number": pan, "name": ("!=", self.name)})
			if existing:
				frappe.throw(_("PAN Number {0} is already linked to another Person").format(pan))

	def validate_ckyc(self):
		if self.ckyc_number:
			ckyc = self.ckyc_number.upper()
			ckyc_pattern = re.compile(r"^[0-9]{14}$")

			if len(ckyc) != 14:
				frappe.throw(_("cKYC Number must be 14 digits"))

			if not ckyc_pattern.match(ckyc):
				frappe.throw(_("Invalid cKYC format. Expected 14 digit numeric"))

			self.ckyc_number = ckyc

			existing = frappe.db.exists("FMS Person", {"ckyc_number": ckyc, "name": ("!=", self.name)})
			if existing:
				frappe.throw(_("cKYC Number {0} is already linked to another Person").format(ckyc))

	def set_age(self):
		if self.date_of_birth:
			dob = self.date_of_birth
			if isinstance(dob, str):
				dob = frappe.utils.getdate(dob)
			today = date.today()
			age = today.year - dob.year
			if (today.month, today.day) < (dob.month, dob.day):
				age -= 1
			self.age = max(0, age)
			self.set_age_formatted(dob)
		else:
			self.age = 0
			self.age_formatted = ""

	def set_age_formatted(self, dob):
		today = date.today()
		years = today.year - dob.year
		months = today.month - dob.month
		days = today.day - dob.day
		if days < 0:
			months -= 1
			prev_month = today.month - 1 if today.month > 1 else 12
			days_in_prev_month = (date(today.year, prev_month + 1, 1) - date(today.year, prev_month, 1)).days
			days += days_in_prev_month
		if months < 0:
			years -= 1
			months += 12
		years = max(0, years)
		months = max(0, months)
		days = max(0, days)
		parts = []
		if years > 0:
			parts.append(f"{years} year{'s' if years != 1 else ''}")
		if months > 0:
			parts.append(f"{months} month{'s' if months != 1 else ''}")
		if days > 0:
			parts.append(f"{days} day{'s' if days != 1 else ''}")
		if not parts:
			self.age_formatted = "0 days"
		elif len(parts) > 1:
			self.age_formatted = ", ".join(parts[:-1]) + " and " + parts[-1]
		else:
			self.age_formatted = parts[0]

	def validate_date_of_birth(self):
		if self.date_of_birth:
			dob = self.date_of_birth
			if isinstance(dob, str):
				dob = frappe.utils.getdate(dob)
			today = frappe.utils.getdate(frappe.utils.today())
			if dob > today:
				frappe.throw(_("Date of Birth cannot be in the future"))
			age = today.year - dob.year
			if (today.month, today.day) < (dob.month, dob.day):
				age -= 1
			if age < 0:
				frappe.throw(_("Person cannot have negative age"))
			if age > MAX_AGE:
				frappe.throw(_("Person cannot be older than {0} years").format(MAX_AGE))


def get_permission_query_conditions(user: str | None = None) -> str:
	if not user:
		user = frappe.session.user

	if "System Manager" in frappe.get_roles(user):
		return None

	return "`tabFMS Person`.`status` != 'Deceased'"
