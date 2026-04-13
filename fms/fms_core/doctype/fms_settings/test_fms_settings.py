# Copyright (c) 2026, KNAPS and Contributors
# See license.txt

import contextlib
import unittest
from unittest.mock import MagicMock, patch

import frappe
from frappe import ValidationError
from frappe.tests import IntegrationTestCase

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = []


class IntegrationTestFMSSettings(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete(
			"File", {"attached_to_doctype": "FMS Person", "attached_to_name": ("like", "TEST-%")}
		)

	def tearDown(self):
		frappe.db.delete(
			"File", {"attached_to_doctype": "FMS Person", "attached_to_name": ("like", "TEST-%")}
		)

	def test_encryption_key_valid_length(self):
		settings = frappe.get_single("FMS Settings")
		settings.kyc_encryption_key = "a" * 32
		settings.save()
		self.assertEqual(settings.kyc_encryption_key, "a" * 32)

	def test_has_encryption_key_true(self):
		from fms.fms_core.doctype.fms_settings.fms_settings import has_encryption_key

		settings = frappe.get_single("FMS Settings")
		settings.kyc_encryption_key = "a" * 32
		settings.save()
		self.assertTrue(has_encryption_key())

	def test_has_encryption_key_false_when_none(self):
		from fms.fms_core.doctype.fms_settings.fms_settings import has_encryption_key

		settings = frappe.get_single("FMS Settings")
		settings.kyc_encryption_key = None
		settings.save()
		self.assertFalse(has_encryption_key())

	def test_has_encryption_key_false_when_empty(self):
		from fms.fms_core.doctype.fms_settings.fms_settings import has_encryption_key

		settings = frappe.get_single("FMS Settings")
		settings.kyc_encryption_key = ""
		settings.save()
		self.assertFalse(has_encryption_key())

	def test_has_encryption_key_false_when_whitespace_only(self):
		from fms.fms_core.doctype.fms_settings.fms_settings import has_encryption_key

		settings = frappe.get_single("FMS Settings")
		settings.kyc_encryption_key = "   "
		settings.save()
		self.assertFalse(has_encryption_key())

	def test_get_next_version_first(self):
		from fms.fms_core.doctype.fms_settings.fms_settings import get_next_version

		frappe.db.delete("File", {"attached_to_doctype": "FMS Person"})
		version = get_next_version("TEST-PER-001", "ABC123")
		self.assertEqual(version, 1)

	def test_get_next_version_increments(self):
		from fms.fms_core.doctype.fms_settings.fms_settings import get_next_version

		frappe.db.delete("File", {"attached_to_doctype": "FMS Person"})
		frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "ABC123_v1.enc",
				"is_private": 1,
				"attached_to_doctype": "FMS Person",
				"attached_to_name": "TEST-PER-001",
			}
		).insert()
		version = get_next_version("TEST-PER-001", "ABC123")
		self.assertEqual(version, 2)

	def test_get_next_version_gap_filling(self):
		from fms.fms_core.doctype.fms_settings.fms_settings import get_next_version

		frappe.db.delete("File", {"attached_to_doctype": "FMS Person"})
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
		frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "ABC123_v3.enc",
				"content": b"test",
				"is_private": 1,
				"attached_to_doctype": "FMS Person",
				"attached_to_name": "TEST-PER-001",
			}
		).insert()
		version = get_next_version("TEST-PER-001", "ABC123")
		self.assertEqual(version, 4)

	def test_get_next_version_multiple_files(self):
		from fms.fms_core.doctype.fms_settings.fms_settings import get_next_version

		frappe.db.delete("File", {"attached_to_doctype": "FMS Person", "attached_to_name": "TEST-PER-001"})
		frappe.db.delete("File", {"attached_to_doctype": "FMS Person"})

		for i in range(1, 6):
			frappe.get_doc(
				{
					"doctype": "File",
					"file_name": f"ABC123_v{i}.enc",
					"content": b"test",
					"is_private": 1,
					"attached_to_doctype": "FMS Person",
					"attached_to_name": "TEST-PER-001",
				}
			).insert()

		version = get_next_version("TEST-PER-001", "ABC123")
		self.assertEqual(version, 6)

	def test_get_next_version_different_person(self):
		from fms.fms_core.doctype.fms_settings.fms_settings import get_next_version

		frappe.db.delete("File", {"attached_to_doctype": "FMS Person"})
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
		version = get_next_version("TEST-PER-002", "ABC123")
		self.assertEqual(version, 1)

	def test_get_next_version_different_doc(self):
		from fms.fms_core.doctype.fms_settings.fms_settings import get_next_version

		frappe.db.delete("File", {"attached_to_doctype": "FMS Person"})
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
		version = get_next_version("TEST-PER-001", "DIFFERENT")
		self.assertEqual(version, 1)

	def test_get_next_version_invalid_filename_format(self):
		from fms.fms_core.doctype.fms_settings.fms_settings import get_next_version

		frappe.db.delete("File", {"attached_to_doctype": "FMS Person"})
		frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "invalid.txt",
				"content": b"test",
				"is_private": 1,
				"attached_to_doctype": "FMS Person",
				"attached_to_name": "TEST-PER-001",
			}
		).insert()
		version = get_next_version("TEST-PER-001", "ABC123")
		self.assertEqual(version, 1)

	def test_generate_encryption_key_format(self):
		from fms.fms_core.doctype.fms_settings.fms_settings import generate_encryption_key

		key = generate_encryption_key()
		self.assertIsInstance(key, str)
		self.assertTrue(len(key) > 0)

	def test_generate_encryption_key_unique(self):
		from fms.fms_core.doctype.fms_settings.fms_settings import generate_encryption_key

		keys = [generate_encryption_key() for _ in range(100)]
		self.assertEqual(len(set(keys)), 100)

	def test_generate_encryption_key_valid_fernet(self):
		from cryptography.fernet import Fernet

		from fms.fms_core.doctype.fms_settings.fms_settings import generate_encryption_key

		key = generate_encryption_key()
		cipher = Fernet(key.encode())
		test_data = b"test data"
		encrypted = cipher.encrypt(test_data)
		decrypted = cipher.decrypt(encrypted)
		self.assertEqual(decrypted, test_data)

	def test_test_encryption_key_valid(self):
		from cryptography.fernet import Fernet

		from fms.fms_core.doctype.fms_settings.fms_settings import test_encryption_key

		test_key = Fernet.generate_key().decode()
		with self._mock_settings(kyc_encryption_key=test_key):
			result = test_encryption_key()
			self.assertTrue(result["success"])
			self.assertIn("valid", result["message"].lower())

	def test_test_encryption_key_invalid(self):
		from fms.fms_core.doctype.fms_settings.fms_settings import test_encryption_key

		with self._mock_settings(kyc_encryption_key="invalid_key"):
			result = test_encryption_key()
			self.assertFalse(result["success"])

	def test_test_encryption_key_empty(self):
		from fms.fms_core.doctype.fms_settings.fms_settings import test_encryption_key

		with self._mock_settings(kyc_encryption_key=""):
			result = test_encryption_key()
			self.assertFalse(result["success"])

	@contextlib.contextmanager
	def _mock_settings(self, kyc_encryption_key: str | None = None):
		mock_doc = MagicMock()
		mock_doc.kyc_encryption_key = kyc_encryption_key
		with patch("fms.fms_core.doctype.fms_settings.fms_settings.frappe.get_single", return_value=mock_doc):
			yield
