"""从 data.html / data2.html（猎聘职位详情页）提取信息，输出 Excel。"""
import json
import re
from html import unescape
from pathlib import Path
from bs4 import BeautifulSoup
from openpyxl import Workbook

DATA_FILE = Path("data2.html")
OUTPUT_FILE = Path("提取结果.xlsx")
JOB_TYPE_LEVEL_1 = "生活服务"

HEADERS = [
    "序号",
    "招聘平台",
    "岗位类型\n一级",
    "岗位类型\n二级",
    "岗位名称",
    "岗位类型\n企业/公务员/事业单位/军队文职",
    "公司名称",
    "公司规模",
    "所在省份",
    "城市",
    "详细地址",
    "学历要求",
    "经验要求",
    "薪资范围",
    "福利标签",
    "工作内容",
    "任职要求",
    "岗位链接",
    "发布时间",
    "投递起始时间",
    "投递截止时间",
    "证书要求",
    "备注（技能要求）",
]

CITY_PROVINCE = {
    '北京': '北京市', '天津': '天津市', '上海': '上海市', '重庆': '重庆市',
    '石家庄': '河北省', '唐山': '河北省', '秦皇岛': '河北省', '邯郸': '河北省',
    '邢台': '河北省', '保定': '河北省', '张家口': '河北省', '承德': '河北省',
    '沧州': '河北省', '廊坊': '河北省', '衡水': '河北省',
    '太原': '山西省', '大同': '山西省', '阳泉': '山西省', '长治': '山西省',
    '晋城': '山西省', '朔州': '山西省', '晋中': '山西省', '运城': '山西省',
    '忻州': '山西省', '临汾': '山西省', '吕梁': '山西省',
    '呼和浩特': '内蒙古自治区', '包头': '内蒙古自治区', '乌海': '内蒙古自治区',
    '赤峰': '内蒙古自治区', '通辽': '内蒙古自治区', '鄂尔多斯': '内蒙古自治区',
    '呼伦贝尔': '内蒙古自治区', '巴彦淖尔': '内蒙古自治区', '乌兰察布': '内蒙古自治区',
    '沈阳': '辽宁省', '大连': '辽宁省', '鞍山': '辽宁省', '抚顺': '辽宁省',
    '本溪': '辽宁省', '丹东': '辽宁省', '锦州': '辽宁省', '营口': '辽宁省',
    '阜新': '辽宁省', '辽阳': '辽宁省', '盘锦': '辽宁省', '铁岭': '辽宁省',
    '朝阳': '辽宁省', '葫芦岛': '辽宁省',
    '长春': '吉林省', '吉林': '吉林省', '四平': '吉林省', '辽源': '吉林省',
    '通化': '吉林省', '白山': '吉林省', '松原': '吉林省', '白城': '吉林省',
    '哈尔滨': '黑龙江省', '齐齐哈尔': '黑龙江省', '鸡西': '黑龙江省',
    '鹤岗': '黑龙江省', '双鸭山': '黑龙江省', '大庆': '黑龙江省',
    '伊春': '黑龙江省', '佳木斯': '黑龙江省', '七台河': '黑龙江省',
    '牡丹江': '黑龙江省', '黑河': '黑龙江省', '绥化': '黑龙江省',
    '南京': '江苏省', '无锡': '江苏省', '徐州': '江苏省', '常州': '江苏省',
    '苏州': '江苏省', '南通': '江苏省', '连云港': '江苏省', '淮安': '江苏省',
    '盐城': '江苏省', '扬州': '江苏省', '镇江': '江苏省', '泰州': '江苏省',
    '宿迁': '江苏省',
    '杭州': '浙江省', '宁波': '浙江省', '温州': '浙江省', '嘉兴': '浙江省',
    '湖州': '浙江省', '绍兴': '浙江省', '金华': '浙江省', '衢州': '浙江省',
    '舟山': '浙江省', '台州': '浙江省', '丽水': '浙江省',
    '合肥': '安徽省', '芜湖': '安徽省', '蚌埠': '安徽省', '淮南': '安徽省',
    '马鞍山': '安徽省', '淮北': '安徽省', '铜陵': '安徽省', '安庆': '安徽省',
    '黄山': '安徽省', '滁州': '安徽省', '阜阳': '安徽省', '宿州': '安徽省',
    '六安': '安徽省', '亳州': '安徽省', '池州': '安徽省', '宣城': '安徽省',
    '福州': '福建省', '厦门': '福建省', '莆田': '福建省', '三明': '福建省',
    '泉州': '福建省', '漳州': '福建省', '南平': '福建省', '龙岩': '福建省',
    '宁德': '福建省',
    '南昌': '江西省', '景德镇': '江西省', '萍乡': '江西省', '九江': '江西省',
    '新余': '江西省', '鹰潭': '江西省', '赣州': '江西省', '吉安': '江西省',
    '宜春': '江西省', '抚州': '江西省', '上饶': '江西省',
    '济南': '山东省', '青岛': '山东省', '淄博': '山东省', '枣庄': '山东省',
    '东营': '山东省', '烟台': '山东省', '潍坊': '山东省', '济宁': '山东省',
    '泰安': '山东省', '威海': '山东省', '日照': '山东省', '临沂': '山东省',
    '德州': '山东省', '聊城': '山东省', '滨州': '山东省', '菏泽': '山东省',
    '郑州': '河南省', '开封': '河南省', '洛阳': '河南省', '平顶山': '河南省',
    '安阳': '河南省', '鹤壁': '河南省', '新乡': '河南省', '焦作': '河南省',
    '濮阳': '河南省', '许昌': '河南省', '漯河': '河南省', '三门峡': '河南省',
    '南阳': '河南省', '商丘': '河南省', '信阳': '河南省', '周口': '河南省',
    '驻马店': '河南省',
    '武汉': '湖北省', '黄石': '湖北省', '十堰': '湖北省', '宜昌': '湖北省',
    '襄阳': '湖北省', '鄂州': '湖北省', '荆门': '湖北省', '孝感': '湖北省',
    '荆州': '湖北省', '黄冈': '湖北省', '咸宁': '湖北省', '随州': '湖北省',
    '长沙': '湖南省', '株洲': '湖南省', '湘潭': '湖南省', '衡阳': '湖南省',
    '邵阳': '湖南省', '岳阳': '湖南省', '常德': '湖南省', '张家界': '湖南省',
    '益阳': '湖南省', '郴州': '湖南省', '永州': '湖南省', '怀化': '湖南省',
    '娄底': '湖南省',
    '广州': '广东省', '深圳': '广东省', '珠海': '广东省', '汕头': '广东省',
    '佛山': '广东省', '韶关': '广东省', '河源': '广东省', '梅州': '广东省',
    '惠州': '广东省', '汕尾': '广东省', '东莞': '广东省', '中山': '广东省',
    '江门': '广东省', '阳江': '广东省', '湛江': '广东省', '茂名': '广东省',
    '肇庆': '广东省', '清远': '广东省', '潮州': '广东省', '揭阳': '广东省',
    '云浮': '广东省',
    '南宁': '广西壮族自治区', '柳州': '广西壮族自治区', '桂林': '广西壮族自治区',
    '梧州': '广西壮族自治区', '北海': '广西壮族自治区', '防城港': '广西壮族自治区',
    '钦州': '广西壮族自治区', '贵港': '广西壮族自治区', '玉林': '广西壮族自治区',
    '百色': '广西壮族自治区', '贺州': '广西壮族自治区', '河池': '广西壮族自治区',
    '来宾': '广西壮族自治区', '崇左': '广西壮族自治区',
    '海口': '海南省', '三亚': '海南省', '儋州': '海南省',
    '成都': '四川省', '自贡': '四川省', '攀枝花': '四川省', '泸州': '四川省',
    '德阳': '四川省', '绵阳': '四川省', '广元': '四川省', '遂宁': '四川省',
    '内江': '四川省', '乐山': '四川省', '南充': '四川省', '眉山': '四川省',
    '宜宾': '四川省', '广安': '四川省', '达州': '四川省', '雅安': '四川省',
    '巴中': '四川省', '资阳': '四川省',
    '贵阳': '贵州省', '六盘水': '贵州省', '遵义': '贵州省', '安顺': '贵州省',
    '毕节': '贵州省', '铜仁': '贵州省',
    '昆明': '云南省', '曲靖': '云南省', '玉溪': '云南省', '保山': '云南省',
    '昭通': '云南省', '丽江': '云南省', '普洱': '云南省', '临沧': '云南省',
    '拉萨': '西藏自治区', '日喀则': '西藏自治区', '昌都': '西藏自治区',
    '林芝': '西藏自治区', '山南': '西藏自治区', '那曲': '西藏自治区',
    '西安': '陕西省', '铜川': '陕西省', '宝鸡': '陕西省', '咸阳': '陕西省',
    '渭南': '陕西省', '延安': '陕西省', '汉中': '陕西省', '榆林': '陕西省',
    '安康': '陕西省', '商洛': '陕西省',
    '兰州': '甘肃省', '嘉峪关': '甘肃省', '金昌': '甘肃省', '白银': '甘肃省',
    '天水': '甘肃省', '武威': '甘肃省', '张掖': '甘肃省', '平凉': '甘肃省',
    '酒泉': '甘肃省', '庆阳': '甘肃省', '定西': '甘肃省', '陇南': '甘肃省',
    '西宁': '青海省', '海东': '青海省',
    '银川': '宁夏回族自治区', '石嘴山': '宁夏回族自治区', '吴忠': '宁夏回族自治区',
    '固原': '宁夏回族自治区', '中卫': '宁夏回族自治区',
    '乌鲁木齐': '新疆维吾尔自治区', '克拉玛依': '新疆维吾尔自治区',
    '吐鲁番': '新疆维吾尔自治区', '哈密': '新疆维吾尔自治区',
    '香港': '香港特别行政区', '澳门': '澳门特别行政区',
    '台北': '台湾省', '新北': '台湾省', '桃园': '台湾省', '台中': '台湾省',
    '台南': '台湾省', '高雄': '台湾省',
    '吉林市': '吉林省', '凉山': '四川省', '红河': '云南省', '伊犁': '新疆维吾尔自治区',
    '湘西': '湖南省', '陵水': '海南省', '定安': '海南省', '保亭': '海南省',
    '澄迈': '海南省', '巴音郭楞': '新疆维吾尔自治区',
}


