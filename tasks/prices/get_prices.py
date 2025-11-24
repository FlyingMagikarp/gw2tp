import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
import requests
import logging
import sys
import argparse
from typing import List, Iterable

from psycopg2._json import Json

from utils.rate_limit import TokenBucket
from utils.http import http_get
from utils.db import load_sql, execute_values_batch, fetch_column_list
from utils.constants import GW2_API_TP_LIST_URL
from utils.constants import MAX_IDS_PER_REQUEST
from utils.constants import DEFAULT_BURST
from utils.constants import DEFAULT_REFILL_RATE


PRICES_INSERT_SQL = load_sql(Path(__file__).parent / 'sql' /'update_prices.sql')


def load_all_item_ids() -> List[int]:
    return fetch_column_list("SELECT id FROM t_item WHERE accountbound = FALSE AND soulbound = FALSE")


def load_quick_item_ids() -> List[int]:
    return fetch_column_list("SELECT id FROM t_item WHERE accountbound = FALSE AND soulbound = FALSE")


def chunked(iterable: Iterable[int]) -> Iterable[List[int]]:
    batch = []
    for x in iterable:
        batch.append(x)
        if len(batch) >= MAX_IDS_PER_REQUEST:
            yield batch
            batch = []
    if batch:
        yield batch


def fetch_prices_details_and_write(ids: List[int], session: requests.Session, limiter: TokenBucket, logger: logging.Logger):
    params = {"ids": ",".join(map(str, ids))}
    response = http_get(GW2_API_TP_LIST_URL, session, params=params, limiter=limiter, logger=logger)
    listings = response.json()
    if not isinstance(listings, list):
        raise RuntimeError(f"Unexpected response for /v2/commerce/listings (expected a list of IDs). Got Type: {type(listings)}")
    write_prices(listings, logger=logger)


def _parse_price_row(item: dict):
    id_ = int(item.get("id"))
    buy_orders = item.get("buys") or None
    sell_listings = item.get("sells") or None

    return (
        id_,
        SNAPSHOT_TIMESTAMP,
        Json(buy_orders),
        Json(sell_listings),
    )


def write_prices(listings:List, logger: logging.Logger):
    if not listings:
        return

    rows = []
    for it in listings:
        try:
            rows.append(_parse_price_row(it))
        except Exception as e:
            logger.warning(f"Skipping listing due to parse error: {e} ; payload={str(it)[:200]}")

    if not rows:
        return

    execute_values_batch(PRICES_INSERT_SQL, rows, page_size=MAX_IDS_PER_REQUEST, logger=logger)
    logger.debug(f"Upserted {len(rows)} items into 't_item'.")


def main():
    parser = argparse.ArgumentParser(description="Get prices for items, rate-limit handling, and retries.")
    parser.add_argument("--log-file", default=None, help="Optional path to a rotating log file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging to console")
    parser.add_argument("-m", "--mode", default='full', action="store_true", help="'full' for full index, 'quick' for only tradable items")
    args = parser.parse_args()

    logger = logging.getLogger("gw2_price_dump")
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    console.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(console)

    if args.log_file:
        Path(args.log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(args.log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(file_handler)

    session = requests.Session()
    limiter = TokenBucket(capacity=DEFAULT_BURST, refill_rate=DEFAULT_REFILL_RATE)

    try:
        if args.mode == "quick":
            all_ids = load_quick_item_ids()
        else:
            all_ids = load_all_item_ids()

    except Exception as e:
        logger.exception(f"Failed to fetch item IDs: {e}")
        sys.exit(1)

    logger.info(f"Processing all {len(all_ids)} IDs.")
    start_time = time.time()
    global SNAPSHOT_TIMESTAMP
    SNAPSHOT_TIMESTAMP = datetime.fromtimestamp(start_time, tz=timezone.utc)
    processed = 0
    remaining_ids = all_ids
    try:
        for batch in chunked(remaining_ids):
            fetch_prices_details_and_write(batch, session, limiter, logger)
            processed += len(batch)
            if processed % (MAX_IDS_PER_REQUEST * 10) == 0 or processed == len(remaining_ids):
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                logger.info(f"Progress: {processed}/{len(remaining_ids)} ({rate:.1f} ids/sec)")
    except Exception as e:
        logger.exception(f"Error while fetching prices: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()