#!/usr/bin/env python3
"""Fail-closed upstream snapshot guard for Hrules source ingestion."""
from __future__ import annotations
import argparse, hashlib, json, os, tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

def sha256_bytes(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def meaningful_lines(data: bytes) -> int:
    text=data.decode("utf-8",errors="replace")
    return sum(1 for x in text.splitlines() if x.strip() and not x.lstrip().startswith(("!","#","[")))
def looks_like_html(data:bytes,content_type:str|None=None)->bool:
    head=data[:2048].decode("utf-8",errors="ignore").lower()
    c=(content_type or "").lower()
    return "text/html" in c or "<!doctype html" in head or "<html" in head
def assess(data:bytes,*,min_bytes:int,min_entries:int,previous_bytes:int|None=None,previous_entries:int|None=None,max_shrink_ratio:float=.50,max_growth_ratio:float=5.0,content_type:str|None=None)->list[str]:
    e=[]; size=len(data); entries=meaningful_lines(data)
    if looks_like_html(data,content_type): e.append("payload looks like HTML/error page")
    if size<min_bytes:e.append(f"payload too small: {size} < {min_bytes} bytes")
    if entries<min_entries:e.append(f"too few meaningful entries: {entries} < {min_entries}")
    if previous_bytes:
        if size<previous_bytes*(1-max_shrink_ratio):e.append(f"byte-size anomaly: {size} vs previous {previous_bytes}")
        if size>previous_bytes*(1+max_growth_ratio):e.append(f"byte-growth anomaly: {size} vs previous {previous_bytes}")
    if previous_entries:
        if entries<previous_entries*(1-max_shrink_ratio):e.append(f"entry-count anomaly: {entries} vs previous {previous_entries}")
        if entries>previous_entries*(1+max_growth_ratio):e.append(f"entry-growth anomaly: {entries} vs previous {previous_entries}")
    return e
def fetch(url:str,timeout:int):
    req=Request(url,headers={"User-Agent":"Hrules-Upstream-Guard/0.2","Accept":"text/plain,*/*"})
    with urlopen(req,timeout=timeout) as r:
        return r.read(),{"status":getattr(r,"status",None),"content_type":r.headers.get("Content-Type"),"etag":r.headers.get("ETag"),"last_modified":r.headers.get("Last-Modified")}
def atomic_write(path:Path,data:bytes):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",dir=path.parent)
    try:
        with os.fdopen(fd,"wb") as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def main()->int:
    p=argparse.ArgumentParser();p.add_argument("url");p.add_argument("--out",required=True);p.add_argument("--meta",required=True)
    p.add_argument("--min-bytes",type=int,default=128);p.add_argument("--min-entries",type=int,default=1);p.add_argument("--previous-meta")
    p.add_argument("--max-shrink-ratio",type=float,default=.50);p.add_argument("--max-growth-ratio",type=float,default=5.0);p.add_argument("--timeout",type=int,default=20)
    a=p.parse_args();previous={}
    if a.previous_meta and Path(a.previous_meta).exists():previous=json.loads(Path(a.previous_meta).read_text())
    data,http=fetch(a.url,a.timeout)
    errors=assess(data,min_bytes=a.min_bytes,min_entries=a.min_entries,previous_bytes=previous.get("bytes"),previous_entries=previous.get("entries"),max_shrink_ratio=a.max_shrink_ratio,max_growth_ratio=a.max_growth_ratio,content_type=http.get("content_type"))
    meta={"url":a.url,"fetched_at":datetime.now(timezone.utc).isoformat(),"sha256":sha256_bytes(data),"bytes":len(data),"entries":meaningful_lines(data),**http}
    if errors: print("REFUSED upstream anomaly: "+"; ".join(errors));return 1
    atomic_write(Path(a.out),data);atomic_write(Path(a.meta),(json.dumps(meta,indent=2)+"\n").encode())
    print(f"ACCEPTED {a.url}: entries={meta['entries']} bytes={meta['bytes']} sha256={meta['sha256']}");return 0
if __name__=="__main__":raise SystemExit(main())
