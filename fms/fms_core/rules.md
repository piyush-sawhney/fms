# @rules/fms-core.md

## 1. Module Philosophy
The Core Module handles **Identity** and **Logistics**. It is the foundation for all financial transactions. No financial product (MF, Insurance) may exist without linking to an `FMS Investor`.

---

## 2. DocType Specifications

### **1. FMS Person (Master Hub)**
This is the biological record. Every human enters the system here.
* **Primary Key:** `pan` (Must be unique and validated via Regex).
* **Mandatory Fields:** `full_name`
* **Virtual Fields:** `age` (Calculated from DOB).
* **Child Tables:** * `contact_numbers`: Links to `FMS Contact Number`.
    * `email_addresses`: Links to `FMS Email Address`.
* **Logic:** * Enforce **Private** file storage for KYC.
    * `after_insert` Hook: Automatically create a default `FMS Investor` (Type: Individual) for this person.

### **2. FMS Investor (The Tax Entity)**
The legal persona that "owns" assets.
* **Tax Status:** Select (Individual, HUF, Partnership, Private Ltd, Trust, NRI).
* **Entity PAN:** (If HUF/Corporate, it has its own; if Individual, it fetches from `FMS Person`).
* **Primary Person:** Link to `FMS Person`.
* **Signatories/Karta:** Child Table linking to other `FMS Person` records with roles (Director, Karta, Partner).
* **Logic:** Filter Asset reports based on this DocType.

### **3. FMS Contact Number (Child Table)**
Standardized phone management.
* **Fields:** `phone_number`, `type` (Mobile, WhatsApp, Landline, Office), `is_primary` (Check).
* **Logic:** Only the `Primary` number marked as `WhatsApp` should be used by the **Frappe WhatsApp** integration for automated alerts.

### **4. FMS Email Address (Child Table)**
Standardized email management.
* **Fields:** `email_id`, `type` (Personal, Work, Billing), `is_primary` (Check).
* **Logic:** The `Primary` email is the default target for all "Gain/Loss" and "Maturity" reports.

### **5. FMS Bank**
Stores the payout/bank details for an Investor.
* **Fields:** `bank_name`, `account_number`, `ifsc_code`, `account_type` (Savings, Current, NRE, NRO), `branch`.
* **Logic:** * Linked to `FMS Investor`.
    * Include a `Cancelled Cheque` attachment field (Private).
    * Validate `IFSC` format via Regex.

---

## 3. Core Functional Rules

### **The "Inheritance" Rule**
An `FMS Investor` must inherit the `Full Name` and `PAN` from the `FMS Person` if the status is **Individual**. For **Non-Individuals**, the user must provide the entity-specific PAN.

### **Dynamic Global Search**
The `FMS Person` controller must implement a method to fetch all "Roles" across the system:
* Search all Asset DocTypes (MF, Insurance) for where this `person_id` appears as a **Joint Holder**, **Nominee**, or **Guardian**.
* This must be displayed in a **Custom HTML Dashboard** on the Person record.

### **Address Integration**
Use the standard Frappe `Address` DocType. 
* **Link Type:** Link to `FMS Person` (for KYC) and `FMS Investor` (for Billing).
* **Constraint:** An Investor cannot be "Active" without at least one "Permanent" address linked to the Primary Person.

---

## 4. Code Reviewer Guardrails
* **Reject** if `FMS Contact Number` is a plain data field in `FMS Person`. It must be a Child Table to support multiple numbers.
* **Reject** if `FMS Bank` is stored inside `FMS Person`. It belongs to the `FMS Investor` (Tax Entity).
* **Reject** if any PII (Personally Identifiable Information) is set to "Public" file access.

---