# Copyright (c) 2026, FMS and Contributors
# License: MIT
import re
from datetime import date

import frappe
from cryptography.fernet import Fernet, InvalidToken
from frappe import _
from frappe.contacts.address_and_contact import (
	delete_contact_and_address,
	load_address_and_contact,
)
from frappe.model.document import Document
from frappe.utils import flt
from frappe.utils.file_manager import save_file

from fms.fms_core.doctype.fms_settings.fms_settings import (
	get_encryption_key,
	get_next_version,
)


def get_or_create_kyc_folder(person_name: str):
	safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in person_name)

	kyc_base = "Home/KYC"
	kyc_base_exists = frappe.db.get_value("File", {"file_name": "KYC", "folder": "Home", "is_folder": 1})
	if not kyc_base_exists:
		try:
			base_folder = frappe.get_doc(
				{
					"doctype": "File",
					"file_name": "KYC",
					"is_folder": 1,
					"folder": "Home",
				}
			)
			base_folder.insert(ignore_if_duplicate=True)
			frappe.db.commit()
		except Exception:
			pass

	existing_folder = frappe.db.get_value(
		"File",
		{"file_name": safe_name, "folder": kyc_base, "is_folder": 1},
		"name",
	)
	if existing_folder:
		return frappe.get_doc("File", existing_folder)

	kyc_folder = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": safe_name,
			"is_folder": 1,
			"folder": kyc_base,
		}
	)
	kyc_folder.insert(ignore_if_duplicate=True)
	frappe.db.commit()

	return kyc_folder


@frappe.whitelist()
def upload_kyc_document(person_name: str, file_url: str, doc_name: str):
	if not doc_name:
		return {
			"success": False,
			"message": _("Document Number is required"),
		}

	encryption_key = get_encryption_key()

	file_doc = None
	if file_url:
		file_doc = frappe.get_list(
			"File",
			filters={"file_url": file_url},
			fields=["name", "file_name"],
		)
		if file_doc:
			file_doc = frappe.get_doc("File", file_doc[0].name)

	if not file_doc:
		return {
			"success": False,
			"message": _("File not found"),
		}

	try:
		full_path = file_doc.get_full_path()
		with open(full_path, "rb") as f:
			file_content = f.read()
	except Exception as e:
		return {
			"success": False,
			"message": _("Could not read file: {}").format(str(e)),
		}

	if not file_content:
		return {
			"success": False,
			"message": _("Could not read file content"),
		}

	cipher = Fernet(encryption_key.encode())
	encrypted_content = cipher.encrypt(file_content)

	original_file_name = file_doc.file_name or ""
	version = get_next_version(person_name, doc_name)
	safe_doc_number = "".join(c if c.isalnum() or c in "-_" else "_" for c in doc_name)
	encrypted_filename = f"{safe_doc_number}_v{version}.enc"

	kyc_folder = get_or_create_kyc_folder(person_name)

	new_file = save_file(
		fname=encrypted_filename,
		content=encrypted_content,
		dt="FMS Person",
		dn=person_name,
		is_private=1,
		folder=kyc_folder.name,
	)

	kyc_docs = frappe.get_all(
		"FMS KYC Document Details",
		filters={"parent": person_name, "document_number": doc_name},
		fields=["name"],
		limit=1,
	)

	if kyc_docs:
		frappe.db.set_value(
			"FMS KYC Document Details",
			kyc_docs[0].name,
			{
				"file_url": new_file.file_url,
				"file_name": encrypted_filename,
				"original_file_name": original_file_name,
			},
		)
		frappe.db.commit()

	frappe.delete_doc("File", file_doc.name)
	frappe.db.commit()

	return {
		"success": True,
		"message": _("Document encrypted and saved"),
		"file_url": new_file.file_url,
		"file_name": encrypted_filename,
		"original_file_name": original_file_name,
	}


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
		self.validate_no_duplicate_kyc_docs()
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

	def validate_no_duplicate_kyc_docs(self):
		if self.kyc_documents:
			doc_numbers = []
			for doc in self.kyc_documents:
				if doc.document_number:
					if doc.document_number in doc_numbers:
						frappe.throw(
							_(
								"Duplicate document number {0} found in KYC documents".format(
									doc.document_number
								)
							),
							title=_("Validation Error"),
						)
					doc_numbers.append(doc.document_number)

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
					if contact.is_primary and contact.is_whatsapp:
						if not self.primary_whatsapp:
							self.primary_whatsapp = contact.number

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
def request_kyc_otp(person_name, doc_name):
	otp = str(frappe.utils.random_string(6))
	cache_key = f"kyc_otp:{frappe.session.user}:{person_name}:{doc_name}"
	frappe.cache().set_value(cache_key, otp, expires_in_sec=300)

	frappe.msgprint(
		_("OTP for KYC download is: <b>{0}</b>").format(otp),
		_("OTP Sent"),
	)

	return {
		"message": _("OTP for KYC download is: {}").format(otp),
		"otp": otp,
	}


