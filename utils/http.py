import time
import logging
from typing import Dict, Optional
import requests

def http_get(
    url: str,
    session: requests.Session,
    params: Optional[Dict] = None,
    limiter=None,
    max_retries: int = 5,
    logger: Optional[logging.Logger] = None,
):
    if limiter:
        limiter.consume(1)

    backoff = 1.0
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(url, params=params, timeout=60)
            if resp.status_code == 200:
                if logger:
                    rem = resp.headers.get("X-Rate-Limit-Remaining")
                    reset = resp.headers.get("X-Rate-Limit-Reset")
                    if rem is not None:
                        logger.debug(f"Rate remaining: {rem}, reset: {reset}")
                return resp
            elif resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", backoff))
                if logger:
                    logger.warning(f"429 Too Many Requests. Sleeping {retry_after:.2f}s (attempt {attempt}/{max_retries}).")
                time.sleep(retry_after)
            elif 500 <= resp.status_code < 600:
                if logger:
                    logger.warning(f"Server error {resp.status_code}. Backing off {backoff:.1f}s (attempt {attempt}/{max_retries}).")
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
            else:
                if logger:
                    logger.error(f"HTTP {resp.status_code} for {url} params={params} body={resp.text[:300]}")
                resp.raise_for_status()
        except (requests.Timeout, requests.ConnectionError) as e:
            if logger:
                logger.warning(f"Network error '{e}'. Backing off {backoff:.1f}s (attempt {attempt}/{max_retries}).")
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)

    raise RuntimeError(f"Failed to GET {url} after {max_retries} attempts")
