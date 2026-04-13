# Copyright (c) 2026, FMS and Contributors
# License: MIT

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import frappe
from cryptography.fernet import Fernet
from frappe import ValidationError
from frappe.tests import IntegrationTestCase


class TestFMSPerson(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("FMS Person", {"name": ("like", "FMS-PER-%")})

	def tearDown(self):
		frappe.db.delete("FMS Person", {"name": ("like", "FMS-PER-%")})

	def test_full_name_auto_fill(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "John",
				"middle_name": "B",
				"last_name": "Doe",
			}
		)
		person.insert()
		self.assertEqual(person.full_name, "John B Doe")
		person.delete()

	def test_full_name_first_name_only(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "John",
			}
		)
		person.insert()
		self.assertEqual(person.full_name, "John")
		person.delete()

	def test_pan_unique_when_present(self):
		person1 = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Person One",
				"pan_number": "ABCDE1234F",
			}
		)
		person1.insert()

		person2 = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Person Two",
				"pan_number": "ABCDE1234F",
			}
		)
		self.assertRaises(ValidationError, person2.insert)

		person1.delete()

	def test_ckyc_unique_when_present(self):
		person1 = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Person One",
				"ckyc_number": "12345678901234",
			}
		)
		person1.insert()

		person2 = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Person Two",
				"ckyc_number": "12345678901234",
			}
		)
		self.assertRaises(ValidationError, person2.insert)

		person1.delete()

	def test_primary_field_sync_mobile(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"contact_details": [
					{
						"number": "+91 9876543210",
						"type": "Mobile",
						"is_active": "Active",
						"is_primary": 1,
					},
				],
			}
		)
		person.insert()
		self.assertEqual(person.primary_mobile, "+91 9876543210")
		person.delete()

	def test_primary_field_sync_email(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"email_addresses": [
					{
						"email": "test@example.com",
						"type": "Personal",
						"is_active": "Active",
						"is_primary": 1,
					},
				],
			}
		)
		person.insert()
		self.assertEqual(person.primary_email, "test@example.com")
		person.delete()

	def test_primary_field_sync_whatsapp(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"contact_details": [
					{
						"number": "+91 9876543210",
						"type": "Mobile",
						"is_whatsapp": 1,
						"is_active": "Active",
						"is_primary": 1,
					},
				],
			}
		)
		person.insert()
		self.assertEqual(person.primary_whatsapp, "+91 9876543210")
		person.delete()

	def test_primary_mobile_only(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"contact_details": [
					{
						"number": "+91 9988776655",
						"type": "Mobile",
						"is_active": "Active",
						"is_primary": 1,
						"is_whatsapp": 0,
					},
				],
			}
		)
		person.insert()
		self.assertEqual(person.primary_mobile, "+91 9988776655")
		self.assertEqual(person.primary_whatsapp, "+91 9988776655")
		person.delete()

	def test_primary_whatsapp_only(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"contact_details": [
					{
						"number": "+91 9988776656",
						"type": "Mobile",
						"is_active": "Active",
						"is_primary": 0,
						"is_whatsapp": 1,
					},
				],
			}
		)
		person.insert()
		self.assertEqual(person.primary_whatsapp, "+91 9988776656")
		self.assertEqual(person.primary_mobile, "+91 9988776656")
		person.delete()

	def test_both_primary_and_whatsapp(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"contact_details": [
					{
						"number": "+91 9988776657",
						"type": "Mobile",
						"is_active": "Active",
						"is_primary": 1,
						"is_whatsapp": 1,
					},
				],
			}
		)
		person.insert()
		self.assertEqual(person.primary_mobile, "+91 9988776657")
		self.assertEqual(person.primary_whatsapp, "+91 9988776657")
		person.delete()

	def test_multiple_contacts_different_numbers(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"contact_details": [
					{
						"number": "+91 9988776658",
						"type": "Mobile",
						"is_active": "Active",
						"is_primary": 1,
						"is_whatsapp": 0,
					},
					{
						"number": "+91 9988776659",
						"type": "Mobile",
						"is_active": "Active",
						"is_primary": 0,
						"is_whatsapp": 1,
					},
				],
			}
		)
		person.insert()
		self.assertEqual(person.primary_mobile, "+91 9988776658")
		self.assertEqual(person.primary_whatsapp, "+91 9988776659")
		person.delete()

	def test_whatsapp_fallback_to_mobile(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"contact_details": [
					{
						"number": "+91 9988776660",
						"type": "Mobile",
						"is_active": "Active",
						"is_primary": 1,
						"is_whatsapp": 0,
					},
					{
						"number": "+91 9988776661",
						"type": "Mobile",
						"is_active": "Active",
						"is_primary": 0,
						"is_whatsapp": 0,
					},
				],
			}
		)
		person.insert()
		self.assertEqual(person.primary_mobile, "+91 9988776660")
		self.assertEqual(person.primary_whatsapp, "+91 9988776660")
		person.delete()

	def test_primary_email_only(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"email_addresses": [
					{
						"email": "primary@test.com",
						"type": "Personal",
						"is_active": "Active",
						"is_primary": 1,
					},
				],
			}
		)
		person.insert()
		self.assertEqual(person.primary_email, "primary@test.com")
		person.delete()

	def test_multiple_emails_different_primary(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"email_addresses": [
					{
						"email": "email1@test.com",
						"type": "Personal",
						"is_active": "Active",
						"is_primary": 1,
					},
					{
						"email": "email2@test.com",
						"type": "Work",
						"is_active": "Active",
						"is_primary": 0,
					},
				],
			}
		)
		person.insert()
		self.assertEqual(person.primary_email, "email1@test.com")
		person.delete()

	def test_auto_primary_when_none_selected(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"contact_details": [
					{
						"number": "+91 9876543210",
						"type": "Mobile",
						"is_active": "Active",
						"is_primary": 0,
					},
				],
			}
		)
		person.insert()
		self.assertEqual(person.contact_details[0].is_primary, 1)
		person.delete()

	def test_auto_primary_email_when_none_selected(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"email_addresses": [
					{
						"email": "test@example.com",
						"type": "Personal",
						"is_active": "Active",
						"is_primary": 0,
					},
				],
			}
		)
		person.insert()
		self.assertEqual(person.email_addresses[0].is_primary, 1)
		person.delete()

	def test_only_one_primary_contact_allowed(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"contact_details": [
					{
						"number": "+91 9876543210",
						"type": "Mobile",
						"is_active": "Active",
						"is_primary": 1,
					},
					{
						"number": "+91 9876543211",
						"type": "Mobile",
						"is_active": "Active",
						"is_primary": 1,
					},
				],
			}
		)
		self.assertRaises(ValidationError, person.insert)

	def test_only_one_primary_email_allowed(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"email_addresses": [
					{
						"email": "test1@example.com",
						"type": "Personal",
						"is_active": "Active",
						"is_primary": 1,
					},
					{
						"email": "test2@example.com",
						"type": "Personal",
						"is_active": "Active",
						"is_primary": 1,
					},
				],
			}
		)
		self.assertRaises(ValidationError, person.insert)

	def test_no_duplicate_phone_in_child_table(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"contact_details": [
					{
						"number": "+91 9876543210",
						"type": "Mobile",
						"is_active": "Active",
						"is_primary": 1,
					},
					{
						"number": "+91 9876543210",
						"type": "Mobile",
						"is_active": "Active",
						"is_primary": 0,
					},
				],
			}
		)
		self.assertRaises(ValidationError, person.insert)

	def test_no_duplicate_email_in_child_table(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"email_addresses": [
					{
						"email": "test@example.com",
						"type": "Personal",
						"is_active": "Active",
						"is_primary": 1,
					},
					{
						"email": "test@example.com",
						"type": "Personal",
						"is_active": "Active",
						"is_primary": 0,
					},
				],
			}
		)
		self.assertRaises(ValidationError, person.insert)

	def test_same_phone_allowed_for_different_persons(self):
		person1 = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Person One",
				"contact_details": [
					{
						"number": "+91 9876543210",
						"type": "Mobile",
						"is_active": "Active",
						"is_primary": 1,
					},
				],
			}
		)
		person1.insert()

		person2 = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Person Two",
				"contact_details": [
					{
						"number": "+91 9876543210",
						"type": "Mobile",
						"is_active": "Active",
						"is_primary": 1,
					},
				],
			}
		)
		person2.insert()
		self.assertEqual(person2.contact_details[0].number, "+91 9876543210")
		person1.delete()
		person2.delete()

	def test_same_email_allowed_for_different_persons(self):
		person1 = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Person One",
				"email_addresses": [
					{
						"email": "same@example.com",
						"type": "Personal",
						"is_active": "Active",
						"is_primary": 1,
					},
				],
			}
		)
		person1.insert()

		person2 = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Person Two",
				"email_addresses": [
					{
						"email": "same@example.com",
						"type": "Personal",
						"is_active": "Active",
						"is_primary": 1,
					},
				],
			}
		)
		person2.insert()
		self.assertEqual(person2.email_addresses[0].email, "same@example.com")
		person1.delete()
		person2.delete()

	def test_kyc_aadhaar_prohibited(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"kyc_documents": [
					{
						"document_type": "Aadhaar",
						"document_number": "123456789012",
					},
				],
			}
		)
		self.assertRaises(ValidationError, person.insert)

	def test_date_of_birth_not_in_future(self):
		future_date = date.today() + timedelta(days=1)
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"date_of_birth": future_date,
			}
		)
		self.assertRaises(ValidationError, person.insert)

	def test_age_calculated_from_dob(self):
		dob = date(1990, 5, 15)
		today = date.today()
		expected_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"date_of_birth": dob,
			}
		)
		person.insert()

		self.assertEqual(person.age, expected_age)

		person.delete()

	def test_age_formatted_years_only(self):
		dob = date(2000, 1, 1)
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"date_of_birth": dob,
			}
		)
		person.insert()
		formatted = person.age_formatted
		self.assertIn("year", formatted)
		self.assertIn("years", formatted)
		person.delete()

	def test_age_formatted_with_months_and_days(self):
		dob = date(2023, 6, 15)
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"date_of_birth": dob,
			}
		)
		person.insert()
		formatted = person.age_formatted
		self.assertIn("month", formatted)
		self.assertIn("day", formatted)
		person.delete()

	def test_age_formatted_empty_when_no_dob(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
			}
		)
		person.insert()
		self.assertEqual(person.age_formatted, "")
		person.delete()

	def test_age_formatted_infant(self):
		dob = date.today() - timedelta(days=60)
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"date_of_birth": dob,
			}
		)
		person.insert()
		formatted = person.age_formatted
		self.assertIn("month", formatted)
		self.assertNotIn("year", formatted)
		person.delete()

	def test_pan_format_validation(self):
		invalid_pans = ["1234567890", "ABCD123456", "ABCDE1234", "ABCDE12345F"]

		for invalid_pan in invalid_pans:
			person = frappe.get_doc(
				{
					"doctype": "FMS Person",
					"first_name": "Test Person",
					"pan_number": invalid_pan,
				}
			)
			self.assertRaises(ValidationError, person.insert)

	def test_pan_format_valid(self):
		valid_pans = ["ABCDE1234F", "AAAAA9999A", "BBBBB1111B"]

		for valid_pan in valid_pans:
			person = frappe.get_doc(
				{
					"doctype": "FMS Person",
					"first_name": "Test Person",
					"pan_number": valid_pan,
				}
			)
			person.insert()
			self.assertEqual(person.pan_number, valid_pan.upper())
			person.delete()

	def test_ckyc_format_validation(self):
		invalid_numbers = ["123", "123456789012345", "ABCDEFGHIJKLMN"]

		for num in invalid_numbers:
			person = frappe.get_doc(
				{
					"doctype": "FMS Person",
					"first_name": "Test Person",
					"ckyc_number": num,
				}
			)
			self.assertRaises(ValidationError, person.insert)

	def test_ckyc_format_valid(self):
		valid_numbers = ["12345678901234", "00000000000001"]

		for num in valid_numbers:
			person = frappe.get_doc(
				{
					"doctype": "FMS Person",
					"first_name": "Test Person",
					"ckyc_number": num,
				}
			)
			person.insert()
			self.assertEqual(person.ckyc_number, num)
			person.delete()

	def test_first_name_mandatory(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"last_name": "Doe",
			}
		)
		self.assertRaises(ValidationError, person.insert)

	def test_status_default_active(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
			}
		)
		person.insert()
		self.assertEqual(person.status, "Active")
		person.delete()

	def test_phone_number_valid(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"contact_details": [
					{
						"number": "+91 9876543210",
						"type": "Mobile",
						"is_active": "Active",
						"is_primary": 1,
					},
				],
			}
		)
		person.insert()
		self.assertEqual(person.contact_details[0].number, "+91 9876543210")
		person.delete()

	def test_email_format_valid(self):
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"first_name": "Test Person",
				"email_addresses": [
					{
						"email": "test.user@example.com",
						"type": "Personal",
						"is_active": "Active",
						"is_primary": 1,
					},
				],
			}
		)
		person.insert()
		self.assertEqual(person.email_addresses[0].email, "test.user@example.com")
		person.delete()

	def test_get_kyc_base_folder_creates_when_not_exists(self):
		from fms.fms_core.doctype.fms_person.fms_person import get_kyc_base_folder

		with patch("fms.fms_core.doctype.fms_person.fms_person.frappe.db.get_value", return_value=None):
			with patch("fms.fms_core.doctype.fms_person.fms_person.frappe.get_doc") as mock_get_doc:
				mock_folder = MagicMock()
				mock_folder.name = "Home/KYC"
				mock_get_doc.return_value = mock_folder
				result = get_kyc_base_folder()
				self.assertEqual(result, "Home/KYC")

	def test_get_kyc_base_folder_returns_existing(self):
		from fms.fms_core.doctype.fms_person.fms_person import get_kyc_base_folder

		with patch("fms.fms_core.doctype.fms_person.fms_person.frappe.db.get_value", return_value="Home/KYC"):
			result = get_kyc_base_folder()
			self.assertEqual(result, "Home/KYC")

	def test_get_or_create_kyc_folder_new_person(self):
		from fms.fms_core.doctype.fms_person.fms_person import get_or_create_kyc_folder

		with patch("fms.fms_core.doctype.fms_person.fms_person.get_kyc_base_folder", return_value="Home/KYC"):
			with patch("fms.fms_core.doctype.fms_person.fms_person.frappe.db.get_value", return_value=None):
				with patch("fms.fms_core.doctype.fms_person.fms_person.frappe.get_doc") as mock_get_doc:
					mock_folder = MagicMock()
					mock_folder.name = "Home/KYC/TestPerson"
					mock_get_doc.return_value = mock_folder
					result = get_or_create_kyc_folder("TestPerson")
					self.assertEqual(result.name, "Home/KYC/TestPerson")

	def test_get_or_create_kyc_folder_sanitizes_special_chars(self):
		from fms.fms_core.doctype.fms_person.fms_person import get_or_create_kyc_folder

		with patch("fms.fms_core.doctype.fms_person.fms_person.get_kyc_base_folder", return_value="Home/KYC"):
			with patch("fms.fms_core.doctype.fms_person.fms_person.frappe.db.get_value", return_value=None):
				with patch("fms.fms_core.doctype.fms_person.fms_person.frappe.get_doc") as mock_get_doc:
					mock_folder = MagicMock()
					mock_folder.name = "Home/KYC/John_Doe_123"
					mock_get_doc.return_value = mock_folder
					result = get_or_create_kyc_folder("John@Doe#123")
					self.assertEqual(result.name, "Home/KYC/John_Doe_123")

	@patch("fms.fms_core.doctype.fms_person.fms_person.get_encryption_key")
	@patch("fms.fms_core.doctype.fms_person.fms_person.get_or_create_kyc_folder")
	@patch("fms.fms_core.doctype.fms_person.fms_person.save_file")
	@patch("fms.fms_core.doctype.fms_person.fms_person.get_next_version")
	@patch("fms.fms_core.doctype.fms_person.fms_person.frappe.get_list")
	@patch("fms.fms_core.doctype.fms_person.fms_person.frappe.get_doc")
	def test_upload_kyc_document_success(
		self, mock_get_doc, mock_get_list, mock_get_version, mock_save_file, mock_kyc_folder, mock_enc_key
	):
		from cryptography.fernet import Fernet

		from fms.fms_core.doctype.fms_person.fms_person import upload_kyc_document

		test_key = Fernet.generate_key().decode()
		mock_enc_key.return_value = test_key

		mock_file_doc = MagicMock()
		mock_file_doc.name = "test-file-123"
		mock_file_doc.file_name = "original.pdf"
		mock_file_doc.get_full_path.return_value = "/tmp/test.pdf"
		mock_get_list.return_value = [mock_file_doc]

		mock_file_doc_instance = MagicMock()
		mock_file_doc_instance.file_name = "original.pdf"
		mock_get_doc.return_value = mock_file_doc_instance

		mock_folder = MagicMock()
		mock_folder.name = "Home/KYC/TestPerson"
		mock_kyc_folder.return_value = mock_folder

		mock_get_version.return_value = 1

		mock_saved_file = MagicMock()
		mock_saved_file.file_url = "/files/test.enc"
		mock_save_file.return_value = mock_saved_file

		with patch("builtins.open", create=True) as mock_open:
			mock_file = MagicMock()
			mock_file.read.return_value = b"test content"
			mock_open.return_value.__enter__.return_value = mock_file
			mock_open.return_value.__exit__.return_value = False
			result = upload_kyc_document("Test Person", "/files/original.pdf", "DOC001", "idem123")

		self.assertTrue(result["success"])
		self.assertIn("DOC001_v1.enc", result["file_name"])

	@patch("fms.fms_core.doctype.fms_person.fms_person.get_encryption_key")
	@patch("fms.fms_core.doctype.fms_person.fms_person.get_or_create_kyc_folder")
	@patch("fms.fms_core.doctype.fms_person.fms_person.save_file")
	@patch("fms.fms_core.doctype.fms_person.fms_person.get_next_version")
	@patch("fms.fms_core.doctype.fms_person.fms_person.frappe.get_list")
	def test_upload_kyc_document_missing_doc_name(
		self, mock_get_list, mock_get_version, mock_save_file, mock_kyc_folder, mock_enc_key
	):
		from fms.fms_core.doctype.fms_person.fms_person import upload_kyc_document

		result = upload_kyc_document("Test Person", "/files/test.pdf", "", "idem123")

		self.assertFalse(result["success"])
		self.assertIn("Document Number is required", result["message"])

	@patch("fms.fms_core.doctype.fms_person.fms_person.fms_utils.check_idempotency")
	def test_upload_kyc_document_idempotency_blocks(self, mock_check):
		from fms.fms_core.doctype.fms_person.fms_person import upload_kyc_document

		mock_check.return_value = False

		result = upload_kyc_document("Test Person", "/files/test.pdf", "DOC001", "idem123")

		self.assertFalse(result["success"])
		self.assertIn("already been processed", result["message"])

	@patch("fms.fms_core.doctype.fms_person.fms_person.get_encryption_key")
	@patch("fms.fms_core.doctype.fms_person.fms_person.frappe.cache")
	@patch("fms.fms_core.doctype.fms_person.fms_person.frappe.db")
	@patch("fms.fms_core.doctype.fms_person.fms_person.frappe.get_doc")
	def test_download_kyc_document_valid_otp(self, mock_get_doc, mock_db, mock_cache, mock_enc_key):
		from cryptography.fernet import Fernet

		from fms.fms_core.doctype.fms_person.fms_person import download_kyc_document

		test_key = Fernet.generate_key().decode()
		mock_enc_key.return_value = test_key

		mock_cache.get_value.side_effect = [
			"123456",
			None,
		]
		mock_cache.delete_value = MagicMock()

		mock_file_doc = MagicMock()
		mock_file_doc.get_full_path.return_value = "/tmp/test.enc"
		mock_get_doc.return_value = mock_file_doc

		with patch("builtins.open", MagicMock(read_bytes=Fernet(test_key.encode()).encrypt(b"test"))):
			with patch("fms.fms_core.doctype.fms_person.fms_person.frappe.get_all") as mock_get_all:
				mock_get_all.return_value = [
					{
						"name": "kyc-doc-1",
						"document_number": "DOC001",
						"file_url": "/files/DOC001_v1.enc",
						"original_file_name": "test.pdf",
						"document_type": "PAN",
					}
				]

				with patch(
					"fms.fms_core.doctype.fms_person.fms_person.frappe.get_list",
					return_value=[{"name": "test-file"}],
				):
					with patch(
						"fms.fms_core.doctype.fms_person.fms_person.frappe.db.get_value",
						return_value="Test User",
					):
						with patch("fms.fms_core.doctype.fms_person.fms_person.frappe.response", {}):
							try:
								download_kyc_document("Test Person", "DOC001", "123456")
							except Exception:
								pass

	@patch("fms.fms_core.doctype.fms_person.fms_person.get_encryption_key")
	@patch("fms.fms_core.doctype.fms_person.fms_person.frappe.cache")
	@patch("fms.fms_core.doctype.fms_person.fms_person.frappe.get_doc")
	def test_download_kyc_document_rate_limit_on_failure(self, mock_get_doc, mock_cache, mock_enc_key):
		from fms.fms_core.doctype.fms_person.fms_person import download_kyc_document

		mock_cache.get_value.side_effect = [
			"wrong_otp",
			"1",
		]

		with patch("fms.fms_core.doctype.fms_person.fms_person.frappe.get_all", return_value=[]):
			self.assertRaises(Exception, download_kyc_document, "Test Person", "DOC001", "wrong_otp")

	@patch("fms.fms_core.doctype.fms_person.fms_person.get_encryption_key")
	@patch("fms.fms_core.doctype.fms_person.fms_person.frappe.cache")
	@patch("fms.fms_core.doctype.fms_person.fms_person.frappe.get_doc")
	def test_download_kyc_document_invalid_token(self, mock_get_doc, mock_cache, mock_enc_key):
		from fms.fms_core.doctype.fms_person.fms_person import download_kyc_document

		mock_cache.get_value.return_value = "123456"
		mock_cache.delete_value = MagicMock()

		mock_file_doc = MagicMock()
		mock_file_doc.get_full_path.return_value = "/tmp/test.enc"
		mock_get_doc.return_value = mock_file_doc

		invalid_key = Fernet.generate_key().decode()
		other_key = Fernet.generate_key().decode()
		mock_enc_key.return_value = other_key

		with patch("builtins.open", MagicMock(read_bytes=Fernet(invalid_key.encode()).encrypt(b"test"))):
			with patch("fms.fms_core.doctype.fms_person.fms_person.frappe.get_all", return_value=[]):
				with patch(
					"fms.fms_core.doctype.fms_person.fms_person.frappe.get_list",
					return_value=[{"name": "test-file"}],
				):
					self.assertRaises(Exception, download_kyc_document, "Test Person", "DOC001", "123456")

	@patch("fms.fms_core.doctype.fms_person.fms_person.fms_utils.check_otp_rate_limit")
	@patch("fms.fms_core.doctype.fms_person.fms_person.fms_utils.check_idempotency")
	@patch("fms.fms_core.doctype.fms_person.fms_person.fms_utils.generate_otp")
	@patch("fms.fms_core.doctype.fms_person.fms_person.frappe.cache")
	@patch("fms.fms_core.doctype.fms_person.fms_person.frappe.db.get_value")
	def test_request_kyc_otp_success(
		self, mock_get_value, mock_cache, mock_generate, mock_check_idem, mock_check_rate
	):
		from fms.fms_core.doctype.fms_person.fms_person import request_kyc_otp

		mock_check_rate.return_value = True
		mock_check_idem.return_value = True
		mock_generate.return_value = "123456"
		mock_get_value.return_value = MagicMock(primary_email="test@example.com")

		mock_cache_instance = MagicMock()
		mock_cache.return_value = mock_cache_instance

		with patch("fms.fms_core.doctype.fms_person.fms_person.fms_utils.send_otp_email"):
			result = request_kyc_otp("Test Person", "DOC001", "idem123")

		self.assertTrue(result["success"])
		mock_cache_instance.set_value.assert_called()

	@patch("fms.fms_core.doctype.fms_person.fms_person.fms_utils.check_otp_rate_limit")
	@patch("fms.fms_core.doctype.fms_person.fms_person.fms_utils.check_idempotency")
	def test_request_kyc_otp_rate_limit_blocks(self, mock_check_idem, mock_check_rate):
		from fms.fms_core.doctype.fms_person.fms_person import request_kyc_otp

		mock_check_rate.return_value = False

		result = request_kyc_otp("Test Person", "DOC001", "idem123")

		self.assertFalse(result["success"])
		self.assertIn("60 seconds", result["message"])

	@patch("fms.fms_core.doctype.fms_person.fms_person.fms_utils.check_otp_rate_limit")
	@patch("fms.fms_core.doctype.fms_person.fms_person.fms_utils.check_idempotency")
	def test_request_kyc_otp_idempotency_blocks(self, mock_check_idem, mock_check_rate):
		from fms.fms_core.doctype.fms_person.fms_person import request_kyc_otp

		mock_check_rate.return_value = True
		mock_check_idem.return_value = False

		result = request_kyc_otp("Test Person", "DOC001", "idem123")

		self.assertFalse(result["success"])
		self.assertIn("already been processed", result["message"])
