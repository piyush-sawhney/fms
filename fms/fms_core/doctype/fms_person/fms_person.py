# Copyright (c) 2026, FMS and Contributors
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
from frappe.utils import flt


class FMSPerson(Document):
	def onload(self):
		load_address_and_contact(self)

	def on_trash(self):
		delete_contact_and_address("FMS Person", self.name)

	def validate(self):
		self.validate_aadhaar_prohibited()
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
			primary_count = sum(1 for c in self.contact_details if c.is_primary)
			if primary_count > 1:
				frappe.throw(
					_("Only one contact can be marked as primary"),
					title=_("Validation Error"),
				)

	def validate_only_one_primary_email(self):
		if self.email_addresses:
			primary_count = sum(1 for e in self.email_addresses if e.is_primary)
			if primary_count > 1:
				frappe.throw(
					_("Only one email can be marked as primary"),
					title=_("Validation Error"),
				)

	def auto_set_primary_contact(self):
		if self.contact_details:
			has_primary = any(c.is_primary for c in self.contact_details)
			if not has_primary:
				for contact in self.contact_details:
					if contact.is_active == "Active":
						contact.is_primary = 1
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
			frappe.throw(_("First Name is required"))

	def validate_aadhaar_prohibited(self):
		if self.kyc_documents:
			for doc in self.kyc_documents:
				if doc.document_type and doc.document_type.lower() == "aadhaar":
					frappe.throw(
						_("Aadhaar is not allowed as a KYC document type"),
						title=_("KYC Validation Error"),
					)

	def set_full_name(self):
		parts = [self.first_name or ""]
		if self.middle_name:
			parts.append(self.middle_name)
		if self.last_name:
			parts.append(self.last_name)
		self.full_name = " ".join(parts).strip()

	def sync_primary_fields(self):
		self.primary_mobile = None
		self.primary_whatsapp = None
		self.primary_email = None

		if self.contact_details:
			for contact in self.contact_details:
				if contact.is_active == "Active":
					if contact.is_primary:
						if not self.primary_mobile:
							self.primary_mobile = contact.number
					if contact.is_whatsapp:
						if not self.primary_whatsapp:
							self.primary_whatsapp = contact.number

		if not self.primary_whatsapp and self.primary_mobile:
			self.primary_whatsapp = self.primary_mobile

		if self.email_addresses:
			for email in self.email_addresses:
				if email.is_active == "Active" and email.is_primary and not self.primary_email:
					self.primary_email = email.email

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
			self.age = flt(today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day)))

	def validate_date_of_birth(self):
		if self.date_of_birth:
			dob = self.date_of_birth
			if isinstance(dob, str):
				dob = frappe.utils.getdate(dob)
			if dob > frappe.utils.getdate(frappe.utils.today()):
				frappe.throw(_("Date of Birth cannot be in the future"))


@frappe.whitelist()
def get_decrypted_kyc(
	person_name: str,
	doc_name: str,
	idempotency_key: str,
	otc: str,
) -> bytes:
	frappe.flags.in_kyc_decrypt = True

	existing_key = frappe.cache().get_value(f"kyc_decrypt:{idempotency_key}")
	if existing_key:
		frappe.throw(
			_("This request has already been processed"),
			title=_("Idempotency Error"),
		)

	person = frappe.get_doc("FMS Person", person_name)

	valid_otc = frappe.cache().get_value(f"kyc_otc:{person_name}")
	if not valid_otc or valid_otc != otc:
		frappe.throw(
			_("Invalid One-Time Code"),
			title=_("Authentication Error"),
		)

	doc = None
	for kyc_doc in person.kyc_documents:
		if kyc_doc.name == doc_name:
			doc = kyc_doc
			break

	if not doc or not doc.attachment:
		frappe.throw(_("KYC document not found"))

	file_path = doc.attachment
	try:
		with open(file_path, "rb") as f:
			content = f.read()
	except OSError:
		frappe.throw(_("Unable to read KYC document"))

	decrypted_content = _decrypt_kyc_content(content)

	frappe.cache().set_value(f"kyc_decrypt:{idempotency_key}", 1)

	return decrypted_content


def _decrypt_kyc_content(content: bytes) -> bytes:
	return content


def get_permission_query_conditions(user: str | None = None) -> str:
	if not user:
		user = frappe.session.user

	if "System Manager" in frappe.get_roles(user):
		return None

	return "`tabFMS Person`.`status` != 'Deceased'"
