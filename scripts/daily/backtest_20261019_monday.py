# -*- coding: utf-8 -*-
"""2026-10-19 周一8场回测（规则79基本面口径；008待官方开奖）"""
import json, io, os, re

BASE = r'e:\VibeCoding\football'
PRED = json.load(open(os.path.join(BASE, 'reports/data/20261019_predictions.json'), encoding='utf-8'))
RAW = json.load(open(os.path.join(BASE, 'reports/data/20261019_results_raw.json'), encoding='utf-8-sig'))
RES = {int(r['matchId']): r for r in RAW['value']['matchResult']}
# 008 体彩官方 matchResultStatus=1 未开奖，按用户 2026-10-20 告知补录：半场0-1、全场1-1
MANUAL = {2042080: dict(matchResultStatus='2', sectionsNo1='0:1', sectionsNo999='1:1',
                        matchNumStr='周一008', source='用户告知（体彩官方未开奖）')}
DM = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HM = {'home': '让胜', 'draw': '让平', 'away': '让负'}
HAFU = {('home','home'):'胜胜',('home','draw'):'胜平',('home','away'):'胜负',
        ('draw','home'):'平胜',('draw','draw'):'平平',('draw','away'):'平负',
        ('away','home'):'负胜',('away','draw'):'负平',('away','away'):'负负'}

def res_of(h,a): return 'home' if h>a else ('draw' if h==a else 'away')
def tier(g):
    return '闷战超小球' if g<=1 else ('小球' if g==2 else ('常规正常球' if g==3 else ('大球' if g==4 else ('超大球' if g==5 else '穿盘可能'))))

rows=[]; miss_dir=[]; miss_hhad=[]
t=dict(n=0,dirAll=0,dirFirst=0,dirSecond=0,hhadAll=0,hhadFirst=0,hhadSecond=0,ttg=0,hafu=0,crs=0,ht=0,size=0,kband=0)
pending=[]

for p in PRED:
    mid = int(p['match_id'])
    r = RES.get(mid)
    manual = False
    if (not r or r.get('matchResultStatus') != '2' or not r.get('sectionsNo999')) and mid in MANUAL:
        r = MANUAL[mid]; manual = True
    if not r or r.get('matchResultStatus') != '2' or not r.get('sectionsNo999'):
        pending.append(p['match_num'][-3:])
        rows.append(dict(id=p['match_num'][-3:], league=p['league'], home=p['home'], away=p['away'],
                         conf=p['confidence'], single=bool(p['is_single']), status='pending',
                         reason='体彩官方 matchResultStatus=1，未开奖', result=None))
        continue
    fh,fa = map(int, r['sectionsNo999'].split(':'))
    th,ta = map(int, r['sectionsNo1'].split(':'))
    ad = res_of(fh,fa); ah = HAFU[(res_of(th,ta),ad)]
    line = int(p['hhad_line'])
    # direction
    if ad == p['primary']: ds='✅首'; t['dirFirst']+=1
    elif ad == p['secondary']: ds='✅次'; t['dirSecond']+=1
    else: ds='❌'; miss_dir.append(p['match_num'][-3:])
    if ds!='❌': t['dirAll']+=1
    # handicap
    adj = fh + line
    ha = 'home' if adj>fa else ('draw' if adj==fa else 'away')
    hf = p['hhad_recommend']['first']
    hs = p['hhad_recommend']['second']
    if ha==hf: hstat='✅首'; t['hhadFirst']+=1
    elif ha==hs: hstat='✅次'; t['hhadSecond']+=1
    else: hstat='❌'; miss_hhad.append(p['match_num'][-3:])
    if hstat!='❌': t['hhadAll']+=1
    # ttg
    tg=fh+fa; ttg_actual='7+' if tg>=7 else str(tg)
    ttg_pick=[str(x['goals']) for x in p['ttg_top2']]
    ttg_hit=ttg_actual in ttg_pick
    if ttg_hit: t['ttg']+=1
    # hafu
    hafu_pick=[x['code'] for x in p['hafu_top3']]
    hafu_hit=ah in hafu_pick
    if hafu_hit: t['hafu']+=1
    # crs
    crs_pick=[x['score'] for x in p['score_top5']]
    ft=f'{fh}-{fa}'; crs_hit=ft in crs_pick
    if crs_hit: t['crs']+=1
    # ht
    ht_pick=[x['score'] for x in p['ht_scores_top3']]
    ht=f'{th}-{ta}'; ht_hit=ht in ht_pick
    if ht_hit: t['ht']+=1
    # size
    size_hit=(p['size_tier']['name'].split('(')[0]==tier(tg))
    if size_hit: t['size']+=1
    # k band
    band=[x['score'] for x in p['band_top3']]
    kb=ft in band
    if kb: t['kband']+=1
    t['n']+=1
    rows.append(dict(
        id=p['match_num'][-3:], league=p['league'], home=p['home'], away=p['away'],
        conf=p['confidence'], single=bool(p['is_single']), status='settled', result=dict(ht=ht,ft=ft,line=line),
        source=('用户告知（体彩官方未开奖）' if manual else '体彩官方 getUniformMatchResultV1'),
        had=dict(first=DM[p['primary']],second=DM[p['secondary']],actual=DM[ad],hit=ds,
                 first_prob=p['primary_prob'],second_prob=p['secondary_prob'],actual_prob=p['fused'][ad]),
        hhad=dict(line=line,first=p['hhad_recommend']['first'],second=p['hhad_recommend']['second'],
                  actual=HM[ha],hit=hstat),
        crs=dict(top5=crs_pick,actual=ft,hit=crs_hit,rank=(crs_pick.index(ft)+1 if crs_hit else 0)),
        ttg=dict(pick=ttg_pick,actual=ttg_actual,hit=ttg_hit),
        hafu=dict(top3=hafu_pick,actual=ah,hit=hafu_hit,rank=(hafu_pick.index(ah)+1 if hafu_hit else 0)),
        htScore=dict(top3=ht_pick,actual=ht,hit=ht_hit,rank=(ht_pick.index(ht)+1 if ht_hit else 0)),
        size=dict(tier=p['size_tier']['name'],actual=tier(tg),goals=tg,hit=size_hit),
        k=dict(k_dist=p['k_dist']['value'],k_rec=p['k_rec']['value'],actual=fh-fa,band=band,hit=kb),
    ))

