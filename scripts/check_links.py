#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verify every URL in cv.yaml still resolves.

    python scripts/check_links.py            # report, exit non-zero on failures
    python scripts/check_links.py --quiet     # only print failures

A dead link on a CV is worse than no link, and links rot silently: a Vercel
project gets deleted, a DOI is withdrawn, a repository is renamed. Nothing
else in this repo would notice, so this does.

Network-dependent, so it is deliberately NOT part of test_build.py. CI runs it
on the monthly schedule, where a transient failure costs nothing.
"""
from __future__ import annotations

import argparse
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cvdata  # noqa: E402

TIMEOUT = 25
UA = "sunwhi-cv-link-check (+https://github.com/gdrpaul3-byte/sunwhi-cv)"


def collect(d: dict) -> list[tuple[str, str]]:
    """Every (where, url) pair worth checking."""
    out: list[tuple[str, str]] = []

    for key, url in (d["person"].get("links") or {}).items():
        out.append(("person.links.%s" % key, url))
    if d["person"].get("orcid"):
        out.append(("person.orcid", "https://orcid.org/%s" % d["person"]["orcid"]))
    scholar = (d["person"].get("ids") or {}).get("scholar")
    if scholar:
        out.append(("person.ids.scholar",
                    "https://scholar.google.com/citations?user=%s" % scholar))

    for pub in cvdata.all_publications(d):
        if pub.get("doi"):
            out.append(("publication %s" % pub["id"], "https://doi.org/%s" % pub["doi"]))
        elif pub.get("url"):
            out.append(("publication %s" % pub["id"], pub["url"]))

    for s in d.get("software") or []:
        name = s.get("name_en") or s.get("name_kr")
        if s.get("url"):
            out.append(("software %s" % name, s["url"]))
        # `repo` is intentionally skipped: those are private and always 404
        # for an anonymous client.

    for o in d.get("outreach") or []:
        if o.get("url"):
            out.append(("outreach %s" % (o.get("name_en") or o.get("name_kr")), o["url"]))

    return out


def probe(url: str) -> tuple[bool, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            code = resp.getcode()
            return (200 <= code < 400), "HTTP %s" % code
    except urllib.error.HTTPError as exc:
        # 403 usually means a bot wall (Google Scholar does this), not a dead link.
        if exc.code in (403, 429):
            return True, "HTTP %s (bot wall — treated as live)" % exc.code
        return False, "HTTP %s" % exc.code
    except Exception as exc:  # noqa: BLE001
        return False, "%s: %s" % (type(exc).__name__, exc)


def main() -> int:
    ap = argparse.ArgumentParser(description="Check that cv.yaml URLs resolve")
    ap.add_argument("--quiet", action="store_true", help="print only failures")
    args = ap.parse_args()

    d = cvdata.load(private=False)
    targets = collect(d)
    failures = []
    for where, url in targets:
        ok, detail = probe(url)
        if ok:
            if not args.quiet:
                print("  ok    %-34s %s" % (detail, url))
        else:
            failures.append((where, url, detail))
            print("  DEAD  %-34s %s\n        in %s" % (detail, url, where))

    print("\n%d checked, %d dead" % (len(targets), len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