def clean_header(value):
    if value is None:
        return ""
    return re.sub(r"\s+", "", str(value))


CLEANED_HEADERS = [clean_header(h) for h in HEADERS]


def _get_ld_json(soup):
    for script in soup.select("script[type='application/ld+json']"):
        raw = script.string
        if not raw:
            continue
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and data.get("@type") == "JobPosting":
                return data
        except json.JSONDecodeError:
            pass
        try:
            decoder = json.JSONDecoder(strict=False)
            data = decoder.decode(raw)
            if isinstance(data, dict) and data.get("@type") == "JobPosting":
                return data
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def _parse_location(location_text):
    if not location_text:
        return "", ""
    if "-" in location_text:
        city = location_text.split("-")[0].strip()
    else:
        city = location_text.strip()
    province = CITY_PROVINCE.get(city, "")
    return city, province


def _clean_description(text):
    if not text:
        return ""
    text = unescape(str(text))
    text = re.sub(r"(?i)<\s*br\s*/?\s*>", "\n", text)
    text = re.sub(r"(?i)</?\s*(div|p|li|section|tr|h[1-6])\s*/?\s*>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\r", "\n").replace("　", " ").replace("\xa0", " ")
    lines = []
    for line in text.splitlines():
        line = re.sub(r"[ \t]+", " ", line).strip()
        if not line:
            continue
        if line not in lines[-2:]:
            lines.append(line)
    return "\n".join(lines)


