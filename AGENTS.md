# 🏦 FMS - Financial Management Software
> **Lead Architect Blueprint | Frappe Framework v16**

## 🏗️ Executive Summary & Philosophy
You are the **Lead Architect** for a production-grade, data-driven Wealth Management System. The system architecture is strictly governed by the **Person-Centric Trinity**, ensuring zero data redundancy and infinite relational scalability.

### The Core Mandate: The Trinity Architecture
1.  **The Person (Identity):** The unique biological human (**Master Hub**). Holds PAN, KYC status, and contact details.
2.  **The Investor (Tax Entity):** The financial persona (Individual, HUF, Corporate) linked to a `Person`. This is the tax-paying unit.
3.  **The Asset (The Product):** Financial instruments (MF, Insurance, FD, Insurance, NPS etc) linked to one `Investor` (Owner) and multiple `Persons` (Nominees, Joint Holders, Guardians).

---

## 📂 Directory of Rules (Lazy-Loading)
*CRITICAL: Use the `Read` tool to load these files only when the specific task requires them. Defaults are overridden by these files.*

* **Global Guidelines:** `app/fms/fms/rules.md`
* **Module Specifics:** `app/fms/fms/<module_name>/rules.md`
* **DocType Specs:** `app/fms/fms/<module_name>/doctype/<doctype_name>/rules.md`

---

## 🛠️ Tech Stack & Conventions
| Component | Specification |
| :--- | :--- |
| **Backend** | Python 3.14+ (Typing via `frappe.types.DF`) |
| **Frontend** | Node 24 (JS Assets), Frappe UI / Vue 3 |
| **Linters** | Ruff (Python), ESLint & Prettier (JS/CSS) |
| **CI/CD** | GitHub Actions (Pre-commit, Semgrep, Pip-audit) |
| **Indentation** | Tabs (per `.editorconfig`) |
| **Formatting** | Double Quotes, Line Length: 110 (Ruff) |

### 📝 Schema & Naming Conventions
- **Namespace Enforcement:** All custom DocTypes MUST be prefixed with `fms_` (e.g., `fms_person`) to avoid collisions with Frappe/ERPNext core updates.
- **Naming Case:**
    - **DocType Name:** `PascalCase` (e.g., `FMS MF Investment`)
    - **DocFields:** `snake_case` (e.g., `folio_number`)
    - **Folder Names:** `snake_case` (e.g., `app/fms/fms/investments/doctype/fms_mf_investment/`)

---

## 🧪 TDD & Secure Coding Guidelines
### Test-Driven Development (TDD)
- **Location:** `app/fms/fms/<module_name>/doctype/<doctype_name>/test_<doctype_name>.py`
- **Standard:** Every financial calculation (Commissions, NAV, Maturity) must have 100% test coverage. Use `frappe.tests.IntegrationTestCase` for full-stack validation.

### Secure Financial Operations
- **Idempotency:** All `@whitelist` methods handling transactions or financial records MUST implement an `idempotency_key` check to prevent duplicate entries or payments.
- **Data Vaulting:** All KYC/Sensitive attachments MUST be stored in `/private/files`.
- **PII Masking:** Never store full Aadhaar strings. Mask all but the last 4 digits.
- **Audit Trail:** Enable `Track Changes` on all Identity, Investor, and Asset DocTypes.

---

## 🚀 Key Commands
```bash
# Setup
bench get-app fms <repo_path>
bench --site <site> install-app fms

# Testing
bench --site <site> set-config allow_tests true
bench --site <site> run-tests --app fms               # Run all
bench --site <site> run-tests --app fms -k <test>    # Run specific

# Quality Control
pre-commit run --all-files
ruff check . --fix
```

---

## UI/UX & Form Structure Governance

### **1. Visual Hierarchy & Form Layout**
The AI must treat every DocType as a professional workspace. Do not allow "flat" forms with long vertical lists of fields.
* **Logical Grouping (Tabs):** Every primary DocType must use **Tabs** to categorize data (e.g., General Info, Details, Documents, System Audit).
* **Information Density (Columns):** Use **Column Breaks** to create a 2-column or 3-column layout for data density. Related fields (e.g., "City" and "Pincode") must sit side-by-side.
* **Sectioning:** Use **Section Breaks** with descriptive labels to provide visual anchors for the user's eye.

### **2. Interaction Standards**
* **Proactive Visibility:** Use **Section Breaks** to create "Dashboards" at the top of records. These should contain read-only or HTML fields that summarize the record's status.
* **Progressive Disclosure:** Use the "Allow Collapse" feature for secondary metadata or system-generated logs to keep the primary interface clean.
* **Meaningful Labels:** All fields must have clear, professional labels. Use the `description` property for fields that require specific formats (e.g., PAN, IFSC).

### **3. Content Presentation**
* **Table Management:** For Child Tables, always use the "Grid" view and ensure only the most critical 3-4 columns are visible in the grid to prevent horizontal scrolling.
* **Standardized Elements:** All identity-linked DocTypes must include a dedicated section or tab for **Frappe Standard Links** (Address, Contact, and Communication Timeline).
* **Status Highlighting:** Use **Indicator Colors** (Green for Verified, Red for Pending/Expired) on status fields to allow for "at-a-glance" auditing.

---

## 💡 Important Implementation Notes
- **Virtual DocFields:** Use Virtual DocFields in Asset UIs to display `Person` details (Name, PAN) without duplicating the data in the Asset's database table.
- **Dependency:** This app requires `frappe-bench` and is designed for Frappe v16.
- **Permission Control:** Strictly define permissions in `hooks.py` via `permission_query_conditions` and `has_permission` hooks.
- **Only Codebase changes :** No code change to be done in apps/frappe/ directory. Only changes in fms allowed.
---