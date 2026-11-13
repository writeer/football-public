# -*- coding: utf-8 -*-
"""2026-11-04 预测归档 + 知乎报告生成（数据取自 model_output 与官方赔率快照）"""
import json, io, os

mo = json.load(io.open('reports/data/20261104_model_output.json', encoding='utf-8'))
raw = json.load(io.open('reports/data/20261104_matches.json', encoding='utf-8'))
RD = {x['num']: x for x in raw}

M = {
 '周三001': dict(city='浦项', stadium='Steelyard Stadium（浦项钢园球场）', status='正常',
   value=(6.70, 17.00), url=('https://www.transfermarkt.com/pohang-steelers/startseite/verein/311',
     'https://www.transfermarkt.com/gamba-osaka/startseite/verein/596'),
   form='浦项：韩K联第9，亚冠东亚区3战0分、进0失7（垫底）；钢巴：J1第16（13轮14:21，场均1.08/1.62），亚冠东亚区第3、近3轮全胜。',
   recent='浦项亚冠3战0球；钢巴亚冠3连胜（冲击4连胜）。',
   inj='浦项——全珉洸（红牌停赛）、朱宁约（累计黄牌停赛）2人，无伤病；钢巴——6人伤缺：荒木琉偉（肘）、三浦弦太（膝）、半田陸（膝）、横井裕也（膝）、奥抜侃志（足）、植中朝日（膝）。来源：中文平台/自媒体（虎扑、新浪），**未验证**；未取到 Fotmob/Transfermarkt 一手名单。',
   inj_level='参考（未验证）',
   h2h='两队亚冠层面首次交手，无历史样本。',
   level='亚冠精英（跨国俱乐部赛事）｜韩K联 vs J1，J1 高约1档；主队亚冠3战0球，等级差先验偏向客队',
   tier='闷战超小球(0-1球)', tier_note='0球10.1%＋1球19.7%＝29.8%，为全轮最高band（L266低端预留）；模型单点最高是2球27.2%',
   ttg_pick=('2', '1'), conf='★', first='away', second='draw', hc=('push', 'lose'),
   note='客队6人伤停集中在门将与后卫线，但主队亚冠3战0球，进攻端更不可信。方向首选39.2%不到四成，本场只做观察、不进任何串关。让(+1)胜59.9%是结构腿（等于主队不败），按 L268 取让平21.5%、让负18.6%。',
   risk='客队防线残阵（6人）／首选39.2%<45%'),
 '周三002': dict(city='武里南', stadium='Chang Arena（昌竞技场）', status='正常',
   value=(15.10, 21.93), url=('https://www.transfermarkt.com/buriram-united/startseite/verein/25449',
     'https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query=Kashima+Antlers'),
   form='布里兰：泰超第5（6轮11:7），亚冠东亚区第13；鹿岛：J1第1，亚冠东亚区第2。',
   recent='布里兰泰超6轮11:7；鹿岛J1榜首、亚冠东亚区第2。',
   inj='双方均未检索到公开伤停名单（Fotmob 无 unavailable 列表、TM 缺阵栏为空）。**按“无重大减员”处理，来源缺失、标注未验证。**',
   inj_level='缺失（未验证）',
   h2h='两队近年无正式交锋记录。',
   level='亚冠精英｜泰超 vs J1，J1 高约2档；客队为东亚区第2、联赛领头羊',
   tier='常规正常球(2-3球)', tier_note='2球25.5%、3球22.0%',
   ttg_pick=('2', '3'), conf='★★', first='away', second='draw', hc=('lose', 'push'),
   note='客队纸面与状态双优，但泰超主场气候与草皮是变量。方向首选44.7%<45%，按 L268 本场让球腿不进串关。让(+1)胜54.4%属结构腿，取让负23.6%、让平21.9%。',
   risk='客队伤停信息缺失'),
 '周三003': dict(city='雷恩', stadium='Roazhon Park（罗阿宗公园）', status='正常',
   value=(253.40, 185.65), url=('https://www.transfermarkt.com/stade-rennais/startseite/verein/273',
     'https://www.transfermarkt.com/olympiacos/startseite/verein/412'),
   form='雷恩：法甲第5（9轮20:19，场均2.22/2.11），欧联第13；奥林匹亚科斯：希超第2（9轮15:4、5连胜），欧联第5。',
   recent='雷恩9轮20:19（攻强守漏）；奥林匹亚科斯9轮15:4、5连胜。',
   inj='雷恩——Brice Samba（大腿撞伤）、Estéban Lepaul（踝扭伤）、Ayanda Sishuba（无报名资格）；奥林匹亚科斯——Ayoub El Kaabi（伤）、Yusuf Yazıcı（无报名资格）。来源：Fotmob + Transfermarkt（一手）。',
   inj_level='一手（Fotmob/TM）',
   h2h='欧战层面近年无交手，交锋信息缺失。',
   level='欧罗巴（跨国俱乐部赛事）｜法甲 vs 希超，法甲高约1档；**跨联赛赛事，法甲平局上修（规则69）不适用**',
   tier='常规正常球(2-3球)', tier_note='2球25.5%、3球22.0%',
   ttg_pick=('2', '3'), conf='★★', first='home', second='draw', hc=('home', 'push'),
   note='雷恩攻强守漏（场均失2.11），奥林匹亚科斯防守极稳（场均失0.44）但客场。主胜44.7%、市场39.9%，分歧+4.8pp 同向。让(-1)负54.4%属结构腿（主队不赢2球），按 L268 取让胜23.6%、让平21.9%。',
   risk='主队防线场均失2.11／首选44.7%<45%'),
 '周三004': dict(city='伊斯坦布尔', stadium='Şükrü Saracoğlu（Chobani Stadyumu）', status='正常',
   value=(261.20, 1090.00), url=('https://www.transfermarkt.com/fenerbahce/startseite/verein/36',
     'https://www.transfermarkt.com/fc-liverpool/startseite/verein/31'),
   form='费内巴切：土超第6（10轮24:10），欧冠第31；利物浦：英超第5（9轮11:9），欧冠第4，近5轮2胜2平1负。',
   recent='费内巴切土超10轮24:10；利物浦近5轮2胜2平1负。',
   inj='费内巴切——Mert Hakan Yandaş 等（TM 缺阵栏，名单截断）；利物浦——7人：远藤航、基耶萨（无报名资格）、弗林蓬（肌肉）、亚罗什（膝手术）、莱奥尼（十字韧带撕裂）、布拉德利（膝手术）、埃基蒂克（跟腱断裂）；格拉芬贝赫（脚跟）未随队，索博斯洛伊已替补复出。来源：利物浦官网 + Transfermarkt + Fotmob（一手）。',
   inj_level='一手（俱乐部官网/TM/Fotmob）',
   h2h='两队欧冠近年无交手。',
   level='欧冠｜土超 vs 英超，英超高约2档；等级差先验强烈偏向客队，但客队7人减员',
   tier='常规正常球(2-3球)', tier_note='2球22.9%、3球22.4%',
   ttg_pick=('2', '3'), conf='★', first='away', second='home', hc=('lose', 'push'),
   note='模型客胜46.4%、市场66.0%，**分歧-19.6pp**（全轮第二大）：市场按“英超碾压”定价，模型按利物浦7人减员与客场折扣。让(+1)胜52.8%属结构腿，取让负26.0%、让平21.2%。',
   risk='模型-市场分歧19.6pp／利物浦7人残阵'),
 '周三005': dict(city='莱比锡', stadium='Red Bull Arena（红牛竞技场）', status='正常',
   value=(514.95, 1500.00), url=('https://www.transfermarkt.com/rb-leipzig/startseite/verein/23826',
     'https://www.transfermarkt.com/manchester-city/startseite/verein/281'),
   form='莱比锡：德甲第4（8轮22:11，场均2.75/1.38），欧冠第28；曼城：英超第2（9轮20:10），欧冠第12，近5轮3胜2负。',
   recent='莱比锡8轮22:11；曼城近5轮3胜2负。',
   inj='莱比锡——Ouedraogo（肩部手术，预计12月复出）、Guiu（肌肉）、Estève（撞伤成疑）、Finkgräfe（大腿）、Zingerle（无报名）；曼城——多纳鲁马、哈兰德、多库、迪亚斯等全员随队，无重大伤停。来源：曼城官网 + Transfermarkt + Fotmob（一手）。',
   inj_level='一手（俱乐部官网/TM/Fotmob）',
   h2h='两队欧冠近年无交手。',
   level='欧冠｜德甲 vs 英超，两个联赛相邻（≤1档），等级差不构成跨级',
   tier='常规正常球(2-3球)', tier_note='3球21.7%、2球19.6%；λ=3.45 偏高但单点众数仍在3球',
   ttg_pick=('3', '2'), conf='★', first='away', second='home', hc=('lose', 'push'),
   note='双方攻强守有洞（莱比锡场均2.75进、曼城2.22进），λ合计3.45。模型客胜42.6%、市场65.0%，**分歧-22.4pp（全轮最大）**，市场明显过热。让(+1)胜56.7%属结构腿，取让负23.9%、让平19.3%。',
   risk='模型-市场分歧22.4pp／市场过热'),
 '周三006': dict(city='波尔图', stadium='Estádio do Dragão（巨龙球场）', status='正常',
   value=(471.50, 425.00), url=('https://www.transfermarkt.com/fc-porto/startseite/verein/720',
     'https://www.transfermarkt.com/ssc-napoli/startseite/verein/6195'),
   form='波尔图：葡超第1（10轮25:4、5连胜），欧冠第35；那不勒斯：意甲第8（10轮17:13），欧冠第24。',
   recent='波尔图10轮25:4、5连胜；那不勒斯10轮17:13。',
   inj='波尔图——William Gomes、Vasco Sousa（伤）、Pietuszewski（大腿成疑）、Zaidu（膝成疑）、Smalling（体能/未报名）；那不勒斯——**10人缺阵**：Alisson Santos、Badiashile、Buongiorno、Di Lorenzo、Favasuli、Lobotka、Neres、Olivera、Spinazzola、Marianiuk（无报名），De Bruyne（大腿成疑）。来源：Fotmob（一手）+ 罗马体育报中文转载（**未验证**）。',
   inj_level='一手（Fotmob）＋参考（未验证）',
   h2h='两队欧冠近年无交手。',
   level='欧冠｜葡超 vs 意甲，意甲高约1档；但客队10人减员抵消等级差',
   tier='常规正常球(2-3球)', tier_note='2球26.6%、3球21.4%',
   ttg_pick=('2', '3'), conf='★★', first='home', second='draw', hc=('home', 'push'),
   note='那不勒斯10人缺阵（含德布劳内成疑），规则32 减员降级生效。主胜49.4%、市场46.7%，同向+2.7pp。让(-1)负49.7%属结构腿，取让胜26.6%、让平23.7%。',
   risk='客队10人残阵／主队欧冠场场丢球'),
 '周三007': dict(city='埃因霍温', stadium='Philips Stadion（飞利浦球场）', status='正常',
   value=(306.50, 238.20), url=('https://www.transfermarkt.com/psv/startseite/verein/383',
     'https://www.transfermarkt.com/club-brugge/startseite/verein/2282'),
   form='PSV：荷甲第3（11轮35:13，场均3.18/1.18，O2.5 81.8%），欧冠第21；布鲁日：比甲第1（10轮26:8、5连胜，O2.5 80%），欧冠第13。',
   recent='PSV 11轮35:13；布鲁日10轮26:8、5连胜。',
   inj='PSV——Wanner、Nagalo、Lammers、Pléa、Schouten（5人）；布鲁日——Ordóñez（1人）。来源：Fotmob（一手）。',
   inj_level='一手（Fotmob）',
   h2h='两队欧战近年无交手。',
   level='欧冠｜荷甲 vs 比甲，两个联赛相邻（≤1档）',
   tier='超大球(5-6球)', tier_note='λ=4.05 为全轮最高；P(≥5球)=38.1% 高于单点4球19.5%，按 L266 落高端预留位；球数TOP2 4球/5球',
   ttg_pick=('4', '5'), conf='★★', first='home', second='away', hc=('home', 'push'),
   note='全轮唯一 λ≥4.0 的场次（4.05），双方联赛 O2.5 均超80%。主胜45.3%、市场45.7%，几乎完全一致。L258：布鲁日近5场全胜、客场战绩优 → 次选强制客胜32.2%。让(-1)负54.0%属结构腿，取让胜27.4%、让平18.6%。',
   risk='双方均为高进攻低容错'),
 '周三008': dict(city='多特蒙德', stadium='Signal Iduna Park（伊杜纳信号公园）', status='正常',
   value=(587.90, 258.10), url=('https://www.transfermarkt.com/borussia-dortmund/startseite/verein/16',
     'https://www.transfermarkt.com/real-betis/startseite/verein/150'),
   form='多特：德甲第2（8轮14:6，场均1.75/0.75），欧冠第16；贝蒂斯：西甲第4（11轮18:15），欧冠第7，近5轮2胜2平1负。',
   recent='多特8轮14:6（场均失0.75）；贝蒂斯近5轮2胜2平1负。',
   inj='多特——Kauã Prates、Justin Lerma、Konstantelias、Emre Can（4人，含无报名资格）；贝蒂斯——Bernal（停赛）、Juan Hernández、Júnior Firpo（3人）。来源：Fotmob + Transfermarkt（一手）。',
   inj_level='一手（Fotmob/TM）',
   h2h='两队欧战近年无交手。',
   level='欧冠｜德甲 vs 西甲，两个联赛相邻（≤1档）',
   tier='常规正常球(2-3球)', tier_note='2球24.0%、3球22.4%',
   ttg_pick=('2', '3'), conf='★★★', first='home', second='draw', hc=('home', 'push'),
   note='全轮最高置信度：上修后主胜53.3%、市场54.8%，同向，分歧由-0.5pp扩大至-1.6pp（上修抬高平局、压低主胜）；多特主场场均失0.75。次选给平（27.1%）而非客胜（19.7%），因贝蒂斯客场近5场胜场不足2场、交锋无样本，L258 次选结构未触发。让(-1)负44.8%属结构腿，取让胜32.3%、让平23.0%。',
   risk='客队欧冠排名高于主队'),
 '周三009': dict(city='斯塔万格', stadium='SR-Bank Arena', status='正常',
   value=(56.00, 19.00), url=('https://www.transfermarkt.com/viking-fk/startseite/verein/1029',
     'https://www.transfermarkt.com/sabah-fk/startseite/verein/63993'),
   form='维京：挪超第1（25轮64:26，场均2.56/1.04），欧冠第33；萨巴赫：阿塞拜疆第2（9轮20:4），欧冠第25。',
   recent='维京25轮64:26；萨巴赫9轮20:4。',
   inj='维京——Bærtelsen、Roseth、Bjørshol、D\'Agostino、Berisha（5人）；萨巴赫——无缺阵。来源：Fotmob（一手）。',
   inj_level='一手（Fotmob）',
   h2h='两队无正式交锋记录。',
   level='欧冠｜挪超 vs 阿塞拜疆超，挪超高约2档，且主队为联赛领头羊',
   tier='常规正常球(2-3球)', tier_note='2球22.8%、3球22.4%',
   ttg_pick=('2', '3'), conf='★★', first='home', second='draw', hc=('home', 'push'),
   note='主胜62.2%、市场70.2%，分歧-8.0pp；主队5人伤停但客队身价仅19M。主胜62.2%≥55%，L260 禁让负生效 → 让胜40.1%首选（同时是模型最高腿）。',
   risk='主队5人伤停'),
 '周三010': dict(city='朗斯', stadium='Stade Bollaert-Delelis（博拉尔-德勒利斯）', status='正常',
   value=(243.00, 568.15), url=('https://www.transfermarkt.com/rc-lens/startseite/verein/826',
     'https://www.transfermarkt.com/como/startseite/verein/1047'),
   form='朗斯：法甲第9（9轮16:13），欧冠第26；科莫：意甲第4（10轮18:8，场均1.80/0.80），欧冠第11。',
   recent='朗斯9轮16:13；科莫10轮18:8。',
   inj='朗斯——Édouard、Ganiou、Sima、Nawrocki、Chávez（5人）+ Haidara（其他原因）；科莫——Addai、Jesús Rodríguez、Chalobah、Diao、Kean（5人，锋线为主）。来源：Fotmob（朗斯一手）+ 新浪/StatsHub（科莫，**未验证**）。',
   inj_level='一手（Fotmob）＋参考（未验证）',
   h2h='两队无正式交锋记录。',
   level='欧冠｜法甲 vs 意甲，意甲高约1档；**跨联赛赛事，法甲特化规则不适用**',
   tier='常规正常球(2-3球)', tier_note='2球24.8%、3球22.2%',
   ttg_pick=('2', '3'), conf='★', first='away', second='draw', hc=('lose', 'push'),
   note='双方各5人伤停（重叠残阵，规则29 例外：不套用“主胜≥55%禁让负”）。科莫身价568M 是朗斯2.3倍。客胜44.9%、市场48.7%，同向。让(+1)胜54.3%属结构腿，取让负24.1%、让平21.7%。',
   risk='双方重叠残阵／首选44.9%<45%'),
 '周三011': dict(city='布拉格', stadium='Eden Arena（福图纳竞技场）', status='正常',
   value=(111.20, 1380.00), url=('https://www.transfermarkt.com/slavia-prague/startseite/verein/62',
     'https://www.transfermarkt.com/arsenal/startseite/verein/11'),
   form='斯拉维亚：捷甲第1（13轮32:7），欧冠第32；阿森纳：英超第1（9轮14:5、8胜1负），欧冠第9。',
   recent='斯拉维亚13轮32:7；阿森纳英超8胜1负。',
   inj='斯拉维亚——主力门将马尔科维奇、主力前锋乔里（4球）伤缺（来源：腾讯/新浪，**未验证**）；阿森纳——萨卡缺阵；萨利巴已回归训练但出场存疑（阿森纳官网与中文源冲突，取官网）。来源：阿森纳官网（一手）＋中文平台（未验证）。',
   inj_level='一手（阿森纳官网）＋参考（未验证）',
   h2h='两队上赛季欧冠联赛阶段交手，阿森纳客场取胜（历史样本1场）。',
   level='欧冠｜捷甲 vs 英超，英超高约2-3档，等级差最大的一场',
   tier='常规正常球(2-3球)', tier_note='2球25.7%、3球21.9%',
   ttg_pick=('2', '3'), conf='★', first='away', second='draw', hc=('push', 'lose'),
   note='模型客胜55.6%、市场77.6%，**分歧-22.0pp**：市场按等级差碾压定价，模型给阿森纳客场+轮换折扣。让(+2)胜67.6%属结构腿（等于阿森纳不赢2球），按 L268 取让平17.7%（输2球）、让负14.7%。',
   risk='模型-市场分歧22.0pp／主队门将+前锋伤缺'),
 '周三012': dict(city='布里斯托尔', stadium='Ashton Gate（阿什顿门）', status='正常',
   value=(57.15, 246.45), url=('https://www.transfermarkt.com/bristol-city/startseite/verein/698',
     'https://www.transfermarkt.com/wolves/startseite/verein/543'),
   form='布里斯托：英冠第14（13轮15:17，场均1.15/1.31）；狼队：英冠第4（13轮23:16，场均1.77/1.23，近5轮3胜1平1负）。',
   recent='布里斯托13轮15:17；狼队近5轮3胜1平1负。',
   inj='布里斯托——Noah Eile（伤）、主力中卫迪基（中文源，**未验证**）；狼队——Jordan James、Bertrand Traoré、Boubacar Traoré、Raúl Jiménez（4人）。来源：Fotmob（狼队一手）+ 搜狐（布里斯托，未验证）。',
   inj_level='一手（Fotmob）＋参考（未验证）',
   h2h='两队英冠历史交锋布里斯托15胜占优，但近季样本不足。',
   level='英冠（同联赛内战，不触发规则76）',
   tier='常规正常球(2-3球)', tier_note='2球26.7%、3球21.4%',
   ttg_pick=('2', '3'), conf='★★', first='away', second='draw', hc=('lose', 'push'),
   note='客胜44.4%、市场45.3%，几乎一致；主队场均仅1.15球、狼队4人伤停中含3名锋线。让(+1)胜54.7%属结构腿，取让负22.7%、让平22.6%。',
   risk='客队锋线4人伤停／首选44.4%<45%'),
}

