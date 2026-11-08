# AroNexa P01-T07 UI selector contract

**Grounded current branch:** `feature/p01-t07c1-reception-demo` includes `#fullName`, `#dobPrecision`, `#dob`, a `Review & continue` button, `role=dialog` with duplicate suggestions, and `Confirm new demo registration`.

**Proposed appointment selectors** below are **not yet verified** in the local integrated app. Add these `data-testid` attributes to the corresponding existing React components (or update `support/p01-t07-helpers.mjs` to map to current selectors). Do not change business behavior just to satisfy the test.

| data-testid | Role / element | Expected behavior |
|---|---|---|
| `reception-dashboard` | dashboard region/heading (optional fallback) | visible at entry |
| `patient-register-open` | button (fallback) | opens registration form |
| `patient-registration-form` | form/region (fallback) | registration fields visible |
| `patient-full-name` | input (fallback) | patient name |
| `patient-date-of-birth` | input (fallback) | DOB YYYY-MM-DD |
| `patient-registration-review` | button (fallback) | opens review dialog |
| `patient-duplicate-review` | dialog (fallback) | shows exact-name duplicates |
| `patient-registration-confirm` | button (fallback) | explicitly creates new record |
| `patient-registration-success` | success region (fallback) | shows successful registration |
| `patient-list-open` | button (fallback) | opens patient list |
| `patient-row` | row (fallback) | patient appears in directory |
| `appointments-nav` | link/button | opens appointments |
| `appointments-workspace` | region | appointment management loaded |
| `appointment-create` | button | starts new booking |
| `appointment-patient-search` | input | filters by registered patient |
| `appointment-patient-result` | option/button | selects registered patient |
| `appointment-date` | date input | select date |
| `appointment-slot` | button; unique visible time | available slot enabled; booked slot disabled/absent |
| `appointment-save` | button | confirms booking |
| `appointment-save-success` | confirmation/status | booking persisted in isolated QA backend |
| `appointment-search` | input | searches appointments by patient |
| `appointment-row` | row | shows patient, date, slot, status |
| `appointment-reschedule` | button inside row | opens reschedule |
| `appointment-reschedule-date` | date input | replacement date |
| `appointment-reschedule-save` | button | saves replacement slot |
| `appointment-reschedule-success` | confirmation/status | reschedule persisted |
| `appointment-cancel` | button inside row | requests cancellation |
| `appointment-cancel-confirm` | button inside confirmation | confirms cancellation |
| `appointment-cancel-success` | confirmation/status | cancellation persisted |
| `appointment-checkin` | button inside row | check in today’s patient |

**Essential assertions:**

1. Dashboard and patient registration open correctly.
2. A unique synthetic patient is visible after registration.
3. On second registration with identical data, duplicate review includes an existing record and does not silently merge it.
4. Appointment booking yields a `Booked`, `Scheduled` or `Confirmed` status and displays selected date + slot.
5. Rescheduling replaces the original date/slot, not creates another appointment.
6. Cancelling yields `Cancelled/Canceled`; on reopening new booking, original date/time is selectable again.
7. Check-in is allowed only on a current-day appointment and yields `Checked In` / `Arrived`.

**Contract clarification:** for stronger evidence on rescheduling/check-in, expose stable appointment identifiers and provide a read-only audit/status field, so tests can verify the same appointment record instead of merely matching the patient name. Filter results by patient and appointment ID in QA when available.
