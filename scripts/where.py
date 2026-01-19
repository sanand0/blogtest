#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pandas>=2.2"]
# ///
from pathlib import Path
import re
import pandas as pd


def update_travel_schedule() -> None:
    """Update where.md travel schedule (2023+) from ~/Dropbox/Travel/travel.csv."""

    df = pd.read_csv(Path.home() / "Dropbox" / "Travel" / "travel.csv")
    df["Date"] = pd.to_datetime(df["Date"], format="%d-%b-%y")
    df = df.sort_values("Date", ascending=False)
    df = df[df["Date"].dt.year >= 2023]
    md = "\n".join(f"- {d.strftime('%a %d %b %Y')}: {to}" for d, to in zip(df["Date"], df["To"]))

    where_path = Path("pages") / "where.md"
    source = where_path.read_text()
    pattern = r"(<!-- +TRAVELSTART +-->)(.*?)(<!-- +TRAVELEND +-->)"
    updated, count = re.subn(pattern, rf"\1\n\n{md}\n\n\3", source, flags=re.DOTALL)
    where_path.write_text(updated)


if __name__ == "__main__":
    update_travel_schedule()
