"""Rebuild every dataset, table and figure the study's data section uses.

Run from the backend folder:  python -m ml.prepare_data
The same seed always produces the same files.
"""
import numpy as np

from . import cleaning, config, eda, simulate, uci


def main():
    for folder in (config.SIMULATED_DIR, config.PROCESSED_DIR, config.FIGURES_DIR, config.TABLES_DIR):
        folder.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(config.SEED)
    history, current, directory = simulate.simulate_cohorts(rng)
    raw = simulate.add_record_keeping_noise(history, rng)
    raw.to_csv(config.SIM_RAW_CSV, index=False)
    current.to_csv(config.SIM_CURRENT_CSV, index=False)
    directory.to_csv(config.SIM_DIRECTORY_CSV, index=False)
    clean, log = cleaning.clean_records(raw)
    clean.to_csv(config.SIM_CLEAN_CSV, index=False)

    prepared = {}
    for course in ("por", "mat"):
        prepared[course] = uci.prepare(uci.load_raw(course), course)
        prepared[course].to_csv(config.UCI_PREPARED_CSV[course], index=False)

    outputs = eda.run(clean, prepared["por"], log)

    print(f"Simulated raw export:  {len(raw):,} records -> {config.SIM_RAW_CSV.relative_to(config.PROJECT_DIR)}")
    print(f"Simulated clean data:  {len(clean):,} records, {clean['student_code'].nunique():,} students"
          f" -> {config.SIM_CLEAN_CSV.relative_to(config.PROJECT_DIR)}")
    print(f"Current semester:      {len(current):,} records (2025/2026 first semester, before exams)"
          f" -> {config.SIM_CURRENT_CSV.relative_to(config.PROJECT_DIR)}")
    print(f"Demo directory:        {len(directory):,} fictional students"
          f" -> {config.SIM_DIRECTORY_CSV.relative_to(config.PROJECT_DIR)}")
    for course, df in prepared.items():
        print(f"UCI {course} prepared:      {len(df):,} students -> "
              f"{config.UCI_PREPARED_CSV[course].relative_to(config.PROJECT_DIR)}")
    print(f"Tables and figures:    {len(outputs)} files in {config.REPORTS_DIR.relative_to(config.PROJECT_DIR)}")
    for step in log:
        print(f"  {step['step']}: {step['records_affected']:,} (remaining {step['records_remaining']:,})")


if __name__ == "__main__":
    main()
