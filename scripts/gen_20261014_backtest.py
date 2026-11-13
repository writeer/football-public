# -*- coding: utf-8 -*-
import json, os

# ---------- 逐场赛果与命中计算 ----------
# 字段: num, match, league, conf, is_single, ht, ft, had(实际), hadHit,
# hafuLine, hafuPick, hafuRes, hafuHit, crsHit, crsTop5, ttgActual, ttgPick, ttgHit,
# htftActual, htftTop3, htftHit, htScoreActual, htTop3, htScoreHit,
# ou_tier, ou_actual, ouHit, bo_pick, bo_type, bo_actual, boHit, boDirOnly,
# k_dist, k_rec, agreement, band_actual

R = []
def add(**k): R.append(k)

add(num="001", match="墨尔本胜利vs首尔FC", league="亚冠乙E组", conf="★★", is_single=False,
    ht="0:0", ft="3:0", had="主胜", hadHit="first",
    hafuLine=-1, hafuPick="让(-1)平/负", hafuRes="让(-1)胜", hafuHit="none",
    crsHit=False, crsTop5=["1-0","2-1","1-1","1-2","2-0"],
    ttgActual="3", ttgPick=["2","3"], ttgHit=True,
    htftActual="平胜", htftTop3=["平胜","胜胜","平负"], htftHit=True,
    htScoreActual="0-0", htTop3=["0-0","1-0","0-1"], htScoreHit=True,
    ou_tier="常规正常球（2-3球）", ou_actual="常规正常球（2-3球）", ouHit=True,
    bo_type="搏冷", bo_pick="1-1", bo_actual="3-0", boHit=False, boDirOnly=False,
    k_dist="+1(26.6%)", k_rec="+1(26.6%)", agreement="一致", band_actual=False)

add(num="002", match="神户胜利船vs全北现代", league="亚冠精英", conf="★★", is_single=False,
    ht="1:0", ft="2:0", had="主胜", hadHit="first",
    hafuLine=-1, hafuPick="让(-1)平/负", hafuRes="让(-1)胜", hafuHit="none",
    crsHit=True, crsTop5=["1-0","2-1","1-1","2-0","0-0"],
    ttgActual="2", ttgPick=["2","1"], ttgHit=True,
    htftActual="胜胜", htftTop3=["平胜","胜胜","平负"], htftHit=True,
    htScoreActual="1-0", htTop3=["0-0","1-0","0-1"], htScoreHit=True,
    ou_tier="小球（1-2球）为主、常规兜底", ou_actual="小球（1-2球）", ouHit=True,
    bo_type="搏冷", bo_pick="1-1", bo_actual="2-0", boHit=False, boDirOnly=False,
    k_dist="+1(27.1%)", k_rec="+1(27.1%)", agreement="一致", band_actual=False)

add(num="003", match="柏太阳神vs曼谷港务", league="亚冠精英", conf="★★", is_single=False,
    ht="5:0", ft="5:1", had="主胜", hadHit="first",
    hafuLine=-2, hafuPick="让(-2)负/胜", hafuRes="让(-2)胜", hafuHit="second",
    crsHit=False, crsTop5=["2-0","3-0","2-1","3-1","1-0"],
    ttgActual="6", ttgPick=["3","4"], ttgHit=False,
    htftActual="胜胜", htftTop3=["胜胜","平胜","胜平"], htftHit=True,
    htScoreActual="5-0", htTop3=["1-0","0-0","2-0"], htScoreHit=False,
    ou_tier="大球（4-5球）上探、常规（2-3）兜底", ou_actual="超大球（5-6球）", ouHit=False,
    bo_type="穿盘大热", bo_pick="3-0", bo_actual="5-1", boHit=False, boDirOnly=True,
    k_dist="+1(24.7%)", k_rec="+1(24.7%)", agreement="一致", band_actual=False)

