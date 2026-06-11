# import requests
# import re
# import json
# from pprint import pprint # 格式化输出

# headers = {
#     "Referer": "https://www.lagou.com/wn/zhaopin/",
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
#     "cookie": "index_location_city=%E5%85%A8%E5%9B%BD; _c_WBKFRo=uKDcSh89RLnhvCfjLKvItGC13UYwxnn0LCGmwDRz; _nb_ioWEgULi=; JSESSIONID=ABAACDGAAAHABDI791C6172ED55E46510B2574BD279A313; WEBTJ-ID=06102026%2C224304-19eb1fca3641026-0e8df24aeffb918-26061151-1474560-19eb1fca36510e3; user_trace_token=20260610224305-1f62caef-fe06-475c-afc0-b45e51c2abfb; LGUID=20260610224305-b4a8467c-ce35-4a5b-a641-a946db531e29; Hm_lvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1781102586; HMACCOUNT=0CAC285AA3ABBE08; _ga=GA1.2.924315593.1781102586; _gid=GA1.2.1667348870.1781102586; sensorsdata2015session=%7B%7D; SEARCH_ID=81f1d2a344a94c25af56d2f34c81ee5b; TG-TRACK-CODE=search_code; Hm_lpvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1781141512; LGRID=20260611093150-075b2860-d79c-483b-bbfc-ceadd16ccdc1; _ga_DDLTLJDLHH=GS2.2.s1781141486$o2$g1$t1781141511$j35$l0$h0; acw_tc=ac11000117811478573583528e00d7c46bdeeb3212e1a21b126e8b655df82c; acw_sc__v3=6a2a28d41875fc186fb3b8b6a2ebfaa501bc66a0; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2219eb1fca4ce17-0a2caa3e50c86a8-26061151-1474560-19eb1fca4cf1240%22%2C%22%24device_id%22%3A%2219eb1fca4ce17-0a2caa3e50c86a8-26061151-1474560-19eb1fca4cf1240%22%2C%22props%22%3A%7B%22%24latest_utm_source%22%3A%22PC_SEARCH%22%2C%22%24os%22%3A%22Windows%22%2C%22%24browser%22%3A%22Chrome%22%2C%22%24browser_version%22%3A%22148.0.0.0%22%7D%7D; ssxmod_itna=1-Qq0xgDyD2Dn7i=DOQG0WKiOD2WDuDwxx4BP01kDuxiK08D6exBRij4hSA44hbutG=3zDDIhg7mqDs45hxGkwC2GGrPViQlhiPdwG0G_CNKldEhsqHtUQh4oTvFAMurWT9QSyX5PoRYDHxi8t=Gs3B5DxxGTDCeDQxirDD4DADibtxD17DDkD0_m7UovW4GWDm_mDWPDYxDrbRYDRrxD0xD8x/x3ateDBaWrY_D_emfLx3dKsmgDU9wmD753DlcqWNmmcFZcqxfLtyuEo2YDXatDv2oKhSn52WEA1zSYPIWhw7WeeQRqd=G=QDqK4OiR4z0DwDO4TNiBqzik70NRr/AArDiTw0DanYK7sw0CEk16M1wGst7oZ7oLnYqDxrD=NB5eBdwDoSG5/GIVGYqAsKBQQBpbY5SkwlEtUQdt7YXexdEsFWwroQKOY4D; ssxmod_itna2=1-Qq0xgDyD2Dn7i=DOQG0WKiOD2WDuDwxx4BP01kDuxiK08D6exBRij4hSA44hbutG=3zDDIhg7Q4iTw/ZD2YqQiD7PKQYQ6o4Dlg_fdKTdn=jdPTPRc0nYAdU10nhTslwMG9ZI_YR9Y6siQUnL=l94Lu0kewKOr5=4o1B254iAEhKBr=5bD",
# }


# url = "https://www.lagou.com/wn/zhaopin"
# params = {
#     "pn": "3"
# }
# res = requests.get(url, headers=headers, params=params).text
# # print(res)
# data = re.findall('<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',res)[0]
# json_data = json.loads(data)['props']['pageProps']['initData']['content']['positionResult']['result']
# i = 0
# for item in json_data:
#     dit = {
#         "序号": i,
#         "招聘平台": "拉钩招聘",
#         "岗位类型\n一级",
#         "岗位类型\n二级",
#         "岗位名称",
#         "岗位类型\n企业/公务员/事业单位/军队文职",
#         "公司名称": item['companyFullName'],
#         "公司规模": item['companySize'],
#         "所在省份": item['province'],
#         "城市": item['city'],
#         "详细地址",
#         "学历要求",
#         "经验要求",
#         "薪资范围",
#         "福利标签",
#         "工作内容",
#         "任职要求",
#         "岗位链接",
#         "发布时间",
#         "投递起始时间",
#         "投递截止时间",
#         "证书要求",
#         "备注（技能要求）",
#     }
#     pprint(item)
#     i += 1
#     if i==2:
#         break