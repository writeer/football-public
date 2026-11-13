# -*- coding: utf-8 -*-
"""提取013场登记字段"""
import json
f = r'E:\VibeCoding\football\reports\data\20261014_model_008_014.json'
raw = open(f, encoding='utf-8').read()
d = json.loads(raw[raw.find('{'):])
matches = d['matches']
if isinstance(matches, dict):
    m = matches.get('013')
elif isinstance(matches, list):
    m = None
    for x in matches:
        if str(x.get('match_num', x.get('matchNumStr', ''))).replace('周三', '') == '013':
            m = x
            break
print(json.dumps(m, ensure_ascii=False, indent=1)[:4000])