add(num="004", match="横滨水手vs清水鼓动", league="日联赛杯", conf="★", is_single=False,
    ht="0:0", ft="2:1", had="主胜", hadHit="first",
    hafuLine=-1, hafuPick="让(-1)负/平", hafuRes="让(-1)平", hafuHit="second",
    crsHit=True, crsTop5=["1-1","2-1","1-0","0-1","1-2"],
    ttgActual="3", ttgPick=["2","1"], ttgHit=False,
    htftActual="平胜", htftTop3=["平胜","平负","平平"], htftHit=True,
    htScoreActual="0-0", htTop3=["0-0","1-0","0-1"], htScoreHit=True,
    ou_tier="小球（1-2球）", ou_actual="常规正常球（2-3球）", ouHit=False,
    bo_type="爆冷", bo_pick="0-1", bo_actual="2-1", boHit=False, boDirOnly=False,
    k_dist="0(25.2%)", k_rec="+1(23.7%)", agreement="分布-方向分歧", band_actual=True)

add(num="005", match="费耶诺德vs科莫", league="欧冠联赛阶段", conf="★★", is_single=False,
    ht="1:1", ft="3:2", had="主胜", hadHit="second",
    hafuLine=1, hafuPick="让(+1)平/胜", hafuRes="让(+1)胜", hafuHit="second",
    crsHit=False, crsTop5=["1-2","1-1","2-2","2-1","1-0"],
    ttgActual="5", ttgPick=["2","3"], ttgHit=False,
    htftActual="平胜", htftTop3=["平负","负负","平胜"], htftHit=True,
    htScoreActual="1-1", htTop3=["0-0","0-1","1-0"], htScoreHit=False,
    ou_tier="常规（2-3球）基准、上探大球（4-5）", ou_actual="大球（4-5球）", ouHit=True,
    bo_type="穿盘大热", bo_pick="1-2", bo_actual="3-2", boHit=False, boDirOnly=False,
    k_dist="-1(25.1%)", k_rec="-1(25.1%)", agreement="一致", band_actual=False)

add(num="006", match="LASK林茨vs利物浦", league="欧冠联赛阶段", conf="★★", is_single=False,
    ht="0:3", ft="3:6", had="客胜", hadHit="first",
    hafuLine=1, hafuPick="让(+1)平/负", hafuRes="让(+1)负", hafuHit="second",
    crsHit=False, crsTop5=["0-2","1-2","0-3","1-1","0-1"],
    ttgActual="9", ttgPick=["3","4"], ttgHit=False,
    htftActual="负负", htftTop3=["负负","平负","胜负"], htftHit=True,
    htScoreActual="0-3", htTop3=["0-1","0-0","0-2"], htScoreHit=False,
    ou_tier="常规（2-3球）基准、大球（4-5）次选预留", ou_actual="穿盘可能（6-7+球）", ouHit=False,
    bo_type="穿盘大热", bo_pick="0-2", bo_actual="3-6", boHit=False, boDirOnly=True,
    k_dist="-1(21.8%)", k_rec="-1(21.8%)", agreement="一致", band_actual=False)

add(num="007", match="诺维奇vs南安普敦", league="英冠", conf="★", is_single=False,
    ht="0:0", ft="0:1", had="客胜", hadHit="second",
    hafuLine=-1, hafuPick="让(-1)负/平", hafuRes="让(-1)负", hafuHit="first",
    crsHit=False, crsTop5=["2-1","1-1","1-2","2-2","1-0"],
    ttgActual="1", ttgPick=["2","1"], ttgHit=True,
    htftActual="平负", htftTop3=["平胜","平负","平平"], htftHit=True,
    htScoreActual="0-0", htTop3=["0-0","1-0","0-1"], htScoreHit=True,
    ou_tier="小球（1-2球）基准、常规兜底", ou_actual="闷战超小球（0-1球）", ouHit=True,
    bo_type="爆冷", bo_pick="2-1", bo_actual="0-1", boHit=False, boDirOnly=False,
    k_dist="0(24.5%)", k_rec="+1(23.9%)", agreement="分布-方向分歧", band_actual=False)

