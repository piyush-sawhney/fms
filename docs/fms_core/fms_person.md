## 🚀 The Power Prompt

**Role:** Senior Frappe Developer & Architect
**Context:** Develop a custom DocType for the `fms` app following the **Trinity Architecture** (Person-Centric).
**Environment:** Frappe v16, Python 3.14+, Tabs for indentation, `fms_` namespace enforcement.

### Task: Create the `fms_person` DocType
Implement the "Identity (Person)" master hub as per the following specifications:

### 1. Schema & Layout
* **Naming:** DocType: `FMS Person` | Table Name: `fms_person`.
* **Header:** Add a Dashboard Section Break with a Read-only HTML summary.
* **Tabs:** Use three tabs: `General`, `Details`, and `Audit/System`.
* **Main Fields:**
    * `first_name` (Data, Mandatory)
    * `middle_name`, `last_name` (Data)
    * `full_name` (Data, Read Only, Title Field)
    * `date_of_birth` (Date), `gender` (Select)
    * `pan_number`, `ckyc_number` (Data, Unique if not empty)
    * `status` (Select: Active, Inactive, Deceased. **Colors:** Active=Green, Inactive=Grey, Deceased=Red).
* **Derived Fields (Read Only):** `primary_mobile`, `primary_whatsapp`, `primary_email`.
* **Integration:** Include an HTML field for `address_html` using standard Frappe Address linking.

### 2. Child Tables
* **fms_contact_details:** `number`, `type`, `is_whatsapp` (Check), `is_active` (Check), `is_primary` (Check).
* **fms_email_addresses:** `email`, `type`, `is_active` (Check), `is_primary` (Check).
* **fms_kyc_docs:** `document_type`, `document_number`, `expiry_date`, `attachment` (Attach). 
    * *Constraint:* Max 4 columns in List View.

### 3. Core Logic (Python Controller)
* **Naming Logic:** On `validate`, set `full_name` as the concatenation of first, middle, and last names.
* **Sync Logic:** Update primary fields (`primary_mobile`, etc.) based on the `is_primary` flag in child tables. Ensure only one row is marked "Primary" at a time.
* **Security (KYC Encryption):**
    * Force all `fms_kyc_docs` attachments to the `private` folder.
    * Implement an encryption wrapper for KYC files.
    * Create a `@whitelist` method `get_decrypted_kyc` that requires an `idempotency_key` and validates a One-Time Code (OTC) before returning the file stream.
* **Validation:** Throw a `frappe.ValidationError` if "Aadhaar" is selected or entered in the KYC Doc table.

### 4. Technical Standards
* Use `frappe.utils.flt` for all numeric/math operations.
* Implement `permission_query_conditions` for row-level security.
* No `get_doc` inside loops; use `frappe.db.get_list`.

### 5. Automated Test Suite (`test_fms_person.py`)
Write Python tests inheriting from `frappe.tests.IntegrationTestCase` to verify:
1.  **Full Name Auto-fill:** Verify "John B Doe" is generated correctly.
2.  **Uniqueness:** Attempt to create two persons with the same PAN/cKYC.
3.  **Syncing:** Change a primary email in the child table and verify the parent field updates.
4.  **Encryption:** Verify files in `fms_kyc_docs` are not stored in plaintext.
5.  **Aadhaar Prohibition:** Ensure the system blocks Aadhaar entries.

---
