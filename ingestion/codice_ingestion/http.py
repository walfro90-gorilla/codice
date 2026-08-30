"""Shared HTTP fetching for scrapers.

Two things every Códice scraper needs and neither should reimplement:

1. **A complete TLS chain.** Several .gob.mx hosts serve a valid certificate
   but omit the intermediate, so verification fails against the system store.
   We append the known intermediates instead of disabling verification —
   a scraper that skips TLS checks is a scraper whose snapshots can't be trusted.
2. **Politeness.** One request at a time, a real delay between them, and an
   identifying User-Agent. These are public servers paid for with public money;
   we do not hammer them.
"""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

# Identifiable crawler UA, same shape Googlebot uses: it names the bot and gives
# a contact URL, while keeping the "Mozilla/5.0 (compatible; ...)" prefix that
# these sites' WAFs require — several .gob.mx hosts answer 403 without it.
USER_AGENT = (
    "Mozilla/5.0 (compatible; CodiceBot/0.1; "
    "+https://github.com/walfro90-gorilla/codice)"
)
MIN_INTERVAL = 1.5  # seconds between requests to the same host

# Intermediates that these hosts fail to send. Fetched once and committed so
# the pipeline is reproducible without a network round trip to the CA.
CERT_DIR = Path(__file__).resolve().parent / "certs"

_last_request: dict[str, float] = {}
_lock = threading.Lock()


def _throttle(host: str) -> None:
    with _lock:
        last = _last_request.get(host, 0.0)
        wait = MIN_INTERVAL - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)
        _last_request[host] = time.monotonic()


# Transport: curl, not urllib.
#
# Several .gob.mx hosts sit behind a WAF that answers urllib with 403 or an
# endless redirect even with cookies and browser-shaped headers, while the same
# request through curl succeeds — the difference is TLS/HTTP2 fingerprinting,
# not anything about the request we control. curl also gets redirects, cookies
# and modern TLS right for free, so it is both the working and the smaller
# option. Verification stays ON: we pass an explicit CA bundle, never -k.
_CURL_CA = CERT_DIR / "_bundle.pem"
_COOKIE_JAR = Path(tempfile.gettempdir()) / "codice-scraper-cookies.txt"


def _ca_bundle() -> Path:
    """System roots plus the intermediates these hosts fail to send."""
    if not _CURL_CA.exists() or _CURL_CA.stat().st_mtime < max(
        (p.stat().st_mtime for p in CERT_DIR.glob("*.pem") if p != _CURL_CA), default=0
    ):
        parts = []
        for sys_ca in ("/etc/ssl/certs/ca-certificates.crt", "/etc/pki/tls/certs/ca-bundle.crt"):
            if Path(sys_ca).exists():
                parts.append(Path(sys_ca).read_text())
                break
        for pem in sorted(CERT_DIR.glob("*.pem")):
            if pem != _CURL_CA:
                parts.append(pem.read_text())
        _CURL_CA.write_text("\n".join(parts))
    return _CURL_CA


def fetch_raw(url: str, timeout: int = 60) -> bytes:
    """Download bytes. No parsing, no decoding, no cleverness (R8)."""
    from urllib.parse import urlparse

    _throttle(urlparse(url).netloc)
    proc = subprocess.run(
        [
            "curl", "--silent", "--show-error", "--location",
            "--max-time", str(timeout),
            "--cacert", str(_ca_bundle()),
            "--user-agent", USER_AGENT,
            "--header", "Accept-Language: es-MX,es;q=0.9",
            # Some hosts hand out a session cookie and redirect back to the same
            # URL; without keeping the jar across requests that is a redirect
            # loop. Ordinary session handling, and it also spares the server
            # from re-issuing a session per page.
            "--cookie-jar", str(_COOKIE_JAR),
            "--cookie", str(_COOKIE_JAR),
            "--fail",
            url,
        ],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"fetch failed ({proc.returncode}) for {url}: {proc.stderr.decode()[:200]}")
    return proc.stdout


def store_snapshot(raw: bytes, dest: Path, url: str, source_key: str, content_type: str) -> dict:
    """Persist raw bytes untouched and return the metadata that proves it (R1)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    now = datetime.now(timezone.utc)
    return {
        "source_key": source_key,
        "url": url,
        "captured_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "content_type": content_type,
        "r2_key": f"{source_key}/{now:%Y-%m-%d}/{dest.name}",
        "local_path": str(dest),
    }
