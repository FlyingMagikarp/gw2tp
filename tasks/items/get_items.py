import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
import requests
import logging
import sys
import argparse
from typing import List, Iterable

from utils.rate_limit import TokenBucket
from utils.http import http_get
from utils.db import load_sql, execute_values_batch
from utils.constants import GW2_API_ITEMS_URL
from utils.constants import MAX_IDS_PER_REQUEST
from utils.constants import DEFAULT_BURST
from utils.constants import DEFAULT_REFILL_RATE


ITEMS_UPSERT_SQL = load_sql(Path(__file__).parent / 'sql' /'upsert_items.sql')


def get_all_item_ids(session: requests.Session, limiter: TokenBucket, logger: logging.Logger) -> List[int]:
    logger.info("Fetching full item ID list...")
    resp = http_get(GW2_API_ITEMS_URL, session, params=None, limiter=limiter, logger=logger)
    ids = resp.json()
    if not isinstance(ids, list):
        raise RuntimeError("Unexpected response for /v2/items (expected a list of IDs).")
    logger.info(f"Received {len(ids)} item IDs.")
    return ids


def chunked(iterable: Iterable[int]) -> Iterable[List[int]]:
    batch = []
    for x in iterable:
        batch.append(x)
        if len(batch) >= MAX_IDS_PER_REQUEST:
            yield batch
            batch = []
    if batch:
        yield batch


def fetch_item_details_and_write(ids: List[int], session: requests.Session, limiter: TokenBucket, logger: logging.Logger):
    params = {"ids": ",".join(map(str, ids))}
    response = http_get(GW2_API_ITEMS_URL, session, params=params, limiter=limiter, logger=logger)
    items = response.json()
    if not isinstance(items, list):
        raise RuntimeError(f"Unexpected response for /v2/items (expected a list of IDs). Got Type: {type(items)}")
    write_item_details(items, logger=logger)


def _parse_item_row(item: dict):
    id_ = int(item.get("id"))
    name = item.get("name") or None
    icon = item.get("icon") or None
    description = item.get("description") or None
    type_ = item.get("type") or None
    rarity = item.get("rarity") or None
    level = item.get("level") or None
    vendor_value = item.get("vendor_value") or None

    flags = set(item.get("flags") or [])
    accountbound = 'AccountBound' in flags
    soulbound = 'SoulbindOnAcquire' in flags

    last_update = datetime.now(timezone.utc)
    return (
        id_,
        name,
        icon,
        description,
        type_,
        rarity,
        level,
        vendor_value,
        accountbound,
        soulbound,
        last_update,
    )


def write_item_details(items:List, logger: logging.Logger):
    if not items:
        return

    rows = []
    for it in items:
        try:
            rows.append(_parse_item_row(it))
        except Exception as e:
            logger.warning(f"Skipping item due to parse error: {e} ; payload={str(it)[:200]}")

    if not rows:
        return

    execute_values_batch(ITEMS_UPSERT_SQL, rows, page_size=MAX_IDS_PER_REQUEST, logger=logger)
    logger.debug(f"Upserted {len(rows)} items into 't_item'.")


def main():
    parser = argparse.ArgumentParser(description="Dump GW2 items to CSV with batching, rate-limit handling, and retries.")
    parser.add_argument("--log-file", default=None, help="Optional path to a rotating log file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging to console")
    args = parser.parse_args()

    logger = logging.getLogger("gw2_item_dump")
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
        all_ids = get_all_item_ids(session, limiter, logger)
    except Exception as e:
        logger.exception(f"Failed to fetch item IDs: {e}")
        sys.exit(1)

    logger.info(f"Processing all {len(all_ids)} IDs.")
    start_time = time.time()
    processed = 0
    remaining_ids = all_ids
    try:
        for batch in chunked(remaining_ids):
            fetch_item_details_and_write(batch, session, limiter, logger)
            processed += len(batch)
            if processed % (MAX_IDS_PER_REQUEST * 10) == 0 or processed == len(remaining_ids):
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                logger.info(f"Progress: {processed}/{len(remaining_ids)} ({rate:.1f} ids/sec)")
    except Exception as e:
        logger.exception(f"Error while fetching item details: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()