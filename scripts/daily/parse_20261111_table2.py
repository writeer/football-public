# -*- coding: utf-8 -*-
import json, io

t = io.open(r"c:\Users\admin\.trae-cn\work\.trae\mcp-output\30cbf335-7604-444e-b901-8b968c07ce10.txt", encoding="utf-8").read()
i = t.index('[{"type":"text"')
d = json.loads(json.loads(t[i:])[0]["text"])
for r in d["table"]:
    print(r["position"], r["team"], r["played"], r["goals_for"], r["goals_against"],
          r["avg_total_goals"], r["last_5_form"])
