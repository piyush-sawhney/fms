# Copyright (c) 2026, KNAPS and contributors
# For license information, please see license.txt

import re

import frappe
from cryptography.fernet import Fernet, InvalidToken
from frappe import _
from frappe.model.document import Document


class FMSSettings(Document):
	pass


def get_encryption_key() -> str:
	doc = frappe.get_single("FMS Settings")
	key = doc.kyc_encryption_key

	if not key:
		frappe.throw(
			_("KYC Encryption Key not configured in FMS Settings. Please set the key first."),
			title=_("Configuration Error"),
		)

	key = key.strip()
	if not key:
		frappe.throw(
			_("KYC Encryption Key is empty after trimming."),
			title=_("Configuration Error"),
		)
	return key


@frappe.whitelist()
def debug_encryption_key():
	doc = frappe.get_single("FMS Settings")
	return {
		"key_length": len(doc.kyc_encryption_key or ""),
		"key_value": repr(doc.kyc_encryption_key),
	}


@frappe.whitelist()
def has_encryption_key() -> bool:
	doc = frappe.get_single("FMS Settings")
	key = doc.kyc_encryption_key
	return bool(key and key.strip())


@frappe.whitelist()
def show_encryption_key():
	key = get_encryption_key()
	frappe.msgprint(
		_(
			"KYC Encryption Key: <br><b style='font-size:14px; word-break:break-all; background:#f5f5f5; padding:8px; border-radius:4px; display:block; margin-top:5px;'>{0}</b>"
		).format(key),
		_("Encryption Key"),
	)
	return key


@frappe.whitelist()
def test_encryption_key():
	doc = frappe.get_single("FMS Settings")
	key = doc.kyc_encryption_key

	if not key or not key.strip():
		return {"success": False, "message": "No key configured"}

	try:
		cipher = Fernet(key.encode())
		test_data = b"Test encryption"
		encrypted = cipher.encrypt(test_data)
		decrypted = cipher.decrypt(encrypted)
		if decrypted == test_data:
			return {"success": True, "message": "Key is valid and working!"}
		else:
			return {"success": False, "message": "Key test failed - data mismatch"}
	except Exception as e:
		return {"success": False, "message": "Key is invalid: " + str(e)}


@frappe.whitelist()
def generate_encryption_key():
	new_key = Fernet.generate_key().decode()
	return {"key": new_key}


def get_next_version(person_name: str, doc_number: str) -> int:
	existing = frappe.db.get_list(
		"File",
		filters={
			"attached_to_doctype": "FMS Person",
			"attached_to_name": person_name,
			"file_name": ("like", f"{doc_number}_v%"),
		},
		fields=["file_name"],
	)
	if not existing:
		return 1

	versions = []
	for f in existing:
		match = re.match(r".*_v(\d+)\.enc", f.file_name or "")
		if match:
			versions.append(int(match.group(1)))

	return max(versions) + 1 if versions else 1