# ---------- 串关（严格按分析报告原始方案） ----------
PARLAYS = [
 ('方向串A（稳健）','方向串',3.08,[('004','had','away'),('008','had','home')]),
 ('方向串B（价值）','方向串',5.68,[('002','had','home'),('004','had','away')]),
 ('方向串C（平局）','方向串',7.80,[('001','had','draw'),('006','had','draw')]),
 ('稳健让球串','让球串',3.45,[('004','hhad','home'),('008','hhad','away')]),
 ('价值让球串','让球串',9.66,[('001','hhad','away'),('005','hhad','away'),('007','hhad','away')]),
 ('连续编号让球串','让球串',2.36,[('002','hhad','home'),('003','hhad','home')]),
 ('半全场串A','混合串',7.74,[('004','hafu','负负'),('008','hafu','胜胜')]),
 ('半全场串B','混合串',9.50,[('002','hafu','胜胜'),('007','hafu','胜胜')]),
 ('方向+半全场A','混合串',4.41,[('004','had','away'),('008','hafu','胜胜')]),
 ('方向+半全场B','混合串',9.97,[('002','had','home'),('004','hafu','负负')]),
 ('混合串C（连续编号）','混合串',8.31,[('001','had','draw'),('002','had','home')]),
 ('混合串D（连续编号）','混合串',6.74,[('003','had','home'),('004','had','away')]),
 ('总进球串A','总进球串',32.22,[('002','ttg','2'),('003','ttg','2'),('008','ttg','2')]),
 ('总进球串B','总进球串',32.06,[('001','ttg','2'),('004','ttg','2'),('006','ttg','2')]),
 ('连续编号总进球串①','总进球串',12.51,[('001','ttg','1'),('002','ttg','2')]),
 ('连续编号总进球串②','总进球串',10.52,[('003','ttg','2'),('004','ttg','2')]),
 ('高赔半全场串A','高赔半全场串',43.34,[('001','hafu','平负'),('006','hafu','平平'),('008','hafu','胜胜')]),
 ('高赔半全场串B','高赔半全场串',34.20,[('002','hafu','胜胜'),('004','hafu','负负'),('007','hafu','胜胜')]),
 ('连续编号高赔半全场串①','高赔半全场串',26.60,[('001','hafu','平负'),('002','hafu','胜胜')]),
 ('连续编号高赔半全场串②','高赔半全场串',7.02,[('004','hafu','负负'),('005','hafu','胜胜')]),
 ('半全场混合A','半全场混合',18.20,[('001','hafu','平负'),('008','ttg','2')]),
 ('半全场混合B','半全场混合',20.43,[('002','hafu','胜胜'),('007','ttg','1')]),
 ('连续编号混合总进球①','半全场混合',17.60,[('003','hafu','胜胜'),('004','ttg','2')]),
 ('连续编号混合总进球②','半全场混合',5.75,[('005','hafu','胜胜'),('006','ttg','2')]),
 ('稳健比分串','比分串',57.00,[('004','crs','0-1'),('008','crs','1-0')]),
 ('搏冷比分串','比分串',20.00,[('005','crs','1-1')]),
 ('连续编号比分串①','比分串',51.30,[('001','crs','1-1'),('002','crs','1-0')]),
 ('连续编号比分串②','比分串',68.88,[('003','crs','1-0'),('004','crs','0-1')]),
 ('单挑比分①','比分串',9.50,[('004','crs','0-1')]),
 ('单挑比分②','比分串',9.00,[('001','crs','0-0')]),
]
for x in rows:
    x['_hafu'] = x.get('hafu',{}).get('actual')
    x['_ft'] = x.get('result',{}).get('ft') if x.get('result') else None
    x['_tg'] = (int(x['result']['ft'].split('-')[0])+int(x['result']['ft'].split('-')[1])) if x.get('result') else None
    x['_had'] = None
    if x.get('result'):
        fh,fa=map(int,x['result']['ft'].split('-')); x['_had']=res_of(fh,fa)
        x['_hhad'] = 'home' if fh+int(x['hhad']['line'])>fa else ('draw' if fh+int(x['hhad']['line'])==fa else 'away')
