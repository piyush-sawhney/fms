# @rules/fms-person.md

## 1. DocType Definition: FMS Person
The `FMS Person` is the master hub for all individual identity data. It must be unique, validated, and secure.

### **Core Fields & Constraints**
| Field Label | Field Name | Type | Rules |
| :--- | :--- | :--- | :--- |
| **Full Name** | `full_name` | Data | **Mandatory.** As per official records. |
| **PAN Number** | `pan` | Data | **Mandatory & Unique.** Format: `[A-Z]{5}[0-9]{4}[A-Z]{1}`. |
| **Date of Birth** | `date_of_birth` | Date | **Mandatory.** Used for age and senior citizen logic. |
| **Age** | `age` | Int (Virtual) | Calculated in Python: `today.year - dob.year`. Must be non-zero. |
| **Gender** | `gender` | Select | Male, Female, Other, Non-Individual (for Corporate signatories). |
| **Address View** | `address_html` | HTML | Rendered via a custom script fetching from Frappe standard `Address`. |

---

## 2. Advanced Identity Logic

### **The "Identity Anchor" (PAN)**
* The `pan` field is the **Unique Key**.
* **Validation:** A server-side `before_save` script must verify the 10-character alphanumeric pattern.
* **De-duplication:** If a user attempts to save a PAN already in the system, throw a `frappe.ValidationError`.

### **Child Tables (Communication & Identity)**
To ensure scalability, contact details are not single fields but child tables:
* **FMS Contact Number:** Supports multiple numbers (Mobile, WhatsApp, Landline).
* **FMS Email Address:** Supports multiple IDs (Personal, Work, Billing).
* **KYC Vault (Table):** Stores metadata for PAN, Voter ID, and Passport. **Files must be marked Private.**


### **The Dynamic Portfolio Dashboard**
The `FMS Person` view must include a **Global Association Table**. This is a virtual table that queries all Asset DocTypes (MF, Insurance, FD, etc) in real-time to show:
* Where this person is a **Primary Holder**.
* Where this person is a **Joint Holder**.
* Where this person is a **Nominee** or **Guardian**.

---


## 5. Implementation Instructions for AI Developer
1.  **Strictly use Base Frappe.** Do not use ERPNext standard Customer logic.
2.  **Naming Series:** Generate ID as `FMS-PER-.YYYY.-.#####.`.
3.  **Client-Script:** Implement a "Refresh" trigger to render the `address_html` by fetching all linked `Address` records where `Link DocType == "FMS Person"`.

---