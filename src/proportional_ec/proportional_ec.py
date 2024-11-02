import csv
import re
from pathlib import Path
from typing import TypeAlias

Year: TypeAlias = int
StatePo: TypeAlias = str
Vote: TypeAlias = int
Candidate: TypeAlias = str


STATE_PO = {
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "district of columbia": "DC",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
}


def process_electoral_college_per_year(path: Path) -> dict[Year, dict[StatePo, Vote]]:
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


def process_candidate_totals(
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


def calculate_quota(ec_votes: Vote, state_total_votes: Vote) -> Vote:
    return state_total_votes // ec_votes


if __name__ == "__main__":
    print(
        process_electoral_college_per_year(
            Path("data/electoral_college/electoral_college.csv")
        )
    )
    print(process_candidate_totals(Path("data/state_votes/1976-2020-president.csv")))