def _split_description(text):
    text = _clean_description(text)
    if not text:
        return "", ""

    requirement_pattern = re.compile(
        r"(任职要求|任职资格|职位要求|岗位要求|应聘要求|资格要求|任职条件|职位要求)[:：】\]\s]*"
    )
    match = requirement_pattern.search(text)
    if not match:
        return text.strip(), ""

    work_content = text[: match.start()].strip()
    requirements = text[match.start():].strip()
    return work_content, requirements


def _make_base_record():
    return {key: "" for key in CLEANED_HEADERS}


def extract_main_job(soup):
    """提取企业直招职位（jobKind=2）。"""
    rec = _make_base_record()
    rec["招聘平台"] = "猎聘"
    rec["岗位类型一级"] = JOB_TYPE_LEVEL_1
    rec["岗位类型企业/公务员/事业单位/军队文职"] = "企业"

    name_el = soup.select_one(".name.ellipsis-2")
    if name_el:
        rec["岗位名称"] = name_el.get_text(strip=True)

    salary_el = soup.select_one(".job-apply-content .salary")
    if salary_el:
        rec["薪资范围"] = salary_el.get_text(strip=True)

    props = soup.select_one(".job-properties")
    if props:
        non_split_texts = []
        for s in props.find_all("span"):
            classes = s.get("class") or []
            if "split" not in classes:
                non_split_texts.append(s.get_text(strip=True))

        if non_split_texts:
            loc_text = non_split_texts[0]
            city, province = _parse_location(loc_text)
            rec["城市"] = city
            rec["所在省份"] = province
            rec["详细地址"] = loc_text

        for text in non_split_texts:
            if re.search(r"年以上|经验|应届|在校", text) and "更新" not in text:
                rec["经验要求"] = text
            elif re.search(r"本科|大专|硕士|博士|学历不限|高中|中专|初中|统招", text):
                rec["学历要求"] = text

    recruit_el = soup.select_one(".recruit-cnt")
    if recruit_el:
        rec["备注（技能要求）"] = recruit_el.get_text(strip=True)

    update_el = soup.select_one(".update-time")
    if update_el:
        rec["发布时间"] = update_el.get_text(strip=True)

    # 福利标签
    labels_container = soup.select_one(".job-apply-container-desc .labels")
    if labels_container:
        labels = [s.get_text(strip=True) for s in labels_container.find_all("span")]
        rec["福利标签"] = " / ".join(labels)

    desc_el = soup.select_one("dd[data-selector='job-intro-content']")
    if desc_el:
        work_content, requirements = _split_description(str(desc_el))
        rec["工作内容"] = work_content
        rec["任职要求"] = requirements

    # 公司名称（企业直招来自侧边栏）
    comp_name_el = soup.select_one(".company-info-container .name")
    if comp_name_el:
        rec["公司名称"] = comp_name_el.get_text(strip=True)

    # 侧边栏：公司规模、详细地址
    for label_box in soup.select(".company-other .label-box"):
        label_el = label_box.select_one(".label")
        text_el = label_box.select_one(".text")
        if not label_el or not text_el:
            continue
        label = label_el.get_text(strip=True)
        text = text_el.get_text(strip=True)
        if "人数规模" in label:
            rec["公司规模"] = text
        elif "职位地址" in label:
            rec["详细地址"] = text
            city, province = _parse_location(text)
            if city:
                rec["城市"] = city
                rec["所在省份"] = province

    # 猎头职位：公司名称来自 title-box
    if not rec["公司名称"]:
        title_box = soup.select_one(".recruiter-container .title-box")
        if title_box:
            spans = title_box.find_all("span")
            if len(spans) >= 2:
                company_text = spans[1].get_text(strip=True)
                company_text = company_text.lstrip("· ").strip()
                if company_text:
                    rec["公司名称"] = company_text

    ld = _get_ld_json(soup)
    if ld:
        if not rec["岗位名称"]:
            rec["岗位名称"] = ld.get("title", "")
        rec["岗位链接"] = ld.get("url", "")
        if ld.get("datePosted"):
            rec["投递起始时间"] = ld["datePosted"]
        # 投递截止时间置空
        if ld.get("industry"):
            info_parts = []
            if rec["备注（技能要求）"]:
                info_parts.append(rec["备注（技能要求）"])
            info_parts.append(f"行业要求：{ld['industry']}")
            rec["备注（技能要求）"] = "；".join(info_parts)
        if not rec["经验要求"] and ld.get("experienceRequirements"):
            rec["经验要求"] = ld["experienceRequirements"]
        if not rec["学历要求"] and ld.get("educationRequirements"):
            rec["学历要求"] = ld["educationRequirements"]
        if not rec["公司名称"]:
            org = ld.get("hiringOrganization", {})
            if org.get("name"):
                rec["公司名称"] = org["name"]

    other_dds = soup.select(".job-intro-container .paragraph:nth-of-type(2) .ellipsis-1")
    for dd in other_dds:
        text = dd.get_text(strip=True)
        if not text:
            continue
        existing = rec["备注（技能要求）"]
        if text not in existing:
            rec["备注（技能要求）"] = f"{existing}；{text}".strip("；") if existing else text

    return rec


