# -*- coding: utf-8 -*-
"""规则76：为联赛知识库JSON批量补充 cross_league_level / competition_tier 字段（2026-10-14）
- 国内联赛JSON：league_info 新增 cross_league_level（L1-L4）
- 国际赛事JSON：league_info 新增 competition_tier（1-6）+ cross_league_level=null
只新增字段，不改动已有内容；幂等（已存在则跳过）。
"""
import json, os

BASE = r"E:\VibeCoding\football\memory\leagues"

# 国内联赛 → L档（规则76分档表）
LEAGUE_TIER = {
    "premier_league_en.json": "L1",
    "la_liga_es.json": "L1",
    "serie_a_it.json": "L1",
    "bundesliga_de.json": "L1",
    "ligue_1_fr.json": "L1",
    "eredivisie_nl.json": "L2",
    "primeira_liga_pt.json": "L2",
    "pro_league_be.json": "L2",
    "super_lig_tr.json": "L2",
    "rpl_ru.json": "L2",
    "bundesliga_at.json": "L3",
    "allsvenskan_se.json": "L3",
    "eliteserien_no.json": "L3",
    "superliga_dk.json": "L3",
    "super_league_gr.json": "L3",
    "serie_a_br.json": "L3",
    "liga_profesional_ar.json": "L3",
    "liga_mx_mx.json": "L3",
    "mls_us.json": "L3",
    "j_league_jp.json": "L3",
    "k_league_kr.json": "L3",
    "pro_league_sa.json": "L3",
    "a_league_au.json": "L3",
    "efl_championship_en.json": "L4",
    "ligue_2_fr.json": "L4",
    "2_bundesliga_de.json": "L4",
    "eerste_divisie_nl.json": "L4",
    "j2_league_jp.json": "L4",
}

# 国际赛事 → 赛事档（规则76 Step1；1最高）
COMPETITION_TIER = {
    "champions_league.json": 1,
    "europa_league.json": 2,
    "super_cup_uefa.json": 2,   # 欧超杯≈欧联档
    "acl_elite.json": 3,        # 亚冠精英
    "copa_libertadores.json": 4,
    "nations_league.json": 5,
    "asian_games.json": 6,
    # 国内杯赛/友谊赛：不适用跨联赛等级判定（同联赛内战或非正式赛事）
    "efl_cup_en.json": None,
    "kfa_cup_kr.json": None,
    "international_friendly.json": None,
}

changed = []
for fn in sorted(os.listdir(BASE)):
    if not fn.endswith(".json"):
        continue
    path = os.path.join(BASE, fn)
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    li = d.setdefault("league_info", {})
    if fn in LEAGUE_TIER:
        tier = LEAGUE_TIER[fn]
        if "cross_league_level" not in li:
            li["cross_league_level"] = tier
            li["cross_league_level_note"] = "规则76跨联赛等级判定分档（L1欧洲顶级/L2欧洲强二级/L3中二级/L4次级），2026-10-14建立"
            changed.append(f"{fn}: +cross_league_level={tier}")
        else:
            changed.append(f"{fn}: 已存在，跳过")
    elif fn in COMPETITION_TIER:
        t = COMPETITION_TIER[fn]
        if "competition_tier" not in li:
            li["competition_tier"] = t
            li["cross_league_level"] = None
            li["competition_tier_note"] = "规则76赛事本身等级（1欧冠精英/2欧联欧协联/3亚冠精英/4解放者杯/5欧国联/6亚运会；None=不适用），2026-10-14建立"
            changed.append(f"{fn}: +competition_tier={t}")
        else:
            changed.append(f"{fn}: 已存在，跳过")
    # 写回文件（保持缩进格式与原文件一致；均以4空格缩进写入）
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=4)
        f.write("\n")

with open(os.path.join(BASE, "_rule76_tier_log.md"), "w", encoding="utf-8") as f:
    f.write("# 规则76 分档字段批量落地记录（2026-10-14）\n\n")
    f.write("## 国内联赛 cross_league_level\n\n")
    for k, v in sorted(LEAGUE_TIER.items()):
        f.write(f"- {k} → {v}\n")
    f.write("\n## 国际赛事 competition_tier\n\n")
    for k, v in sorted(COMPETITION_TIER.items()):
        f.write(f"- {k} → {v}\n")

print(f"共处理 {len(changed)} 个文件：")
for c in changed:
    print(" ", c)
