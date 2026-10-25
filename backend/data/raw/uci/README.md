# UCI Student Performance dataset

Real, public data used as the study's main real-data source. The school's own records were not available.

| Item | Value |
|---|---|
| Name | Student Performance (UCI Machine Learning Repository, id 320) |
| Source page | https://archive.ics.uci.edu/dataset/320/student+performance |
| Downloaded file | `https://archive.ics.uci.edu/static/public/320/student+performance.zip` (40,735 bytes) |
| SHA-256 of download | `82AE9D66437B9808DF42E8C89D2BB179C46E9CFBCF06F38ABC1D20B3B747E177` |
| Downloaded on | 2026-10-18 |
| Licence | Creative Commons Attribution 4.0 International (CC BY 4.0) |
| Files kept | `student-por.csv` (649 students, Portuguese course), `student-mat.csv` (395 students, Mathematics), `student.txt` (attribute descriptions) |
| Separator | semicolon (`;`) |

## Citation

Cortez, P. and Silva, A. M. G. (2008). Using data mining to predict secondary school student performance. In *Proceedings of the 5th Annual Future Business Technology Conference (FUBUTEC 2008)*, Porto, Portugal, pp. 5–12.

Dataset: Cortez, P. (2008). *Student Performance* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5TG7T

## Notes

- The students attended two Portuguese secondary schools (Gabriel Pereira and Mousinho da Silveira).
- Grades `G1`, `G2` and `G3` run from 0 to 20; `G3` is the final grade.
- 382 students appear in both files. The study uses `student-por.csv` as its main file and `student-mat.csv` only as a robustness check, so no student is counted twice in one analysis.
- `ml/uci.py` explains how each field maps to the study's variables.
