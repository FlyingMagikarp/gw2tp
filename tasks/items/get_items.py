from logging.handlers import RotatingFileHandler
from pathlib import Path

import requests
import logging
import sys
import argparse
from typing import List, Iterable

from utils.rate_limit import TokenBucket
from utils.http import http_get
from utils.constants import GW2_API_ITEMS_URL




def get_all_item_ids(session: requests.Session, limiter: TokenBucket, logger: logging.Logger) -> List[int]:
    logger.info("Fetching full item ID list...")
    resp = http_get(GW2_API_ITEMS_URL, session, params=None, limiter=limiter, logger=logger)
    ids = resp.json()
    if not isinstance(ids, list):
        raise RuntimeError("Unexpected response for /v2/items (expected a list of IDs).")
    logger.info(f"Received {len(ids)} item IDs.")
    return ids


def chunked(iterable: Iterable[int], size: int) -> Iterable[List[int]]:
    batch = []
    for x in iterable:
        batch.append(x)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch



def main():
    parser = argparse.ArgumentParser(description="Dump GW2 items to CSV with batching, rate-limit handling, and retries.")
    parser.add_argument("--out", default="items.csv", help="Output CSV path (default: items.csv)")
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


if __name__ == "__main__":
    main()