# -*- coding: utf-8 -*-
"""生成 2026-11-13（周五）分析报告 + 预测底稿"""
import json, io, os, re

M = {r['num']: r for r in json.load(open('reports/data/20261113_model_output.json', encoding='utf-8'))}
ORDER = ['周五001','周五002','周五003','周五004','周五005','周五006','周五007','周五008','周五009','周五010','周五011']

def pct(x, d=2): return f"{x*100:.{d}f}%"
def o(v): return f"{v:.2f}"
def top_scores(r, n=5): return [(s, p) for s, p in r['probs']['scores'][:n]]
def hafu_cn(k):
    return {'hh':'胜胜','hd':'胜平','ha':'胜负','dh':'平胜','dd':'平平','da':'平负','ah':'负胜','ad':'负平','aa':'负负'}[k]
def hafu_top(r, n=3):
    return sorted(r['probs']['HAFU'].items(), key=lambda x: -x[1])[:n]

STAT = {}
for r in M.values():
    STAT[r['num']] = r

def crs_odds(r, score):
    return r['market']['CRS_odds'].get(score, '')

# ---------------- 每场事实与叙述 ----------------
F = {
'周五001': dict(
  league='国际赛·友谊赛', level='国际友谊赛（A 级国家队，不计积分/排名权重）｜友谊赛数据不用于正式赛推断',
  venue='Singapore National Stadium（新加坡加冷；容量与草皮类型：ESPN 场馆接口无 capacity/surface 字段，信息缺失）',
  wx='🌦 小雨转阵雨，26–28°C，湿度高，风速 3–5km/h（wttr.in 逐小时 2026-11-13 18:00–21:00 当地；单源、非场馆实测）',
  wx_eff='湿热高湿对巴拉圭体能不利、节奏偏慢，利好新加坡低位防守；预计双方均不冒进',
  fund='友谊赛无小组积分。新加坡 Elo 1149（世界第 160 位附近）、巴拉圭 Elo 1836（第 39 位），Elo 差 −687；新加坡近况信息缺失（ESPN lastFiveGames 与本场口径不一致，不采用），巴拉圭近 5 场 3 胜 1 平 1 负（Sports Mole 赛前页）。',
  value='未取得（Transfermarkt .com/.us 均 HTTP 405「Human Verification」WAF 拦截；football-charts MCP 仅覆盖俱乐部联赛，无国家队身价）。',
  injury='新加坡：Ikhsan Fandi（前锋，伤缺）、Nur Adam Abdullah（伤缺），Perry Ng 因陪产缺席（Sports Mole 2026-11-13 预览）；巴拉圭：Antonio Sanabria（前锋，伤缺）。**首发：** 新加坡（4-2-3-1）Mahbud；Pereira、Harun、Baharudin、Stewart；Kweh、Shahiran、Stewart、Nakamura、Song；Fandi；巴拉圭（4-3-3）Gill；Caceres、Gomez、Alderete、Alonso；Villasanti、Galarza、Bobadilla；Almiron、Benitez、Enciso（Sports Mole 预计首发，非官方）。',
  style='新加坡五后卫/低位 4-2-3-1 收缩，靠 Song Ui-young 与 Ilhan Fandi 反击；巴拉圭 4-3-3 边路 Almiron/Enciso 单点爆破、Villasanti 后插上。风格相克：新加坡退守能压低对手射门质量，但个体差距过大。',
  conf='★', conf_reason='首选客胜 75.63%、与前二差 57.9pp，方向本身清晰；但本场无 HAD 池、无法做胜平负市场对齐，让球端（+3）模型 72.28% 对市场去水 44.25% 差 +28.03pp 属大幅分歧，叠加友谊赛战意不可控与身价缺失，按 L8 降为 ★。',
  single_note='接口 bettingSingle=0，未开单关；若你的投注端显示 001 可单关，以你的端为准并触发平局上修（本报告按非单关口径）。',
),
'周五002': dict(
  league='欧国联 C 级 C3 组', level='欧国联（国家 C 级赛事·League C）｜C3 组第 5 轮，同级别对话（不触发等级差判定）',
  venue='Stadionul Zimbru（摩尔多瓦基希讷乌；容量与草皮类型：ESPN 场馆接口无对应字段，信息缺失）',
  wx='🌫 阴，7–8°C，降水概率 15–31%，风速 19–28km/h（wttr.in 逐小时 2026-11-13 19:00–22:00 当地；单源）',
  wx_eff='低温+阵风，长传与定位球质量下降，利好身体对抗更强的一方；对技术型中场不利',
  fund='C3 组前 4 轮：摩尔多瓦 1 胜 1 平 2 负、3 进 8 失（4 分），哈萨克 0 胜 2 平 2 负、5 进 7 失（2 分）；同组斯洛伐克 9-2（10 分）、法罗 5-5（4 分）。两队防守都偏漏，C3 组场均 2.75 球为四个小组最高。',
  value='未取得（Transfermarkt 405 WAF；国家队身价无可用源），不作倍数推断。',
  injury='摩尔多瓦：无人停赛，Iovu/Rata/Reabciuk 再吃牌将停赛；哈萨克：Sergey Malyy（中卫，红牌停赛）。**首发：** 摩尔多瓦（4-4-2）Celeadnic；Reabciuk、Baboglo、Iovu、Dumbravanu；Motpan、Perciun、Cojocari、Fratea；Popescu、Clescenco；哈萨克（4-4-2）Pokatilov；Alip、Kassym、Zhagorov、Tapalov；Ashirbek、Kuat、Zhukov、Amir；Kenzhebek、Karimov（Sports Mole 预计首发）。',
  style='两队均 4-4-2 直来直去，摩尔多瓦靠边路传中找 Popescu，哈萨克依赖 Zhukov 的locating长传与 Karimov 反击。中场控制力都弱，比赛容易变成拉锯与定位球决胜。',
  conf='★', conf_reason='首选客胜 39.57% 未过 50%、模型（客胜 39.57%）与市场去水（客胜 30.89%）差 +8.68pp 已属分歧，样本仅 4 轮，降为 ★。',
  single_note='接口 bettingSingle=0，非单关。',
),
'周五003': dict(
  league='欧国联 C 级 C4 组', level='欧国联（国家 C 级赛事·League C）｜C4 组第 5 轮，同级别对话',
  venue='Hristo Botev Stadium（保加利亚普罗夫迪夫；容量与草皮类型：ESPN 接口无对应字段，信息缺失）',
  wx='🌙 晴，12–15°C，降水概率 11–14%，风速 2–5km/h（wttr.in 逐小时 2026-11-13 21:00–24:00 当地；单源）',
  wx_eff='夜间低温、无风无雨，场地条件干净，利好传控与远射',
  fund='C4 组前 4 轮：保加利亚 1 胜 1 平 2 负、3 进 5 失（4 分），冰岛 2 胜 2 平 0 负、7 进 1 失（8 分，小组第一且失球最少）；同组爱沙尼亚 2-1（6 分）、卢森堡 2-7（3 分）。冰岛防守是 C4 组最强。',
  value='未取得（Transfermarkt 405 WAF）。',
  injury='保加利亚：门将 Dimitar Mitov、边锋 Lukas Petkov 回归首发；8 人处于再吃牌停赛边缘（Sports Mole）。冰岛：无停赛/伤缺要点。**首发：** 保加利亚（4-2-3-1）Mitov；Stoyanov、Velkov、Tsenov、Petrov；Kraev、Gruev；Petkov、Rusev、Balov；Iliev；冰岛（4-2-3-1）Valdimarsson；Palsson、Bjarnason、Magnusson、Gretarsson；Sigurdsson、Johannesson；Gudjohnsen、Oskarsson（Sports Mole 预计首发）。',
  style='保加利亚双后腰 Kraev/Gruev 保护防线、靠 Petkov 右路推进；冰岛 Gudjohnsen 回撤做球、Oskarsson 冲击身后，防守端 4 轮仅失 1 球。冰岛的转换效率与防守纪律明显更好。',
  conf='★★', conf_reason='首选客胜 51.00% ≥50%，与市场去水（55.94%）同向、差 −4.94pp；伤停/首发一手信息已取得；身价缺失故不给 ★★★。',
  single_note='接口 bettingSingle=0，非单关。',
),
'周五004': dict(
  league='欧国联 B 级 B1 组', level='欧国联（国家 B 级赛事·League B）｜B1 组第 5 轮，同级别对话',
  venue='Hampden Park（苏格兰格拉斯哥；容量与草皮类型：ESPN 接口无对应字段，信息缺失）',
  wx='🌧 多云有阵雨，4–5°C，降水概率 11–19%，风速 13–15km/h（wttr.in 逐小时 2026-11-13 19:00–22:00 当地；单源）',
  wx_eff='低温湿冷、夜场，技术动作易变形，利好身体对抗与定位球；对北马其顿的脚下配合不利',
  fund='B1 组前 4 轮：苏格兰 1 胜 1 平 2 负、3 进 5 失（4 分），北马其顿 0 胜 0 平 4 负、0 进 10 失（0 分，全组唯一零进球）；同组瑞士 11-1（12 分）、斯洛文尼亚 5-3（7 分）。北马其顿 4 轮零进球是本期最极端的进攻荒。',
  value='未取得（Transfermarkt 405 WAF）。',
  injury='苏格兰：Scott McTominay 心脏手术后首次回归，直接进首发（前 4 轮未出场）；北马其顿：无伤停要点，Bardhi 领衔。**首发：** 苏格兰（3-5-1-1）Gunn；Hickey、Hendry、Binks；Doak、McGinn、Ferguson、Gilmour、Robertson；McTominay；McBurnie；北马其顿（4-2-3-1）Dimitrievski；Ilievski、Meljichi、Misliu、Aliti；Elmas、Atanasov；Doriev、Bardhi、Mitrovski；Rastoder（Sports Mole 预计首发）。',
  style='苏格兰三中卫+双翼卫压上，McGinn/Ferguson 中场冲击，McTominay 回归增强禁区到位率；北马其顿 4-2-3-1 想打 Bardhi 的肋部直塞，但 4 轮 0 进球说明终结环节全面失灵。',
  conf='★★', conf_reason='首选主胜 64.93% ≥50%、与市场同向（85.32%）但差 −20.39pp，属"模型不追热"；让球 -2 端分歧更大，故只给 ★★ 并明确让球只做次选。',
  single_note='接口 bettingSingle=0，非单关。',
),
'周五005': dict(
  league='欧国联 A 级 A2 组', level='欧国联（国家 A 级赛事·League A）｜A2 组第 5 轮，同级别对话',
  venue='Rajko Mitic Stadium（塞尔维亚贝尔格莱德；容量与草皮类型：ESPN 接口无对应字段，信息缺失）',
  wx='🌧 小雨，9–11°C，降水概率 43–55%，风速 15–23km/h（wttr.in 逐小时 2026-11-13 19:00–22:00 当地；单源）',
  wx_eff='湿滑草皮+夜雨，传球失误率上升，利好防守反击与远射，削弱德国的阵地渗透',
  fund='A2 组前 4 轮：塞尔维亚 0 胜 0 平 4 负、3 进 8 失（0 分，垫底），德国 1 胜 2 平 1 负、3 进 2 失（5 分）；同组荷兰 7-5（8 分）、希腊 5-3（8 分）。注意：德国 4 轮只进 3 球，市场却给出 1.16 的客胜，属极端热度。',
  value='未取得（Transfermarkt 405 WAF）。',
  injury='塞尔维亚：Sasa Lukic、Nemanja Maksimovic 双双停赛（中场屏障缺失），Mitrovic 第 107 帽、Milinkovic-Savic 坐镇中场；德国：Treu/Thiaw/Bisseck 再吃牌将停赛，Havertz、Wirtz 预计首发，ter Stegen 确认一门。**首发：** 塞尔维亚（3-4-2-1）V. Milinkovic-Savic；Nedeljkovic、Gudelj、Babic、Erakovic、Sukacev；Samardzic、S. Milinkovic-Savic、Zivkovic；Cvetkovic、Mitrovic；德国（4-2-3-1）ter Stegen；Treu、Tah、Schlotterbeck、Brown；Nmecha、Kimmich；El Mala、Wirtz、Karl；Havertz（Sports Mole 预计首发）。',
  style='塞尔维亚三中卫+双后腰收缩，靠 Mitrovic 支点与 Samardzic 反击推进；德国 4-2-3-1 由 Kimmich 组织、Wirtz 肋部串联，但缺少高中锋时攻坚偏慢。塞尔维亚两名后腰停赛，正面拦截下降是最大隐患。',
  conf='★', conf_reason='首选客胜 51.17% 与市场去水 79.98% 相差 −28.81pp，属本期最大模型-市场对立（L8），不作博胆、仅小注娱乐；降为 ★。',
  single_note='接口 bettingSingle=0，非单关。',
),
'周五006': dict(
  league='欧国联 C 级 C4 组', level='欧国联（国家 C 级赛事·League C）｜C4 组第 5 轮，同级别对话',
  venue='Stade de Luxembourg（卢森堡市；容量与草皮类型：ESPN 接口无对应字段，信息缺失）',
  wx='🌫 雾/薄雾，2–3°C，降水概率 20–29%，风速 4–8km/h（wttr.in 逐小时 2026-11-13 19:00–22:00 当地；单源）',
  wx_eff='低温薄雾、能见度下降，长传与门将出击风险上升；湿冷对双方体能消耗均匀',
  fund='C4 组前 4 轮：卢森堡 1 胜 0 平 3 负、2 进 7 失（3 分），爱沙尼亚 1 胜 3 平 0 负、2 进 1 失（6 分，4 轮不败）；同组冰岛 7-1（8 分）、保加利亚 3-5（4 分）。爱沙尼亚 4 轮只失 1 球，是低比分结构。',
  value='未取得（Transfermarkt 405 WAF）。',
  injury='卢森堡：Dick Carlson（中卫，两黄停赛），Florian Bohnert 内收中卫，队长 Laurent Jans 伤愈回归右后卫；爱沙尼亚：Marten Kuusk、Robi Saarma 不在名单，Karol Mets 进三中卫，Mattias Kait 可能回中场。**首发：** 卢森堡（4-1-4-1）Moris；Jans、Bohnert、Selimovic、Veiga；Cruz；Natami、V.Thill、Dos Santos、Kadamani；Videira；爱沙尼亚（3-5-2）Igonen；Mets、Paskotsi、Tougjas；Peetson、Palumets、Kristal、Poom、Saliste；Mustmaa、Mannilaan（Sports Mole 预计首发）。',
  style='卢森堡单后腰 Cruz 保护、两翼 Kadamani/Videira 快速反击；爱沙尼亚三中卫+五中场压缩中路，4 轮 2 进球说明进攻极低产。两队都缺终结者，闷战概率高。',
  conf='★', conf_reason='首选客胜 37.53% 未过 50%，模型（37.53%）与市场（24.75%）差 +12.78pp 为分歧场；低进球结构方差大，给 ★。',
  single_note='接口 bettingSingle=0，非单关。',
),
'周五007': dict(
  league='欧国联 C 级 C3 组', level='欧国联（国家 C 级赛事·League C）｜C3 组第 5 轮，同级别对话',
  venue='Košická futbalová aréna（斯洛伐克科希策；容量与草皮类型：ESPN 接口无对应字段，信息缺失）',
  wx='🌧 小到中雨，1–3°C，降水概率 16–66%，风速 5–12km/h（wttr.in 逐小时 2026-11-13 19:00–22:00 当地；单源）',
  wx_eff='低温降雨、草皮湿重，球速加快且控球难度上升；法罗的密集防守更占便宜',
  fund='C3 组前 4 轮：斯洛伐克 3 胜 1 平 0 负、9 进 2 失（10 分，小组第一），法罗群岛 0 胜 4 平 0 负、5 进 5 失（4 分，4 轮全平）；同组摩尔多瓦 3-8（4 分）、哈萨克 5-7（2 分）。法罗 4 轮不败但全部打平，韧性极强。',
  value='未取得（Transfermarkt 405 WAF）。',
  injury='斯洛伐克：Stanislav Lobotka（踝伤）、Tomas Suslov（腿筋）缺阵，Pokorny/Rigo/Duda 组成中场；法罗群岛：Martin Agnarsson（左翼卫，红牌停赛）。**首发：** 斯洛伐克（4-3-3）Greif；Mesik、Skriniar、Obert、Hancko；Rigo、Pokorny、Duda；Bobcek、Strelec、Haraslin；法罗（3-4-3）Lamhauge；Faero、Vatnhamar、Edmundsson；Danielsen、Turi、Bjartalid、Chukwudi；Samuelsen、Knudsen、Sorensen（Sports Mole 预计首发）。',
  style='斯洛伐克 4-3-3 靠 Hancko 左路推进与 Haraslin 内切，但双中场核心缺阵使推进变直；法罗 3-4-3 低位五后卫、靠 Knudsen 支点与 Samuelsen 反击，4 轮 4 平说明其"拖平"能力强。',
  conf='★', conf_reason='首选主胜 63.53% 与市场 76.54% 差 −13.01pp，属分歧场（模型不追热）；法罗 4 轮全平、斯洛伐克两中场缺阵，降为 ★。',
  single_note='接口 bettingSingle=0，非单关。',
),
'周五008': dict(
  league='欧国联 B 级 B1 组', level='欧国联（国家 B 级赛事·League B）｜B1 组第 5 轮，同级别对话',
  venue='Ljudski vrt（斯洛文尼亚马里博尔；容量与草皮类型：ESPN 接口无对应字段，信息缺失）',
  wx='🌧 小雨，6–8°C，降水概率 19–38%，风速 4–6km/h（wttr.in 逐小时 2026-11-13 19:00–22:00 当地；单源）',
  wx_eff='湿冷夜雨，地面传递受限；斯洛文尼亚本就缺少支点，进攻组织更依赖定位球',
  fund='B1 组前 4 轮：斯洛文尼亚 2 胜 1 平 1 负、5 进 3 失（7 分），瑞士 4 胜 0 平 0 负、11 进 1 失（12 分，小组第一）；同组苏格兰 3-5（4 分）、北马其顿 0-10（0 分）。瑞士 4 轮 11 球、1 失球，是本期攻防最均衡的球队。',
  value='未取得（Transfermarkt 405 WAF）。',
  injury='斯洛文尼亚：David Zec、Erik Janza 停赛（后防两人），Benjamin Sesko（曼联前锋，胫骨伤）预计 2027 年初才复出；瑞士：无停赛，Johan Manzambi（小腿）返回维拉缺席，Freuler/Ndoye/Amdouni 首发。**首发：** 斯洛文尼亚（5-4-1）Oblak；Karnicnik、Brekalo、Bijol、Drkusic、Kuzmic；Matko、Zabukovnik、Gnezda Cerin、Sturm；Vipotnik；瑞士（4-2-3-1）Kobel；Britschgi、Elvedi、Akanji、Rodriguez；Freuler、Xhaka；Ndoye、Amdouni、Vargas；Embolo（Sports Mole 预计首发）。',
  style='斯洛文尼亚五后卫+Oblak 兜底，锋线只剩 Vipotnik 单点；瑞士 4-2-3-1 由 Xhaka 控节奏、Ndoye/Vargas 两翼冲击，攻防转换速度是 B1 组最快。斯洛文尼亚三人缺阵（两后卫+头号射手），结构性受损。',
  conf='★★', conf_reason='首选客胜 59.54% ≥50%，与市场（61.08%）同向、差 −1.54pp，是本期对齐度最高的一场；伤停/首发齐全；身价缺失故不给 ★★★。',
  single_note='接口 bettingSingle=0，非单关。',
),
'周五009': dict(
  league='欧国联 A 级 A2 组', level='欧国联（国家 A 级赛事·League A）｜A2 组第 5 轮，同级别对话',
  venue='Johan Cruijff Arena（荷兰阿姆斯特丹；容量与草皮类型：ESPN 接口无对应字段，信息缺失）',
  wx='🌧 零星小雨，7°C，降水概率 16–18%，风速 8–12km/h（wttr.in 逐小时 2026-11-13 19:00–22:00 当地；单源）',
  wx_eff='湿冷小雨，场地略滑；对荷兰的传控与希腊的反击都属中性影响',
  fund='A2 组前 4 轮：荷兰 2 胜 2 平 0 负、7 进 5 失（8 分），希腊 2 胜 2 平 0 负、5 进 3 失（8 分）；同组德国 3-2（5 分）、塞尔维亚 3-8（0 分）。两队同分同净胜球，本场是小组头名直接对话。',
  value='未取得（Transfermarkt 405 WAF）。',
  injury='荷兰：Van Dijk（队长）、Gravenberch、Kenneth Taylor、Brobbey 全部伤退，Van den Berg 递补；希腊：Christos Zafeiris、Manolis Saliakas 两黄停赛。**首发：** 荷兰（4-2-3-1）Verbruggen；Dumfries、Van Hecke、Timber、Ake；Koopmeiners、De Jong；Malen、Reijnders、Gakpo；Meerdink；希腊（4-2-3-1）Vlachodimos；Rota、Mavropanos、Koulierakis、Tsimikas；Siopis、Kourbelis；Tzolis、Karetsas、Kostoulas；Pavlidis（Sports Mole 预计首发）。',
  style='荷兰 4-2-3-1 由 De Jong/Koopmeiners 出球、Gakpo 左路内切，但 Van Dijk 缺阵使防线指挥与高空球下降；希腊 4-2-3-1 低位+两翼快反，Pavlidis 支点做球。荷兰中卫重组是本场最大变量。',
  conf='★', conf_reason='首选主胜 48.13% 未过 50%，与市场 67.21% 差 −19.08pp，属大幅分歧（L8）；荷兰四主力伤缺，降为 ★。',
  single_note='接口 bettingSingle=0，非单关。',
),
'周五010': dict(
  league='国际赛·友谊赛', level='国际友谊赛（A 级国家队，不计积分/排名权重）｜友谊赛数据不用于正式赛推断',
  venue='La Bombonera（阿根廷布宜诺斯艾利斯；容量与草皮类型：ESPN 接口无对应字段，信息缺失）',
  wx='☁️ 阴，24–26°C，降水概率 10–11%，风速 9–14km/h（wttr.in 逐小时 2026-11-13 19:00–22:00 当地；单源）',
  wx_eff='温和无雨，场地条件理想，利于阿根廷的短传渗透；对乌拉圭的高强度逼抢同样友好',
  fund='友谊赛无积分。阿根廷 Elo 2175（世界第 1），近 5 场 4 胜 1 负；乌拉圭 Elo 1851（第 15 位附近），近 6 场 2 胜 3 平 1 负（Sports Mole 赛前页，Elo 取自 eloratings.net 2026-11-13 快照）。Elo 差 +324（含主场 +65）。',
  value='未取得（Transfermarkt 405 WAF）。',
  injury='信息缺失：Sports Mole 截至 2026-11-13 未发布本场预览（阿根廷队页仅 argentina-vs-benin 等旧预览），比赛页仅有 form/last game/数据模型，无 Team News 段；ESPN 本场 `injuries` 字段为空、`rosters.roster` 为 0 人。**首发：** 未公布（同上，无预计首发来源）。',
  style='阿根廷以控球+梅西/阿尔瓦雷斯肋部配合为主，乌拉圭 Belisario 时代偏高强度逼抢与快速纵向推进；风格相克上阿根廷控球能压缩乌拉圭的反击次数，但友谊赛轮换会削弱强度。',
  conf='★', conf_reason='首选主胜 76.24% 高，但与市场 65.67% 差 +10.57pp 属分歧；且伤停/首发/身价三项缺失、友谊赛战意不可控，按 L46 封顶 ★。',
  single_note='接口 bettingSingle=0，非单关。',
),
'周五011': dict(
  league='国际赛·友谊赛', level='国际友谊赛（A 级国家队，不计积分/排名权重）｜友谊赛数据不用于正式赛推断',
  venue='Estadio Pascual Guerrero（哥伦比亚卡利；容量与草皮类型：ESPN 接口无对应字段，信息缺失）',
  wx='🌧 阵雨，22–24°C，湿度高，降水概率 56–61%，风速 0–2km/h（wttr.in 逐小时 2026-11-13 18:00–21:00 当地；单源）',
  wx_eff='高温高湿+降雨，节奏被拖慢、体能消耗大；对智利的老化中后场不利',
  fund='友谊赛无积分。哥伦比亚 Elo 1990（世界前十附近），智利 Elo 1723（第 39 位附近），Elo 差 +267（含主场 +65）；智利近 6 场 2 胜 2 平 2 负、哥伦比亚近 6 场 4 胜 1 平 1 负（Sports Mole 赛前页）。',
  value='未取得（Transfermarkt 405 WAF）。',
  injury='哥伦比亚：Richard Rios、Luis Diaz（伤缺），Jaminton Campaz 因肌肉不适退出（补招 Oscar Cortes），Lorenzo 招入多名新人；智利：Benjamin Kuscevic（右脚踝扭伤）缺阵，Paulo Diaz 训练中受伤出战成疑，Marcelino Nunez、Matias Sepulveda、Marcelo Morales 不在名单，Maripan 回归。**首发：** 哥伦比亚（4-2-3-1）Vargas；Munoz、Sanchez、Lucumi、Velasquez；Puerta、Lerma；Asprilla、Arias、Perea；Suarez；智利（4-3-3）Vigouroux；Suazo、Villagra、Roman、Ulloa；Pizarro、Loyola、Osorio；Tapia、Gutierrez、Diaz（Sports Mole 预计首发）。',
  style='哥伦比亚 4-2-3-1 靠 Arias/Asprilla 两翼与 Suarez 支点，缺 Luis Diaz 后左路爆点下降；智利 4-3-3 老龄中轴、靠 Tapia 组织与 Gutierrez 反击。整体速度与对抗哥伦比亚占优。',
  conf='★★', conf_reason='首选主胜 68.34% ≥50%，与市场 71.57% 同向、差 −3.23pp；伤停/首发已取得；身价缺失故不给 ★★★。',
  single_note='接口 bettingSingle=0，非单关。',
),
}

