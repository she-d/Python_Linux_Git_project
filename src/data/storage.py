from pathlib import Path
import pandas as pd


def upsert_csv(df: pd.DataFrame, path: str) -> pd.DataFrame:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    if p.exists():
        old = pd.read_csv(p, parse_dates=["timestamp"])
        combined = pd.concat([old, df], ignore_index=True)
    else:
        combined = df.copy()

    combined = (
        combined.drop_duplicates(subset=["timestamp", "asset"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    combined.to_csv(p, index=False)
    return combined
