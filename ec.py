from pathlib import Path

from proportional_ec.data import (
    load_candidate_totals_and_parties,
    load_electoral_college_per_year,
)
from proportional_ec.draw import draw_ec_map
from proportional_ec.election import run_election
from proportional_ec.election_method import run_droop_quota_largest_remainder
from proportional_ec.summarise import aggregate_election_results

if __name__ == "__main__":
    year_ec_votes = load_electoral_college_per_year(
        Path("data/electoral_college/electoral_college.csv"),
    )
    year_candidate_totals, year_candidate_party = load_candidate_totals_and_parties(
        Path("data/state_votes/1976-2020-president.csv"),
    )

    for year in year_candidate_totals:
        # year = 2020

        election_results = run_election(
            run_droop_quota_largest_remainder,
            year_candidate_totals[year],
            year_ec_votes[2020],
        )
        overall_results = aggregate_election_results(election_results)

        print(year, overall_results)

        topo_file = Path(f"data/topo_data/tiles{2020}.topo.json")
        draw_ec_map(topo_file, election_results, year_candidate_party[year])
        # break
