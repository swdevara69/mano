# User Stories & Acceptance Criteria — EZ-1391

**Source Documents:**
- `OptimusCore/1_Base_Repo/Userstory/EZ-1391.doc` (JIRA story export)
- `OptimusCore/1_Base_Repo/Userstory/EZ-1391 logic.csv` (Logic tab expectations)
- `OptimusCore/1_Base_Repo/Template/Template.md` (Test case template)

---

## 📌 Project Context
- **Project:** eZdocs
- **Story:** EZ-1391 — QA - IPSIntegration - Validate Received Liability Information Screen - Logic - AdditionalInsured
- **Status:** Closed (per JIRA export)
- **Sprint:** IPS/eZdocs Sprint 8
- **Fix Version:** eZdocs/IPS Integration
- **Primary Objective:** Ensure the Liability Information screen in eZdocs correctly reflects the IPS-provided “Additional Named Insured” data when the user triggers the sync action.

---

## 🎯 High-Level Goal (Epic)
**As an** eZdocs end user (underwriter/agent/QC),
**I want** the Liability Information screen to properly sync and display IPS-provided Additional Named Insured data when I click the “Sync CIIM” button,
**So that** I am confident the policy record reflects the latest received liability information from IPS and can proceed with accurate underwriting and documentation.

---

## ✅ Acceptance Criteria (Detailed)

### AC-01: Sync button triggers IPS data retrieval
- **Given** an existing submission is opened in eZdocs
- **When** the user clicks the **"Sync CIIM"** button on the Liability Information screen
- **Then** the system must invoke the IPS integration logic to request the most recent received liability data
- **And** the system must update the Liability Information screen fields based on the returned IPS payload
- **And** if IPS is unreachable, show a clear error message and do not overwrite existing data.

### AC-02: Additional Named Insured displays correctly
- **Given** IPS returns one or more Additional Named Insured entries
- **When** the sync completes successfully
- **Then** the **"Additional Named Insured"** section on the **Information** tab must show the list of names from IPS
- **And** the list must display names one-by-one in the expected order (per logic tab requirement)
- **And** if IPS returns no names, the field should be empty and display a placeholder message (e.g., "No additional named insureds returned").

### AC-03: Logic tab consistency (as per CSV/logic spec)
- **Given** the JIRA story references the logic tab in the spreadsheet
- **When** the user inspects the **Logic** tab for “AdditionalInsured”
- **Then** the system’s behavior must match the expected action value:
  - Input: **List of Names**
  - Expected Output: **Show the names one by one**
- **And** if the IPS payload is formatted as a delimited list, the UI should parse and render each name separately.

### AC-04: No data corruption / repeat results
- **Given** the user runs sync multiple times in the same session
- **When** the IPS return contains the same list of names
- **Then** the UI must not duplicate existing names (no repeated entries)
- **And** the UI must maintain the correct order as returned by IPS.

---

## 🧩 Fields & Behavior (Liability Information Screen)

| Field / Control | Tab | Type | Expected Behavior | Notes |
|-----------------|-----|------|-------------------|-------|
| Additional Named Insured | Information | List / Multi-line Text | Populated from IPS “AdditionalNamedInsured” result set. Display each name in a separate line or list item. | Sourced from IPS; logic defines "List of Names" → "Show the names one by one" |
| Sync CIIM (button) | Information | Action Button | Triggers IPS integration call, retries on transient failures; updates fields on success. | Key trigger for synchronization flow |

---

## 🧪 Suggested Test Coverage (from Template.md)

### TC_01 - Verify the Information Screen - Logic - AdditionalInsured Auto
**Objective:** Validate that the Information screen syncs and populates the Additional Named Insured data correctly when the user triggers the sync.

**Preconditions:**
- User is logged into eZdocs
- A submission exists under the Received Liability LOB
- User navigated to the Liability Information screen

**Test Steps:**
1. Click on any existing submission.
2. Navigate to the Information screen by clicking **Next** (per existing workflow).
3. Click the **"Sync CIIM"** button on the Information screen.

**Expected Results:**
- The system syncs default Additional Named Insured data from IPS and populates it on the eZdocs Information screen.
- Each name received from IPS is displayed individually (one by one).
- No duplicate names appear if the sync is performed multiple times.
- If the sync fails, an informative error message is shown and existing data remains unchanged.

---

## 🧠 Notes & Cross-References
- The JIRA description explicitly calls out validating functional, UI, and validation behavior for the **Liability Information** screen.
- The attached spreadsheet referenced in the doc (Received Liability Master.xlsx) is the authoritative source for all tab/field/action matrix expectations; the logic tab specifically drives the **AdditionalNamedInsured** display behavior.
- This story is part of the larger **IPS Integration** effort; it ensures data consistency between IPS and eZdocs.

---

## 📌 Traceability
- **JIRA Story:** EZ-1391
- **Test case:** TC_01 (from template)
- **Logic spec:** `EZ-1391 logic.csv` (Action = IPS Check, Actual Value = Logic - AdditionalInsured)

---

## ✅ Completion Criteria
- [ ] IPS integration returns data and UI reflects it in the Additional Named Insured section.
- [ ] Re-syncing does not duplicate existing list entries.
- [ ] Behavior matches logic matrix (List of Names → show names one by one).
- [ ] QA can reproduce success and failure paths and record defects if deviations occur.
