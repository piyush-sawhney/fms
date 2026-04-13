# Copyright (c) 2026, FMS and Contributors
# License: MIT

import unittest
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase

from fms.fms_core import utils as fms_utils


class TestFMSUtils(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("FMS Person", {"name": ("like", "FMS-PER-%")})

	def tearDown(self):
		frappe.db.delete("FMS Person", {"name": ("like", "FMS-PER-%")})

	def test_generate_otp_default_length(self):
		otp = fms_utils.generate_otp()
		self.assertEqual(len(otp), 6)
		self.assertTrue(otp.isdigit())

	def test_generate_otp_custom_length(self):
		for length in [4, 8, 10]:
			otp = fms_utils.generate_otp(length)
			self.assertEqual(len(otp), length)
			self.assertTrue(otp.isdigit())

	def test_generate_otp_all_numeric(self):
		for _ in range(100):
			otp = fms_utils.generate_otp()
			self.assertTrue(otp.isdigit())
			self.assertFalse(any(c.isalpha() for c in otp))

	def test_generate_otp_unique(self):
		otps = [fms_utils.generate_otp() for _ in range(100)]
		self.assertGreaterEqual(len(set(otps)), 95)

	def test_check_otp_rate_limit_first_call(self):
		with patch.object(frappe.cache, "get_value", return_value=None) as mock_get:
			with patch.object(frappe.cache, "set_value") as mock_set:
				result = fms_utils.check_otp_rate_limit("user1", "person1", "doc1")
				self.assertTrue(result)
				mock_get.assert_called_once()
				mock_set.assert_called_once()
				call_args = mock_set.call_args
				self.assertIn(60, call_args[1].values())

	def test_check_otp_rate_limit_block_repeated_call(self):
		with patch.object(frappe.cache, "get_value", return_value="1") as mock_get:
			result = fms_utils.check_otp_rate_limit("user1", "person1", "doc1")
			self.assertFalse(result)
			mock_get.assert_called_once()

	def test_check_idempotency_no_key(self):
		result = fms_utils.check_idempotency(None, "operation1")
		self.assertTrue(result)

	def test_check_idempotency_first_request(self):
		with patch.object(frappe.cache, "get_value", return_value=None) as mock_get:
			with patch.object(frappe.cache, "set_value") as mock_set:
				result = fms_utils.check_idempotency("key123", "upload")
				self.assertTrue(result)
				mock_get.assert_called_once()
				mock_set.assert_called_once()
				call_args = mock_set.call_args
				self.assertIn(3600, call_args[1].values())

	def test_check_idempotency_blocks_duplicate(self):
		with patch.object(frappe.cache, "get_value", return_value="1"):
			result = fms_utils.check_idempotency("key123", "upload")
			self.assertFalse(result)

	def test_check_idempotency_different_operations(self):
		with patch.object(frappe.cache, "get_value", return_value=None):
			result = fms_utils.check_idempotency("key123", "upload")
			self.assertTrue(result)
			result = fms_utils.check_idempotency("key123", "otp")
			self.assertTrue(result)

	def test_check_idempotency_different_keys_same_operation(self):
		with patch.object(frappe.cache, "get_value", return_value=None):
			result = fms_utils.check_idempotency("key1", "upload")
			self.assertTrue(result)
			result = fms_utils.check_idempotency("key2", "upload")
			self.assertTrue(result)

	def test_sanitize_filename_alphanumeric(self):
		result = fms_utils.sanitize_filename("file123_2024")
		self.assertEqual(result, "file123_2024")

	def test_sanitize_filename_special_chars(self):
		result = fms_utils.sanitize_filename("file@#$%^&.txt")
		self.assertEqual(result, "file______.txt")

	def test_sanitize_filename_spaces(self):
		result = fms_utils.sanitize_filename("my file name.txt")
		self.assertEqual(result, "my_file_name.txt")

	def test_sanitize_filename_mixed(self):
		result = fms_utils.sanitize_filename("file-2024_01@test.pdf")
		self.assertEqual(result, "file-2024_01_test.pdf")

	def test_sanitize_filename_empty_result(self):
		result = fms_utils.sanitize_filename("!@#$%^&*()")
		self.assertEqual(result, "_" * 9)

	def test_sanitize_filename_only_special(self):
		result = fms_utils.sanitize_filename("@@@")
		self.assertEqual(result, "___")

	@patch("fms.fms_core.utils.frappe")
	def test_send_otp_email_no_recipient(self, mock_frappe):
		mock_sendmail = MagicMock()
		mock_frappe.sendmail = mock_sendmail
		fms_utils.send_otp_email("", "DOC001", "123456")
		mock_sendmail.assert_not_called()

	@patch("fms.fms_core.utils.frappe")
	def test_send_otp_email_success(self, mock_frappe):
		mock_sendmail = MagicMock()
		mock_frappe.sendmail = mock_sendmail
		fms_utils.send_otp_email("test@example.com", "DOC001", "123456")
		mock_sendmail.assert_called_once()
		call_kwargs = mock_sendmail.call_args.kwargs
		self.assertIn("test@example.com", call_kwargs["recipients"])
		self.assertEqual(call_kwargs["subject"], "OTP for KYC Download")

	@patch("fms.fms_core.utils.frappe")
	def test_send_otp_email_otp_in_message(self, mock_frappe):
		mock_sendmail = MagicMock()
		mock_frappe.sendmail = mock_sendmail
		fms_utils.send_otp_email("test@example.com", "DOC001", "999999")
		call_kwargs = mock_sendmail.call_args.kwargs
		self.assertIn("999999", call_kwargs["message"])
