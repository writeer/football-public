# -*- coding: utf-8 -*-
"""解析2026-10-14体彩比赛数据概要"""
import json, io, sys

raw = open(r'E:\VibeCoding\football\reports\data\20261014_matches_raw.json', encoding='utf-8').read()
start = raw.find('{')
data = json.loads(raw[start:])
print('updatedAt:', data['data']['updatedAt'])
print('matchCount:', data['data']['matchCount'])
for m in data['data']['matches']:
    had = m['markets'].get('had', {})
    hhad = m['markets'].get('hhad', {})
    had_o = {o['code']: o['odds'] for o in had.get('outcomes', [])}
    hhad_o = {o['code']: o['odds'] for o in hhad.get('outcomes', [])}
    print('%s %s %s %svs%s 单关=%s HAD=%s HHAD=%s gl=%s' % (
        m['matchNumStr'], m['matchTime'], m['league']['abbName'],
        m['home']['abbName'], m['away']['abbName'], m['bettingSingle'],
        had_o, hhad_o, hhad.get('goalLine')))
