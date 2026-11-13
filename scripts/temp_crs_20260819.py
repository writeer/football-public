# -*- coding: utf-8 -*-
import json
raw = open(r"C:\Users\admin\AppData\Local\Temp\trae\toolcall-output\f8c26ce4-932a-4018-84b2-21db0420eae5.txt", encoding="utf-8").read()
s = raw.split("The MCP server responded with: ", 1)[1].strip()
data = json.loads(json.loads(s)[0]["text"])
want = {"周三001": ["1:1","0:1","0:0","1:0","1:2","2:1","2:2"],
        "周三002": ["2:0","1:0","3:0","1:1","0:0","2:1","3:1"],
        "周三003": ["1:1","0:0","0:1","1:0","1:2","2:1","2:0"],
        "周三006": ["1:1","2:0","1:0","2:1","0:0","3:0","3:1"],
        "周三007": ["1:1","1:2","0:1","2:1","0:2","1:3","2:2"],
        "周三008": ["1:1","1:0","2:0","2:1","0:0","3:0","3:1"]}
for m in data["matches"]:
    k = m["matchNumStr"]
    if k not in want:
        continue
    crs = {o["labelZh"]: o["odds"] for o in m["markets"]["crs"]["outcomes"]}
    print(k, " | ".join("{}@{}".format(x, crs.get(x, "?")) for x in want[k]))
