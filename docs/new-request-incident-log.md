# Full Specification — FM-IT03-02 Incident Log API Ingestion (3rd-Party Form → Microsoft Lists)

> Document: **full-spec.md**
> Date (Asia/Bangkok): **2026-01-15**
> Owner: **P’Jiap (PM/PO)**
> Prepared by: **Kate (EA/Strategic Secretary)**

---

## WiSER

### W — Who (Roles & Stakeholders)

* **P’Jiap (PM/PO):** defines scope, required fields, governance, acceptance criteria.
* **IT/Platform (M365/SharePoint Admin):** app registration, permissions, site/list access.
* **Backend Developer:** implements API, validation, integration to Microsoft Graph, logging, monitoring.
* **Support Ops (CS/IT Support):** uses Microsoft List as operational console.
* **3rd-Party Form Owner/Vendor:** sends incident data payloads to ingestion endpoint; handles retries.
* **Security/Compliance:** PDPA controls, access review, retention policy.

### I — Instructions / Inputs / Constraints

**Target system (destination):** Microsoft Lists (SharePoint)

* Site: `SOP` (SharePoint site)
* List: `FM-IT03-02 Incident Log 2025`
* View: `Case all` (view only; not a data entity)

**Observed columns (from current list view):**

* `ID` (auto)
* `วันที่` (datetime)
* `Name` (text)
* `จำนวนเคส` (number)
* `Environment` (choice) — values observed: `PROD`
* `System` (likely lookup/choice) — values observed: `JDID EKYC`, `SGF+`, `PAH Advance`, `ONE ID`, `JMB_CRM`, `JOIN`, `Teenoi`, `J Wallet`, `JAS_CRM`, `Baanbaan`
* `Raised by` (person)
* `Problem Category` (choice) — observed: `System`
* `ที่มาของปัญหา` (choice) — observed: `Line`, `Telephone`, `Line Group ...`, `Facebook Page ...`, `Support ...`
* `ประเภท` (choice) — observed: `Very low (1 customer)` (note mismatch with `จำนวนเคส`)
* `ปัญหา JMB_CRM` (choice/lookup)
* `สาเหตุ JMB_CRM` (choice/lookup)
* `รายละเอียดของปัญหา` (long text)
* `แนวทางการแก้ไข` (long text)
* `ผลการแก้ไข` (choice/text) — observed: `Information`, `Change info`, `coupon`
* `รายละเอียดของสาเหตุ` (long text)
* `หมายเหตุ` (long text)
* `ผู้แก้ไข` (person)
* `Category` (choice/text) — observed: `Register JDIDeKYC`, `KYC`, `OTP`, etc.
* `Attachments` (file)
* `status` (choice) — observed: `Done`, `Pending`
* `ผู้รับเรื่อง` (person)
* `cs name` (text)
* `Closed date` (datetime)

**Compliance constraints (default):**

* **PDPA:** do not ingest/store unnecessary PII in free text. Mask common patterns.
* **PCI DSS / EMV/3DS / BOT PSA:** not directly in scope, but treat incident data as potentially sensitive operational data.

**Non-functional constraints:**

* Idempotent ingest: same external record must not create duplicate list items.
* Observable: logs, metrics, and failure tracking.
* Least privilege access to SharePoint site/list.

### S — Steps (Method / Design)

## 1) Goal & Scope

### 1.1 Goal

Provide a secure API for 3rd-party forms to submit incident records into `FM-IT03-02 Incident Log 2025` Microsoft List.

### 1.2 In Scope

* Public-facing ingestion endpoint (authenticated)
* Payload validation & normalization
* PII minimization (mask/reject patterns)
* Create List Item via Microsoft Graph
* Idempotency using `externalRef`
* Basic monitoring and audit logs

### 1.3 Out of Scope (for this phase)

* Complex workflow automation (SLA, escalation engine)
* BI dashboard build (Power BI)
* Full taxonomy redesign of incident categories

---

## 2) Recommended Architecture

### Option A (Recommended for long run): **API Service → Microsoft Graph → SharePoint List**

**Flow**

1. 3rd-party form submits JSON to `POST /incidents`.
2. API validates fields, normalizes enums, masks PII.
3. API calls Microsoft Graph to create list item.
4. API returns `listItemId`, `status`, and `externalRef`.

**Why**

* Central gate for validation, rate limit, logging, and compliance controls.

### Option B (Fast but limited): **Power Automate HTTP Trigger → Create item**

* Faster to stand up, weaker versioning/validation, harder observability.

---

## 3) API Contract

### 3.1 Endpoint

* `POST /incidents`

### 3.2 Authentication

**Preferred (server-to-server):**

