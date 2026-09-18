#!/usr/bin/env python3
"""Fail-closed upstream snapshot guard for Hrules source ingestion."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from urllib.request import Request, urlopen

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def meaningful_lines(data: bytes) -> int:
    text=data.decode("utf-8", errors="replace")
    return sum(1 for x in text.splitlines() if x.strip() and not x.lstrip().startswith(("!","#","[")))

def assess(data: bytes, *, min_bytes: int, min_entries: int, previous_bytes: int|None=None,
           previous_entries: int|None=None, max_shrink_ratio: float=0.50) -> list[str]:
    errors=[]
    size=len(data); entries=meaningful_lines(data)
    if size < min_bytes: errors.append(f"payload too small: {size} < {min_bytes} bytes")
    if entries < min_entries: errors.append(f"too few meaningful entries: {entries} < {min_entries}")
    if previous_bytes and size < previous_bytes * (1-max_shrink_ratio):
        errors.append(f"byte-size anomaly: {size} vs previous {previous_bytes}")
    if previous_entries and entries < previous_entries * (1-max_shrink_ratio):
        errors.append(f"entry-count anomaly: {entries} vs previous {previous_entries}")
    return errors

def fetch(url: str, timeout: int) -> tuple[bytes, dict]:
    req=Request(url, headers={"User-Agent":"Hrules-Upstream-Guard/0.1","Accept":"text/plain,*/*"})
    with urlopen(req, timeout=timeout) as r:
        data=r.read()
        return data, {"status":getattr(r,"status",None),"content_type":r.headers.get("Content-Type"),
                      "etag":r.headers.get("ETag"),"last_modified":r.headers.get("Last-Modified")}

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("url"); p.add_argument("--out", required=True); p.add_argument("--meta", required=True)
    p.add_argument("--min-bytes", type=int, default=128); p.add_argument("--min-entries", type=int, default=1)
    p.add_argument("--previous-meta"); p.add_argument("--max-shrink-ratio", type=float, default=.50)
    p.add_argument("--timeout", type=int, default=20)
    a=p.parse_args()
    previous={}
    if a.previous_meta and Path(a.previous_meta).exists():
        previous=json.loads(Path(a.previous_meta).read_text())
    data, http=fetch(a.url,a.timeout)
    errors=assess(data,min_bytes=a.min_bytes,min_entries=a.min_entries,
                  previous_bytes=previous.get("bytes"),previous_entries=previous.get("entries"),
                  max_shrink_ratio=a.max_shrink_ratio)
    meta={"url":a.url,"sha256":sha256_bytes(data),"bytes":len(data),"entries":meaningful_lines(data),**http}
    if errors:
        print("REFUSED upstream anomaly: "+"; ".join(errors))
        return 1
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(data)
    mp=Path(a.meta); mp.parent.mkdir(parents=True,exist_ok=True); mp.write_text(json.dumps(meta,indent=2)+"\n")
    print(f"ACCEPTED {a.url}: entries={meta['entries']} bytes={meta['bytes']} sha256={meta['sha256']}")
    return 0
if __name__=="__main__": raise SystemExit(main())
