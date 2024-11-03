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
) -> dict[Year, dict[StatePo, dict[Candidate, Vote]]]:
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

            if candidate == "":
                candidate = p_detailed
                if candidate == "":
                    if writein == "TRUE":
                        candidate = "write in"
                    elif writein == "NA":
                        candidate = "unknown"
                    else:
                        print(year, state, po, candidate, p_detailed, writein)
                        msg = "Not sufficient information for candidate."
                        raise ValueError(msg)
            if year not in year_state_cand_votes:
                year_state_cand_votes[year] = {}
                year_state_total_votes[year] = {}

            if po not in year_state_cand_votes[year]:
                year_state_cand_votes[year][po] = {}
                year_state_total_votes[year][po] = total

            if year_state_total_votes[year][po] != total:
                msg = "Different vote totals"
                raise ValueError(msg)

            if candidate not in year_state_cand_votes[year][po]:
                year_state_cand_votes[year][po][candidate] = votes
            else:
                # Some entries include candidates running for multiple parties
                # e.g. Gerald Ford 1976 New York (Republican+Conservative)
                year_state_cand_votes[year][po][candidate] += votes

        for year in year_state_total_votes:
            for state in year_state_total_votes[year]:
                if (
                    sum(year_state_cand_votes[year][state].values())
                    != year_state_total_votes[year][state]
                ):
                    msg = "Votes for candidates do not sum to total votes."
                    raise ValueError(msg)
                for invalid_candidate in [
                    "UNDERVOTES",
                    "OVERVOTES",
                    "unknown",
                    "BLANK VOTE/SCATTERING",
                    "BLANK VOTE",
                    "OVER VOTE",
                ]:
                    if invalid_candidate in year_state_cand_votes[year][state]:
                        del year_state_cand_votes[year][state][invalid_candidate]
        return year_state_cand_votes
