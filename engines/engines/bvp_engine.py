import pandas as pd
import baseball_scraper as bs

def get_bvp_history(pitcher_name: str, batter_name: str):
    """
    Safest, smoothest BvP engine:
    - Returns PA, AB, H, HR, K, BB, AVG, SLG, OPS
    - Returns empty DataFrame if no history exists
    """

    try:
        df = bs.bvp(pitcher_name, batter_name)

        if df.empty:
            return pd.DataFrame()

        # Clean columns
        df = df.rename(columns={
            "PA": "Plate Appearances",
            "AB": "At Bats",
            "H": "Hits",
            "HR": "Home Runs",
            "K": "Strikeouts",
            "BB": "Walks",
            "AVG": "Batting Avg",
            "SLG": "Slugging",
            "OPS": "OPS"
        })

        return df

    except Exception:
        return pd.DataFrame()