CODE_CN = {'HH': '胜胜', 'HD': '胜平', 'HA': '胜负', 'DH': '平胜', 'DD': '平平',
           'DA': '平负', 'AH': '负胜', 'AD': '负平', 'AA': '负负'}
OUT_CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HC_CN = {'home': '胜', 'draw': '平', 'push': '平', 'lose': '负', 'away': '负'}
# 让球腿键 → 模型键
HC_KEY = {'home': 'win', 'draw': 'push', 'push': 'push', 'away': 'lose', 'lose': 'lose'}
TIME = {'周三001': '18:00', '周三002': '20:15', '周三003': '23:30', '周三004': '01:45',
        '周三005': '04:00', '周三006': '04:00', '周三007': '04:00', '周三008': '04:00',
        '周三009': '04:00', '周三010': '04:00', '周三011': '04:00', '周三012': '04:00'}


def hc_label(line, key):
    sign = f"+{line}" if line > 0 else str(line)
    return f"让({sign}){HC_CN[key]}"


def pools(x):
    def one(pool, key='outcomes'):
        if pool not in x or not x[pool]:
            return None
        src = x[pool][key] if key in x[pool] else x[pool]
        return {c['key']: c['odds'] for c in src}
    return (one('had'), one('hhad'), one('crs'), one('ttg'), one('hafu'))

