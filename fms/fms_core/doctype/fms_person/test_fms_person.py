# Copyright (c) 2026, FMS and Contributors
# License: MIT

from datetime import date, timedelta

import frappe
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
