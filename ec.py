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
        election_results = run_election(
            run_droop_quota_largest_remainder,
            year_candidate_totals[year],
            year_ec_votes[year],
        )
        overall_results = aggregate_election_results(election_results)

        print(year, overall_results)

        topo_file = Path(f"data/topo_data/tiles{year}.topo.json")
        fig_out_path = Path(f"images/{year}_election.png")
        draw_ec_map(
            fig_out_path,
            topo_file,
            year,
            election_results,
            year_candidate_party[year],
        )