# ---------------- 逐场点评（模板「点评」段） ----------------
POINT = {
'周五001': '巴拉圭的身价与个体能力是碾压级，但新加坡湿热夜 + 低位五后卫能把比赛拖成"少机会"，模型因此压住 0-2、把 0-1 排到第一；让球 +3 端模型与市场差 28pp，说明市场预期巴拉圭进球更多，这一分歧只登记、不作方向依据。',
'周五002': '两队防守都漏、进攻都不稳，模型给出的 2 球结构最合理；客胜只比主胜高 6.6pp，方向价值有限，让(-1)负（67.07%）才是本场唯一高置信单项，但它建立在"哈萨克无法净胜"的低门槛上，只作次选。',
'周五003': '冰岛 4 轮失 1 球的防守纪律被模型充分计价，客胜 51.00% 过线但只领先主胜 30pp 中的一部分来自"保加利亚锋线低产"；市场给客胜 55.94% 更高，分歧 −4.94pp 属可接受范围。',
'周五004': '北马其顿 4 轮 0 进球是本场最硬的基本面，但"苏格兰能赢几个"比"能不能赢"难判得多：模型对让(-2)负给到 61.41%、市场只有 39.95%，这是本期最大的让球端分歧，也是模拟盘唯一一注方向性下注的来源。',
'周五005': '德国 4 轮只进 3 球却被市场压到 1.16，是本期的"名气定价"典型；塞尔维亚两后腰停赛削弱中场屏障，但主场夜雨 + Mitrovic 支点让比赛更像 0-1/1-1 的低比分拉锯，模型因此给出 51.17% 客胜与 28.86% 平局。',
'周五006': '爱沙尼亚 4 轮仅失 1 球、卢森堡 2 进球，这场是本期最标准的闷战结构；模型 0-0（15.51%）与 0-1（14.60%）几乎并排，平平（22.86%）是半全场端最高项，方向端没有可下注的确定性。',
'周五007': '法罗 4 轮全平、斯洛伐克两名中场核心（Lobotka/Suslov）缺阵，模型把主胜从 76% 压到 63.53%；但斯洛伐克仍有个体优势，1-0（15.45%）与 1 球（20.82%）构成最合理的低比分取胜剧本。',
'周五008': '斯洛文尼亚三人缺阵（两后卫 + Sesko 长期伤缺）对瑞士是结构性利好，模型与市场差仅 −1.54pp、是本期对齐度最高的一场；瑞士 4 轮 11 球 1 失球，客胜 59.54% 可信度高，唯一悬念是让 1 球能否打出。',
'周五009': '荷兰 Van Dijk/Gravenberch/Taylor/Brobbey 四主力伤退，中卫重组是最大变量，市场仍给主胜 67.21%、模型只给 48.13%，差 −19.08pp；希腊 4 轮不败且擅长低位快反，这场是本期最不该追热的强队主场。',
'周五010': '阿根廷 Elo 世界第一、主场对乌拉圭，方向没有争议；但伤停/首发/身价三项全缺，友谊赛轮换幅度未知，模型 76.24% 对市场 65.67% 的 +10.57pp 更可能是"市场担心轮换"而非模型发现了价值，只作方向参考。',
'周五011': '哥伦比亚缺 Luis Diaz、Rios，智利中后场老化且多人缺阵，主胜 68.34% 与市场 71.57% 基本对齐；但两队都是友谊赛、轮换不可控，2-0/1-0 的比分带比胜负方向更值得看。',
}

