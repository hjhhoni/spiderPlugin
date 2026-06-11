import requests
import re
import json
import time

# ==================== 省份映射 ====================
CITY_PROVINCE = {
    '北京': '北京市', '天津': '天津市', '上海': '上海市', '重庆': '重庆市',
    # 河北
    '石家庄': '河北省', '唐山': '河北省', '秦皇岛': '河北省', '邯郸': '河北省', '邢台': '河北省',
    '保定': '河北省', '张家口': '河北省', '承德': '河北省', '沧州': '河北省', '廊坊': '河北省',
    '衡水': '河北省',
    # 山西
    '太原': '山西省', '大同': '山西省', '阳泉': '山西省', '长治': '山西省', '晋城': '山西省',
    '朔州': '山西省', '晋中': '山西省', '运城': '山西省', '忻州': '山西省', '临汾': '山西省',
    '吕梁': '山西省',
    # 内蒙古
    '呼和浩特': '内蒙古自治区', '包头': '内蒙古自治区', '乌海': '内蒙古自治区', '赤峰': '内蒙古自治区',
    '通辽': '内蒙古自治区', '鄂尔多斯': '内蒙古自治区', '呼伦贝尔': '内蒙古自治区', '巴彦淖尔': '内蒙古自治区',
    '乌兰察布': '内蒙古自治区',
    # 辽宁
    '沈阳': '辽宁省', '大连': '辽宁省', '鞍山': '辽宁省', '抚顺': '辽宁省', '本溪': '辽宁省',
    '丹东': '辽宁省', '锦州': '辽宁省', '营口': '辽宁省', '阜新': '辽宁省', '辽阳': '辽宁省',
    '盘锦': '辽宁省', '铁岭': '辽宁省', '朝阳': '辽宁省', '葫芦岛': '辽宁省',
    # 吉林
    '长春': '吉林省', '吉林': '吉林省', '四平': '吉林省', '辽源': '吉林省', '通化': '吉林省',
    '白山': '吉林省', '松原': '吉林省', '白城': '吉林省',
    # 黑龙江
    '哈尔滨': '黑龙江省', '齐齐哈尔': '黑龙江省', '鸡西': '黑龙江省', '鹤岗': '黑龙江省',
    '双鸭山': '黑龙江省', '大庆': '黑龙江省', '伊春': '黑龙江省', '佳木斯': '黑龙江省',
    '七台河': '黑龙江省', '牡丹江': '黑龙江省', '黑河': '黑龙江省', '绥化': '黑龙江省',
    # 江苏
    '南京': '江苏省', '无锡': '江苏省', '徐州': '江苏省', '常州': '江苏省', '苏州': '江苏省',
    '南通': '江苏省', '连云港': '江苏省', '淮安': '江苏省', '盐城': '江苏省', '扬州': '江苏省',
    '镇江': '江苏省', '泰州': '江苏省', '宿迁': '江苏省',
    # 浙江
    '杭州': '浙江省', '宁波': '浙江省', '温州': '浙江省', '嘉兴': '浙江省', '湖州': '浙江省',
    '绍兴': '浙江省', '金华': '浙江省', '衢州': '浙江省', '舟山': '浙江省', '台州': '浙江省',
    '丽水': '浙江省',
    # 安徽
    '合肥': '安徽省', '芜湖': '安徽省', '蚌埠': '安徽省', '淮南': '安徽省', '马鞍山': '安徽省',
    '淮北': '安徽省', '铜陵': '安徽省', '安庆': '安徽省', '黄山': '安徽省', '滁州': '安徽省',
    '阜阳': '安徽省', '宿州': '安徽省', '六安': '安徽省', '亳州': '安徽省', '池州': '安徽省',
    '宣城': '安徽省',
    # 福建
    '福州': '福建省', '厦门': '福建省', '莆田': '福建省', '三明': '福建省', '泉州': '福建省',
    '漳州': '福建省', '南平': '福建省', '龙岩': '福建省', '宁德': '福建省',
    # 江西
    '南昌': '江西省', '景德镇': '江西省', '萍乡': '江西省', '九江': '江西省', '新余': '江西省',
    '鹰潭': '江西省', '赣州': '江西省', '吉安': '江西省', '宜春': '江西省', '抚州': '江西省',
    '上饶': '江西省',
    # 山东
    '济南': '山东省', '青岛': '山东省', '淄博': '山东省', '枣庄': '山东省', '东营': '山东省',
    '烟台': '山东省', '潍坊': '山东省', '济宁': '山东省', '泰安': '山东省', '威海': '山东省',
    '日照': '山东省', '临沂': '山东省', '德州': '山东省', '聊城': '山东省', '滨州': '山东省',
    '菏泽': '山东省',
    # 河南
    '郑州': '河南省', '开封': '河南省', '洛阳': '河南省', '平顶山': '河南省', '安阳': '河南省',
    '鹤壁': '河南省', '新乡': '河南省', '焦作': '河南省', '濮阳': '河南省', '许昌': '河南省',
    '漯河': '河南省', '三门峡': '河南省', '南阳': '河南省', '商丘': '河南省', '信阳': '河南省',
    '周口': '河南省', '驻马店': '河南省',
    # 湖北
    '武汉': '湖北省', '黄石': '湖北省', '十堰': '湖北省', '宜昌': '湖北省', '襄阳': '湖北省',
    '鄂州': '湖北省', '荆门': '湖北省', '孝感': '湖北省', '荆州': '湖北省', '黄冈': '湖北省',
    '咸宁': '湖北省', '随州': '湖北省',
    # 湖南
    '长沙': '湖南省', '株洲': '湖南省', '湘潭': '湖南省', '衡阳': '湖南省', '邵阳': '湖南省',
    '岳阳': '湖南省', '常德': '湖南省', '张家界': '湖南省', '益阳': '湖南省', '郴州': '湖南省',
    '永州': '湖南省', '怀化': '湖南省', '娄底': '湖南省',
    # 广东
    '广州': '广东省', '深圳': '广东省', '珠海': '广东省', '汕头': '广东省', '佛山': '广东省',
    '韶关': '广东省', '河源': '广东省', '梅州': '广东省', '惠州': '广东省', '汕尾': '广东省',
    '东莞': '广东省', '中山': '广东省', '江门': '广东省', '阳江': '广东省', '湛江': '广东省',
    '茂名': '广东省', '肇庆': '广东省', '清远': '广东省', '潮州': '广东省', '揭阳': '广东省',
    '云浮': '广东省',
    # 广西
    '南宁': '广西壮族自治区', '柳州': '广西壮族自治区', '桂林': '广西壮族自治区', '梧州': '广西壮族自治区',
    '北海': '广西壮族自治区', '防城港': '广西壮族自治区', '钦州': '广西壮族自治区', '贵港': '广西壮族自治区',
    '玉林': '广西壮族自治区', '百色': '广西壮族自治区', '贺州': '广西壮族自治区', '河池': '广西壮族自治区',
    '来宾': '广西壮族自治区', '崇左': '广西壮族自治区',
    # 海南
    '海口': '海南省', '三亚': '海南省', '儋州': '海南省',
    # 四川
    '成都': '四川省', '自贡': '四川省', '攀枝花': '四川省', '泸州': '四川省', '德阳': '四川省',
    '绵阳': '四川省', '广元': '四川省', '遂宁': '四川省', '内江': '四川省', '乐山': '四川省',
    '南充': '四川省', '眉山': '四川省', '宜宾': '四川省', '广安': '四川省', '达州': '四川省',
    '雅安': '四川省', '巴中': '四川省', '资阳': '四川省',
    # 贵州
    '贵阳': '贵州省', '六盘水': '贵州省', '遵义': '贵州省', '安顺': '贵州省', '毕节': '贵州省',
    '铜仁': '贵州省',
    # 云南
    '昆明': '云南省', '曲靖': '云南省', '玉溪': '云南省', '保山': '云南省', '昭通': '云南省',
    '丽江': '云南省', '普洱': '云南省', '临沧': '云南省',
    # 西藏
    '拉萨': '西藏自治区', '日喀则': '西藏自治区',
    # 陕西
    '西安': '陕西省', '铜川': '陕西省', '宝鸡': '陕西省', '咸阳': '陕西省', '渭南': '陕西省',
    '延安': '陕西省', '汉中': '陕西省', '榆林': '陕西省', '安康': '陕西省', '商洛': '陕西省',
    # 甘肃
    '兰州': '甘肃省', '嘉峪关': '甘肃省', '金昌': '甘肃省', '白银': '甘肃省', '天水': '甘肃省',
    '武威': '甘肃省', '张掖': '甘肃省', '平凉': '甘肃省', '酒泉': '甘肃省', '庆阳': '甘肃省',
    '定西': '甘肃省', '陇南': '甘肃省',
    # 青海
    '西宁': '青海省', '海东': '青海省',
    # 宁夏
    '银川': '宁夏回族自治区', '石嘴山': '宁夏回族自治区', '吴忠': '宁夏回族自治区', '固原': '宁夏回族自治区',
    '中卫': '宁夏回族自治区',
    # 新疆
    '乌鲁木齐': '新疆维吾尔自治区', '克拉玛依': '新疆维吾尔自治区', '吐鲁番': '新疆维吾尔自治区',
    '哈密': '新疆维吾尔自治区',
    # 香港/澳门/台湾
    '香港': '香港特别行政区', '澳门': '澳门特别行政区',
    '台北': '台湾省', '新北': '台湾省', '桃园': '台湾省', '台中': '台湾省', '台南': '台湾省',
    '高雄': '台湾省',
}

