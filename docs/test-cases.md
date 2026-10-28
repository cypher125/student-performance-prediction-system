# Test cases and results

For Chapter 4, Section 4.11 (Section 3.18 promised unit, integration, system, performance and user acceptance testing). Every row below is checked by an automated test that runs with `python -m pytest` from the `backend` folder; the results section records the latest run.

## Unit tests (Table 4.17a)

| Module | What is tested | Tests |
|---|---|---|
| `ml/grading.py` | NBTE grade boundaries (75 = A, 74.4 = AB, 39.5 rounds to 40 = E), credit-weighted GPA, GPA class cut-offs (3.495 = Distinction, 2.99 = Pass, 1.99 = Fail), UCI class mapping | `tests/test_grading.py` |
| `ml/simulate.py` | Same seed gives identical data; only Table 3.1 fields are written; sessions, levels and semesters in scope; at least 500 records; values in range; previous GPA equals the previous semester's GPA; first-semester rules; current semester has no results; demo directory uses `SIM/` matric numbers | `tests/test_simulate.py` |
| `ml/cleaning.py` | Label normalisation ("nd 1", "1st", "2021/22"); every cleaning rule; noisy data cleaned back to the source values | `tests/test_cleaning.py` |
| `ml/uci.py` | All 649 and 395 students kept; grades rescaled to percentages; class boundaries on the 0–20 scale | `tests/test_uci.py` |

## Integration and system tests (Table 4.18)

