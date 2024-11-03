from pathlib import Path

from proportional_ec.data import (
    load_candidate_totals,
    load_electoral_college_per_year,
)

if __name__ == "__main__":
    print(
        load_electoral_college_per_year(
            Path("data/electoral_college/electoral_college.csv")
        ),
    )
    print(load_candidate_totals(Path("data/state_votes/1976-2020-president.csv")))
