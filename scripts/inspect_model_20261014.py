# -*- coding: utf-8 -*-
"""查看模型输出JSON结构"""
import json
f = r'E:\VibeCoding\football\reports\data\20261014_model_001_007.json'
raw = open(f, encoding='utf-8').read()
start = raw.find('{')
d = json.loads(raw[start:])
print('top type:', type(d).__name__)
if isinstance(d, dict):
    print('top keys:', list(d.keys())[:30])
    for k, v in list(d.items())[:3]:
        print('---', k, type(v).__name__)
        if isinstance(v, (dict, list)):
            print(json.dumps(v, ensure_ascii=False)[:800])
elif isinstance(d, list):
    print('len:', len(d))
    print(json.dumps(d[0], ensure_ascii=False)[:1500])