add(num="008", match="罗马vs皇家马德里", league="欧冠联赛阶段", conf="★★", is_single=True,
    ht="1:1", ft="3:4", had="客胜", hadHit="first",
    hafuLine=1, hafuPick="让(+1)胜/负", hafuRes="让(+1)平", hafuHit="none",
    crsHit=False, crsTop5=["0-1","1-2","0-2","1-1","1-0"],
    ttgActual="7", ttgPick=["2","3"], ttgHit=False,
    htftActual="平负", htftTop3=["平负","负负","平平"], htftHit=True,
    htScoreActual="1-1", htTop3=["0-0","0-1","1-0"], htScoreHit=False,
    ou_tier="常规正常球（2-3球）下沿、偏小球", ou_actual="穿盘可能（6-7+球）", ouHit=False,
    bo_type="穿盘大热", bo_pick="0-1", bo_actual="3-4", boHit=False, boDirOnly=True,
    k_dist="0(24.7%)", k_rec="-1(23.5%)", agreement="分布-方向分歧", band_actual=True)

add(num="009", match="博德闪耀vs多特蒙德", league="欧冠联赛阶段", conf="★★", is_single=False,
    ht="0:0", ft="1:0", had="主胜", hadHit="first",
    hafuLine=1, hafuPick="让(+1)胜/平", hafuRes="让(+1)胜", hafuHit="first",
    crsHit=True, crsTop5=["1-0","2-1","1-1","1-2","2-2"],
    ttgActual="1", ttgPick=["2","3"], ttgHit=False,
    htftActual="平胜", htftTop3=["平胜","平负","胜胜"], htftHit=True,
    htScoreActual="0-0", htTop3=["0-0","1-0","0-1"], htScoreHit=True,
    ou_tier="常规正常球（2-3球）上沿、候选大球（4-5）下沿", ou_actual="闷战超小球（0-1球）", ouHit=False,
    bo_type="爆冷", bo_pick="2-1", bo_actual="1-0", boHit=False, boDirOnly=True,
    k_dist="0(25.3%)", k_rec="+1(20.4%)", agreement="分布-方向分歧", band_actual=True)

add(num="010", match="皇家贝蒂斯vs波尔图", league="欧冠联赛阶段", conf="★★", is_single=False,
    ht="0:0", ft="3:2", had="主胜", hadHit="first",
    hafuLine=-1, hafuPick="让(-1)负/胜", hafuRes="让(-1)平", hafuHit="none",
    crsHit=False, crsTop5=["2-0","2-1","1-0","1-1","1-2"],
    ttgActual="5", ttgPick=["2","3"], ttgHit=False,
    htftActual="平胜", htftTop3=["平胜","胜胜","平负"], htftHit=True,
    htScoreActual="0-0", htTop3=["0-0","1-0","0-1"], htScoreHit=True,
    ou_tier="常规正常球（2-3球）", ou_actual="大球（4-5球）", ouHit=False,
    bo_type="搏冷", bo_pick="1-1", bo_actual="3-2", boHit=False, boDirOnly=False,
    k_dist="0(24.8%)", k_rec="+1(23.0%)", agreement="分布-方向分歧", band_actual=True)

add(num="011", match="曼城vs巴黎圣日耳曼", league="欧冠联赛阶段", conf="★★", is_single=True,
    ht="0:3", ft="2:4", had="客胜", hadHit="none",
    hafuLine=-1, hafuPick="让(-1)负/胜", hafuRes="让(-1)负", hafuHit="first",
    crsHit=False, crsTop5=["2-1","2-2","3-1","1-2","1-0"],
    ttgActual="6", ttgPick=["3","2"], ttgHit=False,
    htftActual="负负", htftTop3=["平胜","胜胜","平平"], htftHit=False,
    htScoreActual="0-3", htTop3=["0-0","1-0","0-1"], htScoreHit=False,
    ou_tier="常规正常球（2-3球）上沿→大球（4-5）下沿", ou_actual="超大球（5-6球）", ouHit=False,
    bo_type="搏冷", bo_pick="2-2", bo_actual="2-4", boHit=False, boDirOnly=False,
    k_dist="0(23.2%)", k_rec="+1(21.9%)", agreement="分布-方向分歧", band_actual=False)