def market_line(r):
    if 'HAD' in r['market']:
        mk = r['market']['HAD']; sh = mk['shin']
        return (f"市场去水（Shin） 主胜{pct(sh[0])} / 平{pct(sh[1])} / 客胜{pct(sh[2])}，"
                f"模型差 {r['probs']['gap'][0]*100:+.2f}/{r['probs']['gap'][1]*100:+.2f}/{r['probs']['gap'][2]*100:+.2f}pp；"
                f"体彩 HAD {mk['odds'][0]:.2f}/{mk['odds'][1]:.2f}/{mk['odds'][2]:.2f}")
    hh = r['market']['HHAD']; sh = hh['shin']
    return (f"本场未开胜平负（HAD 池为空），改用让球盘对照：市场去水 让(+{hh['line']})胜{pct(sh[0])} / 让平{pct(sh[1])} / 让负{pct(sh[2])}，"
            f"模型 让(+{hh['line']})胜{pct(r['probs']['HHAD'][0])} / 让平{pct(r['probs']['HHAD'][1])} / 让负{pct(r['probs']['HHAD'][2])}；体彩 {hh['odds'][0]:.2f}/{hh['odds'][1]:.2f}/{hh['odds'][2]:.2f}")

def match_block(num):
    r = M[num]; f = F[num]; pr = r['probs']
    IDX = {'h': 0, 'd': 1, 'a': 2}
    CN = {'h': '主胜', 'd': '平', 'a': '客胜'}
    order = sorted(['h', 'd', 'a'], key=lambda k: -pr['HAD'][IDX[k]])
    first_cn = CN[pr['first']]
    second_cn = CN[order[1]]
    p1 = pct(pr['HAD'][IDX[order[0]]]); p2 = pct(pr['HAD'][IDX[order[1]]])
    had = "首选 **%s**(%s) / 次选 **%s**(%s)" % (CN[order[0]], p1, second_cn, p2)
    if 'HAD' not in r['market']:
        had += "（本场无 HAD 池，为纯模型口径）"
    hh = r['market']['HHAD']; line = hh['line']
    hs = pr['HHAD']
    hh_first = max(range(3), key=lambda i: hs[i])
    hh_name = ["让(%+d)胜" % line, "让(%+d)平" % line, "让(%+d)负" % line]
    hh_second = 1 if hh_first != 1 else 0
    hh_rec = "首选 **%s**(%s) / 次选 **%s**(%s)" % (hh_name[hh_first], pct(hs[hh_first]), hh_name[hh_second], pct(hs[hh_second]))
    sc = top_scores(r, 5)
    sc_txt = ' > '.join(["**%s**(%s)" % (s, pct(p)) for s, p in sc])
    ht = r['probs']['ht_scores']
    ht_txt = ' > '.join(["%s(%s)" % (s, pct(p)) for s, p in ht])
    hf = hafu_top(r, 3)
    hf_txt = ' > '.join(["**%s**(%s)" % (hafu_cn(k), pct(p)) for k, p in hf])
    t2 = pr['top2_ttg']
    ttg_txt = "**%s**：**%s球**(%s) / **%s球**(%s)" % (pr['bucket'], t2[0][0], pct(t2[0][1]), t2[1][0], pct(t2[1][1]))
    kd, kdv = pr['k_dist']; kr, krv = pr['k_rec']
    def ktxt(k):
        return "k=%+d" % k if k != 0 else "k=0（平）"
    diverg = "**众数一致**" if (kd == kr) else "**分布-方向分歧**（以推荐众数为准）"
    fl = CN[pr['first']]
    if r['league'] != 'fifa.friendly':
        recent = "小组赛前 4 轮进失球见基本面段落；λ 主 %.3f / 客 %.3f" % (r['lam']['final'][0], r['lam']['final'][1])
    else:
        recent = "友谊赛，近况见基本面段落；λ 主 %.3f / 客 %.3f" % (r['lam']['final'][0], r['lam']['final'][1])
    return """## %s %s vs %s（%s）

**联赛等级：** %s

⏰ %s（北京 %s %s） ｜ 🏟 %s ｜ %s，影响：%s

%s

**身价对比：** %s

**伤停：** %s

**模型 vs 市场：** 融合概率 主胜%s / 平%s / 客胜%s；%s。λ：主 %.3f / 客 %.3f（总 %.3f）。**单关：** %s

> **比分推演（参考模型，L62-F）：**
> - 球队近期数据：%s。
> - 比赛风格：%s
> - 比分推演：%s。
> - 局势解读：半场 %s；TTG 指向%s（%s球%s / %s球%s），半全场指向%s(%s)。

**推荐：**

| 玩法 | 推荐 |
|:---|:---|
| **比分TOP5** | %s |
| **半全场TOP3** | %s |
| **HAD** | %s |
| **HAFU** | %s |
| **大小球·总进球** | %s |
| **半场比分** | %s |

**置信度：** %s — %s

> %s

**净胜球众数：** 分布众数 %s（%s）｜推荐众数 %s（%s）｜%s；锚点方向=%s。
""" % (
        num, r['home'], r['away'], f['league'], f['level'], r['time'][:5], r['date'], r['time'][:5],
        f['venue'], f['wx'], f['wx_eff'], f['fund'], f['value'], f['injury'],
        pct(pr['HAD'][0]), pct(pr['HAD'][1]), pct(pr['HAD'][2]), market_line(r),
        r['lam']['final'][0], r['lam']['final'][1], sum(r['lam']['final']), f['single_note'],
        recent, f['style'], sc_txt, ht_txt, pr['bucket'], t2[0][0], pct(t2[0][1]), t2[1][0], pct(t2[1][1]),
        hafu_cn(hf[0][0]), pct(hf[0][1]), sc_txt, hf_txt, had, hh_rec, ttg_txt, ht_txt,
        f['conf'], f['conf_reason'], POINT[num], ktxt(kd), pct(kdv), ktxt(kr), pct(krv), diverg, fl)