headers = {
    "Referer": "https://www.lagou.com/wn/zhaopin/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "cookie": "index_location_city=%E5%85%A8%E5%9B%BD; _c_WBKFRo=uKDcSh89RLnhvCfjLKvItGC13UYwxnn0LCGmwDRz; _nb_ioWEgULi=; JSESSIONID=ABAACDGAAAHABDI791C6172ED55E46510B2574BD279A313; WEBTJ-ID=06102026%2C224304-19eb1fca3641026-0e8df24aeffb918-26061151-1474560-19eb1fca36510e3; user_trace_token=20260610224305-1f62caef-fe06-475c-afc0-b45e51c2abfb; LGUID=20260610224305-b4a8467c-ce35-4a5b-a641-a946db531e29; Hm_lvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1781102586; HMACCOUNT=0CAC285AA3ABBE08; _ga=GA1.2.924315593.1781102586; _gid=GA1.2.1667348870.1781102586; sensorsdata2015session=%7B%7D; SEARCH_ID=81f1d2a344a94c25af56d2f34c81ee5b; TG-TRACK-CODE=search_code; Hm_lpvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1781141512; LGRID=20260611093150-075b2860-d79c-483b-bbfc-ceadd16ccdc1; _ga_DDLTLJDLHH=GS2.2.s1781141486$o2$g1$t1781141511$j35$l0$h0; acw_tc=ac11000117811643689537590e01724b6e3c77864d7576237348efb0b4357e; acw_sc__v3=6a2a6955afec346200bb1c40484bd2761a5cb4a8; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2219eb1fca4ce17-0a2caa3e50c86a8-26061151-1474560-19eb1fca4cf1240%22%2C%22%24device_id%22%3A%2219eb1fca4ce17-0a2caa3e50c86a8-26061151-1474560-19eb1fca4cf1240%22%2C%22props%22%3A%7B%22%24latest_utm_source%22%3A%22PC_SEARCH%22%2C%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%2C%22%24os%22%3A%22Windows%22%2C%22%24browser%22%3A%22Chrome%22%2C%22%24browser_version%22%3A%22148.0.0.0%22%7D%7D; ssxmod_itna=1-Qq0xgDyD2Dn7i=DOQG0WKiOD2WDuDwxx4BP01kDuxiK08D6exBRij4hSA44h_4G=t_QDx4D0mT2GCDBT2wr7DB9YHQYClv25tanQ44q3RZ7GXpKlajoOuQil7E8ctdC9Hmcp6dyLh_27AYxwGxK8AAMzSLrDB3Dbdfx_YvoxYYDC4GwDGoD34DiDDPDb33DAqqD7qDF/jWWT=WDm4GW/eGfDDoDYSuQxit3DDtDiu2Nirn_DDNxPjbefmDkyc2s2BqT57yz/eDMixGXzYl_/W72oXAFy1MzA1EQxB=gxBjW20cA/YKrsaa8=4o6eo=_wex4Q4Bmek7GDaKKQ_PlGDoesYIzi25lD4QDKBwC70izeDnWt3_7tRrQD452lj5/n5VKr41iTSrTRgrKbebuqlxxDuYDEtB2NCGa9x4WAxiwk_GetgYI0YI3zKbrAAsi0H8_45gYQDabExPD; ssxmod_itna2=1-Qq0xgDyD2Dn7i=DOQG0WKiOD2WDuDwxx4BP01kDuxiK08D6exBRij4hSA44h_4G=t_QDx4D0mT2GrD88WeebRPoRqDLeh0GxaaWQb25DBwiaH3_W1i20IdkqxyU37kciSgUjSdZ8HMM2H7N2cDMP2OBEGaUW01jx5wM=DzQBImQeFrpxHhOFKqVEIvIZTG84wqCx9A3WPxrQ3qPao4rBqL0ZGxw/Gmy8Km1agqq09DA2YO_S4q6SHLdv3QA6lq64BR=7c2x4jIvc=_C61sQjapqGEdC9=86ST26r=j00pRuEoa1k5yP0KqQGQrAbsgxeYQPSTmdQQ7r/iT_84pr4xRFp25iqx4SWND_uOYTmQQDFp_rkktD4KkObhopSYiHAQqQ=083pohwmhUx82qt8_xdGtmEd3LN/0t3fAjr_e==8jzSTdd63F2Cz_sZ21AMGAx_mCNIrb0b=s48uxGHCp5jmoWWGZdnQFa2YVL384xMfzvmtW==_E=8bHjEa8SAqUb=B3gZ1lktujwaCN=nEhgNC8=AxLwE3bImsd=PTO0mkHT55jbUBzzfaWgXmrbpLYs/5zxhkhrAk=N7rS3UIdm21byWuXnQe5O7qptutTiiAUWjem/EkAzkVShUx=RfUQbucuQ3cQvbESqKCf7q7rEyrYNyj8psjQ31ris=UeLwBYwYVlVY/Y5MiNDeKiD6qYiVhGPhDD"
}

