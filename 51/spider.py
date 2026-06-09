import json
import logging
import random
import time
from copy import deepcopy
from pathlib import Path

import requests
from requests.exceptions import SSLError, ConnectionError, ReadTimeout

from extract import extract_to_xlsx, parse_items
from ua_true import IdentityGenerator

JOB_CATEGORIES = [
    {
        "job_type_level_1": "保健理疗",
        "keywords": ["按摩师", "足疗"],
    },
    {
        "job_type_level_1": "婚庆",
        "keywords": ["婚礼/庆典策划服务", "司仪"],
    },
    {
        "job_type_level_1": "宠物服务",
        "keywords": ["宠物美容", "宠物医生"],
    },
    {
        "job_type_level_1": "物流/运输",
        "keywords": [
            "货运司机", "物流专员/助理", "物流经理", "物流主管",
            "单证员", "报关与报检", "运输经理/主管", "物流总监",
            "海关事务管理", "货运代理/物流销售",
        ],
    },
    {
        "job_type_level_1": "仓储",
        "keywords": ["仓库管理员", "仓库经理/主管", "仓储理货员", "仓库文员"],
    },
    {
        "job_type_level_1": "配送管理",
        "keywords": ["快递员", "船务/空运陆运操作", "订单处理员", "调度员", "安检员", "集装箱业务"],
    },
    {
        "job_type_level_1": "供应链",
        "keywords": ["供应链专员", "供应链主管", "供应链经理", "供应链总监", "生产计划/物料管理(PMC)"],
    },
]

TOTAL_PAGES = 80          # 保留作为最大页码上限，实际会被 totalPage 覆盖
PAGE_SIZE = 30
RANDOM_WAIT_RANGE = (5, 9)
MAX_RETRIES = 6
RETRY_BASE_WAIT = 1
OUTPUT_FILE = "提取结果.xlsx"
PROGRESS_FILE = Path("crawl_progress.json")
SEARCH_URL = "https://cupid.51job.com/pc/open/noauth/search-h5"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class SkipKeywordError(Exception):
    """用于跳出当前关键词的异常"""
    pass


headers = {
    "referer": "https://msearch.51job.com/jobs/",
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Mobile Safari/537.36 Edg/148.0.0.0",
}


def page_name(page):
    return f"第{page}页"


def log_prefix(job_type_level_1, keyword, page):
    return f"{job_type_level_1}->{keyword}->{page_name(page)}"


def load_progress():
    if not PROGRESS_FILE.exists():
        return {"category_index": 0, "keyword_index": 0, "page": 1}

    try:
        progress = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("断点文件读取失败，将从头开始爬取：%s", PROGRESS_FILE)
        return {"category_index": 0, "keyword_index": 0, "page": 1}

    category_index = progress.get("category_index", 0)
    keyword_index = progress.get("keyword_index", 0)
    page = progress.get("page", 1)
    if not isinstance(category_index, int) or category_index < 0:
        category_index = 0
    if not isinstance(keyword_index, int) or keyword_index < 0:
        keyword_index = 0
    if not isinstance(page, int) or page < 1:
        page = 1
    return {"category_index": category_index, "keyword_index": keyword_index, "page": page}