add(num="012", match="阿斯顿维拉vs费内巴切", league="欧冠联赛阶段", conf="★★", is_single=False,
    ht="3:0", ft="6:0", had="主胜", hadHit="first",
    hafuLine=-1, hafuPick="让(-1)负/胜", hafuRes="让(-1)胜", hafuHit="second",
    crsHit=False, crsTop5=["2-1","1-0","1-1","1-2","2-2"],
    ttgActual="6", ttgPick=["2","3"], ttgHit=False,
    htftActual="胜胜", htftTop3=["平胜","胜胜","平负"], htftHit=True,
    htScoreActual="3-0", htTop3=["0-0","1-0","0-1"], htScoreHit=False,
    ou_tier="常规正常球（2-3球）上沿", ou_actual="超大球（5-6球）", ouHit=False,
    bo_type="搏冷", bo_pick="1-1", bo_actual="6-0", boHit=False, boDirOnly=False,
    k_dist="0(24.6%)", k_rec="+1(23.3%)", agreement="分布-方向分歧", band_actual=False)

add(num="013", match="弗鲁米嫩塞vs帕尔梅拉斯", league="解放者杯半决赛", conf="★", is_single=False,
    ht="0:1", ft="1:2", had="客胜", hadHit="none",
    hafuLine=1, hafuPick="让(+1)胜/平", hafuRes="让(+1)平", hafuHit="second",
    crsHit=False, crsTop5=["0-0","1-0","0-1","1-1","2-0"],
    ttgActual="3", ttgPick=["1","0"], ttgHit=False,
    htftActual="负负", htftTop3=["平平","平胜","平负"], htftHit=False,
    htScoreActual="0-1", htTop3=["0-0","0-1","1-0"], htScoreHit=True,
    ou_tier="闷战超小球（0-1球）→小球（1-2球）", ou_actual="常规正常球（2-3球）", ouHit=False,
    bo_type="搏冷", bo_pick="0-0", bo_actual="1-2", boHit=False, boDirOnly=False,
    k_dist="0(35.3%)", k_rec="0(35.3%)", agreement="一致", band_actual=False)

add(num="014", match="圣路易斯城vs温哥华白帽", league="美职", conf="★★", is_single=False,
    ht="0:0", ft="0:0", had="平", hadHit="second",
    hafuLine=-1, hafuPick="让(-1)负/胜", hafuRes="让(-1)负", hafuHit="first",
    crsHit=False, crsTop5=["2-1","1-1","2-0","1-0","1-2"],
    ttgActual="0", ttgPick=["2","3"], ttgHit=False,
    htftActual="平平", htftTop3=["平胜","胜胜","平平"], htftHit=True,
    htScoreActual="0-0", htTop3=["0-0","1-0","0-1"], htScoreHit=True,
    ou_tier="常规正常球（2-3球）", ou_actual="闷战超小球（0-1球）", ouHit=False,
    bo_type="爆冷", bo_pick="2-1", bo_actual="0-0", boHit=False, boDirOnly=False,
    k_dist="0(25.5%)", k_rec="+1(24.0%)", agreement="分布-方向分歧", band_actual=False)

# ---------- 汇总 ----------
N=14
had_first=sum(1 for x in R if x["hadHit"]=="first")
had_second=sum(1 for x in R if x["hadHit"]=="second")
had_hit=had_first+had_second
hf_first=sum(1 for x in R if x["hafuHit"]=="first")
hf_second=sum(1 for x in R if x["hafuHit"]=="second")
hf_hit=hf_first+hf_second
crs_hit=sum(1 for x in R if x["crsHit"])
ttg_hit=sum(1 for x in R if x["ttgHit"])
htft_hit=sum(1 for x in R if x["htftHit"])
hts_hit=sum(1 for x in R if x["htScoreHit"])
ou_hit=sum(1 for x in R if x["ouHit"])
bo_hit=sum(1 for x in R if x["boHit"])
bo_dir=sum(1 for x in R if x["boDirOnly"])
band_hit=sum(1 for x in R if x["band_actual"])

