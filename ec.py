from pathlib import Path

from proportional_ec.proportional_ec import (
    process_candidate_totals,
    process_electoral_college_per_year,
)

if __name__ == "__main__":
    print(
        process_electoral_college_per_year(
            Path("data/electoral_college/electoral_college.csv")
        ),
    )
    print(process_candidate_totals(Path("data/state_votes/1976-2020-president.csv")))