def save_progress(category_index, keyword_index, page):
    progress = {"category_index": category_index, "keyword_index": keyword_index, "page": page}
    PROGRESS_FILE.write_text(
        json.dumps(progress, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def fetch_page(job_type_level_1, keyword, page):
    """请求搜索接口，返回 (response_data, count, total_page)"""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            params = {
                "api_key": "51job",
                "timestamp": int(time.time()),
                "keyword": keyword,
                "searchType": "2",
                "jobArea": "",
                "pageSize": str(PAGE_SIZE),
                "pageNum": str(page),
                "source": "3",
                "accountId": "",
                "requestId": "",
                "sortType": "1",
            }

            request_headers = headers.copy()
            request_headers.update(IdentityGenerator.generate_headers())

            response = requests.get(
                SEARCH_URL,
                headers=request_headers,
                params=params,
                timeout=20,
            )

            if response.status_code == 500:
                logger.error("%s返回500，停止当前关键词", log_prefix(job_type_level_1, keyword, page))
                raise SkipKeywordError

            response_data = response.json()
            job_block = response_data.get("resultbody", {}).get("job", {})
            items = job_block.get("items", [])
            count = len(items)

            total_page = job_block.get("totalPage", 0)
            if not total_page:
                total_count = job_block.get("totalCount", 0)
                if total_count:
                    total_page = (total_count + PAGE_SIZE - 1) // PAGE_SIZE

            if response.status_code == 200 and count == 0:
                if total_page and page > total_page:
                    logger.info("%s已超出总页数(%d)，正常结束", log_prefix(job_type_level_1, keyword, page), total_page)
                    raise SkipKeywordError
                else:
                    if attempt == MAX_RETRIES:
                        logger.warning("%s连续%d次返回0条，停止翻页", log_prefix(job_type_level_1, keyword, page), MAX_RETRIES)
                        raise SkipKeywordError
                    else:
                        wait = RETRY_BASE_WAIT * (2 ** (attempt - 1))
                        logger.warning("%s返回0条，第%d次重试", log_prefix(job_type_level_1, keyword, page), attempt)
                        time.sleep(wait)
                        continue

            response.raise_for_status()
            logger.info("%s爬取成功，获取%d条数据，总页数=%d", log_prefix(job_type_level_1, keyword, page), count, total_page)
            return response_data, count, total_page

        except SkipKeywordError:
            raise
        except (SSLError, ConnectionError, ReadTimeout) as net_err:
            if attempt >= MAX_RETRIES:
                logger.error("%s网络错误重试%d次后仍失败: %s", log_prefix(job_type_level_1, keyword, page), MAX_RETRIES, net_err)
                raise SkipKeywordError
            wait = RETRY_BASE_WAIT * (2 ** (attempt - 1)) + random.uniform(1, 3)  # 加长等待
            logger.warning("%s网络错误（%s），%d秒后重试", log_prefix(job_type_level_1, keyword, page), type(net_err).__name__, wait)
            time.sleep(wait)
        except Exception as exc:
            if attempt >= MAX_RETRIES:
                logger.error("%s爬取失败%d次: %s", log_prefix(job_type_level_1, keyword, page), MAX_RETRIES, exc)
                raise SkipKeywordError
            wait = RETRY_BASE_WAIT * (2 ** (attempt - 1))
            logger.warning("%s第%d次爬取失败，%d秒后重试，原因：%s", log_prefix(job_type_level_1, keyword, page), attempt, wait, exc)
            time.sleep(wait)

    raise SkipKeywordError  # 所有重试后仍失败，跳过该关键词


def save_page(job_type_level_1, keyword, page, response_data):
    try:
        result = extract_to_xlsx(response_data, OUTPUT_FILE, job_type_level_1=job_type_level_1, job_type_level_2=keyword)
        logger.info(
            "%s保存成功，追加%s条数据，文件：%s",
            log_prefix(job_type_level_1, keyword, page),
            result["count"],
            result["output_file"],
        )
        return True
    except Exception as exc:
        logger.error("%s保存失败，终止执行，原因：%s", log_prefix(job_type_level_1, keyword, page), exc)
        return False


def crawl():
    progress = load_progress()
    start_category_index = progress["category_index"]
    start_keyword_index = progress["keyword_index"]
    start_page = progress["page"]

    if start_category_index >= len(JOB_CATEGORIES):
        logger.info("所有分类已爬取完成，无需继续")
        return 0

    start_category = JOB_CATEGORIES[start_category_index]
    logger.info(
        "从断点继续：%s->%s->%s",
        start_category["job_type_level_1"],
        start_category["keywords"][start_keyword_index] if start_keyword_index < len(start_category["keywords"]) else "?",
        page_name(start_page),
    )

    for category_index in range(start_category_index, len(JOB_CATEGORIES)):
        category = JOB_CATEGORIES[category_index]
        job_type = category["job_type_level_1"]
        keywords = category["keywords"]

        kw_start = start_keyword_index if category_index == start_category_index else 0

        for keyword_index in range(kw_start, len(keywords)):
            keyword = keywords[keyword_index]
            first_page = start_page if (category_index == start_category_index and keyword_index == start_keyword_index) else 1
            keyword_total_page = None

            page = first_page
            while True:
                if keyword_total_page and page > keyword_total_page:
                    logger.info("关键词[%s]所有页面已爬完(总%d页)", keyword, keyword_total_page)
                    break

                wait_seconds = random.uniform(*RANDOM_WAIT_RANGE)
                logger.info("%s等待%.2f秒后开始爬取", log_prefix(job_type, keyword, page), wait_seconds)
                time.sleep(wait_seconds)

                try:
                    response_data, count, total_page = fetch_page(job_type, keyword, page)
                except SkipKeywordError:
                    save_progress(category_index, keyword_index + 1, 1)
                    break

                if keyword_total_page is None and total_page:
                    keyword_total_page = total_page
                    logger.info("关键词[%s]总页数：%d", keyword, keyword_total_page)

                if not save_page(job_type, keyword, page, response_data):
                    return 1

                save_progress(category_index, keyword_index, page)

                if not keyword_total_page and count < PAGE_SIZE:
                    logger.info("%s返回数据不足一页，可能为最后一页，停止翻页", log_prefix(job_type, keyword, page))
                    save_progress(category_index, keyword_index + 1, 1)
                    break

                page += 1

    logger.info("所有分类全部爬取完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(crawl())