byConf={}
for x in R:
    c="★★" if x["conf"].startswith("★★") else "★"
    d=byConf.setdefault(c,{"total":0,"hit":0})
    d["total"]+=1
    if x["hadHit"] in ("first","second"): d["hit"]+=1
for c in byConf: byConf[c]["rate"]=round(byConf[c]["hit"]/byConf[c]["total"],3)

summary={
 "direction":{"total":N,"first":had_first,"second":had_second,"hit":had_hit,"rate":round(had_hit/N,3),"firstOnly":round(had_first/N,3)},
 "handicap":{"total":N,"first":hf_first,"second":hf_second,"hit":hf_hit,"rate":round(hf_hit/N,3),"firstOnly":round(hf_first/N,3)},
 "scoreTop5":{"total":N,"hit":crs_hit,"rate":round(crs_hit/N,3)},
 "totalGoals":{"total":N,"hit":ttg_hit,"rate":round(ttg_hit/N,3)},
 "halfFull":{"total":N,"hit":htft_hit,"rate":round(htft_hit/N,3)},
 "halfScore":{"total":N,"hit":hts_hit,"rate":round(hts_hit/N,3)},
 "ouTier":{"total":N,"hit":ou_hit,"rate":round(ou_hit/N,3),"note":"六档：闷战超小球0-1/小球1-2/常规2-3/大球4-5/超大5-6/穿盘6-7+"},
 "boScore":{"total":N,"exactHit":bo_hit,"exactRate":round(bo_hit/N,3),"dirOnly":bo_dir,"dirRate":round(bo_dir/N,3),"note":"博分精确命中0场，方向对但比分未中4场(003/006/008/009)"},
 "kRecBand":{"total":N,"inBand":band_hit,"rate":round(band_hit/N,3),"note":"实际净胜球落在k_rec带内场次"},
 "byConfidence":byConf
}

# ---------- 串关 29 ----------
P=[]
def par(name,typ,matches,results,hit,odds):
    P.append({"name":name,"type":typ,"matches":matches,"results":results,"hit":hit,"odds_est":odds})

