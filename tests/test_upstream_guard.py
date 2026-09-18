#!/usr/bin/env python3
import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.upstream_guard import assess,meaningful_lines,looks_like_html,atomic_write
def check(n,c):
 if not c:raise AssertionError(n)
 print("PASS",n)
def main():
 data=b"! header\nexample.com\n||ads.example^\n"
 check("counts meaningful lines",meaningful_lines(data)==2)
 check("healthy snapshot accepted",assess(data,min_bytes=10,min_entries=2)==[])
 check("tiny payload blocked",bool(assess(b"x",min_bytes=10,min_entries=1)))
 check("entry collapse blocked",any("entry-count anomaly" in x for x in assess(data,min_bytes=1,min_entries=1,previous_entries=10,max_shrink_ratio=.5)))
 check("byte collapse blocked",any("byte-size anomaly" in x for x in assess(data,min_bytes=1,min_entries=1,previous_bytes=100,max_shrink_ratio=.5)))
 check("entry growth blocked",any("entry-growth anomaly" in x for x in assess(data*10,min_bytes=1,min_entries=1,previous_entries=2,max_growth_ratio=2)))
 check("html blocked",looks_like_html(b"<!doctype html><html>Error</html>","text/html"))
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)/"snapshot";atomic_write(p,b"good");check("atomic write",p.read_bytes()==b"good")
 print("All upstream guard tests passed")
if __name__=="__main__":main()
