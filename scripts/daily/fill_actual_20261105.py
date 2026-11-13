import json
import pathlib

BASE = pathlib.Path(r"e:\VibeCoding\football")
SUMMARY = BASE / "reports" / "data" / "20261105_backtest_summary.json"
TARGETS = [
    BASE / "reports" / "data" / "20261105_predictions_final.json",
    BASE / "memory" / "predictions" / "20261105_thursday" / "prediction.json",
]

SOURCE_SETTLED = "体彩官方 getUniformMatchResultV1（sectionsNo999/sectionsNo1）"
SOURCE_PENDING = "体彩官方 getUniformMatchResultV1（sectionsNo999 为空，待结算）"

summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
rows = {r["num"]: r for r in summary["rows"]}

written = 0
for target in TARGETS:
    data = json.loads(target.read_text(encoding="utf-8"))
    for match in data:
        row = rows.get(match.get("num"))
        if not row:
            continue
        if row.get("status") == "pending":
            match["actual"] = {
                "score": None,
                "ht_score": None,
                "direction": None,
                "handicap": None,
                "total_goals": None,
                "hafu": None,
                "ou": None,
                "single_api": row.get("single_api", 0),
                "settled": False,
                "source": SOURCE_PENDING,
            }
            match["backtest"] = None
        else:
            a = row["actual"]
            match["actual"] = {
                "score": a["score"],
                "ht_score": a["ht"],
                "direction": a["had"],
                "handicap": a["hc"],
                "total_goals": a["goals"],
                "hafu": a["hafu"],
                "ou": a["ou"],
                "single_api": a["single_api"],
                "settled": True,
                "source": SOURCE_SETTLED,
            }
            match["backtest"] = {
                "had_primary": row["had_primary"],
                "had_cover": row["had_combined"],
                "hc_primary": row["hc_primary"],
                "hc_cover": row["hc_combined"],
                "score_top5": row["cr_top5"],
                "ttg_top2": row["ttg_top2"],
                "hafu_top3": row["hafu_top3"],
                "ht_top3": row["ht_top3"],
                "tier": row["tier_hit"],
                "ou": row["ou_hit"],
            }
        written += 1
    target.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"updated {target}")

print(f"rows injected: {written}")
