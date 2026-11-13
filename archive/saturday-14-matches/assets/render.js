// render.js — Dynamic content rendering from embedded data
(function() {

// ===== MATCH INFO (static, not in JSON) =====
var MATCH_INFO = {
  201: { hrank: 10, arank: 5, hinj: "6人缺阵，中前场重创（前锋迪奥戈、中场严元相等）", ainj: "2人缺阵（中卫科特、高中锋法里亚斯），核心亚戈8球健康", key: "大田联赛唯一主场0胜，主场场均0.56球垫底；6人伤停严重削弱本已薄弱的主场进攻", h2h: "近3次大田全胜含首回合4-1客场大胜；但近10次5胜2平3负蔚山历史占优", xg: "大田xG 0.87（倒数第三）实际进球率6.9%远低于联赛12.7%；蔚山xG 1.59转化13.4%", vmr: "1.15 标准泊松适用", zerorate: "8% 无需ZIP" },
  202: { hrank: 3, arank: 11, hinj: "无伤停无停赛，满配出战", ainj: "轮换中场李东炅累计黄牌停赛", key: "江原17轮仅丢11球联赛最少，近7轮4胜3平不败；金泉17轮仅2胜平局率60%", h2h: "首回合金泉0-3负江原；近6次交手江原3胜1平2负全部零封", xg: "未获取详细xG；模型反推λ江原1.45/金泉0.70", vmr: "1.15 标准泊松适用", zerorate: "8% 无需ZIP" },
  203: { hrank: 8, arank: 4, hinj: "头号射手内格巴红牌停赛、队长李昌珉出战成疑", ainj: "特兰齐斯卡出战成疑、儒尼尼奥足踝缺阵，核心李昊宰8球健康", key: "济州主场场均0.67球联赛垫底，连续4轮不胜；浦项客场胜率56%近期4胜1负", h2h: "首回合济州客场2-0完胜浦项；济州主场近2次交锋全胜。历史总交锋济州17胜15胜11平", xg: "济州xG 1.62但实际进球转化率仅6.8%联赛最低之一；浦项xG 1.45转化率9.8%", vmr: "1.15 标准泊松适用", zerorate: "8% 无需ZIP" },
  204: { hrank: 7, arank: 2, hinj: "无伤停无停赛，中轴线完整", ainj: "主力中锋孔帕尼奥伤缺、边路朴主英伤缺、李昇祐停赛（前场损失中等）", key: "仁川主场无平局（非赢即输），近3主场连续输球且一球未进。全北客场不败率89%场均失0.56球，上轮3-1逆转蔚山士气高涨", h2h: "首回合仁川客场2-1爆冷全北；近5次仁川2胜2平1负占优。但历史近41次全北19胜16平6负绝对上风", xg: "未获取详细xG；模型反推λ仁川0.96/全北1.21", vmr: "1.15 标准泊松适用", zerorate: "8% 无需ZIP" },
  205: { hrank: 6, arank: 1, hinj: "前锋诺亚·亚历山德森长期伤缺（1人）", ainj: "前锋埃克布洛姆腹股沟伤、后卫奥伊万伤停、主力边卫瓦内里德红牌停赛（3人）", key: "汉坎主场龙（5胜1负83%胜率）但客场崩盘；特罗姆瑟榜首但客场进球仅场均0.8球，后防核心停赛", h2h: "近10次汉坎1胜3平6负，2022重返挪超后0胜2平5负。特罗姆瑟完全压制", xg: "模型反推xG汉坎0.986/特罗姆瑟1.364", vmr: "1.35 过离散启用NB", zerorate: "7% 无需ZIP" },
  206: { hrank: 5, arank: 3, hinj: "2名主力中卫停赛+主力门将伤缺（防线毁灭性打击）；前锋大卫-艾泽克、中场安东-尼伦德缺阵", ainj: "仅一名前锋长期伤停，阵容基本齐整", key: "赫尔辛基防线毁灭性伤病（2中卫+门将），近2轮0-2负+0-4负防守崩盘。瓦萨客场防守出色（7场丢5球）", h2h: "首回合瓦萨2-1胜赫尔辛基；近6次赫尔辛基4胜1平1负占优", xg: "模型反推xG赫尔辛基1.750/瓦萨1.228", vmr: "1.25 过离散启用NB", zerorate: "9% 推荐ZIP" },
  207: { hrank: 9, arank: 5, hinj: "后卫西塞踝关节伤、中场艾林森长期缺阵、后卫雷德金膝伤（3人）", ainj: "4人停赛+3人伤病（门将+中场+后卫），但多为非现役球员", key: "索尔纳主场分胜负属性强（2胜0平3负），主场防守漏洞大；盖斯客场近期2连胜含金量高", h2h: "瑞典杯盖斯3-2胜索尔纳；联赛1-1平。近5次盖斯3胜1平1负占优", xg: "模型反推xG索尔纳1.275/盖斯1.285（几乎均等）", vmr: "1.20 标准泊松适用", zerorate: "8% 无需ZIP" },
  208: { hrank: 4, arank: 13, hinj: "中场基托拉诺赛季报销、轮换后卫兰吉尔休战、后卫加纳斯红牌停赛（3人）", ainj: "7人缺阵（中场文乔尔停赛+前锋埃克雷姆等3人伤停+后卫2人缺阵+门将伤缺），攻防体系双重残缺", key: "利勒斯特罗姆主帅厄德高父亲执教40场35胜5平不败；KFUM客场连续11场不胜且7人缺阵严重", h2h: "友谊赛7-2、挪威杯2-0、联赛1-0，利勒斯特罗姆三杀。近10次正式交手8胜2负无平局", xg: "未获取详细xG；模型反推λ利勒斯特罗姆1.85/KFUM 0.70", vmr: "1.35 过离散启用NB", zerorate: "7% 无需ZIP" },
  209: { hrank: 16, arank: 12, hinj: "5-6人伤停（利恩、迈耶、滕内森等），规模极大", ainj: "仅替补轮换球员有伤，中场核心塞尔纳斯、锋线主力全部健康", key: "斯达垫底+6人伤停 vs 罗森博格客场零进球（5场0球9失）。双方各致命短板", h2h: "近18次正式交手罗森博格14胜4平不败；近7次联赛5胜2平", xg: "模型反推xG斯达1.223/罗森博格1.473", vmr: "1.35 过离散启用NB", zerorate: "7% 无需ZIP" },
  210: { hrank: 15, arank: 7, hinj: "中场斯文森受伤、后卫威廉森长期缺阵、前锋图费克西奇大腿伤（3人）", ainj: "后卫罗斯特德踝关节伤、前锋卡尔斯滕森长期缺阵（2人，非核心）", key: "克里斯蒂安松联赛最少进球仅11球，三连败；萨尔普斯堡三连胜含金量极高（胜维京、布兰、莫尔德）", h2h: "友谊赛萨尔普斯堡1-0胜；上赛季克里斯蒂安松1-0胜+0-0平。近10次克里斯蒂安松4胜3平3负占优", xg: "模型反推xG克里斯蒂安松1.313/萨尔普斯堡1.605", vmr: "1.35 过离散启用NB", zerorate: "7% 无需ZIP" },
  211: { hrank: 4, arank: 6, hinj: "两名轮换中场轻伤，不影响主力框架", ainj: "全队无主力伤停", key: "AC奥卢主场金身不败（5胜1平84%胜率）仅丢3球，防守联赛顶级；火花客场胜率仅15%", h2h: "首回合火花主场1-5惨败奥卢；去年火花双杀奥卢。近6次奥卢1胜1平4负", xg: "模型反推xG奥卢1.424/火花1.141", vmr: "1.25 过离散启用NB", zerorate: "9% 推荐ZIP" },
  212: { hrank: 10, arank: 1, hinj: "边路主力长期伤缺（1人）", ainj: "主力全员健康。但刚经历欧冠资格赛两回合加时被华达淘汰，体能心态双消耗", key: "库奥皮奥榜首+场均进球1.9丢0.7联赛最强攻防，但欧冠加时被淘汰后体能心态存疑。联赛杯3-0输给本场对手存在心理阴影", h2h: "联赛杯塞伊奈约基3-0胜库奥皮奥；去年库奥皮奥双杀。近6次库奥皮奥5胜1平完全压制", xg: "模型反推xG塞伊奈约基1.343/库奥皮奥1.575", vmr: "1.25 过离散启用NB", zerorate: "9% 推荐ZIP" },
  213: { hrank: 5, arank: 9, hinj: "主力门将基肯博格赛季报销、后卫达尔膝伤缺阵（2人），中卫厄伊万复出", ainj: "主力中卫博阿基耶赛季报销、中场古蒙德松奥普萨尔伤停（3人，后防线重创）", key: "莫尔德主场5胜1负仅丢4球，主场统治力极强。布兰客场1胜5负场均丢1.8球+中卫报销", h2h: "近10次正式交手莫尔德9胜1负；近4次主场全部大胜。上赛季4-0、3-0、4-0碾压", xg: "模型反推xG莫尔德1.689/布兰1.365", vmr: "1.35 过离散启用NB", zerorate: "7% 无需ZIP" },
  214: { hrank: 2, arank: 10, hinj: "锋线、后防各1人伤停（2人，影响有限）", ainj: "1人因伤缺阵、中场核心红牌停赛（2人，攻防转换受影响）", key: "维京主场全胜场均进4.2球联赛第一火力，距榜首仅1分争冠战意强。桑纳菲尤尔541死守+中场核心停赛", h2h: "近5次交手维京全胜（5胜0平0负），历史完全一边倒", xg: "模型反推xG维京2.575/桑纳菲尤尔0.846", vmr: "1.35 过离散启用NB", zerorate: "7% 无需ZIP" }
};

var DATA = [
  {"id":201,"league":"韩职","home":"大田市民","away":"蔚山现代","odds":{"win":2.3,"draw":3.3,"lose":2.85},"ou_line":2.25,"shin":{"win":0.387,"draw":0.289,"lose":0.324},"fused":{"win":0.225,"draw":0.295,"lose":0.482},"dc":{"win":0.181,"draw":0.267,"lose":0.552},"nb":{"win":0.174,"draw":0.292,"lose":0.534},"zip":{"win":0.164,"draw":0.311,"lose":0.524},"skellam":{"win":0.169,"draw":0.290,"lose":0.541},"mc":{"win":0.173,"draw":0.281,"lose":0.537},"confidence":{"level":"中","stars":"★★","score":1},"avg_std":0.0097,"max_diff":0.2146,"scores_top10":[{"score":"0:1","dc":"20.7%","zip":"18.9%","mc":"18.9%","combined":"19.7%"},{"score":"0:0","dc":"13.8%","zip":"17.5%","mc":"14.4%","combined":"14.8%"},{"score":"0:2","dc":"12.8%","zip":"12.4%","mc":"12.4%","combined":"12.5%"},{"score":"1:1","dc":"10.4%","zip":"11.3%","mc":"11.2%","combined":"10.9%"}],"over_under":{"over":0.297,"under":0.700,"line":2.25},"half_full_top3":[{"result":"AA","prob":"24.6%"},{"result":"DA","prob":"17.9%"},{"result":"DD","prob":"16.3%"}],"lambda_adjusted":{"home":0.595,"away":1.307}},
  {"id":202,"league":"韩职","home":"江原FC","away":"金泉尚武","odds":{"win":1.81,"draw":3.41,"lose":4.04},"ou_line":2.5,"shin":{"win":0.473,"draw":0.279,"lose":0.248},"fused":{"win":0.528,"draw":0.290,"lose":0.182},"dc":{"win":0.554,"draw":0.241,"lose":0.205},"nb":{"win":0.530,"draw":0.265,"lose":0.205},"zip":{"win":0.512,"draw":0.283,"lose":0.205},"skellam":{"win":0.540,"draw":0.248,"lose":0.212},"mc":{"win":0.533,"draw":0.253,"lose":0.214},"confidence":{"level":"中","stars":"★★","score":2},"avg_std":0.0136,"max_diff":0.0554,"scores_top10":[{"score":"1:0","dc":"13.1%","zip":"11.7%","mc":"12.5%","combined":"12.4%"},{"score":"2:0","dc":"11.3%","zip":"10.4%","mc":"10.9%","combined":"10.8%"},{"score":"1:1","dc":"9.9%","zip":"11.4%","mc":"10.5%","combined":"10.7%"},{"score":"0:0","dc":"10.1%","zip":"12.6%","mc":"10.8%","combined":"10.9%"}],"over_under":{"over":0.365,"under":0.635,"line":2.5},"half_full_top3":[{"result":"DH","prob":"22.1%"},{"result":"HH","prob":"17.2%"},{"result":"DD","prob":"15.6%"}],"lambda_adjusted":{"home":1.450,"away":0.700}},
  {"id":203,"league":"韩职","home":"济州SK","away":"浦项制铁","odds":{"win":2.8,"draw":3.18,"lose":2.19},"ou_line":2.5,"shin":{"win":0.278,"draw":0.292,"lose":0.430},"fused":{"win":0.247,"draw":0.287,"lose":0.466},"dc":{"win":0.214,"draw":0.271,"lose":0.515},"nb":{"win":0.207,"draw":0.291,"lose":0.502},"zip":{"win":0.195,"draw":0.305,"lose":0.500},"skellam":{"win":0.209,"draw":0.284,"lose":0.507},"mc":{"win":0.211,"draw":0.283,"lose":0.506},"confidence":{"level":"中","stars":"★★","score":1},"avg_std":0.0124,"max_diff":0.0360,"scores_top10":[{"score":"0:1","dc":"13.5%","zip":"12.2%","mc":"12.6%","combined":"12.7%"},{"score":"1:1","dc":"10.7%","zip":"12.2%","mc":"11.0%","combined":"11.3%"},{"score":"0:0","dc":"10.6%","zip":"13.6%","mc":"11.2%","combined":"11.6%"},{"score":"0:2","dc":"10.3%","zip":"9.5%","mc":"10.1%","combined":"9.9%"}],"over_under":{"over":0.310,"under":0.690,"line":2.5},"half_full_top3":[{"result":"DA","prob":"19.5%"},{"result":"AA","prob":"17.3%"},{"result":"DD","prob":"16.0%"}],"lambda_adjusted":{"home":0.720,"away":1.188}},
  {"id":204,"league":"韩职","home":"仁川联","away":"全北现代","odds":{"win":3.1,"draw":3.15,"lose":2.28},"ou_line":2.5,"shin":{"win":0.282,"draw":0.296,"lose":0.422},"fused":{"win":0.259,"draw":0.332,"lose":0.409},"dc":{"win":0.222,"draw":0.311,"lose":0.467},"nb":{"win":0.217,"draw":0.332,"lose":0.451},"zip":{"win":0.206,"draw":0.347,"lose":0.447},"skellam":{"win":0.213,"draw":0.328,"lose":0.459},"mc":{"win":0.219,"draw":0.327,"lose":0.454},"confidence":{"level":"高","stars":"★★★","score":3},"avg_std":0.0184,"max_diff":0.0130,"scores_top10":[{"score":"0:1","dc":"12.3%","zip":"11.4%","mc":"11.6%","combined":"11.8%"},{"score":"1:1","dc":"10.1%","zip":"11.8%","mc":"10.8%","combined":"10.9%"},{"score":"0:0","dc":"10.7%","zip":"13.6%","mc":"11.2%","combined":"11.6%"},{"score":"0:2","dc":"9.2%","zip":"8.5%","mc":"9.0%","combined":"8.9%"}],"over_under":{"over":0.360,"under":0.640,"line":2.5},"half_full_top3":[{"result":"DA","prob":"18.8%"},{"result":"DD","prob":"17.5%"},{"result":"DH","prob":"12.5%"}],"lambda_adjusted":{"home":0.903,"away":1.335}},
  {"id":205,"league":"挪超","home":"汉坎","away":"特罗姆瑟","odds":{"win":2.45,"draw":3.35,"lose":2.65},"ou_line":2.5,"shin":{"win":0.368,"draw":0.276,"lose":0.356},"fused":{"win":0.479,"draw":0.267,"lose":0.254},"dc":{"win":0.478,"draw":0.234,"lose":0.288},"nb":{"win":0.454,"draw":0.256,"lose":0.290},"zip":{"win":0.436,"draw":0.270,"lose":0.294},"skellam":{"win":0.463,"draw":0.245,"lose":0.292},"mc":{"win":0.457,"draw":0.248,"lose":0.295},"confidence":{"level":"低","stars":"★","score":0},"avg_std":0.0156,"max_diff":0.1114,"scores_top10":[{"score":"1:0","dc":"11.5%","zip":"10.2%","mc":"10.8%","combined":"10.9%"},{"score":"2:1","dc":"10.4%","zip":"9.7%","mc":"10.2%","combined":"10.1%"},{"score":"1:1","dc":"9.5%","zip":"10.6%","mc":"9.7%","combined":"9.9%"},{"score":"2:0","dc":"8.5%","zip":"7.6%","mc":"8.1%","combined":"8.1%"}],"over_under":{"over":0.463,"under":0.537,"line":2.5},"half_full_top3":[{"result":"HD","prob":"17.2%"},{"result":"HH","prob":"15.7%"},{"result":"DH","prob":"14.2%"}],"lambda_adjusted":{"home":1.520,"away":0.920}},
  {"id":206,"league":"芬超","home":"赫尔辛基","away":"瓦萨","odds":{"win":1.77,"draw":3.7,"lose":3.4},"ou_line":3.0,"shin":{"win":0.491,"draw":0.262,"lose":0.247},"fused":{"win":0.449,"draw":0.288,"lose":0.263},"dc":{"win":0.473,"draw":0.250,"lose":0.277},"nb":{"win":0.441,"draw":0.274,"lose":0.285},"zip":{"win":0.422,"draw":0.289,"lose":0.289},"skellam":{"win":0.453,"draw":0.261,"lose":0.286},"mc":{"win":0.449,"draw":0.265,"lose":0.286},"confidence":{"level":"中","stars":"★★","score":1},"avg_std":0.0127,"max_diff":0.0421,"scores_top10":[{"score":"1:0","dc":"11.8%","zip":"10.5%","mc":"11.3%","combined":"11.2%"},{"score":"2:1","dc":"10.0%","zip":"9.4%","mc":"9.8%","combined":"9.7%"},{"score":"1:1","dc":"9.3%","zip":"10.3%","mc":"9.5%","combined":"9.7%"},{"score":"2:0","dc":"8.2%","zip":"7.3%","mc":"7.9%","combined":"7.8%"}],"over_under":{"over":0.250,"under":0.750,"line":3.0},"half_full_top3":[{"result":"HD","prob":"17.5%"},{"result":"HH","prob":"15.9%"},{"result":"DH","prob":"12.7%"}],"lambda_adjusted":{"home":1.426,"away":0.960}},
  {"id":207,"league":"瑞超","home":"AIK索尔纳","away":"哥德堡盖斯","odds":{"win":2.33,"draw":3.25,"lose":2.55},"ou_line":2.5,"shin":{"win":0.369,"draw":0.274,"lose":0.357},"fused":{"win":0.379,"draw":0.315,"lose":0.306},"dc":{"win":0.360,"draw":0.292,"lose":0.348},"nb":{"win":0.348,"draw":0.306,"lose":0.346},"zip":{"win":0.332,"draw":0.322,"lose":0.346},"skellam":{"win":0.350,"draw":0.305,"lose":0.345},"mc":{"win":0.353,"draw":0.307,"lose":0.340},"confidence":{"level":"高","stars":"★★★","score":3},"avg_std":0.0122,"max_diff":0.0101,"scores_top10":[{"score":"1:0","dc":"9.7%","zip":"9.0%","mc":"9.3%","combined":"9.3%"},{"score":"1:1","dc":"9.1%","zip":"10.5%","mc":"9.4%","combined":"9.7%"},{"score":"0:1","dc":"8.3%","zip":"9.0%","mc":"8.7%","combined":"8.7%"},{"score":"0:0","dc":"7.4%","zip":"9.3%","mc":"7.8%","combined":"8.2%"}],"over_under":{"over":0.426,"under":0.574,"line":2.5},"half_full_top3":[{"result":"DH","prob":"13.7%"},{"result":"DD","prob":"13.5%"},{"result":"HD","prob":"11.6%"}],"lambda_adjusted":{"home":1.140,"away":1.095}},
  {"id":208,"league":"挪超","home":"利勒斯特罗姆","away":"奥斯陆KFUM","odds":{"win":1.42,"draw":4.2,"lose":6.5},"ou_line":2.5,"shin":{"win":0.632,"draw":0.220,"lose":0.148},"fused":{"win":0.637,"draw":0.220,"lose":0.143},"dc":{"win":0.676,"draw":0.187,"lose":0.137},"nb":{"win":0.640,"draw":0.208,"lose":0.152},"zip":{"win":0.619,"draw":0.215,"lose":0.166},"skellam":{"win":0.660,"draw":0.200,"lose":0.140},"mc":{"win":0.653,"draw":0.204,"lose":0.143},"confidence":{"level":"中","stars":"★★","score":1},"avg_std":0.0220,"max_diff":0.0049,"scores_top10":[{"score":"2:0","dc":"12.3%","zip":"11.1%","mc":"11.8%","combined":"11.7%"},{"score":"1:0","dc":"11.7%","zip":"10.6%","mc":"11.2%","combined":"11.1%"},{"score":"2:1","dc":"10.6%","zip":"9.8%","mc":"10.2%","combined":"10.2%"},{"score":"3:0","dc":"7.8%","zip":"7.0%","mc":"7.5%","combined":"7.4%"}],"over_under":{"over":0.439,"under":0.561,"line":2.5},"half_full_top3":[{"result":"HH","prob":"27.9%"},{"result":"DH","prob":"18.5%"},{"result":"HD","prob":"11.4%"}],"lambda_adjusted":{"home":1.850,"away":0.560}},
  {"id":209,"league":"挪超","home":"斯达","away":"罗森博格","odds":{"win":3.2,"draw":3.4,"lose":2.05},"ou_line":2.5,"shin":{"win":0.279,"draw":0.278,"lose":0.443},"fused":{"win":0.283,"draw":0.342,"lose":0.375},"dc":{"win":0.268,"draw":0.332,"lose":0.400},"nb":{"win":0.262,"draw":0.351,"lose":0.387},"zip":{"win":0.252,"draw":0.364,"lose":0.384},"skellam":{"win":0.262,"draw":0.345,"lose":0.393},"mc":{"win":0.264,"draw":0.344,"lose":0.392},"confidence":{"level":"中","stars":"★★","score":1},"avg_std":0.0114,"max_diff":0.0680,"scores_top10":[{"score":"1:1","dc":"11.0%","zip":"12.3%","mc":"11.0%","combined":"11.4%"},{"score":"0:1","dc":"10.0%","zip":"9.3%","mc":"10.0%","combined":"9.8%"},{"score":"1:0","dc":"8.2%","zip":"7.3%","mc":"8.0%","combined":"7.9%"},{"score":"0:0","dc":"8.6%","zip":"11.0%","mc":"8.7%","combined":"9.4%"}],"over_under":{"over":0.337,"under":0.663,"line":2.5},"half_full_top3":[{"result":"DD","prob":"17.0%"},{"result":"DA","prob":"15.5%"},{"result":"AD","prob":"14.3%"}],"lambda_adjusted":{"home":0.920,"away":1.155}},
  {"id":210,"league":"挪超","home":"克里斯蒂安松","away":"萨尔普斯堡","odds":{"win":2.65,"draw":3.4,"lose":2.45},"ou_line":2.5,"shin":{"win":0.330,"draw":0.274,"lose":0.396},"fused":{"win":0.316,"draw":0.282,"lose":0.402},"dc":{"win":0.302,"draw":0.272,"lose":0.426},"nb":{"win":0.293,"draw":0.287,"lose":0.420},"zip":{"win":0.282,"draw":0.296,"lose":0.422},"skellam":{"win":0.295,"draw":0.281,"lose":0.424},"mc":{"win":0.297,"draw":0.281,"lose":0.422},"confidence":{"level":"中","stars":"★★","score":1},"avg_std":0.0141,"max_diff":0.0059,"scores_top10":[{"score":"0:1","dc":"10.5%","zip":"9.9%","mc":"10.2%","combined":"10.2%"},{"score":"1:1","dc":"9.9%","zip":"10.9%","mc":"10.0%","combined":"10.2%"},{"score":"1:2","dc":"8.5%","zip":"8.3%","mc":"8.5%","combined":"8.5%"},{"score":"0:0","dc":"8.6%","zip":"10.1%","mc":"8.5%","combined":"9.0%"}],"over_under":{"over":0.452,"under":0.548,"line":2.5},"half_full_top3":[{"result":"DA","prob":"15.7%"},{"result":"DD","prob":"15.3%"},{"result":"AD","prob":"14.6%"}],"lambda_adjusted":{"home":1.040,"away":1.290}},
  {"id":211,"league":"芬超","home":"AC奥卢","away":"赫尔辛基火花","odds":{"win":2.15,"draw":3.43,"lose":3.02},"ou_line":2.5,"shin":{"win":0.413,"draw":0.271,"lose":0.316},"fused":{"win":0.491,"draw":0.281,"lose":0.228},"dc":{"win":0.511,"draw":0.244,"lose":0.245},"nb":{"win":0.488,"draw":0.261,"lose":0.251},"zip":{"win":0.466,"draw":0.276,"lose":0.258},"skellam":{"win":0.496,"draw":0.254,"lose":0.250},"mc":{"win":0.499,"draw":0.252,"lose":0.249},"confidence":{"level":"低","stars":"★","score":0},"avg_std":0.0189,"max_diff":0.0781,"scores_top10":[{"score":"1:0","dc":"13.0%","zip":"11.6%","mc":"12.7%","combined":"12.5%"},{"score":"2:0","dc":"10.1%","zip":"9.1%","mc":"10.0%","combined":"9.7%"},{"score":"1:1","dc":"9.0%","zip":"10.2%","mc":"9.4%","combined":"9.5%"},{"score":"2:1","dc":"7.7%","zip":"7.2%","mc":"7.5%","combined":"7.5%"}],"over_under":{"over":0.414,"under":0.586,"line":2.5},"half_full_top3":[{"result":"HD","prob":"20.4%"},{"result":"HH","prob":"15.1%"},{"result":"DH","prob":"12.6%"}],"lambda_adjusted":{"home":1.500,"away":0.850}},
  {"id":212,"league":"芬超","home":"塞伊奈约基","away":"库奥皮奥","odds":{"win":2.62,"draw":3.35,"lose":2.23},"ou_line":2.5,"shin":{"win":0.337,"draw":0.278,"lose":0.386},"fused":{"win":0.322,"draw":0.273,"lose":0.407},"dc":{"win":0.305,"draw":0.268,"lose":0.427},"nb":{"win":0.297,"draw":0.278,"lose":0.425},"zip":{"win":0.287,"draw":0.289,"lose":0.424},"skellam":{"win":0.298,"draw":0.275,"lose":0.427},"mc":{"win":0.300,"draw":0.277,"lose":0.423},"confidence":{"level":"中","stars":"★★","score":2},"avg_std":0.0114,"max_diff":0.0209,"scores_top10":[{"score":"0:1","dc":"11.9%","zip":"10.3%","mc":"10.6%","combined":"11.1%"},{"score":"1:1","dc":"11.5%","zip":"12.1%","mc":"11.4%","combined":"11.6%"},{"score":"1:0","dc":"10.3%","zip":"8.8%","mc":"9.1%","combined":"9.6%"},{"score":"1:2","dc":"8.7%","zip":"8.3%","mc":"7.6%","combined":"8.2%"}],"over_under":{"over":0.466,"under":0.534,"line":2.5},"half_full_top3":[{"result":"AA","prob":"17.7%"},{"result":"DA","prob":"14.3%"},{"result":"HA","prob":"13.2%"}],"lambda_adjusted":{"home":1.175,"away":1.377}},
  {"id":213,"league":"挪超","home":"莫尔德","away":"布兰","odds":{"win":1.48,"draw":4.1,"lose":5.8},"ou_line":2.5,"shin":{"win":0.561,"draw":0.241,"lose":0.198},"fused":{"win":0.608,"draw":0.223,"lose":0.171},"dc":{"win":0.638,"draw":0.194,"lose":0.168},"nb":{"win":0.610,"draw":0.214,"lose":0.176},"zip":{"win":0.618,"draw":0.226,"lose":0.156},"skellam":{"win":0.630,"draw":0.210,"lose":0.160},"mc":{"win":0.608,"draw":0.210,"lose":0.176},"confidence":{"level":"中","stars":"★★","score":1},"avg_std":0.0100,"max_diff":0.0466,"scores_top10":[{"score":"1:0","dc":"12.1%","zip":"11.1%","mc":"11.5%","combined":"11.7%"},{"score":"2:0","dc":"11.2%","zip":"11.0%","mc":"10.3%","combined":"10.8%"},{"score":"2:1","dc":"9.9%","zip":"9.7%","mc":"8.2%","combined":"9.1%"},{"score":"1:1","dc":"9.2%","zip":"9.8%","mc":"9.4%","combined":"9.4%"}],"over_under":{"over":0.525,"under":0.475,"line":2.5},"half_full_top3":[{"result":"HH","prob":"30.1%"},{"result":"DH","prob":"18.9%"},{"result":"DD","prob":"10.0%"}],"lambda_adjusted":{"home":1.980,"away":0.880}},
  {"id":214,"league":"挪超","home":"维京","away":"桑纳菲尤尔","odds":{"win":1.3,"draw":5.0,"lose":8.5},"ou_line":3.0,"shin":{"win":0.623,"draw":0.210,"lose":0.167},"fused":{"win":0.704,"draw":0.183,"lose":0.114},"dc":{"win":0.741,"draw":0.156,"lose":0.103},"nb":{"win":0.705,"draw":0.181,"lose":0.114},"zip":{"win":0.720,"draw":0.185,"lose":0.095},"skellam":{"win":0.733,"draw":0.170,"lose":0.097},"mc":{"win":0.716,"draw":0.168,"lose":0.112},"confidence":{"level":"低","stars":"★","score":0},"avg_std":0.0102,"max_diff":0.0814,"scores_top10":[{"score":"2:0","dc":"13.2%","zip":"12.9%","mc":"12.6%","combined":"12.8%"},{"score":"1:0","dc":"12.1%","zip":"11.2%","mc":"12.4%","combined":"12.1%"},{"score":"3:0","dc":"10.1%","zip":"9.9%","mc":"8.8%","combined":"9.5%"},{"score":"2:1","dc":"9.2%","zip":"9.0%","mc":"8.0%","combined":"8.6%"}],"over_under":{"over":0.352,"under":0.648,"line":3.0},"half_full_top3":[{"result":"HH","prob":"37.6%"},{"result":"DH","prob":"20.7%"},{"result":"HD","prob":"9.4%"}],"lambda_adjusted":{"home":2.300,"away":0.700}}
];

// ===== HELPERS =====
function pct(v) { return (v * 100).toFixed(1) + '%'; }
function getBest(m) {
  var f = m.fused;
  if (f.win >= f.draw && f.win >= f.lose) return { name: '主胜', key: 'win', val: f.win };
  if (f.draw >= f.lose) return { name: '平局', key: 'draw', val: f.draw };
  return { name: '客胜', key: 'lose', val: f.lose };
}
function getSecond(m) {
  var f = m.fused, best = getBest(m);
  var items = [{n:'主胜',v:f.win},{n:'平局',v:f.draw},{n:'客胜',v:f.lose}]
    .filter(function(i){ return i.n !== best.name; })
    .sort(function(a,b){ return b.v - a.v; });
  return items[0];
}
function hfLabel(code) {
  var map = {H:'胜',D:'平',A:'负'};
  return map[code[0]] + map[code[1]];
}
function confClass(level) {
  if (level === '高') return 'conf-high';
  if (level === '中') return 'conf-mid';
  return 'conf-low';
}
function isDivergent(m) {
  var best = getBest(m);
  return Math.abs(m.fused[best.key] - m.shin[best.key]) > 0.15;
}

// ===== RENDER SUMMARY TABLE =====
function renderSummaryTable() {
  var tbody = document.getElementById('summary-body');
  var html = '';
  DATA.forEach(function(m) {
    var best = getBest(m);
    var second = getSecond(m);
    var ou = m.over_under;
    var ouDir = ou.over > ou.under ? '大' : '小';
    var ouClass = ou.over > ou.under ? 'ou-over' : 'ou-under';
    var warn = isDivergent(m) ? '<span class="warn-badge">⚠️分歧</span>' : '';
    var dirClass = 'dir-' + best.name;
    html += '<tr>'
      + '<td>' + m.id + '</td>'
      + '<td class="td-match"><span class="league-tag league-' + m.league + '">' + m.league + '</span>' + m.home + ' vs ' + m.away + '</td>'
      + '<td>' + m.league + '</td>'
      + '<td><span class="dir-badge ' + dirClass + '">' + best.name + '</span>' + warn + '</td>'
      + '<td style="font-weight:700">' + pct(best.val) + '</td>'
      + '<td>' + second.n + ' ' + pct(second.v) + '</td>'
      + '<td class="' + confClass(m.confidence.level) + '">' + m.confidence.level + ' ' + m.confidence.stars + '</td>'
      + '<td style="font-weight:600">' + m.scores_top10[0].score + '</td>'
      + '<td><span class="ou-tag ' + ouClass + '">' + ouDir + ou.line + ' ' + pct(Math.max(ou.over, ou.under)) + '</span></td>'
      + '</tr>';
  });
  tbody.innerHTML = html;
}

// ===== RENDER STABLE & SPECULATIVE =====
function renderInsights() {
  var stableEl = document.getElementById('stable-list');
  var specEl = document.getElementById('spec-list');
  var stableHtml = '', specHtml = '';

  DATA.forEach(function(m) {
    var best = getBest(m);
    var diff = Math.abs(m.fused[best.key] - m.shin[best.key]);
    var info = MATCH_INFO[m.id];
    var matchLabel = '#' + m.id + ' ' + m.home + ' vs ' + m.away;

    if (m.confidence.score >= 1 && diff <= 0.08) {
      stableHtml += '<div class="insight-item">'
        + '<div><span class="match-name">' + matchLabel + '</span><br><span class="note">' + info.key.substring(0, 30) + '...</span></div>'
        + '<span class="prob">' + best.name + ' ' + pct(best.val) + '</span>'
        + '</div>';
    }
    if (diff > 0.10 || m.confidence.score < 1) {
      specHtml += '<div class="insight-item">'
        + '<div><span class="match-name">' + matchLabel + '</span><br><span class="note">概率差 ' + (diff > 0 ? '+' : '') + pct(diff) + '</span></div>'
        + '<span class="prob" style="color:var(--accent3)">' + best.name + ' ' + pct(best.val) + '</span>'
        + '</div>';
    }
  });
  if (!stableHtml) stableHtml = '<div class="insight-item" style="color:var(--muted);justify-content:center">本期无高置信度稳定场次</div>';
  stableEl.innerHTML = stableHtml;
  specEl.innerHTML = specHtml;
}

// ===== RENDER MATCH CARDS =====
function renderMatchCards() {
  var container = document.getElementById('match-cards');
  var html = '';

  DATA.forEach(function(m) {
    var best = getBest(m);
    var second = getSecond(m);
    var info = MATCH_INFO[m.id];
    var ou = m.over_under;
    var ouDir = ou.over > ou.under ? '大' : '小';
    var warn = isDivergent(m) ? ' <span style="color:var(--accent3);font-weight:600;">⚠️模型与市场严重分歧（>15%），不确定性极高</span>' : '';

    // Model rows
    var models = [
      { name: 'DC模型', d: m.dc },
      { name: '负二项', d: m.nb },
      { name: 'ZIP', d: m.zip },
      { name: 'Skellam', d: m.skellam },
      { name: '蒙特卡洛', d: m.mc }
    ];

    var modelRows = models.map(function(md) {
      return '<tr><td class="model-name">' + md.name + '</td><td>' + pct(md.d.win) + '</td><td>' + pct(md.d.draw) + '</td><td>' + pct(md.d.lose) + '</td></tr>';
    }).join('');
    modelRows += '<tr class="fused-row"><td class="model-name" style="color:var(--accent)">加权融合</td><td style="color:var(--home)">' + pct(m.fused.win) + '</td><td style="color:var(--draw)">' + pct(m.fused.draw) + '</td><td style="color:var(--away)">' + pct(m.fused.lose) + '</td></tr>';

    // Scores
    var scorePills = m.scores_top10.slice(0, 5).map(function(s, i) {
      var cls = i === 0 ? 'primary' : (i === m.scores_top10.length - 1 ? 'cold' : '');
      return '<span class="score-pill ' + cls + '">' + s.score + ' <small>' + s.combined + '</small></span>';
    }).join('');

    // Half-full
    var hfTags = m.half_full_top3.map(function(h) {
      return '<span class="hf-tag">' + hfLabel(h.result) + ' ' + h.prob + '</span>';
    }).join('');

    // Shin comparison
    var shinDiffW = (m.fused.win - m.shin.win) * 100;
    var shinDiffD = (m.fused.draw - m.shin.draw) * 100;
    var shinDiffA = (m.fused.lose - m.shin.lose) * 100;
    function diffColor(d) { return d > 5 ? 'color:var(--accent)' : d < -5 ? 'color:var(--accent3)' : ''; }

    html += '<div class="match-card">'
      + '<div class="match-header">'
        + '<div class="match-title"><span class="id">#' + m.id + '</span>' + m.home + '<span class="vs">vs</span>' + m.away + '</div>'
        + '<div class="match-meta">'
        + '<span class="league-tag league-' + m.league + '">' + m.league + '</span>'
        + '<span style="font-size:0.8rem;color:var(--muted)">主' + info.hrank + ' vs 客' + info.arank + '</span>'
        + '<span class="' + confClass(m.confidence.level) + '" style="font-size:0.85rem">' + m.confidence.level + ' ' + m.confidence.stars + '</span>'
        + '</div></div>'

      // Probability bars
      + '<div class="prob-row"><span class="prob-label" style="color:var(--home)">主胜</span>'
      + '<div class="prob-bar-wrap"><div class="prob-bar home-bar" style="width:' + (m.fused.win*100) + '%">' + (m.fused.win*100 > 15 ? pct(m.fused.win) : '') + '</div></div>'
      + '<span class="prob-val" style="color:var(--home)">' + pct(m.fused.win) + '</span></div>'

      + '<div class="prob-row"><span class="prob-label" style="color:var(--draw)">平局</span>'
      + '<div class="prob-bar-wrap"><div class="prob-bar draw-bar" style="width:' + (m.fused.draw*100) + '%">' + (m.fused.draw*100 > 15 ? pct(m.fused.draw) : '') + '</div></div>'
      + '<span class="prob-val" style="color:var(--draw)">' + pct(m.fused.draw) + '</span></div>'

      + '<div class="prob-row"><span class="prob-label" style="color:var(--away)">客胜</span>'
      + '<div class="prob-bar-wrap"><div class="prob-bar away-bar" style="width:' + (m.fused.lose*100) + '%">' + (m.fused.lose*100 > 15 ? pct(m.fused.lose) : '') + '</div></div>'
      + '<span class="prob-val" style="color:var(--away)">' + pct(m.fused.lose) + '</span></div>'

      // Grid
      + '<div class="match-grid">'
        + '<div>'
        + '<h4>模型对比 vs Shin去水</h4>'
        + '<table class="model-table"><thead><tr><th>模型</th><th>主胜</th><th>平局</th><th>客胜</th></tr></thead><tbody>'
        + '<tr><td class="model-name">Shin去水</td><td>' + pct(m.shin.win) + '</td><td>' + pct(m.shin.draw) + '</td><td>' + pct(m.shin.lose) + '</td></tr>'
        + modelRows
        + '</tbody></table>'
        + '<div style="margin-top:0.5rem;font-size:0.72rem;color:var(--muted)">概率差 → 主胜 <span style="' + diffColor(shinDiffW) + '">' + (shinDiffW >= 0 ? '+' : '') + shinDiffW.toFixed(1) + '%</span> / 平局 <span style="' + diffColor(shinDiffD) + '">' + (shinDiffD >= 0 ? '+' : '') + shinDiffD.toFixed(1) + '%</span> / 客胜 <span style="' + diffColor(shinDiffA) + '">' + (shinDiffA >= 0 ? '+' : '') + shinDiffA.toFixed(1) + '%</span></div>'
        + '</div>'

        + '<div>'
        + '<h4>比分 Top5 / 半全场</h4>'
        + '<div class="score-pills">' + scorePills + '</div>'
        + '<div style="margin-top:0.8rem"><h4 style="margin-bottom:0.3rem">半全场</h4><div class="hf-tags">' + hfTags + '</div></div>'
        + '<div style="margin-top:0.8rem"><h4 style="margin-bottom:0.3rem">大小球 ' + ou.line + '</h4>'
        + '<span class="ou-tag ' + (ou.over > ou.under ? 'ou-over' : 'ou-under') + '">' + ouDir + '球 ' + pct(Math.max(ou.over, ou.under)) + '</span></div>'
        + '</div>'

        + '<div style="grid-column:1/-1">'
        + '<h4>关键信息</h4>'
        + '<ul class="info-list">'
        + '<li><strong>核心：</strong>' + info.key + '</li>'
        + '<li><strong>交锋：</strong>' + info.h2h + '</li>'
        + '<li><strong>xG：</strong>' + info.xg + '</li>'
        + '<li><strong>主队伤停：</strong>' + info.hinj + '</li>'
        + '<li><strong>客队伤停：</strong>' + info.ainj + '</li>'
        + '<li><strong>诊断：</strong>VMR ' + info.vmr + ' | 零膨胀 ' + info.zerorate + ' | λ调整后 ' + m.lambda_adjusted.home.toFixed(3) + ' / ' + m.lambda_adjusted.away.toFixed(3) + '</li>'
        + '</ul>'
        + '<div style="margin-top:0.6rem;padding:0.5rem 0.7rem;background:var(--bg3);border-radius:4px;font-size:0.82rem">'
        + '<strong>综合推荐' + warn + '</strong>：' + best.name + ' ' + pct(best.val) + '（次选' + second.n + ' ' + pct(second.v) + '）| 比分 ' + m.scores_top10[0].score + ' / ' + m.scores_top10[1].score + ' / 冷门 ' + m.scores_top10[2].score
        + '</div>'
        + '</div>'
        + '</div>'
      + '</div>';
  });

  container.innerHTML = html;
}

// ===== INIT =====
renderSummaryTable();
renderInsights();
renderMatchCards();

})();