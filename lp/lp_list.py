import json
import logging
import random
import sqlite3
import time
from pathlib import Path

import execjs
import requests

from ua_true import IdentityGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

with open("lp_list.js", "r", encoding="utf-8") as f:
    js_code = f.read()
js_compile = execjs.compile(js_code)

DQ = ['410', '010', '020', '030', '040', '050', '060', '070', '080', '090', '100', '110', '120', '130', '140', '150', '160', '170', '180', '190', '200', '210', '220', '230', '240', '250', '260', '270', '280', '290', '300', '310', '320', '330']
INDUSTRY = ['H12$H0095', 'H12$H0096', 'H12$H0097', 'H12$H0098', 'H12$H0099', 'H12$H0100', 'H12$H0101', 'H12$H0102', 'H12$H0103']
JOBKIND = ['1', '2']
KEYWORDS = ["餐饮业", "酒店/民宿", "旅游", "家政服务", "养老服务", "美容/美发/保健", "宠物服务"]
MAX_PAGES = 20
PAGE_SIZE = 40
RANDOM_WAIT_RANGE = (1, 2)
MAX_RETRIES = 3
RETRY_BASE_WAIT = 1
API_URL = 'https://api-c.liepin.com/api/com.liepin.searchfront4c.pc-search-job'
DB_FILE = Path("urls.db")
PROGRESS_FILE = Path("crawl_list_progress.json")


class SkipCombinationError(Exception):
    pass


def table_name(keyword):
    return "urls_" + keyword.replace("/", "").replace("·", "")


def init_db(keywords):
    conn = sqlite3.connect(str(DB_FILE))
    for kw in keywords:
        tbl = table_name(kw)
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS "{tbl}" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()
    return conn


