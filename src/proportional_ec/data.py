import csv
from pathlib import Path

from proportional_ec.constants import STATE_PO
from proportional_ec.typing import Candidate, StatePo, Vote, Year


def load_electoral_college_per_year(path: Path) -> dict[Year, dict[StatePo, Vote]]:
    year_state_ev = {}
    with path.open() as f:
        for line in f:
            state, year, votes = line.strip().split(",")
            year = int(year)
            votes = int(votes)
            po = STATE_PO[state.lower()]

            if year not in year_state_ev:
                year_state_ev[year] = {}
            year_state_ev[year][po] = votes

    return year_state_ev


def load_candidate_totals(
    path: Path,
) -> tuple[
    dict[Year, dict[StatePo, dict[Candidate, Vote]]],
    dict[Year, dict[StatePo, dict[Candidate, Vote]]],
]:
    year_state_cand_votes = {}
    year_state_total_votes = {}
    with path.open() as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            (
                year,
                state,
                po,
                fips,
                cen,
                ic,
                office,
                candidate,
                p_detailed,
                writein,
                votes,
                total,
                version,
                notes,
                simplified,
            ) = row
            year = int(year)
            votes = int(votes)
            total = int(total)
            if year not in year_state_cand_votes:
                year_state_cand_votes[year] = {}
                year_state_total_votes[year] = {}

            if po not in year_state_cand_votes[year]:
                year_state_cand_votes[year][po] = {}
                year_state_total_votes[year][po] = total

            if year_state_total_votes[year][po] != total:
                msg = "Different vote totals"
                raise ValueError(msg)

            year_state_cand_votes[year][po][candidate] = votes
        return year_state_cand_votes, year_state_total_votes
