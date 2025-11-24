import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
import requests
import logging
import sys
import argparse
from typing import List, Iterable

from utils.rate_limit import TokenBucket
from utils.http import http_get
from utils.db import load_sql, execute_values_batch, fetch_column_list
from utils.constants import GW2_API_RECIPE_URL
from utils.constants import MAX_IDS_PER_REQUEST
from utils.constants import DEFAULT_BURST
from utils.constants import DEFAULT_REFILL_RATE


RECIPE_UPSERT_SQL = load_sql(Path(__file__).parent / 'sql' /'upsert_recipes.sql')
INGREDIENTS_UPSERT_SQL = load_sql(Path(__file__).parent / 'sql' /'upsert_ingredients.sql')


def get_all_recipes_ids(session: requests.Session, limiter: TokenBucket, logger: logging.Logger) -> List[int]:
    logger.info("Fetching full recipe ID list...")
    resp = http_get(GW2_API_RECIPE_URL, session, params=None, limiter=limiter, logger=logger)
    ids = resp.json()
    if not isinstance(ids, list):
        raise RuntimeError("Unexpected response for /v2/recipes (expected a list of IDs).")
    logger.info(f"Received {len(ids)} recipe IDs.")
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


def fetch_recipes_details_and_write(ids: List[int], session: requests.Session, limiter: TokenBucket, logger: logging.Logger):
    params = {"ids": ",".join(map(str, ids))}
    response = http_get(GW2_API_RECIPE_URL, session, params=params, limiter=limiter, logger=logger)
    recipes = response.json()
    if not isinstance(recipes, list):
        raise RuntimeError(f"Unexpected response for /v2/recipes (expected a list of IDs). Got Type: {type(recipes)}")
    write_recipes_details(recipes, logger=logger)


def _parse_recipes_row(recipe: dict):
    id_ = int(recipe.get('id'))
    output_item_id = recipe.get('output_item_id') or None
    output_item_count = recipe.get('output_item_count') or None
    disciplines = recipe.get('disciplines') or None
    min_rating = recipe.get('min_rating') or None
    time_to_craft_ms = recipe.get('time_to_craft_ms') or None

    flags = set(recipe.get('flags') or [])
    auto_learned = 'AutoLearned' in flags
    learned_from_item = 'LearnedFromItem' in flags

    return (
        id_,
        output_item_id,
        output_item_count,
        disciplines,
        min_rating,
        auto_learned,
        learned_from_item,
        time_to_craft_ms,
    )


def _parse_ingredients_rows(recipe: dict):
    recipe_id = int(recipe.get("id"))
    ingredients = recipe.get("ingredients") or []
    rows = []

    for ing in ingredients:
        try:
            item_id = ing.get("item_id")
            count = ing.get("count")
            if item_id is None or count is None:
                continue
            rows.append((recipe_id, int(item_id), int(count)))
        except Exception as e:
            continue

    return rows


def write_recipes_details(recipes:List, logger: logging.Logger):
    if not recipes:
        return

    valid_item_ids = load_item_ids()

    recipe_rows = []
    ingredient_rows = []
    for it in recipes:
        try:
            if it.get('output_item_id') not in valid_item_ids:
                logger.warning(f"Skipping recipe {it.get('id')} due to invalid item id: {it['output_item_id']}")
                continue

            recipe_rows.append(_parse_recipes_row(it))
            ingredient_rows.extend(_parse_ingredients_rows(it))
        except Exception as e:
            logger.warning(f"Skipping recipe due to parse error: {e} ; payload={str(it)[:200]}")

    if not recipe_rows:
        return

    execute_values_batch(RECIPE_UPSERT_SQL, recipe_rows, page_size=MAX_IDS_PER_REQUEST, logger=logger)
    logger.debug(f"Upserted {len(recipe_rows)} recipe into 't_recipe'.")

    if ingredient_rows:
        execute_values_batch(INGREDIENTS_UPSERT_SQL, ingredient_rows, page_size=MAX_IDS_PER_REQUEST, logger=logger)
        logger.debug(f"Upserted {len(ingredient_rows)} ingredient rows into 't_ingredient'.")


def load_item_ids():
    return fetch_column_list("SELECT id FROM t_item")


def main():
    parser = argparse.ArgumentParser(description="get recipes, rate-limit handling, and retries.")
    parser.add_argument("--log-file", default=None, help="Optional path to a rotating log file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging to console")
    args = parser.parse_args()

    logger = logging.getLogger("gw2_recipe_dump")
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
        all_ids = get_all_recipes_ids(session, limiter, logger)
    except Exception as e:
        logger.exception(f"Failed to fetch recipe IDs: {e}")
        sys.exit(1)

    logger.info(f"Processing all {len(all_ids)} IDs.")
    start_time = time.time()
    processed = 0
    remaining_ids = all_ids
    try:
        for batch in chunked(remaining_ids):
            fetch_recipes_details_and_write(batch, session, limiter, logger)
            processed += len(batch)
            if processed % (MAX_IDS_PER_REQUEST * 10) == 0 or processed == len(remaining_ids):
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                logger.info(f"Progress: {processed}/{len(remaining_ids)} ({rate:.1f} ids/sec)")
    except Exception as e:
        logger.exception(f"Error while fetching recipe details: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()