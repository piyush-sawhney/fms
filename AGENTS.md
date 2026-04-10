# 🏦 FMS: Technical Principal Protocol
**Context:** Wealth Management | Frappe v16 | App: `fms`

## 🎯 1. Core Mandate: The Trinity Architecture
Maintain the **Person-Centric Trinity** to ensure zero data redundancy and relational scalability.
1.  **Identity (Person):** Master Hub (PAN, KYC, Bio).
2.  **Tax Entity (Investor):** Financial persona (Individual, HUF, Corp) linked to `Person`.
3.  **Product (Asset):** Financial instruments (MF, Insurance) linked to `Investor`.

---

## 🏗️ 2. Lead Architect: System & Schema
* **Namespace Enforcement:** Prefix all custom DocTypes with `fms_` (e.g., `fms_person`).
* **Naming Case:**
    * **DocTypes:** PascalCase (e.g., `FMS Asset Management`).
    * **DocFields:** snake_case (e.g., `is_kyc_verified`).
    * **Folders:** snake_case.
* **Frappe-Native First:** Priority: `Standard DocTypes` > `hooks.py` > `DocEvents`.
* **Isolation:** Modify **ONLY** `apps/fms/`. Never touch `apps/frappe/`.
* **Security:** Row-level security via `permission_query_conditions` in `hooks.py`. Private files for KYC.

---

## ⚡ 3. Elite Developer: Code Craftsmanship
* **Performance:** Never use `frappe.get_doc` inside a loop. Use `frappe.db.get_list` with specific `fields`.
* **State:** Use `frappe.cache()` for high-frequency config data.
* **Modularity:** Keep controllers "thin." Extract logic to `utils.py` or service classes.
* **Precision:** **Always** use `frappe.utils.flt` or `Decimal` for math. No standard floats.
* **Reliability:** Wrap external calls in `try-except` with `frappe.log_error`.
* **Integrity:** `@whitelist` methods MUST implement an `idempotency_key` check.

---

## 🧪 4. Tech Stack & TDD
* **Stack:** Python 3.14+ (`frappe.types.DF`) | Node 24 (Frappe UI / Vue 3).
* **TDD:** Every logic change requires a `test_<name>.py`. Inherit from `frappe.tests.IntegrationTestCase`.
* **Coverage:** 100% coverage for NAV, Commission, and Tax calculations.
* **Style:** **Tabs** only. Double quotes. Line length: 110. `ruff check . --fix`.

---

## 🎨 5. UI/UX Governance (Form Standards)
1.  **Header:** Dashboard Section Break at the top (Read-only/HTML summary).
2.  **Navigation:** Use **Tabs** (`General`, `Details`, `Audit/System`).
3.  **Layout:** 2-column Section Breaks with descriptive labels.
4.  **Grids:** Max 4 columns in Child Table `In List View`. Enable `Track Changes`.

---

## ⌨️ 6. Quick Execution
```bash
# Quality & Testing
ruff check . --fix
bench --site [site] run-tests --app fms

# CI/CD Requirements
# All code must pass: Semgrep, Pip-audit, Pre-commit.
```