# ---------------- 总览 ----------------
def overview_rows():
    rows = []
    for n in ORDER:
        r = M[n]; pr = r['probs']; f = F[n]
        idx = {'h':0,'d':1,'a':2}
        order = sorted(['h','d','a'], key=lambda k: -pr['HAD'][idx[k]])
        cn = {'h':'主胜','d':'平','a':'客胜'}
        a = f"{cn[order[0]]} {pct(pr['HAD'][idx[order[0]]])}" + ("（无HAD池）" if 'HAD' not in r['market'] else "")
        b = f"{cn[order[1]]} {pct(pr['HAD'][idx[order[1]]])}"
        rows.append(f"| {n} | {r['home']} vs {r['away']} | {a} | {b} | {f['conf']} |")
    return '\n'.join(rows)

def md_main():
    conf_count = {}
    for n in ORDER: conf_count[F[n]['conf']] = conf_count.get(F[n]['conf'], 0) + 1
    gap_max = max(M.values(), key=lambda r: max(abs(x) for x in (r['probs']['gap'] or [0])) if r['probs']['gap'] else 0)
    nmax = max(M.values(), key=lambda r: max(abs(x) for x in (r['probs']['gap'] or [0])) if r['probs']['gap'] else 0)['num']
    body = []
    body.append(f"""# 【分析】2026-11-13（周五）11场欧国联+国际赛 | 强弱分化明显，让球盘与总进球定成败

> **报告说明：** 本文为赛前**分析报告**（标题标注【分析】），提供方向/比分/总进球等预测推荐。赛后将发布**回测报告**（标题标注【回测】），对比预测与实际结果并统计命中率。历史报告可去主页查找。

> **风险提示：** 本期为体彩**销售日 2026-11-13（周五）在售的整期**，共 11 场（周五001-011）。一级信息中**伤停与预计首发已从 Sports Mole 赛前预览取得（10/11 场，001 亦有）**，但 **身价全期未取得**（Transfermarkt .com/.us 均 HTTP 405「Human Verification」WAF 拦截，football-charts MCP 仅覆盖俱乐部联赛）；010 阿根廷 vs 乌拉圭**伤停/首发均未取得**（Sports Mole 未发布该场预览、ESPN `injuries` 为空、`rosters.roster` 为 0 人）。欧国联各队仅 4 场样本，方差偏大；005/009/004 三场模型与市场分歧 ≥19pp，均按 L8 标注为高不确定性、不作博胆。**理性看待预测，切勿沉迷赌博。**

> **⚠️ 免责声明：** 本文所有分析、预测、推荐仅供学习交流参考，不构成任何投注建议。足球比赛结果具有高度不确定性，任何预测均无法保证准确性。内容仅供参考，如有错漏请谅解。请遵守当地法律法规，理性购彩，量力而行。

> **📊 近5日置信度命中率（滚动统计，截至 2026-11-12，数据源 memory/stats/confidence_stats.md）：** ★★★高 6/8=75.0% ｜ ★★中 22/25=88.0% ｜ ★低 21/25=84.0% ｜ ☆极低 0/0=—。**结论：** 中★★配次选容错仍是本窗口最稳结构（88.0%），★★★ 样本少且 75.0% 反而最低，不宜单独作方向锚。

*每日更新，关注主页获取最新赛事分析*

本期覆盖销售日 2026-11-13（周五）在售的全部 11 场：001 新加坡 vs 巴拉圭（20:00 开球，唯一无 HAD 池场次）、002-009 欧国联小组赛第 5 轮（11-14 凌晨 01:00/03:45）、010 阿根廷 vs 乌拉圭（11-14 07:00）、011 哥伦比亚 vs 智利（11-14 08:00）。除 001 与 010/011 三场友谊赛外，8 场欧国联全部为同组内第 5 轮对话（A2/B1/C3/C4 各两场），强弱分层明显：B1 组北马其顿 4 轮 0 球 0 分、C4 组冰岛 4 轮仅失 1 球、A2 组德国 4 轮只进 3 球却被市场给到 1.16 客胜——本期的核心矛盾集中在"市场热度"与"小组进攻数据"的背离。数据来源：体彩计算器接口（2026-11-13 抓取，`reports/data/20261113_calc_raw.json`）、ESPN 赛事/积分榜接口、eloratings.net、Sports Mole 赛前预览、wttr.in；融合模型输出 `reports/data/20261113_model_output.json`。

## 总览

| 编号 | 对阵 | 首选 | 次选 | 置信度 |
|:---:|:---|:---:|:---:|:---:|
{overview_rows()}

> 本期 {' / '.join([f'{k} {v} 场' for k, v in sorted(conf_count.items())])}；无 ★★★（身价全期缺失）。001 无 HAD 池，首选为纯模型口径，其让球(+3)端模型 72.28% 对市场 44.25%、差 +28.03pp，与 004/005/009 同列高分歧；其余 10 场模型首选与市场去水首选**无一场方向反转**，但 7 场幅度差 ≥8pp（004 −20.39pp、005 −28.81pp、009 −19.08pp、007 −13.01pp 为模型不追热；006 +12.78pp、010 +10.57pp、002 +8.68pp 为模型高于市场）。**单关：** 接口全期 `bettingSingle=0`，未开单关，故本期不做单关平局上修；若你的投注端显示某场可单关，请以投注端为准并告知，我再按上修口径重算。

> **信息源核验（2026-11-13 抓取，原始快照 `reports/data/`）：** 场地＝ESPN 赛事接口 `site.api.espn.com`（11/11 HTTP 200，`competitions[0].venue`）；天气＝wttr.in 逐小时（11/11 HTTP 200，按球场城市）；伤停/预计首发＝Sports Mole 赛前预览（10/11 场 200，原始文本 `reports/data/raw_sm_*.txt`；010 未发布预览）；身价＝Transfermarkt `.com`/`.us` 均 HTTP 405 WAF「Just a moment/Access Denied」、sofascore 403、football-charts MCP 无国家队联赛，**无可用数值**；首发官方名单＝赛前未公布（ESPN `rosters.roster` 全为 0 人），报告中的首发均为 Sports Mole **预计**首发，非官方。

""")
    for n in ORDER:
        body.append(match_block(n))
    # ---------------- 综合推荐汇总（模板 7 列） ----------------
    def lowest2_hhad(n):
        r = M[n]; hh = r['market']['HHAD']; line = hh['line']
        idx = sorted(range(3), key=lambda i: hh['odds'][i])
        nm = ["让(%+d)胜" % line, "让(%+d)平" % line, "让(%+d)负" % line]
        return nm[idx[0]], hh['odds'][idx[0]], nm[idx[1]], hh['odds'][idx[1]]

    CN3 = {'h': '主胜', 'd': '平', 'a': '客胜'}
    IDX3 = {'h': 0, 'd': 1, 'a': 2}
    body.append("## 综合推荐汇总\n\n| 编号 | 对阵 | 胜平负首选 | 胜平负次选 | 让球首选 | 让球次选 | 总进球 |\n"
                "|:---:|:---|:---:|:---:|:---:|:---:|:---|\n")
    rows = []
    for n in ORDER:
        r = M[n]; pr = r['probs']
        order = sorted(['h', 'd', 'a'], key=lambda k: -pr['HAD'][IDX3[k]])
        f1 = CN3[order[0]] + ' ' + pct(pr['HAD'][IDX3[order[0]]])
        f2 = CN3[order[1]] + ' ' + pct(pr['HAD'][IDX3[order[1]]])
        if 'HAD' not in r['market']:
            f1 += '（无HAD池）'
        h1, o1, h2, o2 = lowest2_hhad(n)
        t2 = pr['top2_ttg']
        tt = '%s球 %s / %s球 %s' % (t2[0][0], pct(t2[0][1]), t2[1][0], pct(t2[1][1]))
        rows.append('| ' + ' | '.join([n, r['home'] + ' vs ' + r['away'], f1, f2,
                                       h1 + ' %.2f' % o1, h2 + ' %.2f' % o2, tt]) + ' |')
    body.append('\n'.join(rows) + '\n')
    body.append("""
> **读表说明：** 胜平负首选/次选取模型融合概率前二；让球首选/次选取该场让球盘赔率最低的两项（市场口径，仅作对照，不代表模型首选）；总进球取模型前两档。001 无胜平负池，其胜负列为纯模型口径；全期 11 场投注单 `bettingSingle` 均为 0，未开单关。

> **虚拟本金凯利模拟盘注单见** `reports/sim/kelly_sim_20261113.md`（虚拟资金，不构成投注建议；串关不进模拟盘）。

""")

    # ---------------- 搏冷推荐汇总（模板 7 列） ----------------
    body.append("## 搏冷推荐汇总\n\n| 编号 | 对阵 | 搏冷方向 | 模型概率 | 市场去水 | 分歧 | 类型 |\n"
                "|:---:|:---|:---:|:---:|:---:|:---:|:---|\n")
    picks = [
        ('周五005', 1, '价值追击：德国 4 轮仅 3 球，客胜被压到 1.16；塞尔维亚两后腰停赛但主场夜雨利好防反，模型给平局 28.86%'),
        ('周五006', 2, '价值追击：爱沙尼亚 4 轮不败仅失 1 球，卢森堡中卫 Carlson 停赛、锋线低产，客胜被市场低估'),
        ('周五004', 1, '价值追击：苏格兰 4 轮仅 3 球、McTominay 刚伤愈；北马其顿 4 轮 0 球但客场摆大巴，闷平概率被压'),
        ('周五010', 0, '价值追击：阿根廷主场对乌拉圭，市场担心友谊赛轮换把主胜压到 65.67%，模型仍给 76.24%'),
        ('周五009', 2, '方向分歧：荷兰 Van Dijk/Gravenberch/Taylor/Brobbey 四主力伤退，希腊 4 轮不败且擅长低位快反'),
    ]
    rows = []
    for n, i, why in picks:
        r = M[n]; pr = r['probs']; mk = r['market']['HAD']
        rows.append('| ' + ' | '.join([n, r['home'] + ' vs ' + r['away'], CN3[['h','d','a'][i]],
                                       pct(pr['HAD'][i]), pct(mk['shin'][i]),
                                       '%+.2fpp' % ((pr['HAD'][i] - mk['shin'][i]) * 100), '价值追击']) + ' |')
    body.append('\n'.join(rows) + '\n')
    body.append("""
> 五场均为「模型概率 − 市场去水 ≥8pp」的选项，按 L8 只做小注娱乐、不作博胆、不进模拟盘主仓。**市场过热场次（去水支持率 >55%）：** 003 客胜 55.94%、004 主胜 85.30%、005 客胜 79.98%、007 主胜 76.54%、008 客胜 61.08%、009 主胜 67.21%、010 主胜 65.67%、011 主胜 71.57%（001 无胜平负池，其让球(+3)端市场去水 44.25%）。其中 005 的 −28.81pp 是本轮最大背离，但德国个体能力足以单点解决比赛，冷门不中属常态。

""")

    # ---------------- 串关 ----------------
    def ho(n, i): return M[n]['market']['HAD']['odds'][i]
    def hho(n, i): return M[n]['market']['HHAD']['odds'][i]
    def to(n, g): return M[n]['market']['TTG_odds'][g]
    def fto(n, k): return M[n]['market']['HAFU_odds'][k]
    def co(n, s): return M[n]['market']['CRS_odds'][s]

    body.append("## 串关思路\n\n### 方向串（胜平负）\n\n| 方案 | 场次 | 估算赔率 | 风险 |\n|:---|:---|:---:|:---|\n")
    rows = [
        '| 稳健方向串 | 周五008 客胜 @%.2f × 周五011 主胜 @%.2f | ~%.2f | 中 |' % (ho('周五008', 2), ho('周五011', 0), ho('周五008', 2) * ho('周五011', 0)),
        '| 对齐方向串 | 周五003 客胜 @%.2f × 周五010 主胜 @%.2f | ~%.2f | 中 |' % (ho('周五003', 2), ho('周五010', 0), ho('周五003', 2) * ho('周五010', 0)),
        '| 低赔防守串 | 周五004 主胜 @%.2f × 周五007 主胜 @%.2f | ~%.2f | 低中 |' % (ho('周五004', 0), ho('周五007', 0), ho('周五004', 0) * ho('周五007', 0)),
    ]
    body.append('\n'.join(rows) + '\n')
    body.append("""
> **稳健方向串：** 008 瑞士（59.54%）与 011 哥伦比亚（68.34%）是「方向清晰＋市场对齐＋伤停首发齐全」的两场，串后约 1.94 倍，容错最高。
> **对齐方向串：** 003 冰岛客胜（51.00%）与 010 阿根廷主胜（76.24%）模型与市场同向，但 010 伤停/首发一手源缺失，属「方向可信、信息不全」，列第二档。
> **低赔防守串：** 004 苏格兰对 4 轮 0 球 0 分的北马其顿，主胜赔率仅 1.09，与 007 斯洛伐克主胜串联后 1.32 倍，适合做防守底仓；代价是收益极薄。

### 让球串（让球胜平负）

| 方案 | 场次 | 估算赔率 | 风险 |
|:---|:---|:---:|:---|
""")
    rows = [
        '| 稳健让球串 | 周五002 让(-1)负 @%.2f × 周五006 让(-1)负 @%.2f | ~%.2f | 中 |' % (hho('周五002', 2), hho('周五006', 2), hho('周五002', 2) * hho('周五006', 2)),
        '| 价值让球串 | 周五008 让(+1)负 @%.2f × 周五011 让(-1)胜 @%.2f | ~%.2f | 中高 |' % (hho('周五008', 2), hho('周五011', 0), hho('周五008', 2) * hho('周五011', 0)),
    ]
    body.append('\n'.join(rows) + '\n')
    body.append("""
> **稳健让球串：** 002 摩尔多瓦让 1 球负（模型 67.07%、市场 63.34%）与 006 卢森堡让 1 球负（模型 70.49%、市场 57.07%）都是「主队净胜 2 球以上概率低」，两端同源但门槛低。
> **价值让球串：** 008 瑞士让 1 球负（模型 32.67%、市场 31.38%）与 011 哥伦比亚让 1 球胜（模型 42.28%、市场 44.01%），两腿都与市场吻合、赔率更高，属赔率第二的次选组合。让球腿仅登记，不进模拟盘。

### 混合串（半全场+方向混合）

| 方案 | 类型 | 场次 | 估算赔率 | 风险 |
|:---|:---|:---|:---:|:---|
""")
    rows = [
        '| 半全场串A | 纯半全场 | 周五004 胜胜 @%.2f × 周五008 负负 @%.2f × 周五002 平平 @%.2f | ~%.2f | 高 |' % (fto('周五004', 'hh'), fto('周五008', 'aa'), fto('周五002', 'dd'), fto('周五004', 'hh') * fto('周五008', 'aa') * fto('周五002', 'dd')),
        '| 半全场串B | 纯半全场 | 周五011 胜胜 @%.2f × 周五003 负负 @%.2f × 周五006 平平 @%.2f | ~%.2f | 高 |' % (fto('周五011', 'hh'), fto('周五003', 'aa'), fto('周五006', 'dd'), fto('周五011', 'hh') * fto('周五003', 'aa') * fto('周五006', 'dd')),
        '| 方向+半全场A | 方向+半全场 | 周五011 主胜 @%.2f × 周五004 胜胜 @%.2f | ~%.2f | 低中 |' % (ho('周五011', 0), fto('周五004', 'hh'), ho('周五011', 0) * fto('周五004', 'hh')),
        '| 方向+半全场B | 方向+半全场 | 周五008 客胜 @%.2f × 周五007 胜胜 @%.2f | ~%.2f | 中 |' % (ho('周五008', 2), fto('周五007', 'hh'), ho('周五008', 2) * fto('周五007', 'hh')),
        '| 连续编号混合串① | 方向+半全场 | 周五002 客胜 @%.2f × 周五003 负负 @%.2f | ~%.2f | 中高 |' % (ho('周五002', 2), fto('周五003', 'aa'), ho('周五002', 2) * fto('周五003', 'aa')),
        '| 连续编号混合串② | 方向+半全场 | 周五010 主胜 @%.2f × 周五011 胜胜 @%.2f | ~%.2f | 中 |' % (ho('周五010', 0), fto('周五011', 'hh'), ho('周五010', 0) * fto('周五011', 'hh')),
    ]
    body.append('\n'.join(rows) + '\n')
    body.append("""
> 半全场串A/B 为三串一，串内路径强制差异化（胜胜/负负/平平），禁止三场全取同一路径；A 的 004 胜胜（41.83%）＋008 负负（37.29%）＋002 平平（16.01%）是本期最稳的三条路径。方向+半全场 A/B 用一场胜负做保险、一场半全场拉赔率；连续编号①为 002+003、②为 010+011，串内编号相邻，满足连续编号硬约束。

""")

    # ---------------- 娱乐串 ----------------
    body.append("""### 娱乐串（高赔率组合）

> **⚠️ 娱乐串风险提示：** 以下方案均为高赔率组合，单次命中概率极低（通常<5%），仅供娱乐参考，切勿重注。建议每注投入不超过总资金的 1%-2%，量力而行，理性购彩。高赔率意味着高风险，未中奖为常态。

> **📋 选场核心原则：** 娱乐串选场以基本面（伤停/战意/状态/赛制）为主、模型概率仅作辅助。本期可用抓手：北马其顿 4 轮 0 球、法罗 4 轮全平、爱沙尼亚 4 轮仅失 1 球、斯洛文尼亚三人缺阵、荷兰四主力伤退、斯洛伐克双中场缺阵。

> **🚫 法甲排除：** 本期 11 场无任何法甲场次（欧国联 8 场＋国际友谊赛 3 场），非 PSG 法甲场次 N=0 → 纳入 0 场。

> **🏗️ 结构说明：** 四个子分类齐全，每子分类 2 个原方案 + 2 个连续编号方案；比分串另含单挑比分①②，合计 18 个方案。本期 >8 场，原方案以三串一为主；同一串内各场进球档位/半全场路径强制差异化。

#### 高赔总进球串（4个方案）

| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |
|:---|:---|:---|:---:|:---|
""")
    rows = [
        '| 总进球串A | 周五001 2球 / 周五008 1球 / 周五010 3球 | %.2f × %.2f × %.2f | ~%.2f | 高 |' % (to('周五001', '2'), to('周五008', '1'), to('周五010', '3'), to('周五001', '2') * to('周五008', '1') * to('周五010', '3')),
        '| 总进球串B | 周五011 2球 / 周五004 3球 / 周五006 1球 | %.2f × %.2f × %.2f | ~%.2f | 高 |' % (to('周五011', '2'), to('周五004', '3'), to('周五006', '1'), to('周五011', '2') * to('周五004', '3') * to('周五006', '1')),
        '| 连续编号总进球串① | 周五002 2球 / 周五003 1球 | %.2f × %.2f | ~%.2f | 高 |' % (to('周五002', '2'), to('周五003', '1'), to('周五002', '2') * to('周五003', '1')),
        '| 连续编号总进球串② | 周五010 2球 / 周五011 3球 | %.2f × %.2f | ~%.2f | 高 |' % (to('周五010', '2'), to('周五011', '3'), to('周五010', '2') * to('周五011', '3')),
    ]
    body.append('\n'.join(rows) + '\n')
    body.append("""
> A/B 均为三串一且串内档位互不相同（A：2/1/3 球；B：2/3/1 球），避免「全取 2 球」的机械同源；连续编号①为 002+003、②为 010+011。核心逻辑：本期 λ 总和集中在 1.9-2.7，2 球档是各场共同首选，1 球/3 球用于拉高赔率。

#### 高赔半全场串（4个方案）

| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |
|:---|:---|:---|:---:|:---|
""")
    rows = [
        '| 高赔半全场串A | 周五003 负负 / 周五007 平胜 / 周五010 胜胜 | %.2f × %.2f × %.2f | ~%.2f | 高 |' % (fto('周五003', 'aa'), fto('周五007', 'dh'), fto('周五010', 'hh'), fto('周五003', 'aa') * fto('周五007', 'dh') * fto('周五010', 'hh')),
        '| 高赔半全场串B | 周五004 胜胜 / 周五006 负负 / 周五009 平平 | %.2f × %.2f × %.2f | ~%.2f | 高 |' % (fto('周五004', 'hh'), fto('周五006', 'aa'), fto('周五009', 'dd'), fto('周五004', 'hh') * fto('周五006', 'aa') * fto('周五009', 'dd')),
        '| 连续编号高赔半全场串① | 周五005 负负 / 周五006 平平 | %.2f × %.2f | ~%.2f | 中高 |' % (fto('周五005', 'aa'), fto('周五006', 'dd'), fto('周五005', 'aa') * fto('周五006', 'dd')),
        '| 连续编号高赔半全场串② | 周五010 胜胜 / 周五011 平胜 | %.2f × %.2f | ~%.2f | 中高 |' % (fto('周五010', 'hh'), fto('周五011', 'dh'), fto('周五010', 'hh') * fto('周五011', 'dh')),
    ]
    body.append('\n'.join(rows) + '\n')
    body.append("""
> 串A/B 为三串一、串内路径互不相同（A：负负/平胜/胜胜；B：胜胜/负负/平平），与「混合串」中的纯半全场 A/B 取腿不同，避免两章重复；连续编号①为 005+006、②为 010+011。010 胜胜（52.11%）是本期半全场最高项，011 平胜（21.86%）与 007 平胜（21.10%）是「半场僵持、下半场破门」的典型剧本，009 平平（17.43%）对应荷兰中卫重组后的半场试探。

#### 半全场混合总进球串（4个方案）

| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |
|:---|:---|:---|:---:|:---|
""")
    rows = [
        '| 混合串A | 周五011 胜胜 / 周五008 2球 | %.2f × %.2f | ~%.2f | 高 |' % (fto('周五011', 'hh'), to('周五008', '2'), fto('周五011', 'hh') * to('周五008', '2')),
        '| 混合串B | 周五004 胜胜 / 周五005 1球 | %.2f × %.2f | ~%.2f | 高 |' % (fto('周五004', 'hh'), to('周五005', '1'), fto('周五004', 'hh') * to('周五005', '1')),
        '| 连续编号混合串① | 周五002 平平 / 周五003 2球 | %.2f × %.2f | ~%.2f | 极高 |' % (fto('周五002', 'dd'), to('周五003', '2'), fto('周五002', 'dd') * to('周五003', '2')),
        '| 连续编号混合串② | 周五010 平胜 / 周五011 2球 | %.2f × %.2f | ~%.2f | 极高 |' % (fto('周五010', 'dh'), to('周五011', '2'), fto('周五010', 'dh') * to('周五011', '2')),
    ]
    body.append('\n'.join(rows) + '\n')
    body.append("""
> 混合总进球串把「半场领先剧本」与「总进球档位」分开下注，避免同一场同时押半全场与比分造成同源叠加；连续编号①为 002+003、②为 010+011。

#### 比分串（6个方案：2串 + 2连续编号 + 2单挑）

| 方案 | 类型 | 场次 | 估算赔率 | 风险 |
|:---|:---|:---|:---:|:---|
""")
    rows = [
        '| 稳健比分串 | 双锚点同向 | 周五011 2-0 @%.2f × 周五004 1-0 @%.2f | ~%.2f | 高 |' % (co('周五011', '2-0'), co('周五004', '1-0'), co('周五011', '2-0') * co('周五004', '1-0')),
        '| 搏冷比分串 | 剧本：强队主场被逼平 | 周五005 1-1 @%.2f × 周五009 1-1 @%.2f | ~%.2f | 极高 |' % (co('周五005', '1-1'), co('周五009', '1-1'), co('周五005', '1-1') * co('周五009', '1-1')),
        '| 连续编号比分串① | 相邻 004+005 | 周五004 1-0 @%.2f × 周五005 0-1 @%.2f | ~%.2f | 高 |' % (co('周五004', '1-0'), co('周五005', '0-1'), co('周五004', '1-0') * co('周五005', '0-1')),
        '| 连续编号比分串② | 相邻 006+007 | 周五006 0-0 @%.2f × 周五007 1-0 @%.2f | ~%.2f | 高 |' % (co('周五006', '0-0'), co('周五007', '1-0'), co('周五006', '0-0') * co('周五007', '1-0')),
        '| 单挑比分① | 单注 | 周五001 0-1 @%.2f | — | 单注 |' % co('周五001', '0-1'),
        '| 单挑比分② | 单注 | 周五005 0-1 @%.2f | — | 单注 |' % co('周五005', '0-1'),
    ]
    body.append('\n'.join(rows) + '\n')
    body.append("""
> **比分推演口径：** 稳健/连续编号串先取该场无条件净胜球众数 k*，再在带内按联合概率取首选（011 2-0 15.12%、004 1-0 15.62%、007 1-0 15.45%），候选均与 HAD 首选方向一致，未触发「锚点-方向分歧」。
> **搏冷比分串（反向推理）：** 005 德国 4 轮 3 球＋塞尔维亚主场夜雨防反 → 1-1；009 荷兰四主力伤退、希腊低位快反 → 1-1。两场均取 1 个比分（其余候选 p<8% 或赔率<8.00），未凑第二选项。
> **连续编号比分串：** ①004+005、②006+007，串内编号相邻，满足连续编号硬约束，允许复用同一编号段。
> **单挑比分①/②：** 001 0-1（模型 15.25%、赔率 9.00）、005 0-1（模型 15.54%、赔率 10.00），均满足 p≥8%、赔率≥8.00，且不跨净胜球带。

""")

    # ---------------- 本轮规律 ----------------
    body.append("""## 本轮规律

1. **「名气定价」集中在传统强队的低产小组赛。** 005 德国 4 轮只进 3 球却被市场压到客胜 1.16（去水 79.98%），模型仅 51.17%，差 −28.81pp；同类还有 004（−20.39pp）、009（−19.08pp）、007（−13.01pp），四场全部是「强队名气 vs 小组低产」。这类场次模型不追热，但也不构成反向博胆。
2. **C 级组的比分结构高度分散。** C3 组场均 2.75 球被斯洛伐克 9-2 抬升、C4 组仅 1.75 球，同一级别内部差异比级别之间更大；006 的 0-0（15.51%）与 003 的 0-1（14.15%）都落在低进球结构，直接导致本期大量比分候选集中在 1-1/1-0/0-0/0-1 四个值上。
3. **平局概率被市场系统性低估。** 005（平 28.86% vs 13.13%）、004（23.19% vs 11.67%）、009（27.98% vs 19.32%）、006（32.96% vs 29.52%）四场模型平局都高于市场，共同点是双方都缺稳定终结点；这也是本期搏冷汇总五条中三条指向平局的原因。
4. **信息完整度决定了置信度上限。** 8 场欧国联的伤停与预计首发全部取得（Sports Mole），010 三项全缺、全期身价缺失，因此本期无一场 ★★★；★★ 四场（003/004/008/011）恰好也是「伤停首发齐全＋市场对齐或分歧可解释」的四场，信息完整度与置信度排序基本重合。

""")

    # ---------------- 写在最后 ----------------
    body.append("""## ☕ 写在最后

每一篇分析都倾注了大量心血，全部方案免费分享，不设任何门槛。

若觉得有所收获，可请博主赏一杯咖啡——不是要求，而是鼓励。

盈利了，一杯咖啡庆祝好运；未盈利也不必心急，坚持对的逻辑，收获只是时间问题。

你们的支持，是我持续输出的动力。
""")
    md = '\n'.join(body)
    md = re.sub(r'(\|:[-:|\s]+\|)\n\n(\| )', r'\1\n\2', md)
    md = re.sub(r'\n{3,}', '\n\n', md)
    return md


md = md_main()
os.makedirs('reports/analysis', exist_ok=True)
io.open('reports/analysis/20261113_analysis_zhihu.md', 'w', encoding='utf-8').write(md)
print('report chars', len(md))