MAX_PAGES = 10


def get_city_province(city):
    if not city:
        return ""
    for key in (city, city.rstrip("市"), city + "市"):
        if key in CITY_PROVINCE:
            return CITY_PROVINCE[key]
    return ""


def split_position_detail(text):
    if not text:
        return "", ""
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    req_kw_set = {"任职要求", "任职资格", "职位要求", "岗位要求", "应聘要求", "资格要求", "任职条件", "招聘要求"}
    desc_kw_set = {"岗位职责", "工作职责", "职位描述", "工作内容"}
    all_kw = req_kw_set | desc_kw_set
    matches = []
    for kw in all_kw:
        idx = text.find(kw)
        if idx != -1:
            matches.append((idx, kw))
    matches.sort()
    if not matches:
        return text.strip(), ""
    desc_parts, req_parts = [], []
    first_pos = matches[0][0]
    if first_pos > 0:
        desc_parts.append(text[:first_pos].strip())
    for i, (pos, kw) in enumerate(matches):
        next_pos = matches[i + 1][0] if i + 1 < len(matches) else len(text)
        segment = text[pos:next_pos].strip()
        if kw in req_kw_set:
            req_parts.append(segment)
        else:
            desc_parts.append(segment)
    return "\n".join(desc_parts).strip(), "\n".join(req_parts).strip()