# 方向串
par("方向串①（稳健三串一）","方向串",["002","005","014"],["✅主胜2-0","❌客胜(实际主胜3-2)","❌主胜(实际平0-0)"],False,"~5.48")
par("方向串②（稳健二串一）","方向串",["001","012"],["✅主胜3-0","✅主胜6-0"],True,"~2.26")
par("方向串③（价值二串一）","方向串",["010","008"],["✅主胜3-2","✅客胜3-4"],True,"~3.11")
# 让球串
par("稳健让球串（受让不败型）","让球串",["013","007","009"],["❌让(+1)胜(实际让平)","✅让(-1)负","✅让(+1)胜"],False,"~3.62")
par("价值让球串（让平高赔）","让球串",["006","001"],["❌让(+1)平(实际让负)","❌让(-1)平(实际让胜)"],False,"~14.46")
# 混合串
par("纯半全场串A","混合串",["007","002"],["❌平平(实际平负)","❌平胜(实际胜胜)"],False,"~27.30")
par("纯半全场串B","混合串",["004","009"],["❌平平(实际平胜)","✅平胜"],False,"~44.55")
par("方向+半全场混合串A","混合串",["005","004"],["❌客胜(实际主胜)","❌平平(实际平胜)"],False,"~9.40")
par("方向+半全场混合串B","混合串",["012","008"],["✅主胜6-0","✅平负3-4"],True,"~7.60")
par("连续编号混合串①(001+002)","混合串",["001","002"],["✅主胜3-0","❌平胜(实际胜胜)"],False,"~6.38")
par("连续编号混合串②(008+009)","混合串",["008","009"],["✅平负3-4","✅平胜1-0"],True,"~42.07")
# 总进球串
par("总进球串A","总进球串",["013","006"],["❌1球(实际3球)","❌3球(实际9球)"],False,"~13.49")
par("总进球串B","总进球串",["004","011"],["❌1球(实际3球)","❌3球(实际6球)"],False,"~17.39")
par("连续编号总进球串①(001+002)","总进球串",["001","002"],["❌2球(实际3球)","✅2球"],False,"~14.35")
par("连续编号总进球串②(003+004)","总进球串",["003","004"],["❌3球(实际6球)","❌2球(实际3球)"],False,"~12.95")
# 高赔半全场串
par("高赔半全场串A","高赔半全场串",["010","008"],["✅平胜3-2","✅平负3-4"],True,"~25.50")
par("高赔半全场串B","高赔半全场串",["009","005"],["✅平胜1-0","❌平负(实际平胜)"],False,"~42.90")
par("连续编号高赔半全场串①(001+002)","高赔半全场串",["001","002"],["✅平胜3-0","❌平平(实际胜胜)"],False,"~29.30")
par("连续编号高赔半全场串②(013+014)","高赔半全场串",["013","014"],["❌平平(实际负负)","❌平胜(实际平平)"],False,"~21.95")
# 半全场混合
par("混合总进球串A","半全场混合",["006","011"],["✅负负3-6","❌3球(实际6球)"],False,"~6.10")
par("混合总进球串B","半全场混合",["003","012"],["❌3球(实际6球)","❌平胜(实际胜胜)"],False,"~15.91")
par("连续编号混合总进球串①(008+009)","半全场混合",["008","009"],["✅平负3-4","❌3球(实际1球)"],False,"~19.89")
par("连续编号混合总进球串②(013+014)","半全场混合",["013","014"],["❌1球(实际3球)","❌平胜(实际平平)"],False,"~20.23")
# 比分串
par("稳健比分串〔试用期流程〕","比分串",["006","013"],["❌1-2(实际3-6)","❌0-0(实际1-2)"],False,"~48.75")
par("搏冷比分串〔反向推理〕","比分串",["009","004"],["❌2-1(实际1-0)","❌0-1(实际2-1)"],False,"~115.50")
par("连续编号比分串①(001+002)","比分串",["001","002"],["❌1-0(实际3-0)","❌1-0(实际2-0)"],False,"~66.50")
par("连续编号比分串②(005+006)","比分串",["005","006"],["❌0-1(实际3-2)","❌1-2(实际3-6)"],False,"~93.75")
par("单挑比分①","比分串",["003"],["❌1-0(实际5-1)"],False,"单注9.50")
par("单挑比分②","比分串",["005"],["❌0-1(实际3-2)"],False,"单注12.50")

steady_types={"方向串","让球串","混合串"}
ent_types={"总进球串","高赔半全场串","半全场混合","比分串"}
s_hit=sum(1 for p in P if p["hit"] and p["type"] in steady_types)
s_cnt=sum(1 for p in P if p["type"] in steady_types)
e_hit=sum(1 for p in P if p["hit"] and p["type"] in ent_types)
e_cnt=sum(1 for p in P if p["type"] in ent_types)
parlaySummary={
 "totalHit":sum(1 for p in P if p["hit"]),
 "totalCount":len(P),
 "rate":round(sum(1 for p in P if p["hit"])/len(P),3),
 "steadyGroup":{"label":"稳健方案(方向串/让球串/混合串)","hit":s_hit,"count":s_cnt,"rate":round(s_hit/s_cnt,3)},
 "entertainmentGroup":{"label":"娱乐串(总进球串/高赔半全场串/半全场混合/比分串)","hit":e_hit,"count":e_cnt,"rate":round(e_hit/e_cnt,3)},
 "bySubcategory":{
   "方向串":{"hit":1,"count":3},
   "让球串":{"hit":0,"count":2},
   "混合串":{"hit":3,"count":6},
   "总进球串":{"hit":0,"count":4},
   "高赔半全场串":{"hit":1,"count":4},
   "半全场混合":{"hit":0,"count":4},
   "比分串":{"hit":0,"count":6}
 }
}

