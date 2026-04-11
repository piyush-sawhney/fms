# Copyright (c) 2026, KNAPS and contributors
# For license information, please see license.txt

import frappe
from cryptography.fernet import Fernet
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
def has_encryption_key() -> bool:
	doc = frappe.get_single("FMS Settings")
	key = doc.kyc_encryption_key
	return bool(key and key.strip())


@frappe.whitelist()
def test_encryption_key() -> dict:
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
	except Exception:
		return {"success": False, "message": "Key is invalid"}


def generate_encryption_key() -> str:
	return Fernet.generate_key().decode()


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
		fname = f.file_name or ""
		if fname.endswith(".enc"):
			core = fname[:-4]
			if "_v" in core:
				ver_str = core.split("_v")[-1]
				if ver_str.isdigit():
					versions.append(int(ver_str))

	return max(versions) + 1 if versions else 1
