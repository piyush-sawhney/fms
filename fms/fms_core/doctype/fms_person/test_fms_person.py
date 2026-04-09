# Copyright (c) 2026, KNAPS and Contributors
# See license.txt

from datetime import date, timedelta

import frappe
from frappe import ValidationError
from frappe.tests import IntegrationTestCase


class TestFMSPerson(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("FMS Person", {"name": ("like", "FMS-PER-%")})

	def tearDown(self):
		frappe.db.delete("FMS Person", {"name": ("like", "FMS-PER-%")})

	def test_date_of_birth_not_in_future(self):
		future_date = date.today() + timedelta(days=1)
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"full_name": "Test Person",
				"date_of_birth": future_date,
			}
		)
		self.assertRaises(ValidationError, person.insert)

	def test_kyc_verified_on_not_in_future(self):
		future_date = frappe.utils.now_datetime() + timedelta(days=1)
		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"full_name": "Test Person",
				"kyc_verified_on": future_date,
			}
		)
		self.assertRaises(ValidationError, person.insert)

	def test_pan_unique_when_present(self):
		person1 = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"full_name": "Person One",
				"pan": "ABCDE1234F",
			}
		)
		person1.insert()

		person2 = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"full_name": "Person Two",
				"pan": "ABCDE1234F",
			}
		)
		self.assertRaises(ValidationError, person2.insert)

		person1.delete()

	def test_pan_can_be_empty(self):
		person1 = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"full_name": "Person One",
			}
		)
		person1.insert()

		person2 = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"full_name": "Person Two",
			}
		)
		person2.insert()

		self.assertTrue(person1.name)
		self.assertTrue(person2.name)

		person1.delete()
		person2.delete()

	def test_pan_unique_when_both_empty(self):
		person1 = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"full_name": "Person One",
			}
		)
		person1.insert()

		person2 = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"full_name": "Person Two",
			}
		)
		person2.insert()

		self.assertTrue(person1.name)
		self.assertTrue(person2.name)

		person1.delete()
		person2.delete()

	def test_pan_unique_when_both_have_same_value(self):
		person1 = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"full_name": "Person One",
				"pan": "AAAAA9999A",
			}
		)
		person1.insert()

		person2 = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"full_name": "Person Two",
				"pan": "AAAAA9999A",
			}
		)
		self.assertRaises(ValidationError, person2.insert)

		person1.delete()

	def test_pan_unique_when_different(self):
		person1 = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"full_name": "Person One",
				"pan": "BBBBB8888B",
			}
		)
		person1.insert()

		person2 = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"full_name": "Person Two",
				"pan": "CCCCC7777C",
			}
		)
		person2.insert()

		self.assertTrue(person1.name)
		self.assertTrue(person2.name)

		person1.delete()
		person2.delete()

	def test_age_calculated_from_dob(self):
		dob = date(1990, 5, 15)
		today = date.today()
		expected_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

		person = frappe.get_doc(
			{
				"doctype": "FMS Person",
				"full_name": "Test Person",
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
					"full_name": "Test Person",
					"pan": invalid_pan,
				}
			)
			self.assertRaises(ValidationError, person.insert)

	def test_pan_format_valid(self):
		valid_pans = ["ABCDE1234F", "AAAAA9999A", "BBBBB1111B"]

		for valid_pan in valid_pans:
			person = frappe.get_doc(
				{
					"doctype": "FMS Person",
					"full_name": "Test Person",
					"pan": valid_pan,
				}
			)
			person.insert()
			self.assertEqual(person.pan, valid_pan.upper())
			person.delete()