* **API Key + HMAC signature**

  * Header: `X-Api-Key`
  * Header: `X-Signature` (HMAC-SHA256 over raw body, using shared secret)
  * Header: `X-Timestamp` (ISO8601) to prevent replay; reject if too old.

**Alternatives**

* OAuth2 client credentials from partner (more setup)
* IP allowlist (only as additional layer, not sole control)

### 3.3 Request Schema

```json
{
  "externalRef": "FORM-20260115-000123",
  "datetime": "2026-01-15T13:34:00+07:00",
  "name": "Line : มิน",
  "caseCount": 1,
  "environment": "PROD",
  "system": "JDID EKYC",
  "raisedByEmail": "kavalin.sripet@jventures.co.th",
  "sourceChannel": "Line",
  "problemCategory": "System",
  "severity": "Very low (1 customer)",
  "problemDetails": "error อ่านข้อมูลบัตรไม่สำเร็จ (D99)",
  "workaround": "ให้ลองเทสกับบัตรอื่น",
  "result": "Information",
  "category": "Register JDIDeKYC",
  "status": "Pending",
  "assigneeEmail": "wannapha.maensurin@jventures.co.th",
  "csName": "Kavalin",
  "attachments": []
}
```

### 3.4 Required Fields

* `externalRef`
* `datetime`
* `name`
* `environment`
* `system`
* `sourceChannel`
* `problemDetails`

### 3.5 Response Schema

```json
{
  "externalRef": "FORM-20260115-000123",
  "listItemId": 13125,
  "status": "Created",
  "createdAt": "2026-01-15T13:35:10+07:00"
}
```

### 3.6 Error Responses

* `400` invalid payload / enum mismatch
* `401/403` auth failure
* `409` duplicate externalRef (if non-idempotent mode) OR return existing item id in idempotent mode
* `429` rate limit
* `5xx` upstream Graph/SharePoint errors

---

## 4) Data Normalization & Validation Rules

### 4.1 Enum Normalization

* `environment`: allow `{PROD, UAT, DEV}` (current data mostly PROD)
* `status`: `{Pending, Done}`
* `problemCategory`: e.g. `{System, Process, Data, Account}` (current view uses System)
* `sourceChannel`: e.g. `{Line, Telephone, Facebook Page, Line Group, Support}`

### 4.2 Idempotency

* Use `externalRef` as unique key.
* Behavior: if `externalRef` exists, return existing `listItemId` and `status: Exists`.

### 4.3 PII Guardrails (PDPA)

Given current list contains Thai National ID and phone numbers inside free text, ingestion must reduce risk.

**Rules (minimum viable):**

* Detect and mask Thai ID pattern: `\b\d{13}\b` → `*************` (or last 4 visible)
* Detect and mask Thai phone pattern: `\b0\d{8,9}\b` → `0*********`
* Block inclusion of:

  * full name + national id + phone in a single payload field (reject with 400)

**Field guidance:**

* Do not store raw customer PII in `รายละเอียดของปัญหา`.
* If business needs require PII, create dedicated fields with controlled access (Follow-On improvement).

---

## 5) SharePoint/Microsoft Lists Integration via Microsoft Graph

### 5.1 App Registration (Entra ID)

* Create app registration for ingestion service.
* Use **Client Credentials** (application permissions).

### 5.2 Permissions (Least privilege preferred)

* Preferred: `Sites.Selected` + grant access only to SOP site.
* Alternative (broader): `Sites.ReadWrite.All`.

### 5.3 Discover Site ID and List ID

* Get site ID for SOP.
* Get list ID for `FM-IT03-02 Incident Log 2025`.

### 5.4 Retrieve Column Internal Names

Because SharePoint internal names differ (spaces become `_x0020_`), API must fetch columns:

* `GET /sites/{siteId}/lists/{listId}/columns`
  Cache the mapping.

### 5.5 Create Item

* `POST /sites/{siteId}/lists/{listId}/items`

Payload format:

```json
{
  "fields": {
    "Title": "Line : มิน",
    "วันที่": "2026-01-15T06:34:00Z",
    "Name": "Line : มิน",
    "จำนวนเคส": 1,
    "Environment": "PROD",
    "System": "JDID EKYC",
    "Raised_x0020_by": "kavalin.sripet@jventures.co.th",
    "Problem_x0020_Category": "System",
    "ที่มาของปัญหา": "Line",
    "ประเภท": "Very low (1 customer)",
    "รายละเอียดของปัญหา": "error อ่านข้อมูลบัตรไม่สำเร็จ (D99)",
    "แนวทางการแก้ไข": "ให้ลองเทสกับบัตรอื่น",
    "ผลการแก้ไข": "Information",
    "Category": "Register JDIDeKYC",
    "status": "Pending",
    "ผู้รับเรื่อง": "wannapha.maensurin@jventures.co.th",
    "cs_x0020_name": "Kavalin",
    "ExternalRef": "FORM-20260115-000123"
  }
}
```

