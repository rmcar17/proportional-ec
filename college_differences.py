from pathlib import Path

from proportional_ec.data import load_electoral_college_per_year
from proportional_ec.constants import STATE_PO


if __name__ == "__main__":
    year_ec_votes = load_electoral_college_per_year(
        Path("data/electoral_college/electoral_college.csv"),
    )
    baseline = year_ec_votes[2020]

    previous_years = sorted(year_ec_votes.keys())[::-1][1:]

    with open("format.csv") as f:
        data = [line.strip().split(",") for line in f]

    for year in reversed(list(year_ec_votes.keys())):
        differences = {}
        for state in sorted(year_ec_votes[year]):
            difference = year_ec_votes[year][state] - baseline[state]
            if difference != 0:
                differences[state] = difference
        print(year, differences)
        # with open(f"format_{year}.csv", "w") as f:
        #     for geo_id, _, state in data:
        #         f.write(
        #             f"{geo_id},{year_ec_votes[year][STATE_PO[state.lower()]]},{state}\n",
        #         )
        # baseline = year_ec_votes[year]
        input()