| ID | Test case | Input | Expected result | Automated test |
|---|---|---|---|---|
| ST01 | Service health | `GET /api/health` | Status ok and the loaded model's version | `test_health_reports_the_loaded_model` |
| ST02 | Sign in with a wrong password | admin / wrong password | Refused: "Incorrect username or password" | `test_wrong_password_is_rejected` |
| ST03 | Use the system without signing in | `GET /api/students` with no session | Refused (401) | `test_signed_out_requests_are_refused` |
| ST04 | Sign in correctly | lecturer / correct password | Session cookie set (httpOnly, SameSite=Lax); role returned | `test_login_sets_an_httponly_session_cookie` |
| ST05 | Enter an at-risk record by hand | Attendance 45%, CA 30%, assignments 25% | Prediction with probabilities summing to 1; High risk; explanation; advice; an alert raised | `test_manual_entry_returns_prediction_explanation_and_advice` |
| ST06 | Previous GPA left blank | Same record with no previous GPA | Filled from the student's last result (2.75) | `test_manual_entry_returns_prediction_explanation_and_advice` |
| ST07 | Invalid level in manual entry | Level "ND9" | Refused; the field "level" is named | `test_invalid_manual_entry_names_the_field` |
| ST08 | CSV upload, mixed rows | 1 valid row with messy labels, 1 unknown student, 1 attendance of 150 | 1 row saved and predicted; 2 rows rejected with row numbers 3 and 4 and the fields | `test_csv_upload_reports_each_bad_row` |
| ST09 | Student opens another student's record | s0001 opens S0002 | Refused (403) | `test_students_cannot_see_staff_pages_or_other_students` |
| ST10 | Student opens a staff page | s0001 opens the students list | Refused (403); own record and dashboard allowed | `test_students_cannot_see_staff_pages_or_other_students` |
| ST11 | Resolve an alert without an intervention | Status Resolved, no action | Refused: "Describe the intervention…" | `test_alert_workflow_records_the_intervention` |
| ST12 | Record an intervention and resolve | Action text, status Resolved | Status Resolved; staff name and time recorded | `test_alert_workflow_records_the_intervention` |
| ST13 | Lecturer tries admin functions | Users page; retrain | Refused (403) | `test_only_admins_manage_users_and_retraining` |
| ST14 | Admin creates an account | New adviser account | Created (201) | `test_only_admins_manage_users_and_retraining` |
| ST15 | Register a student twice | Same matric number again | First created (201); second refused (409) | `test_template_download_and_student_registration` |
| ST16 | Download the CSV template | `GET /api/records/template` | CSV with the expected header | `test_template_download_and_student_registration` |
| ST17 | Re-score the current semester | "Score current semester" | Only records not yet scored are scored | `test_rescoring_only_scores_records_not_yet_scored` |
| ST18 | Change password | Wrong, then correct, current password | Wrong refused (400); new password works | `test_password_change_requires_the_current_password` |
| ST19 | Retrain with too little data | Retrain with 1 result in the database | Refused: "At least 200 records…" | `test_retraining_refuses_without_enough_results` |
| ST20 | Dashboard, summary report, CSV export | Lecturer opens each | Risk counts, interventions counted, CSV with header | `test_staff_dashboard_and_reports` |
| ST21 | Times shown in local time | Any timestamp from the API | Carries its UTC offset (+00:00), so the browser converts it correctly | `test_times_carry_their_utc_offset` |
| ST22 | The same row twice in one CSV | Two identical rows for one student and semester | Both accepted; the record is scored once (one prediction, at most one alert) | `test_a_repeated_csv_row_is_scored_once` |
| ST23 | Uploading old results | A 2023/2024 record with exam score and GPA | Saved as history and not scored; the student's current level is unchanged | `test_old_results_do_not_move_a_student_back_a_level` |
| ST24 | Resolve an alert with a blank note | Intervention text of spaces only | Refused (422) | `test_a_blank_intervention_cannot_resolve_an_alert` |
| ST25 | Two accounts with the same email | Second account reuses the email | Refused with a clear message (409), not a server error | `test_a_duplicate_email_is_a_clear_conflict` |
| ST26 | Re-scoring an at-risk student | Same record scored twice, then improved to low risk | One open alert, not two; it closes automatically, with a note, when the risk drops | `test_rescoring_keeps_one_alert_and_closes_it_when_risk_drops` |
| ST27 | Editing a finished semester | New CA and attendance for a semester whose GPA is already released | Results kept (GPA 2.75); the record is not scored again | `test_updating_a_finished_semester_keeps_its_results` |
| ST28 | Several semesters in one upload, previous GPA blank | Three consecutive semesters for one student | Each previous GPA is filled from the row before it (3.1, then 2.4) | `test_previous_gpa_fills_from_an_earlier_row_in_the_same_file` |
| ST29 | Reset a forgotten password; disable yourself | Admin sets a new temporary password (first too short), then tries to disable their own account | Short password refused (422); new password works and the old one fails; self-disable refused (400) | `test_an_admin_resets_a_forgotten_password_but_cannot_disable_themselves` |
| ST30 | A student opens their own alerts | Staff note on a student's alert; the student signs in | The student sees the alert and their own advice, but not the staff note, who acknowledged it, or the staff's next step | `test_students_never_see_the_staff_notes_or_next_step` |
| ST31 | Interventions in the summary report | Alerts with staff notes, and one closed automatically | Counts only this semester's alerts with a note written by staff | `test_the_summary_counts_this_semesters_staff_interventions` |

## Performance testing

The model's predictive performance on the held-out test sets is in Chapter 4, Sections 4.5 and 4.8 (`reports/tables/*_model_comparison.csv` and `*_rf_at_risk_detection.csv`).

## User acceptance testing

See `docs/uat-questionnaire.md`. Report only the responses actually collected.

## Results of the latest run

Run on 28 October 2026 (Windows 11, Python 3.13.1) with `.venv\Scripts\python.exe -m pytest` from the `backend` folder:

| Test file | Tests | Passed | Failed |
|---|---|---|---|
| `test_grading.py` | 35 | 35 | 0 |
| `test_simulate.py` | 11 | 11 | 0 |
| `test_cleaning.py` | 21 | 21 | 0 |
| `test_uci.py` | 4 | 4 | 0 |
| `test_api.py` (system tests ST01–ST31) | 26 | 26 | 0 |
| **Total** | **97** | **97** | **0** |

The whole suite ran in 87 seconds. Every system test case in Table 4.18 passed. ST21–ST28 were added after two code reviews found eight defects, each now fixed and covered by its test. This is worth mentioning in Chapter 4 as evidence that the testing found and removed real faults.