# 规则63：008 单关（用户赛前告知）平局上修
PA = {num: dict(r['probs_final']) for num, r in mo.items()}
SINGLE = {}
p8 = PA['周三008']
orig8 = dict(p8)
before = p8['draw']
gap = (p8['home'] - before) * 100
tier, up = ('≥20pp', 1.08) if gap >= 20 else (('10~20pp', 1.11) if gap >= 10 else ('<10pp', 1.13))
after = before * up
ssum = p8['home'] + after + p8['away']
p8 = {'home': p8['home'] / ssum, 'draw': after / ssum, 'away': p8['away'] / ssum}
PA['周三008'] = p8
SINGLE['周三008'] = {
    'is_single': True, 'source': '用户赛前告知（官方接口 bettingSingle=false 与之冲突，以用户投注端为准）',
    'gap_pp': round(gap, 1), 'tier': tier, 'uplift': up,
    'draw_before': round(before, 4), 'draw_after': round(after, 4),
    'model_before': {kk: round(vv, 4) for kk, vv in orig8.items()},
    'renormalized': {kk: round(vv, 4) for kk, vv in p8.items()},
    'second_after': 'draw', 'second_prob_after': round(p8['draw'], 4),
}


preds = []
for num, r in mo.items():
    m = M[num]
    p = PA[num]
    hd = r['handicap']
    first, second = m['first'], m['second']
    hk = m['hc']
    hval = {HC_KEY[hk[0]]: r['handicap'][HC_KEY[hk[0]]], HC_KEY[hk[1]]: r['handicap'][HC_KEY[hk[1]]]}
    need = ['HH', 'DH', 'AH'] if first == 'home' else ['AA', 'DA', 'HA']
    top3 = sorted(need, key=lambda k: -r['htft'][k])
    scores = [{'score': s, 'prob': round(v, 4)} for s, v in r['top_scores'][:5]]
    htt = [{'score': s, 'prob': round(v, 4)} for s, v in r['ht_scores'][:3]]
    k, kr = r['k_dist']['k'], r['k_rec']['k']
    same = (k >= 1 and kr >= 1) or (k <= -1 and kr <= -1) or (k == 0 and kr == 0)
    had_o, hhad_o, crs_o, ttg_o, hafu_o = pools(RD[num])
    preds.append({
        'num': num, 'league': r['league'], 'home': r['home'], 'away': r['away'],
        'kickoff': TIME[num], 'match_date': '2026-11-04',
        'is_single': num in SINGLE,
        'single_note': ('用户赛前告知为单关；官方接口 bettingSingle=false（matchId 2042513），冲突，以用户投注端为准'
                        if num in SINGLE else '官方接口 bettingSingle=false，用户未赛前告知单关'),
        'single_match': SINGLE.get(num),
        'confidence': m['conf'], 'lambda': r['lambda'],
        'model': {kk: round(vv, 4) for kk, vv in p.items()},
        'market': {kk: round(vv, 4) for kk, vv in r['market'].items()},
        'handicap': {'line': hd['line'], 'win': round(hd['win'], 4),
                     'push': round(hd['push'], 4), 'lose': round(hd['lose'], 4)},
        'odds_had': had_o, 'odds_hhad': hhad_o, 'odds_crs': crs_o, 'odds_ttg': ttg_o, 'odds_hafu': hafu_o,
        'value': {'home': f"€{m['value'][0]:.2f}M", 'away': f"€{m['value'][1]:.2f}M",
                  'ratio': round(m['value'][1] / m['value'][0], 2)},
        'value_source': {'home': m['url'][0], 'away': m['url'][1],
                         'provider': 'Transfermarkt（2026-11-04 采集）'},
        'stadium': f"{m['stadium']}（{m['city']}，{m['status']}）",
        'weather': '赛时预报未取到一手源（未验证），无极端天气预警',
        'injuries': {'home': m['inj'], 'source_level': m['inj_level']},
        'recent': m['recent'], 'h2h': m['h2h'],
        'had': {'first': first, 'second': second,
                'firstProb': round(p[first], 4), 'secondProb': round(p[second], 4)},
        'hhad': {'first': HC_CN[hk[0]], 'second': HC_CN[hk[1]],
                 'firstProb': round(list(hval.values())[0], 4),
                 'secondProb': round(list(hval.values())[1], 4)},
        'ttg': {'tier': m['tier'], 'tierNote': m['tier_note'],
                'first': int(m['ttg_pick'][0]), 'second': int(m['ttg_pick'][1]),
                'firstProb': round(r['ttg'][m['ttg_pick'][0]], 4),
                'secondProb': round(r['ttg'][m['ttg_pick'][1]], 4), 'reserve': 'L266'},
        'hafu': {'top3': [CODE_CN[c] for c in top3],
                 'top3Probs': [round(r['htft'][c], 4) for c in top3], 'quota': 'L267'},
        'scoreTop5': scores, 'htScoreTop3': htt,
        'k_dist': {'k': k, 'p': round(r['k_dist']['p'], 4)},
        'k_rec': {'k': kr, 'p': round(r['k_rec']['p'], 4)},
        'k_consistency': '众数一致' if same else '分布-方向分歧',
        'marketDivergence_pp': round((p[first] - r['market'][first]) * 100, 1),
        'risk': m['risk'],
    })