def fetch_page(pn):
    params = {"pn": str(pn)}
    res = requests.get("https://www.lagou.com/wn/zhaopin", headers=headers, params=params)
    res.raise_for_status()
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', res.text)
    if not match:
        print(f"[页码 {pn}] 未找到 __NEXT_DATA__，Cookie 可能已过期")
        return []
    data = json.loads(match.group(1))
    return data["props"]["pageProps"]["initData"]["content"]["positionResult"]["result"]


def build_record(item, idx):
    desc, req = split_position_detail(item.get("positionDetail", ""))
    city = item.get("city", "")
    district = item.get("district", "")
    address = district
    if item.get("positionAddress"):
        address = f"{district}·{item['positionAddress']}" if district else item["positionAddress"]
    link = ""
    pos_id = item.get("positionId")
    if pos_id:
        link = f"https://www.lagou.com/jobs/{pos_id}.html"
    return {
        "序号": idx,
        "招聘平台": "拉钩招聘",
        "岗位类型\n一级": item.get("firstType", ""),
        "岗位类型\n二级": item.get("secondType", ""),
        "岗位名称": item.get("positionName", ""),
        "岗位类型\n企业/公务员/事业单位/军队文职": "企业",
        "公司名称": item.get("companyFullName", ""),
        "公司规模": item.get("companySize", ""),
        "所在省份": get_city_province(city),
        "城市": city,
        "详细地址": address,
        "学历要求": item.get("education", ""),
        "经验要求": item.get("workYear", ""),
        "薪资范围": item.get("salary", ""),
        "福利标签": item.get("positionAdvantage", ""),
        "工作内容": desc,
        "任职要求": req,
        "岗位链接": link,
        "发布时间": item.get("createTime", ""),
        "投递起始时间": "",
        "投递截止时间": "",
        "证书要求": "",
        "备注（技能要求）": ", ".join(item.get("skillLables", [])),
    }


def main():
    all_records = []
    for pn in range(1, MAX_PAGES + 1):
        print(f"正在抓取第 {pn} 页...", end=" ")
        try:
            items = fetch_page(pn)
        except Exception as e:
            print(f"错误: {e}")
            break
        if not items:
            print("无数据，翻页结束")
            break
        for item in items:
            all_records.append(build_record(item, len(all_records) + 1))
        print(f"获取 {len(items)} 条 (累计 {len(all_records)} 条)")
    with open("lagou_jobs.json", "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)
    print(f"\n完成！共 {len(all_records)} 条，已保存到 lagou_jobs.json")


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"耗时: {end_time - start_time:.2f} 秒")
