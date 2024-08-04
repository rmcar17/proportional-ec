from pathlib import Path

import requests
from bs4 import BeautifulSoup

EC_DATA_PATH = Path("data/electoral_college/electoral_college.csv")
SOURCE_URL = "https://www.270towin.com/state-electoral-vote-history/"


def get_ec_html() -> BeautifulSoup:
    return BeautifulSoup(requests.get(SOURCE_URL, timeout=10).content, "html.parser")


def download_dataset() -> None:
    soup = get_ec_html()
    with EC_DATA_PATH.open("w") as f:
        for entry in soup.find("table").find_all(
            "div",
            attrs={"data-toggle": "tooltip"},
        ):
            ec_total = int(entry.contents[0])
            title = entry["title"]
            year = int(title.split()[-1])
            state = " ".join(title.split()[:-1])
            f.write(f"{state},{year},{ec_total}\n")