@frappe.whitelist()
def download_kyc_document(person_name, doc_name, otp):
	cache_key = f"kyc_otp:{frappe.session.user}:{person_name}:{doc_name}"
	cached_otp = frappe.cache().get_value(cache_key)

	if not cached_otp or cached_otp != otp:
		frappe.throw(
			_("Invalid or expired OTP"),
			title=_("Authentication Error"),
		)

	frappe.cache().delete_value(cache_key)

	kyc_docs = frappe.get_all(
		"FMS KYC Document Details",
		filters={"parent": person_name},
		fields=[
			"name",
			"document_number",
			"file_url",
			"original_file_name",
			"document_type",
		],
	)

	doc = None
	original_file_name = ""
	document_type = ""
	for kyc_doc in kyc_docs:
		if kyc_doc.name == doc_name or str(kyc_doc.document_number).upper() == str(doc_name).upper():
			doc = kyc_doc
			original_file_name = kyc_doc.get("original_file_name") or ""
			document_type = kyc_doc.get("document_type") or "DOC"
			break

	if not doc or not doc.file_url:
		frappe.throw(_("No encrypted file to download"))

	try:
		key = get_encryption_key()
		cipher = Fernet(key.encode())

		file_name = doc.file_url.split("/")[-1] if doc.file_url else None
		if not file_name:
			frappe.throw(_("No file path found"))

		file_doc = frappe.get_list(
			"File",
			filters={"file_name": file_name},
			fields=["name"],
			limit=1,
		)
		if not file_doc:
			frappe.throw(_("Encrypted file not found"))

		file_doc = frappe.get_doc("File", file_doc[0].name)
		file_path = file_doc.get_full_path()

		with open(file_path, "rb") as f:
			encrypted_content = f.read()

		decrypted_content = cipher.decrypt(encrypted_content)

	except InvalidToken:
		frappe.throw(
			_("Unable to decrypt document. Encryption key may have changed."),
			title=_("Decryption Error"),
		)
	except FileNotFoundError:
		frappe.throw(_("Encrypted file not found on server"), title=_("File Error"))
	except Exception as e:
		frappe.throw(
			_("Unable to read KYC document: {}").format(str(e)),
			title=_("Error"),
		)

	try:
		person = frappe.get_doc("FMS Person", person_name)
		person_full_name = person.full_name or "Unknown"
	except Exception:
		person_full_name = "Unknown"

	original_extension = "pdf"
	if original_file_name:
		parts = original_file_name.rsplit(".", 1)
		if len(parts) > 1:
			original_extension = parts[1].lower()

	safe_full_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in person_full_name)
	safe_doc_number = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(doc.document_number))
	download_filename = f"{safe_full_name}_{document_type}_{safe_doc_number}.{original_extension}"

	content_types = {
		"pdf": "application/pdf",
		"jpg": "image/jpeg",
		"jpeg": "image/jpeg",
		"png": "image/png",
		"gif": "image/gif",
	}
	content_type = content_types.get(original_extension, "application/octet-stream")

	frappe.response.filename = download_filename
	frappe.response.filecontent = decrypted_content
	frappe.response.content_type = content_type
	frappe.response.type = "download"
	frappe.response.display_content_as = "attachment"


def get_permission_query_conditions(user: str | None = None) -> str:
	if not user:
		user = frappe.session.user

	if "System Manager" in frappe.get_roles(user):
		return None

	return "`tabFMS Person`.`status` != 'Deceased'"