# 搏冷未中场次
bleng=[
 {"num":"004","pick":"客胜","actual":"主胜","hit":False},
 {"num":"008","pick":"平","actual":"客胜","hit":False},
 {"num":"011","pick":"平","actual":"客胜","hit":False},
 {"num":"013","pick":"平","actual":"客胜","hit":False},
]

out={
 "date":"2026-10-14",
 "day":"周三",
 "totalMatches":14,
 "source":"体彩官网开奖接口 getUniformMatchResultV1.qry（lastUpdateTime 2026-10-15 merged）；013/014赛果经新闻源交叉标注",
 "source_files":[
  "reports/data/20261014_wednesday_predictions.json",
  "reports/data/20261014_results_official.json",
  "reports/analysis/20261014_wednesday_analysis_zhihu.md"
 ],
 "results":R,
 "summary":summary,
 "parlays":P,
 "parlaySummary":parlaySummary,
 "blengMatches":bleng,
 "lessons":[],
 "lessons_candidate":[
  "L199候选·总进球/大小球连续第三日崩盘：总进球TOP2 3/14=21.4%、大小球档4/14=28.6%；欧冠8场中003(6球)/006(9球)/008(7球)/011(6球)/012(6球)/005与010(各5球)共7场≥5球，TTG推2-3球档全面失守。L188/L190/L198已三次记录'欧冠对攻大球低估'仍未落地触发，建议规则65/λ_total上修对欧冠联赛阶段强制硬阈值化。",
  "L200候选·让球首选仅28.6%极低、次选补6场：让球合并命中10/14=71.4%但首选仅4/14；001/002让(-1)平首选被3-0/2-0穿盘证伪，008/010实际让平而首选押让胜/让负漏防。与L197'让平漏防'同源，±1盘让平概率≥20%必须进TOP2。",
  "L201候选·单关平局上修双杀+搏冷平局4场全灭：008/011两场单关规则63平局上修后实际均客胜大比分(3-4/2-4)，平局未兑现；搏冷方向004客胜/008平/011平/013平四腿全灭，仅009主胜搏冷命中。'残阵/势均力敌→平局'线性假设连续第二日(承接L196)被证伪。",
  "L202候选·博分精确0/14、方向对4场但量级全偏：穿盘大热方向003/006/008命中(均客胜/主胜方向)，但预测小胜比分(3-0/0-2/0-1)实际打出5-1/3-6/3-4，净胜球量级系统性低估1-2档；001搏冷1-1实际3-0。博分剧本'1球小胜'框架与欧冠开放对攻现实脱节。",
  "L203候选·半全场TOP3 85.7%为本日最大亮点：'平胜'路径单场命中001/004/005/009/010共5场，半场平局高联赛(ht_draw_rate)+下半场决胜的半全场结构有效；仅011(负负押平平胜)、013(负负押平平)两场失手。"
 ]
}

path=r"E:\VibeCoding\football\memory\backtests\20261014_wednesday_backtest.json"
with open(path,"w",encoding="utf-8") as f:
    json.dump(out,f,ensure_ascii=False,indent=1)

# 校验
with open(path,"r",encoding="utf-8") as f:
    chk=json.load(f)
print("JSON OK, matches=",len(chk["results"]),"parlays=",len(chk["parlays"]))
print("summary direction=",chk["summary"]["direction"])
print("summary handicap=",chk["summary"]["handicap"])
print("parlaySummary=",chk["parlaySummary"]["totalHit"],"/",chk["parlaySummary"]["totalCount"])
print("ou=",chk["summary"]["ouTier"]["hit"],"bo exact=",chk["summary"]["boScore"]["exactHit"],"band=",chk["summary"]["kRecBand"]["inBand"])
print("byConf=",chk["summary"]["byConfidence"])