def extract_recommended_jobs(soup):
    """提取 '猜你喜欢' 中的推荐职位卡片。"""
    records = []
    cards = soup.select(".love-job-container .job-card-pc-container")

    for card in cards:
        rec = _make_base_record()
        rec["招聘平台"] = "猎聘"
        rec["岗位类型一级"] = JOB_TYPE_LEVEL_1
        rec["岗位类型企业/公务员/事业单位/军队文职"] = "企业"

        title_el = card.select_one(".job-title-box div[title]")
        if title_el:
            rec["岗位名称"] = title_el.get("title", "").strip()

        salary_el = card.select_one(".job-salary")
        if salary_el:
            rec["薪资范围"] = salary_el.get_text(strip=True)

        dq_el = card.select_one(".job-dq-box .ellipsis-1")
        if dq_el:
            city_full = dq_el.get_text(strip=True)
            city, province = _parse_location(city_full)
            rec["城市"] = city
            rec["所在省份"] = province
            rec["详细地址"] = city_full

        comp_el = card.select_one(".company-name")
        if comp_el:
            rec["公司名称"] = comp_el.get_text(strip=True)

        tags = card.select(".company-tags-box span")
        size_found = False
        for tag in reversed(tags):
            text = tag.get_text(strip=True)
            if re.search(r"\d+.*人", text):
                rec["公司规模"] = text
                size_found = True
                break
        if not size_found and len(tags) >= 3:
            last_text = tags[-1].get_text(strip=True)
            if last_text:
                rec["公司规模"] = last_text

        link_el = card.select_one("a[data-nick='job-detail-job-info']")
        if link_el:
            rec["岗位链接"] = link_el.get("href", "")

        records.append(rec)

    return records


def export_to_excel(records, output_file=OUTPUT_FILE):
    wb = Workbook()
    ws = wb.active
    ws.title = "提取结果"
    ws.append(list(HEADERS))

    for i, rec in enumerate(records):
        rec["序号"] = i + 1
        row = [rec.get(key, "") for key in CLEANED_HEADERS]
        ws.append(row)

    wb.save(output_path := str(output_file))
    return output_path


def main():
    soup = BeautifulSoup(DATA_FILE.read_text(encoding="utf-8"), "html.parser")
    main_job = extract_main_job(soup)
    output_path = export_to_excel([main_job])
    print(f"共提取 1 条数据")
    print(f"输出文件：{output_path}")


if __name__ == "__main__":
    main()
