# Test Cases — EZ-1391 (Sync CIIM / Additional Named Insured)

**Source Materials:**
- User Story: `OptimusCore/1_Base_Repo/Userstory/EZ-1391_UserStories.md`
- Logic: `OptimusCore/1_Base_Repo/Userstory/EZ-1391 logic.csv`
- Template Reference: `OptimusCore/1_Base_Repo/Template/Template.md`
- Navigation Steps: `OptimusCore/1_Base_Repo/Reference/Navigationsteps.md`

---

## ✅ Test Case Coverage Overview
This set of test cases covers **all acceptance criteria** from the user story, including:
- Sync behavior and IPS integration
- Display logic for Additional Named Insured
- Error handling for unreachable IPS
- De-duplication on repeated sync actions
- Format parsing (delimited name lists)
- Navigation flow validation (per reference steps)

---

## 🔎 Test Cases

### TC-01 — Sync CIIM populates Additional Named Insured from IPS
**Priority:** High | **Type:** Functional

**Objective:** Ensure the Sync CIIM button fetches IPS data and displays each Additional Named Insured name individually.

**Preconditions:**
- User is logged into eZdocs.
- A submission exists in Received Liability LOB.
- User is on the Liability Information screen.

**Steps:**
1. Navigate to the Received Liability LOB.
2. Open an existing submission.
3. Navigate to the Information screen.
4. Click **Sync CIIM**.

**Expected Results:**
- IPS integration is invoked.
- Additional Named Insured section displays each name from IPS as a separate line/entry.
- UI behavior matches logic file expectation: list of names is shown one-by-one.

**Traceability:** AC-01, AC-02, AC-03

---

### TC-02 — Sync CIIM shows placeholder when IPS returns no names
**Priority:** Medium | **Type:** Functional

**Objective:** Validate the system handles an empty Additional Named Insured payload gracefully.

**Preconditions:** Same as TC-01, but IPS is configured to return an empty list for Additional Named Insured.

**Steps:**
1. Perform steps 1–4 from TC-01 with IPS returning no names.

**Expected Results:**
- Additional Named Insured section is empty.
- Placeholder message displays (e.g., "No additional named insureds returned").
- No errors are displayed.

**Traceability:** AC-02

---

### TC-03 — Sync CIIM handles IPS connectivity failure
**Priority:** High | **Type:** Negative

**Objective:** Verify error handling when IPS is unreachable and existing data is not overwritten.

**Preconditions:** Same as TC-01, but IPS endpoint is unreachable or returns an error.

**Steps:**
1. Perform steps 1–4 from TC-01 while IPS is offline or returns an error response.

**Expected Results:**
- User sees a clear error message (e.g., "Unable to sync with IPS. Please try again later.").
- Existing Additional Named Insured data remains unchanged.
- No partial or corrupted data is written.

**Traceability:** AC-01

---

### TC-04 — Sync does not duplicate existing names on repeated sync
**Priority:** Medium | **Type:** Regression

**Objective:** Confirm repeated syncs with identical IPS payload do not append duplicates.

**Preconditions:** Same as TC-01; IPS payload contains a fixed list of names.

**Steps:**
1. Perform steps 1–4 from TC-01 with IPS returning a fixed set of names.
2. Repeat step 4 (click **Sync CIIM**) without changing IPS data.

**Expected Results:**
- After the 1st sync, names appear once.
- After the 2nd sync, the list remains unchanged (no duplicates).
- Order remains consistent with the IPS payload.

**Traceability:** AC-01, AC-04

---

### TC-05 — Sync parses delimited Additional Named Insured list correctly
**Priority:** Medium | **Type:** Functional

**Objective:** Validate the UI parses a delimited (comma/semicolon) string into separate names.

**Preconditions:** Same as TC-01; IPS returns Additional Named Insured as a delimited string (e.g., "John Doe; Jane Smith").

**Steps:**
1. Perform steps 1–4 from TC-01 with IPS returning a delimited string for additional insured names.

**Expected Results:**
- UI splits the delimited string into separate entries.
- Each name appears on its own line.
- No combined/concatenated name entries.

**Traceability:** AC-02, AC-03

---

### TC-06 — Navigation to Sync CIIM follows documented workflow
**Priority:** Low | **Type:** Usability

**Objective:** Validate navigation steps match the reference workflow.

**Preconditions:** User is logged into eZdocs and the Received Liability LOB is available.

**Steps:**
1. Follow NavigationSteps.md:
   - Log in.
   - Locate a submission via IPS Contract ID.
   - Open the submission and proceed to the Information screen.
   - Click **Sync CIIM**.

**Expected Results:**
- User can complete the navigation as documented.
- The **Sync CIIM** button is available on the Information screen.
- No missing screens or navigation dead-ends.

**Traceability:** Navigation

---

## 📌 Notes
- These test cases are designed to cover all acceptance criteria from the user story and logic sheet.
- The CSV and MD files are stored in `OptimusCore/4_Designstudio/` for traceability and review.
