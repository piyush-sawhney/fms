# Copyright (c) 2026, KNAPS and Contributors
# See license.txt

import frappe
from frappe import ValidationError
from frappe.tests import IntegrationTestCase

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = []


class IntegrationTestFMSSettings(IntegrationTestCase):
	def test_encryption_key_minimum_length(self):
		settings = frappe.get_single("FMS Settings")
		settings.kyc_encryption_key = "short"
		self.assertRaises(ValidationError, settings.save)

	def test_encryption_key_valid_length(self):
		settings = frappe.get_single("FMS Settings")
		settings.kyc_encryption_key = "a" * 32
		settings.save()
		self.assertEqual(settings.kyc_encryption_key, "a" * 32)

	def test_default_folder_path(self):
		settings = frappe.get_single("FMS Settings")
		self.assertEqual(settings.kyc_folder_path, "private/files/kyc")

	def test_developer_mode_default_off(self):
		settings = frappe.get_single("FMS Settings")
		self.assertFalse(settings.is_developer_mode)

	def test_has_encryption_key_true(self):
		from fms.fms_core.doctype.fms_settings.fms_settings import (
			has_encryption_key,
		)

		settings = frappe.get_single("FMS Settings")
		settings.kyc_encryption_key = "a" * 32
		settings.save()
		self.assertTrue(has_encryption_key())

	def test_has_encryption_key_false(self):
		from fms.fms_core.doctype.fms_settings.fms_settings import (
			has_encryption_key,
		)

		settings = frappe.get_single("FMS Settings")
		settings.kyc_encryption_key = None
		settings.save()
		self.assertFalse(has_encryption_key())

	def test_get_next_version_first(self):
		from fms.fms_core.doctype.fms_settings.fms_settings import (
			get_next_version,
		)

		frappe.db.delete("File", {"attached_to_doctype": "FMS Person"})
		version = get_next_version("TEST-PER-001", "ABC123")
		self.assertEqual(version, 1)

	def test_get_next_version_increments(self):
		from fms.fms_core.doctype.fms_settings.fms_settings import (
			get_next_version,
		)

		frappe.db.delete("File", {"attached_to_doctype": "FMS Person"})
		get_next_version("TEST-PER-001", "ABC123")
		frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "ABC123_v1.enc",
				"content": b"test",
				"is_private": 1,
				"attached_to_doctype": "FMS Person",
				"attached_to_name": "TEST-PER-001",
			}
		).insert()
		version = get_next_version("TEST-PER-001", "ABC123")
		self.assertEqual(version, 2)