**Notes**

* Person fields may require user IDs; if resolution is inconsistent, store as text fields or implement user lookup.
* Lookup fields require numeric lookup IDs, not labels.

---

## 6) Attachments Handling

### 6.1 Scope

* Initial phase: attachments optional, not required.

### 6.2 Approach (Follow-On)

* Upload file to SharePoint drive/library, then link in the list item.
* Avoid uploading PII images (ID card photos) unless required and access-controlled.

---

## 7) Observability & Operations

### 7.1 Logging

* Log per request:

  * `requestId`, `externalRef`, partner identifier, timestamp
  * normalized payload summary (no raw PII)
  * Graph response `listItemId`

### 7.2 Metrics

* count: created, exists, rejected (validation), masked
* latency: p50/p95
* errors: Graph 4xx/5xx breakdown

### 7.3 Retry Policy

* Retry on `429` and transient `5xx` with exponential backoff.
* Do not retry on validation errors.

---

## 8) Security

### 8.1 API Security

* TLS only
* API key rotation support
* HMAC signature + timestamp
* Rate limit per partner

### 8.2 SharePoint Security

* Least privilege Graph permissions
* Restrict list permissions: only necessary teams
* Audit logs enabled

---

## 9) Acceptance Criteria / Definition of Done

### 9.1 Functional AC

* API creates list item with correct field mapping.
* Idempotency: repeated `externalRef` does not create duplicates.
* Enum validation enforced.
* PII masking applied to free-text fields.

### 9.2 Non-functional AC

* Logs contain no raw sensitive identifiers.
* Monitoring dashboards/alerts configured for error spike.

---

## 10) RAID (Risks / Assumptions / Issues / Dependencies)

### Risks

* **Person/Lookup fields fail** due to missing IDs → Mitigation: use text fields or implement lookup resolution.
* **Choice mismatch** breaks inserts → Mitigation: sync enums from Graph columns and validate.
* **PDPA exposure** increases with automation → Mitigation: masking + dedicated sensitive fields + access control.

### Assumptions

* SOP SharePoint site is accessible and admin can grant app permissions.
* List schema is stable (column names/types not changing daily).

### Issues (Known)

* Current dataset already contains PII in free text. This requires remediation policy.

### Dependencies

* Entra ID app registration + admin consent
* Site/list IDs + column internal names

---

## 11) Implementation Plan (Phased)

### Phase 0 — Discovery (1–2 days)

* Identify `siteId`, `listId`
* Pull `/columns` and confirm internal names/types

### Phase 1 — MVP Ingestion (3–5 days)

* Build `POST /incidents`
* Auth + validation + idempotency
* Create list item via Graph

### Phase 2 — Hardening (Follow-On)

* Attachments support
* SLA fields, MTTR calculations, dashboards
* PII redesign (dedicated fields + access control)

---

## 12) Field Mapping Table (External → List)

| External API Field | List Column                | Notes                             |
| ------------------ | -------------------------- | --------------------------------- |
| `datetime`         | `วันที่`                   | Store in UTC in Graph payload     |
| `name`             | `Name` + `Title`           | Title fallback if required        |
| `caseCount`        | `จำนวนเคส`                 | integer                           |
| `environment`      | `Environment`              | choice                            |
| `system`           | `System`                   | choice/lookup; verify type        |
| `raisedByEmail`    | `Raised by`                | person lookup or store email text |
| `problemCategory`  | `Problem Category`         | choice                            |
| `sourceChannel`    | `ที่มาของปัญหา`            | choice                            |
| `severity`         | `ประเภท`                   | choice                            |
| `problemDetails`   | `รายละเอียดของปัญหา`       | mask PII                          |
| `workaround`       | `แนวทางการแก้ไข`           | mask PII                          |
| `result`           | `ผลการแก้ไข`               | choice/text                       |
| `category`         | `Category`                 | choice/text                       |
| `status`           | `status`                   | choice                            |
| `assigneeEmail`    | `ผู้รับเรื่อง`             | person lookup or email text       |
| `csName`           | `cs name`                  | text                              |
| `externalRef`      | `ExternalRef` (new column) | **Add new unique column**         |

---

### E — Expectation (Measurable Outcomes)

* **Outcome:** 3rd-party form can create Microsoft List incident records reliably and securely.
* **Quality bar:** no duplicates, validated enums, masked PII in free text.

### R — Review Checklist

* [ ] Column internal names confirmed via Graph `/columns`
* [ ] Choice values validated against list
* [ ] Person/lookup mapping confirmed
* [ ] PII masking verified with test cases
* [ ] Logs contain no raw national ID / phone