def load_progress():
    if not PROGRESS_FILE.exists():
        return {"keyword_index": 0, "dq_index": 0, "industry_index": 0, "jobkind_index": 0, "page": 0}
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_progress(kw_idx, dq_idx, ind_idx, jk_idx, page):
    PROGRESS_FILE.write_text(
        json.dumps({
            "keyword_index": kw_idx,
            "dq_index": dq_idx,
            "industry_index": ind_idx,
            "jobkind_index": jk_idx,
            "page": page,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def log_prefix(keyword, city, industry, job_kind, page):
    return f"kw={keyword} city={city} ind={industry} jk={job_kind} p={page}"


def fetch_page(city, industry, job_kind, page):
    json_data = {
        'data': {
            'mainSearchPcConditionForm': {
                'city': city,
                'dq': city,
                'currentPage': page,
                'pageSize': PAGE_SIZE,
                'key': '',
                'suggestTag': '',
                'workYearCode': '',
                'compId': '',
                'compName': '',
                'compTag': '',
                'industry': industry,
                'salaryCode': '',
                'jobKind': job_kind,
                'compScale': '',
                'compKind': '',
                'compStage': '',
                'eduLevel': '',
                'salaryLow': '',
                'salaryHigh': '',
                'hrActiveTimeCode': '',
            },
            'passThroughForm': js_compile.call("get_passThroughForm"),
        },
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            params = js_compile.call("get_passThroughForm")
            trace_id = js_compile.call("getHeadersId")
            json_data['data']['passThroughForm'] = params

            headers = {
                'X-Client-Type': 'web',
                'X-Fscp-Fe-Version': '',
                'X-Fscp-Std-Info': '{"client_id": "40108"}',
                'X-Fscp-Trace-Id': trace_id,
                'X-Fscp-Version': '1.1',
                'X-Requested-With': 'XMLHttpRequest',
            }
            headers.update(IdentityGenerator.generate_headers())

            response = requests.post(API_URL, headers=headers, json=json_data, timeout=20)

            if response.status_code in (403, 500):
                logger.error("%s 返回%s，跳过当前组合", log_prefix("", city, industry, job_kind, page), response.status_code)
                raise SkipCombinationError

            response.raise_for_status()
            data = response.json()
            job_card_list = data.get('data', {}).get('data', {}).get('jobCardList', [])

            if not job_card_list:
                return [], 0

            urls = [job.get('job', {}).get('link') for job in job_card_list if job.get('job', {}).get('link')]
            return urls, len(urls)

        except SkipCombinationError:
            raise
        except Exception as exc:
            if attempt >= MAX_RETRIES:
                logger.error("%s 请求失败%s次，跳过当前组合：%s", log_prefix("", city, industry, job_kind, page), MAX_RETRIES, exc)
                raise SkipCombinationError

            wait_seconds = RETRY_BASE_WAIT * (2 ** (attempt - 1))
            logger.warning("%s 第%s次请求失败，%s秒后重试：%s", log_prefix("", city, industry, job_kind, page), attempt, wait_seconds, exc)
            time.sleep(wait_seconds)


def export_results(conn, keywords):
    counts = {}
    for kw in keywords:
        tbl = table_name(kw)
        rows = conn.execute(f'SELECT url FROM "{tbl}" ORDER BY id').fetchall()
        counts[kw] = len(rows)
        output = Path(f"urls_{tbl.replace('urls_', '')}.txt")
        output.write_text("\n".join(row[0] for row in rows), encoding="utf-8")
        logger.info("导出 %s：%s 条 -> %s", kw, len(rows), output)
    return counts


def crawl():
    conn = init_db(KEYWORDS)
    progress = load_progress()
    start_kw = progress["keyword_index"]
    start_dq = progress["dq_index"]
    start_ind = progress["industry_index"]
    start_jk = progress["jobkind_index"]
    start_page = progress["page"]

    if start_kw >= len(KEYWORDS):
        logger.info("所有关键词已采集完成")
        conn.close()
        return 0

    logger.info("从断点继续：keyword_index=%s dq_index=%s industry_index=%s jobkind_index=%s page=%s",
                start_kw, start_dq, start_ind, start_jk, start_page)

    total_new = 0
    total_dup = 0

    for kw_idx in range(start_kw, len(KEYWORDS)):
        keyword = KEYWORDS[kw_idx]
        tbl = table_name(keyword)

        for dq_idx in range(start_dq if kw_idx == start_kw else 0, len(DQ)):
            city = DQ[dq_idx]
            for ind_idx in range(start_ind if kw_idx == start_kw and dq_idx == start_dq else 0, len(INDUSTRY)):
                industry = INDUSTRY[ind_idx]
                for jk_idx in range(start_jk if kw_idx == start_kw and dq_idx == start_dq and ind_idx == start_ind else 0, len(JOBKIND)):
                    job_kind = JOBKIND[jk_idx]
                    first_page = start_page if kw_idx == start_kw and dq_idx == start_dq and ind_idx == start_ind and jk_idx == start_jk else 0

                    for page in range(first_page, MAX_PAGES):
                        save_progress(kw_idx, dq_idx, ind_idx, jk_idx, page)

                        wait_seconds = random.uniform(*RANDOM_WAIT_RANGE)
                        logger.info("%s 等待%.2f秒后开始请求", log_prefix(keyword, city, industry, job_kind, page), wait_seconds)
                        time.sleep(wait_seconds)

                        try:
                            urls, count = fetch_page(city, industry, job_kind, page)
                        except SkipCombinationError:
                            break

                        if count == 0:
                            logger.info("%s 空页，跳过", log_prefix(keyword, city, industry, job_kind, page))
                            break

                        new_count = 0
                        dup_count = 0
                        for url in urls:
                            try:
                                conn.execute(f'INSERT INTO "{tbl}"(url) VALUES(?)', (url,))
                                new_count += 1
                            except sqlite3.IntegrityError:
                                dup_count += 1
                        conn.commit()

                        total_new += new_count
                        total_dup += dup_count
                        logger.info("%s 成功，新增%s条，重复%s条", log_prefix(keyword, city, industry, job_kind, page), new_count, dup_count)

                    start_page = 0
                start_jk = 0
            start_ind = 0

    counts = export_results(conn, KEYWORDS)
    conn.close()
    logger.info("完成！新增 %s 条，重复 %s 条，合计 %s 条", total_new, total_dup, sum(counts.values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(crawl())
