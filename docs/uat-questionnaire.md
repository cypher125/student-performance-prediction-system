# User Acceptance Test questionnaire

For Section 3.18 (User Acceptance Testing) and Chapter 4. It is based on the Technology Acceptance Model (Davis, 1989), the second theory in Chapter 2.3.2. Print it, or copy it into Google Forms.

## How to run the test

1. Invite 10–20 people: lecturers, academic advisers and students (classmates are acceptable; say who took part in Chapter 4).
2. Give each one 10–15 minutes with the system. Staff use the lecturer account; students use a student account (see `docs/user-guide.md`).
3. Ask staff to complete tasks 1–5 and students tasks 6–7, then fill in the questionnaire. Record whether each task was completed without help.
4. Enter the answers into a spreadsheet (one row per participant) and report the mean and standard deviation of each item and each scale (see "Scoring").

## Tasks

| # | Task | Who |
|---|---|---|
| 1 | Find how many students are at high risk this semester | Staff |
| 2 | Open the student with the highest risk and say the main reason they were flagged | Staff |
| 3 | Enter a record by hand for any student and read the prediction | Staff |
| 4 | Upload the sample CSV file `backend/data/simulated/current_semester_2025_2026.csv` | Staff |
| 5 | Record an intervention for one alert and resolve it | Staff |
| 6 | Find your predicted class and the advice given to you | Student |
| 7 | Say which factor most affects your prediction | Student |

## Questionnaire

**Participant:** Lecturer / Academic adviser / Student / Other: ________   **Date:** ________

Tick one box per statement. 1 = Strongly disagree, 2 = Disagree, 3 = Neutral, 4 = Agree, 5 = Strongly agree.

### A. Perceived usefulness

| # | Statement | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| A1 | The system would help identify struggling students earlier than the current approach. | ☐ | ☐ | ☐ | ☐ | ☐ |
| A2 | The risk levels would help decide which students need attention first. | ☐ | ☐ | ☐ | ☐ | ☐ |
| A3 | The recommendations are useful for planning an intervention (or, for students, for improving). | ☐ | ☐ | ☐ | ☐ | ☐ |
| A4 | Using the system would make academic advising more effective. | ☐ | ☐ | ☐ | ☐ | ☐ |

### B. Perceived ease of use

| # | Statement | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| B1 | The system is easy to learn. | ☐ | ☐ | ☐ | ☐ | ☐ |
| B2 | It is easy to find the information I need. | ☐ | ☐ | ☐ | ☐ | ☐ |
| B3 | Uploading or entering records is straightforward. | ☐ | ☐ | ☐ | ☐ | ☐ |
| B4 | The screens are clear and well organised. | ☐ | ☐ | ☐ | ☐ | ☐ |

### C. Clarity and trust of the explanations

| # | Statement | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| C1 | I understand why a student received their prediction. | ☐ | ☐ | ☐ | ☐ | ☐ |
| C2 | The "Why this prediction?" chart is easy to read. | ☐ | ☐ | ☐ | ☐ | ☐ |
| C3 | The explanations make me trust the predictions more. | ☐ | ☐ | ☐ | ☐ | ☐ |

### D. Intention to use

| # | Statement | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| D1 | I would use this system if the department adopted it. | ☐ | ☐ | ☐ | ☐ | ☐ |
| D2 | I would recommend it to colleagues (or fellow students). | ☐ | ☐ | ☐ | ☐ | ☐ |

### E. Comments

1. What did you find most useful? ______________________________________________
2. What should be improved? ______________________________________________

## Scoring

- **Item score:** the mean (and standard deviation) of the 1–5 answers.
- **Scale score:** the mean of a participant's items in that section (A, B, C or D), averaged across participants.
- **Interpretation:** 4.0–5.0 = high acceptance, 3.0–3.9 = moderate, below 3.0 = low.
- **Reliability (optional):** Cronbach's alpha per scale in SPSS or Excel; 0.70 or above is acceptable.

### Table for Chapter 4 (fill in)

| Scale | Items | Mean | SD | Interpretation |
|---|---|---|---|---|
| Perceived usefulness | A1–A4 | | | |
| Perceived ease of use | B1–B4 | | | |
| Explanation clarity and trust | C1–C3 | | | |
| Intention to use | D1–D2 | | | |

| Task | Completed without help (n of N) |
|---|---|
| 1–7 | |

Report only the answers actually collected, and say how many people took part and who they were.
