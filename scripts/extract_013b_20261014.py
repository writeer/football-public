# -*- coding: utf-8 -*-
"""提取013场登记字段（列表结构）"""
import json
f = r'E:\VibeCoding\football\reports\data\20261014_model_008_014.json'
raw = open(f, encoding='utf-8').read()
d = json.loads(raw[raw.find('{'):])
for x in d['matches']:
    if abs(x['lambda_total'] - 1.6) < 0.01 and x['lh'] == 0.8:
        print(json.dumps(x, ensure_ascii=False, indent=1))
        break
