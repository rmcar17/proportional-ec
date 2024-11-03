from pathlib import Path

from proportional_ec.data import (
    load_candidate_totals,
    load_electoral_college_per_year,
)
from proportional_ec.election import run_election
from proportional_ec.election_method import run_droop_quota_largest_remainder
from proportional_ec.summarise import aggregate_election_results

if __name__ == "__main__":
    year_ec_votes = load_electoral_college_per_year(
        Path("data/electoral_college/electoral_college.csv"),
    )
    year_candidate_totals = load_candidate_totals(
        Path("data/state_votes/1976-2020-president.csv"),
    )

    for year in year_candidate_totals:
        election_results = run_election(
            run_droop_quota_largest_remainder,
            year_candidate_totals[year],
            year_ec_votes[year],
        )

        print(year, aggregate_election_results(election_results))