B={x['id']:x for x in rows}
parlay_rows=[]; cat={}
for name,typ,odds,legs in PARLAYS:
    stat='✅'; pending_leg=False; detail=[]; leg_results=[]; leg_hits=[]
    for mid,pool,key in legs:
        x=B[mid]
        if x['status']!='settled': stat='⏳'; pending_leg=True; detail.append(f'{mid}待开奖'); leg_results.append('待开奖'); leg_hits.append(None); continue
        if pool=='had': ok=(x['_had']==key); act=DM[x['_had']]
        elif pool=='hhad': ok=(x['_hhad']==key); act=HM[x['_hhad']]
        elif pool=='ttg': ok=(str(x['_tg'])==key or (key=='7+' and x['_tg']>=7)); act=str(x['_tg'])
        elif pool=='hafu': ok=(x['_hafu']==key); act=x['_hafu']
        elif pool=='crs': ok=(x['_ft']==key); act=x['_ft']
        if not ok: stat='❌'
        detail.append(f'{mid} {act}{"✓" if ok else "✗"}'); leg_results.append(act); leg_hits.append(ok)
    if stat!='❌' and pending_leg: stat='⏳'
    parlay_rows.append(dict(name=name,type=typ,odds=odds,odds_est=odds,legs=legs,
                            matches=[l[0] for l in legs],results=leg_results,leg_hits=leg_hits,
                            hit=stat,detail=detail))
    c=cat.setdefault(typ,[0,0,0])  # hit, settled, pending
    if stat=='✅': c[0]+=1; c[1]+=1
    elif stat=='❌': c[1]+=1
    else: c[2]+=1

summary=dict(n_settled=t['n'],pending=len(pending),
 direction_all=f"{t['dirAll']}/{t['n']}",direction_first=f"{t['dirFirst']}/{t['n']}",
 direction_second=t['dirSecond'],hhad_all=f"{t['hhadAll']}/{t['n']}",hhad_first=f"{t['hhadFirst']}/{t['n']}",
 hhad_second=t['hhadSecond'],ttg=f"{t['ttg']}/{t['n']}",hafu=f"{t['hafu']}/{t['n']}",
 crs=f"{t['crs']}/{t['n']}",ht=f"{t['ht']}/{t['n']}",size=f"{t['size']}/{t['n']}",kband=f"{t['kband']}/{t['n']}",
 parlay_hit=sum(1 for p in parlay_rows if p['hit']=='✅'),parlay_settled=sum(1 for p in parlay_rows if p['hit']!='⏳'),
 parlay_pending=sum(1 for p in parlay_rows if p['hit']=='⏳'))
out=dict(backtest_id='20261019_monday',date='2026-10-19',day='周一',ticket_id='261019',
 result_source='体彩官方 getUniformMatchResultV1（matchBeginDate=2026-10-19&matchEndDate=2026-10-20）；7场官方结算，008官方matchResultStatus=1，按用户2026-10-20告知补录（半场0-1/全场1-1）',
 summary=summary,rows=rows,misses=dict(direction=miss_dir,hhad=miss_hhad),parlays=parlay_rows,parlay_categories=cat)
os.makedirs(os.path.join(BASE,'memory/backtests/20261019_monday'),exist_ok=True)
json.dump(out,io.open(os.path.join(BASE,'reports/data/20261019_backtest_computed.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
json.dump(out,io.open(os.path.join(BASE,'memory/backtests/20261019_monday/backtest.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(json.dumps(summary,ensure_ascii=False,indent=1))
print('miss_dir',miss_dir,'miss_hhad',miss_hhad,'pending',pending)
for p in parlay_rows: print(p['hit'],p['name'],p['odds'],'|','; '.join(p['detail']))
print('categories',cat)
