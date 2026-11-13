# -*- coding: utf-8 -*-
"""解析 japan1 2026-2027 积分榜：取 8 支球队攻防强度 + 联赛均值。"""
import json, io, re, pathlib

p = pathlib.Path(r"c:\Users\admin\.trae-cn\work\.trae\mcp-output\30cbf335-7604-444e-b901-8b968c07ce10.txt")
t = io.open(p, encoding="utf-8").read()
i = t.index('[{"type":"text"')
arr = json.loads(t[i:])
data = json.loads(arr[0]["text"])
table = data["table"]

targets = ["Yokohama F. Marinos", "Kashima Antlers", "Vissel Kobe", "Machida Zelvia",
           "Kawasaki Frontale", "Kashiwa Reysol", "Urawa Reds", "Cerezo Osaka"]

tot_gf = sum(r["goals_for"] for r in table)
tot_ga = sum(r["goals_against"] for r in table)
tot_p = sum(r["played"] for r in table)
print("teams", len(table), "played_sum", tot_p, "gf", tot_gf, "ga", tot_ga)
print("league avg goals/team/match: %.3f" % (tot_gf / tot_p))

for r in table:
    if r["team"] in targets:
        print(json.dumps({k: r[k] for k in ["team", "position", "played", "won", "drawn", "lost",
                                            "goals_for", "goals_against", "avg_goals_scored",
                                            "avg_goals_conceded", "avg_total_goals", "home_goals_avg",
                                            "away_goals_avg", "last_5_form", "over_25_percentage",
                                            "clean_sheets", "failed_to_score"]}, ensure_ascii=False))
