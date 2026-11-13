import json

with open(r'C:\Users\admin\AppData\Local\Temp\trae\toolcall-output\ace8f0d2-8ae3-43ee-adf1-e5e9518de87a.txt', 'r', encoding='utf-8') as f:
    raw = f.read()

# Find the JSON in the text field
text_start = raw.find('"text":"')
if text_start != -1:
    text_start += len('"text":"')
    remaining = raw[text_start:]
    end_idx = remaining.rfind('"}]')
    if end_idx != -1:
        json_str = remaining[:end_idx]
        json_str = json_str.replace('\\"', '"').replace('\\n', '\n')
        data = json.loads(json_str)
        
        for m in data['matches']:
            print(f'\n{"="*80}')
            print(f'{m["matchNumStr"]} | {m["league"]["abbName"]}({m["league"]["code"]}) | {m["home"]["abbName"]}({m["home"]["rank"]}) vs {m["away"]["abbName"]}({m["away"]["rank"]}) | {m["matchTime"]}')
            print(f'matchId={m["matchId"]}, date={m["matchDate"]}')
            
            # HAD
            had = m.get('markets', {}).get('had', {})
            if had and had.get('outcomes'):
                h_odds = had['outcomes'][0]['odds']
                d_odds = had['outcomes'][1]['odds']
                a_odds = had['outcomes'][2]['odds']
                h_nv = had['outcomes'][0].get('noVigProb', 0)
                d_nv = had['outcomes'][1].get('noVigProb', 0)
                a_nv = had['outcomes'][2].get('noVigProb', 0)
                print(f'HAD: {h_odds}/{d_odds}/{a_odds} | noVig: {h_nv:.1%}/{d_nv:.1%}/{a_nv:.1%} | ret={had.get("returnRate","?")}')
            
            # HHAD
            hhad = m.get('markets', {}).get('hhad', {})
            if hhad and hhad.get('outcomes'):
                gl = hhad.get('goalLine', '?')
                h_odds = hhad['outcomes'][0]['odds']
                d_odds = hhad['outcomes'][1]['odds']
                a_odds = hhad['outcomes'][2]['odds']
                print(f'HHAD: 让球{gl} | {h_odds}/{d_odds}/{a_odds}')
            
            # CRS - top 5
            crs = m.get('markets', {}).get('crs', {})
            if crs and crs.get('outcomes'):
                sorted_crs = sorted(crs['outcomes'], key=lambda x: x.get('noVigProb', 0), reverse=True)
                print(f'CRS TOP5: ', end='')
                for o in sorted_crs[:5]:
                    print(f'{o["labelZh"]}({o["odds"]}/{o.get("noVigProb",0):.1%}) ', end='')
                print()
            
            # TTG
            ttg = m.get('markets', {}).get('ttg', {})
            if ttg and ttg.get('outcomes'):
                sorted_ttg = sorted(ttg['outcomes'], key=lambda x: x.get('noVigProb', 0), reverse=True)
                print(f'TTG TOP5: ', end='')
                for o in sorted_ttg[:5]:
                    print(f'{o["labelZh"]}({o["odds"]}/{o.get("noVigProb",0):.1%}) ', end='')
                print()
            
            # HAFU
            hafu = m.get('markets', {}).get('hafu', {})
            if hafu and hafu.get('outcomes'):
                sorted_hafu = sorted(hafu['outcomes'], key=lambda x: x.get('noVigProb', 0), reverse=True)
                print(f'HAFU TOP5: ', end='')
                for o in sorted_hafu[:5]:
                    print(f'{o["labelZh"]}({o["odds"]}/{o.get("noVigProb",0):.1%}) ', end='')
                print()
        
        print(f'\n\nTotal: {data["matchCount"]} matches')
