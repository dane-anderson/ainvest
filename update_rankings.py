from allocation_engine import get_ranked_candidates
from database import get_engine
from datetime import datetime

# Generate rankings
ranked = get_ranked_candidates(
    risk_budget="Medium",
    top_n=100
)

# Save CSV backup
ranked.to_csv(
    "data/ranked_candidates.csv",
    index=False
)



# Save to database
engine = get_engine()

ranked["Last_Updated"] = datetime.utcnow()

ranked.to_sql(
    "ranked_candidates",
    engine,
    if_exists="replace",
    index=False
)

print("Saved ranked candidates to database")

print(
    ranked[
        ["Ticker", "AInvest_Score"]
    ].head(10)
)