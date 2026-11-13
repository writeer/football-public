# -*- coding: utf-8 -*-
"""261014 周三 模型计算 001-007 —— DC矩阵/双轨众数/让球三方向/规则66半全场/Shin融合"""
import math, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def pois(k, lam):
    return math.exp(-lam) * lam**k / math.factorial(k)

def dc_adj(i, j, lh, la, rho=0.13):
    if i == 0 and j == 0: return 1 - rho*lh
    if i == 0 and j == 1: return 1 + rho*lh
    if i == 1 and j == 0: return 1 + rho*la
    if i == 1 and j == 1: return 1 - rho*la
    return 1.0

# num, home, away, lh, la, goalLine, ht_coeff, note
M = [
 ('周三001','墨尔本胜利','首尔FC',1.30,0.88,-1,0.40,'AC2杯赛软0.40;ACL主场1.15'),
 ('周三002','神户胜利船','全北现代',1.42,0.85,-1,0.40,'ACL东亚双谨慎;神户强主场'),
 ('周三003','柏太阳神','曼谷港务',2.30,0.62,-2,0.40,'ACL深盘规则65+0.35'),
 ('周三004','横滨水手','清水鼓动',1.18,1.08,-1,0.38,'JLC日职ht0.534高'),
 ('周三005','费耶诺德','科莫',1.08,1.52,+1,0.45,'UCL标准'),
 ('周三006','LASK林茨','利物浦',0.82,2.70,+1,0.45,'UCL标准'),
 ('周三007','诺维奇','南安普敦',1.25,1.10,-1,0.38,'ED1英冠ht0.425高'),
]

N = 16  # 矩阵阶数 n>=16 强制

def build(lh, la, n=N):
    Mx = [[0.0]*(n+1) for _ in range(n+1)]
    tot = 0.0
    for i in range(n+1):
        for j in range(n+1):
            p = pois(i,lh)*pois(j,la)*dc_adj(i,j,lh,la)
            Mx[i][j] = p; tot += p
    for i in range(n+1):
        for j in range(n+1):
            Mx[i][j] /= tot
    return Mx

def had(Mx):
    h=d=a=0.0
    for i in range(len(Mx)):
        for j in range(len(Mx)):
            if i>j: h+=Mx[i][j]
            elif i==j: d+=Mx[i][j]
            else: a+=Mx[i][j]
    return h,d,a

def net_dist(Mx):
    # k = i-j, range -n..+n, per-k independent, NO tail merging
    n=len(Mx)-1
    d={}
    for i in range(n+1):
        for j in range(n+1):
            k=i-j
            d[k]=d.get(k,0.0)+Mx[i][j]
    return d

def ttg(Mx):
    n=len(Mx)-1; t={}
    for i in range(n+1):
        for j in range(n+1):
            g=i+j; t[g]=t.get(g,0.0)+Mx[i][j]
    return t

results={}
for num,home,away,lh,la,gl,htc,note in M:
    Mx=build(lh,la)
    h,d,a=had(Mx)
    nd=net_dist(Mx)
    tt=ttg(Mx)
    # k_dist unconditional mode
    kd=max(nd.items(), key=lambda x:x[1])
    # HAD first direction
    dirs={'h':h,'d':d,'a':a}
    first=max(dirs,key=lambda x:dirs[x])
    # k_rec within direction interval
    if first=='h': cand={k:v for k,v in nd.items() if k>=1}
    elif first=='a': cand={k:v for k,v in nd.items() if k<=-1}
    else: cand={0:nd.get(0,0)}
    kr=max(cand.items(), key=lambda x:x[1])
    # in-band candidates fixed k_rec
    krec=kr[0]
    band=[]
    for i in range(N+1):
        j=i-krec
        if 0<=j<=N:
            band.append((i,j,Mx[i][j]))
    band.sort(key=lambda x:-x[2])
    band_top=band[:3]
    # CRS top5
    crs=[(i,j,Mx[i][j]) for i in range(N+1) for j in range(N+1)]
    crs.sort(key=lambda x:-x[2])
    crs_top=crs[:6]
    # TTG top
    tt_sorted=sorted(tt.items(),key=lambda x:-x[1])
    t6=sum(v for g,v in tt.items() if g>=6)
    # handicap: adjusted net = net + goalLine
    hc={'让胜':0.0,'让平':0.0,'让负':0.0}
    for k,v in nd.items():
        adj=k+gl
        if adj>0: hc['让胜']+=v
        elif adj==0: hc['让平']+=v
        else: hc['让负']+=v
    # half matrix
    hlh,hla=lh*htc,la*htc
    hM=build(hlh,hla,n=8)
    hh,hd,ha=had(hM)
    # half score top3
    hcrs=[(i,j,hM[i][j]) for i in range(9) for j in range(9)]
    hcrs.sort(key=lambda x:-x[2])
    hcrs_top=hcrs[:3]
    # HAFU joint = P(half res)*P(full res) approx independence
    hres={'h':hh,'d':hd,'a':ha}
    fres={'h':h,'d':d,'a':a}
    hafu={}
    for hr in 'hda':
        for fr in 'hda':
            hafu[hr+fr]=hres[hr]*fres[fr]
    hafu_sorted=sorted(hafu.items(),key=lambda x:-x[1])
    results[num]={'home':home,'away':away,'lh':lh,'la':la,'gl':gl,'htc':htc,'note':note,
      'dc_had':(round(h*100,1),round(d*100,1),round(a*100,1)),
      'k_dist':(kd[0],round(kd[1]*100,1)),
      'had_first':first,
      'k_rec':(kr[0],round(kr[1]*100,1)),
      'band':[(f'{i}-{j}',round(p*100,1)) for i,j,p in band_top],
      'crs':[(f'{i}-{j}',round(p*100,1)) for i,j,p in crs_top],
      'ttg':[(g,round(v*100,1)) for g,v in tt_sorted[:5]],
      'ttg_6plus':round(t6*100,1),
      'hc':{k:round(v*100,1) for k,v in hc.items()},
      'hres':(round(hh*100,1),round(hd*100,1),round(ha*100,1)),
      'hcrs':[(f'{i}-{j}',round(p*100,1)) for i,j,p in hcrs_top],
      'hafu':[(k,round(v*100,1)) for k,v in hafu_sorted],
      'net_mode_note': f'k_dist方向={"主胜" if kd[0]>0 else ("客胜" if kd[0]<0 else "平")} vs HAD首推={"主胜" if first=="h" else ("客胜" if first=="a" else "平")}'}

for num,r in results.items():
    print('='*72)
    print(num,r['home'],'vs',r['away'],f" lh={r['lh']} la={r['la']} gl={r['gl']} htc={r['htc']}")
    print(' DC-HAD 主/平/客:',r['dc_had'])
    print(' 分布众数 k_dist:',r['k_dist'],' 推荐众数 k_rec:',r['k_rec'])
    print(' 分歧:',r['net_mode_note'])
    print(' 带内候选:',r['band'])
    print(' CRS top6:',r['crs'])
    print(' TTG top5:',r['ttg'],' 6+球合计:',r['ttg_6plus'])
    print(' 让球(gl=%d):'%r['gl'],r['hc'])
    print(' 半场结果 主/平/客:',r['hres'],' 半场比分:',r['hcrs'])
    print(' HAFU top6:',r['hafu'][:6])

json.dump(results,open(r'reports\data\20261014_model_calc_001_007.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('\nsaved calc json')