os.makedirs('memory/predictions/20261104_wednesday', exist_ok=True)
json.dump(preds, io.open('memory/predictions/20261104_wednesday/prediction.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
json.dump(preds, io.open('reports/data/20261104_predictions.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('archived', len(preds))

# ---------- 报告 ----------
L = []
A = L.append
A('# 【分析】2026-11-04（周三）12场竞彩全分析 | 亚冠精英2场＋欧罗巴1场＋欧冠8场＋英冠1场；008单关，七场减员')
A('')
A('> **报告说明：** 本文为赛前**分析报告**（标题标注【分析】），提供方向/比分/总进球等预测推荐。赛后将发布**回测报告**（标题标注【回测】），对比预测与实际结果并统计命中率。历史报告可去主页查找。')
A('')
A('> **风险提示：** 今天12场里**7场带减员信号**：004利物浦7人、006那不勒斯10人、001大阪钢巴6人、009维京5人、010朗斯与科莫各5人、011斯拉维亚门将+主力前锋、012狼队4人。**008多特 vs 贝蒂斯为单关（用户赛前告知）：体彩接口 bettingSingle 仍显示 false，两者冲突，本报告以用户投注端信息为准，并按规则63做平局上修（25.6%→27.6%，归一化后平27.1%）。** 004/005/011 三场模型与市场分歧超过15pp，市场明显更热，切勿把市场热度当胜率。')
A('')
A('> **⚠️ 免责声明：** 本文所有分析、预测、推荐仅供学习交流参考，不构成任何投注建议。足球比赛结果具有高度不确定性，任何预测均无法保证准确性。内容仅供参考，如有错漏请谅解。请遵守当地法律法规，理性购彩，量力而行。')
A('')
A('> **📊 近5日置信度命中率（滚动统计，数据源 memory/stats/confidence_stats.md）：** ★★★高 3/3=100.0% ｜ ★★中 28/37=75.7% ｜ ★低 17/24=70.8% ｜ ☆极低 1/1=100.0%。')
A('')
A('*每日更新，关注主页获取最新赛事分析*')
A('')
A('今天12场的结构分三类——**①亚冠东亚区**：001浦项主场迎钢巴、002布里兰主场迎鹿岛，两场都是“弱联赛主场 vs 强联赛客队”；**②欧冠联赛阶段**：8场跨联赛对话，其中004/005/011三场等级差≥2档；**③英冠内战**：012布里斯托尔城 vs 狼队。')
A('')
A('本轮没有稳胆级别的场次：**008多特是唯一★★★（上修后主胜53.3%，单关）**；009主胜62.2%但5人伤停、市场已推到70.2%。同时出现三场“模型明显不跟市场”的分歧——004（-19.6pp）、005（-22.4pp）、011（-22.0pp），全部是英超/豪门客场、市场按联赛等级差定价，而模型把残阵与客场折扣算了进去。')
A('')
A('## 总览')
A('')
A('| 编号 | 对阵 | 首选 | 次选 | 置信度 |')
A('|:---:|:---|:---:|:---:|:---:|')
for num, r in mo.items():
    m = M[num]; p = PA[num]
    A(f"| {num[2:]} | {r['home']} vs {r['away']} | {OUT_CN[m['first']]}({p[m['first']]*100:.1f}%) | {OUT_CN[m['second']]}({p[m['second']]*100:.1f}%) | {m['conf']} |")
A('')
A('> 置信度分布：★★★ 1场（008）、★★ 6场（002/003/006/007/009/012）、★ 5场（001/004/005/010/011）。**008为单关（用户赛前告知，接口 bettingSingle=false 冲突、以用户为准）**，平局已按规则63上修：25.6%→27.6%，归一化后 主53.3%/平27.1%/客19.7%，次选仍为平。其余11场 `single_match` 为 null。')
A('')

for idx, (num, r) in enumerate(mo.items()):
    m = M[num]; p = PA[num]; mk = r['market']
    first, second = m['first'], m['second']
    div = (p[first] - mk[first]) * 100
    hk = m['hc']; hd = r['handicap']
    need = ['HH', 'DH', 'AH'] if first == 'home' else ['AA', 'DA', 'HA']
    top3 = sorted(need, key=lambda k: -r['htft'][k])
    tag = '【单关】' if num in SINGLE else ''
    A(f"## {num} {r['home']} vs {r['away']}（{r['league']}）{tag}")
    A('')
    A(f"**联赛等级：** {m['level']}")
    A('')
    A(f"⏰ 北京时间 {TIME[num]}｜🏟 {m['stadium']}，{m['city']} ｜场地状态：{m['status']} ｜ 🌤 赛时预报未取到一手源（未验证），无极端天气预警")
    A('')
    A(f"**球队动态：** {m['form']}")
    A('')
    A(f"**近期战绩：** {m['recent']}")
    A('')
    A(f"**身价对比：** 主队 €{m['value'][0]:.2f}M vs 客队 €{m['value'][1]:.2f}M（{m['value'][1]/m['value'][0]:.2f}倍）。")
    A('')
    A(f"[Transfermarkt 主队]({m['url'][0]}) ｜ [Transfermarkt 客队]({m['url'][1]})")
    A('')
    A(f"**伤停：** {m['inj']}（来源级别：{m['inj_level']}）")
    A('')
    A(f"**交锋：** {m['h2h']}")
    A('')
    A(f"**模型 vs 市场：** 融合 主{p['home']*100:.1f}%/平{p['draw']*100:.1f}%/客{p['away']*100:.1f}%；市场去水 主{mk['home']*100:.1f}%/平{mk['draw']*100:.1f}%/客{mk['away']*100:.1f}%，首选方向分歧 **{div:+.1f}pp**。λ：主{r['lambda']['home']:.2f}/客{r['lambda']['away']:.2f}（总{r['lambda']['total']:.2f}）。")
    A('')
    sc = r['top_scores'][:5]
    A(f"> **比分推演：** " + "；".join(f"{s}（{v*100:.1f}%）" for s, v in sc) + "。")
    A('')
    A('**推荐：**')
    A('')
    A('| 玩法 | 推荐 |')
    A('|:---|:---|')
    A('| **比分TOP5** | ' + " > ".join(f"**{s}**（{v*100:.1f}%）" for s, v in sc) + ' |')
    A('| **半全场TOP3** | ' + " > ".join(f"**{CODE_CN[k]}**（{r['htft'][k]*100:.1f}%）" for k in top3) + ' |')
    A(f"| **HAD** | 首选 {OUT_CN[first]}({p[first]*100:.1f}%) / 次选 {OUT_CN[second]}({p[second]*100:.1f}%) |")
    A(f"| **HAFU** | 首选 **{hc_label(hd['line'], hk[0])}**({hd[HC_KEY[hk[0]]]*100:.1f}%) / 次选 **{hc_label(hd['line'], hk[1])}**({hd[HC_KEY[hk[1]]]*100:.1f}%) |")
    A(f"| **大小球·总进球** | **{m['tier']}**（{m['tier_note']}）：**{m['ttg_pick'][0]}球**({r['ttg'][m['ttg_pick'][0]]*100:.1f}%) / **{m['ttg_pick'][1]}球**({r['ttg'][m['ttg_pick'][1]]*100:.1f}%) |")
    A('| **半场比分** | ' + " > ".join(f"{s}（{v*100:.1f}%）" for s, v in r['ht_scores'][:3]) + ' |')
    A('')
    A(f"**置信度：** {m['conf']} — {m['risk']}")
    A('')
    A(f"> {m['note']}")
    A('')
    if num in SINGLE:
        sm = SINGLE[num]; ob = sm['model_before']
        A(f"> **单关上修说明（规则63）：** 上修前 主胜{ob['home']*100:.1f}%/平{ob['draw']*100:.1f}%/客{ob['away']*100:.1f}%，首选-次选差距 **{sm['gap_pp']:.1f}pp** → 落 **{sm['tier']}** 档 ×**{sm['uplift']}**，平局 {ob['draw']*100:.1f}%→{sm['draw_after']*100:.1f}%；再按三项归一化得 主{p['home']*100:.1f}%/平{p['draw']*100:.1f}%/客{p['away']*100:.1f}%。上修后平局({p['draw']*100:.1f}%)仍高于客胜({p['away']*100:.1f}%)，**次选仍为平、未被挤出**（不存在昨日003那种“上修把平顶到次选、吃掉原次选”的情形）。")
        A('')
        A("> **单关复核记录：** 2026-11-04 11:36 重新拉取官方在售接口，008（matchId 2042513 / matchNum 3008，status=Selling）`bettingSingle=false`、`bettingAllUp=false`；markets 仅 had/hhad/crs/ttg/hafu 五个常规池，无单关专属赔率结构。**接口字段与用户赛前告知冲突，判定以用户投注端信息为准**（能在单关入口投注即视为单关场），报告与 JSON 均按单关口径处理。")
        A('')
    kk, krr = r['k_dist']['k'], r['k_rec']['k']
    same = (kk >= 1 and krr >= 1) or (kk <= -1 and krr <= -1) or (kk == 0 and krr == 0)
    A(f"> **净胜球众数：** 分布众数 **{kk:+d}**（{r['k_dist']['p']*100:.1f}%）｜推荐众数 **{krr:+d}**（{r['k_rec']['p']*100:.1f}%）｜**{'众数一致' if same else '分布-方向分歧'}**")
    A('')

A('## 综合推荐汇总')
A('')
A('| 编号 | 对阵 | 方向首选 | 方向次选 | 让球首选 | 比分TOP1 | 半全场首选 | 大小球档 |')
A('|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|')
for num, r in mo.items():
    m = M[num]; p = PA[num]; hd = r['handicap']
    need = ['HH', 'DH', 'AH'] if m['first'] == 'home' else ['AA', 'DA', 'HA']
    t3 = sorted(need, key=lambda k: -r['htft'][k])[0]
    A(f"| {num[2:]} | {r['home']} vs {r['away']} | {OUT_CN[m['first']]}({p[m['first']]*100:.1f}%) | {OUT_CN[m['second']]}({p[m['second']]*100:.1f}%) | {hc_label(hd['line'], m['hc'][0])}({hd[HC_KEY[m['hc'][0]]]*100:.1f}%) | {r['top_scores'][0][0]} | {CODE_CN[t3]}({r['htft'][t3]*100:.1f}%) | {m['tier']} |")
A('')
A('## 搏冷推荐汇总')
A('')
A('- **005 莱比锡 vs 曼城 → 主胜 32.4%**：市场只给主胜16.7%，分歧 +15.7pp，全轮最大反向；莱比锡场均2.75球、曼城客场防线场均失1.11。')
A('- **011 斯拉维亚 vs 阿森纳 → 平局 26.5%**：市场14.4%，分歧 +12.1pp；斯拉维亚主场13轮32:7、阿森纳客场轮换概率高。')
A('- **004 费内巴切 vs 利物浦 → 主胜 27.2%**：市场15.3%，分歧 +11.9pp；利物浦7人缺阵+格拉芬贝赫未随队，右后卫只剩客串。')
A('- **001 浦项 vs 钢巴 → 平局 31.0%**：市场27.0%，分歧 +4.0pp；双方进攻都不可靠，0-0/1-1 合计24.1%。')
A('')
A('> 过热提示：005（市场客胜65.0%）、011（77.6%）、004（66.0%）三场市场把英超强队推到极高，模型均不跟，**不建议追高赔客胜**。')
A('')
A('## 串关思路')
A('')
A('> 按 L269 收敛为 **7 注**：方向串2注＋让球串1注＋娱乐串4注；同场最多出现2次、无同组合重复登记；主注全部为“全腿方向首选且单腿赔率<4”，方向腿一律取首选概率≥45%的场次。')
A('')
A('### 方向串（胜平负）')
A('')
A('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
A('|:---|:---|:---|:---:|:---|')
A('| 稳健A（三串一） | 006主胜 × 008主胜 × 009主胜 | 1.88 × 1.60 × 1.25 | 3.76 | 中 |')
A('| 稳健B（二串一） | 006主胜 × 007主胜 | 1.88 × 1.92 | 3.61 | 中 |')
A('')
A('> 两注全腿方向首选、单腿赔率全部<4；006出现2次、009/008/007各1次，未超单场上限。**001（39.2%）、002（44.7%）、003（44.7%）、004（46.4%）、010（44.9%）、012（44.4%）首选不足45%，全部不进方向串**；004/005/011 分歧>15pp 且首选<50%，只做搏冷、不进串。')
A('')
A('### 让球串（让球胜平负）')
A('')
A('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
A('|:---|:---|:---|:---:|:---|')
A('| 稳健A（二串一） | 008让(-1)胜 × 009让(-1)胜 | 2.77 × 1.78 | 4.93 | 中 |')
A('')
A('> 两条让球腿均为“去掉结构性腿后的最高腿”（008让胜32.3%、009让胜40.1%），且008/009方向首选分别为53.3%（单关上修后）/62.2%，均≥45%，符合 L268；009主胜≥55% 同时触发 L260 禁让负。008上修只抬高了平局，不改变让球盘概率与方向首选是否过45%的判定，**该腿保留**。002方向首选44.7%<45%，其让球腿按 L268 硬约束不进串。')
A('')
A('### 娱乐串（连续编号）')
A('')
A('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
A('|:---|:---|:---|:---:|:---|')
A('| ① 半全场连续 | 011负负 × 012负负 | 1.52 × 3.20 | 4.86 | 中 |')
A('| ② 总进球连续 | 003 2球 × 004 3球 | 3.45 × 3.55 | 12.25 | 高 |')
A('| ③ 半全场连续 | 010负负 × 011负负 | 2.80 × 1.52 | 4.26 | 中 |')
A('| ④ 比分连续 | 001 0-1 × 002 0-1 | 8.00 × 8.00 | 64.00 | 极高 |')
A('')
A('> 娱乐串单注≤1%。①由原“008胜胜×009胜胜”改为“011负负×012负负”：008/009 已在稳健A与让球串各出现2次，再进娱乐①会触 L269“同场≤2条串”上限；011/012 均为客胜首选场、半全场首选均为负负（34.6%/25.8%），连续编号且与 L267 同源。④为比分串：001 的 0-1 模型概率10.8%、002 的 0-1 为9.5%，赔率均恰为8.00，同时满足“概率≥8%＋赔率≥8.00”的甜蜜区；两腿都是客胜首选场的**次高比分**（TOP1 均为1-1），不是无依据的长尾。')
A('')
A('## 本轮规律')
A('')
A('1. **残阵集中客队**：那不勒斯10人、利物浦7人、大阪钢巴6人，三场客队残阵直接把模型概率压低，与市场形成反向分歧——这轮不要“看牌面买强队”。')
A('2. **主胜首选只有5场（003/006/007/008/009），仅009≥55%（62.2%）**：008上修后为53.3%（距55%差1.8pp），仍不触发 L260 禁让负，让球取让胜。')
A('3. **L266 两端预留**：低端由001承担（0-1球band合计29.8%为全轮最高，档位落“闷战超小球”，球数TOP2仍按模型 2球/1球）；高端由007承担（λ=4.05、P(≥5球)=38.1%>单点4球19.5%，档位落“超大球(5-6球)”）。中段10场，未出现全轮同档。')
A('4. **L267 半全场配额**：5个主胜首选场（003/006/007/008/009）TOP3 均含“胜胜＋平胜＋负胜”；7个客胜首选场（001/002/004/005/010/011/012）均含“负负＋平负＋胜负”。变盘位（负胜/胜负）全部在位，其中001的“胜负”仅2.1%、属强制配额位。')
A('5. **L268 让球去结构腿**：12场全部剔除了 +1让胜 / -1让负 / +2让胜 这三类结构性高概率腿（如001的让(+1)胜59.9%、011的让(+2)胜67.6%），让球首选改为次高档的真实方向腿。')
A('')
A('## ☕ 写在最后')
A('')
A('这轮的核心不是“谁强”，而是**谁残**。那不勒斯10人、利物浦7人、大阪钢巴6人，三支客队都是残阵出行；市场还在按牌面与联赛等级差给价，模型已经把减员算进去，于是出现了004/005/011三场15pp以上的分歧。')
A('')
A('我的选择是：**分歧场只做方向、不进串**，串关只留006/008/009/007 这些“模型与市场同向、方向首选≥45%”的场次。稳健A（006+008+009）是本轮结构最干净的一条——三场都是主胜首选、赔率全部<4、无15pp分歧。')
A('')
A('最后提醒：008为单关（用户赛前告知，官方接口仍显示 bettingSingle=false，两者冲突、以用户投注端为准），但规则63上修后主胜也只有53.3%，**不是稳胆**；其余11场接口未开单关，任何“单关稳胆”的说法都不适用。12场里没有一场首选≥65%且无减员。理性看待，量力而行。')

io.open('reports/analysis/20261104_analysis_zhihu.md', 'w', encoding='utf-8').write("\n".join(L))
print('report written', len(L), 'lines')
