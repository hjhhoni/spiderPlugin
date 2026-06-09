import json
import logging
import random
import time
from copy import deepcopy
from pathlib import Path

import requests

from extract import extract_to_xlsx, parse_items
from ua_true import IdentityGenerator

JOB_TYPE_LEVEL_1 = "产品"
KEYWORDS = ["产品经理"]

TOTAL_PAGES = 50
PAGE_SIZE = 20
RANDOM_WAIT_RANGE = (1, 5)
MAX_RETRIES = 3
RETRY_BASE_WAIT = 1
OUTPUT_FILE = "提取结果.xlsx"
PROGRESS_FILE = Path("crawl_progress.json")
SEARCH_URL = "https://fe-api.zhaopin.com/c/i/search/positions"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class SkipKeywordError(Exception):
    pass


headers = {
    "referer": "https://www.zhaopin.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
}

base_json_data = {
    "S_SOU_FULL_INDEX": "",
    "S_SOU_WORK_CITY": "489",
    "order": 4,
    "pageSize": PAGE_SIZE,
    "pageIndex": 1,
    "eventScenario": "pcSearchedSouSearch",
    "anonymous": 1,
    "clickFilterBlackCompany": False,
    "platform": 13,
    "version": "0.0.0",
}


def page_name(page):
    return f"第{page}页"


def log_prefix(keyword, page):
    return f"{JOB_TYPE_LEVEL_1}->{keyword}->{page_name(page)}"


def load_progress():
    if not PROGRESS_FILE.exists():
        return {"keyword_index": 0, "page": 1}

    try:
        progress = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("断点文件读取失败，将从头开始爬取：%s", PROGRESS_FILE)
        return {"keyword_index": 0, "page": 1}

    keyword_index = progress.get("keyword_index", 0)
    page = progress.get("page", 1)
    if not isinstance(keyword_index, int) or keyword_index < 0:
        keyword_index = 0
    if not isinstance(page, int) or page < 1:
        page = 1
    return {"keyword_index": keyword_index, "page": page}


def save_progress(keyword_index, page):
    progress = {"keyword_index": keyword_index, "page": page}
    PROGRESS_FILE.write_text(
        json.dumps(progress, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def next_progress(keyword_index, page):
    if page < TOTAL_PAGES:
        return keyword_index, page + 1
    return keyword_index + 1, 1


def fetch_page(keyword, page):
    json_data = deepcopy(base_json_data)
    json_data["S_SOU_FULL_INDEX"] = keyword
    json_data["pageIndex"] = page

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            request_headers = headers.copy()
            request_headers.update(IdentityGenerator.generate_headers())
            response = requests.post(
                SEARCH_URL,
                headers=request_headers,
                json=json_data,
                timeout=20,
            )
            if response.status_code == 500:
                logger.error("%s返回500，停止当前关键词，切换到下一个关键词", log_prefix(keyword, page))
                raise SkipKeywordError
            if response.status_code == 200 and not response.json()['data']['list']:
                logger.error("%s返回200，但数据为空，停止当前关键词，切换到下一个关键词", log_prefix(keyword, page))
                raise SkipKeywordError
            response.raise_for_status()
            response_data = response.json()
            count = len(parse_items(response_data))
            logger.info("%s爬取成功，获取%s条数据", log_prefix(keyword, page), count)
            return response_data, count
        except SkipKeywordError:
            raise
        except Exception as exc:
            if attempt >= MAX_RETRIES:
                logger.error("%s爬取失败3次，终止执行，原因：%s", log_prefix(keyword, page), exc)
                raise

            wait_seconds = RETRY_BASE_WAIT * (2 ** (attempt - 1))
            logger.warning(
                "%s第%s次爬取失败，%s秒后重试，原因：%s",
                log_prefix(keyword, page),
                attempt,
                wait_seconds,
                exc,
            )
            time.sleep(wait_seconds)


def save_page(keyword, page, response_data):
    try:
        result = extract_to_xlsx(response_data, OUTPUT_FILE, job_type_level_2=keyword)
        logger.info(
            "%s保存成功，追加%s条数据，文件：%s",
            log_prefix(keyword, page),
            result["count"],
            result["output_file"],
        )
        return True
    except Exception as exc:
        logger.error("%s保存失败，终止执行，原因：%s", log_prefix(keyword, page), exc)
        return False


def crawl():
    progress = load_progress()
    start_keyword_index = progress["keyword_index"]
    start_page = progress["page"]

    if start_keyword_index >= len(KEYWORDS):
        logger.info("所有关键词已爬取完成，无需继续")
        return 0

    logger.info(
        "从断点继续：%s->%s",
        KEYWORDS[start_keyword_index],
        page_name(start_page),
    )

    for keyword_index in range(start_keyword_index, len(KEYWORDS)):
        keyword = KEYWORDS[keyword_index]
        first_page = start_page if keyword_index == start_keyword_index else 1

        for page in range(first_page, TOTAL_PAGES + 1):
            wait_seconds = random.uniform(*RANDOM_WAIT_RANGE)
            logger.info("%s等待%.2f秒后开始爬取", log_prefix(keyword, page), wait_seconds)
            time.sleep(wait_seconds)

            try:
                response_data, count = fetch_page(keyword, page)
            except SkipKeywordError:
                save_progress(keyword_index + 1, 1)
                break
            except Exception:
                return 1

            if not save_page(keyword, page, response_data):
                return 1

            next_keyword_index, next_page = next_progress(keyword_index, page)
            save_progress(next_keyword_index, next_page)

            if count == 0:
                logger.warning("%s未获取到数据，继续下一页", log_prefix(keyword, page))

    logger.info("所有关键词全部爬取完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(crawl())
