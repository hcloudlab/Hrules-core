#!/usr/bin/env python3
from scripts.upstream_guard import assess, meaningful_lines
def check(n,c):
    if not c: raise AssertionError(n)
    print("PASS",n)
def main():
    data=b"! header\nexample.com\n||ads.example^\n"
    check("counts meaningful lines", meaningful_lines(data)==2)
    check("healthy snapshot accepted", assess(data,min_bytes=10,min_entries=2)==[])
    check("tiny payload blocked", bool(assess(b"x",min_bytes=10,min_entries=1)))
    check("entry collapse blocked", any("entry-count anomaly" in x for x in assess(data,min_bytes=1,min_entries=1,previous_entries=10,max_shrink_ratio=.5)))
    check("byte collapse blocked", any("byte-size anomaly" in x for x in assess(data,min_bytes=1,min_entries=1,previous_bytes=100,max_shrink_ratio=.5)))
    print("All upstream guard tests passed")
if __name__=="__main__": main()
