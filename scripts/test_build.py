#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Checks that must hold before anything is published.

    python scripts/test_build.py

No test framework — plain asserts so it runs anywhere, including CI with only
PyYAML installed. Exits non-zero on the first failure.
"""
from __future__ import annotations

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cvdata  # noqa: E402
import render_html  # noqa: E402
import render_json  # noqa: E402
import render_markdown  # noqa: E402

ROOT = cvdata.ROOT
BUILD = os.path.join(ROOT, "build")

PASSED: list[str] = []
FAILED: list[str] = []


def check(name: str):
    def deco(fn):
        try:
            fn()
        except AssertionError as exc:
            FAILED.append("%s\n      %s" % (name, exc))
        except Exception as exc:  # noqa: BLE001
            FAILED.append("%s\n      %s: %s" % (name, type(exc).__name__, exc))
        else:
            PASSED.append(name)
        return fn
    return deco


PUBLIC = cvdata.load(private=False)


@check("cv.yaml passes validation")
def _validates():
    problems = cvdata.validate(PUBLIC)
    assert not problems, "%d problem(s):\n      - %s" % (
        len(problems), "\n      - ".join(problems))


@check("every renderer produces non-trivial output")
def _renders():
    for name, text in [
        ("cv_en", render_markdown.cv_en(PUBLIC)),
        ("cv_kr", render_markdown.cv_kr(PUBLIC)),
        ("resume_en", render_markdown.resume_en(PUBLIC)),
        ("web_cv", render_html.web_cv(PUBLIC)),
    ]:
        assert len(text) > 1000, "%s produced only %d chars" % (name, len(text))
        assert "None" not in text.replace("None-", ""), \
            "%s leaked a literal 'None' — a field is missing" % name


@check("no private value appears anywhere in build/")
def _no_private_leak():
    if not os.path.exists(cvdata.PRIVATE_PATH):
        return  # nothing to leak
    import yaml
    with io.open(cvdata.PRIVATE_PATH, encoding="utf-8") as fh:
        private = yaml.safe_load(fh) or {}

    secrets: list[str] = []

    def collect(node):
        if isinstance(node, dict):
            for v in node.values():
                collect(v)
        elif isinstance(node, list):
            for v in node:
                collect(v)
        elif isinstance(node, str) and len(node.strip()) >= 6:
            secrets.append(node.strip())

    collect(private)
    # The office number is deliberately public; don't flag it.
    public_phones = set((PUBLIC.get("person", {}).get("phones") or {}).values())
    secrets = [s for s in secrets if s not in public_phones]

    if not os.path.isdir(BUILD):
        return
    hits = []
    for root, _dirs, files in os.walk(BUILD):
        for f in files:
            path = os.path.join(root, f)
            try:
                blob = io.open(path, "rb").read()
            except OSError:
                continue
            for s in secrets:
                if s.encode("utf-8") in blob:
                    hits.append("%s contains %r" % (os.path.relpath(path, ROOT), s))
    assert not hits, "private data leaked into the published build:\n      - " + \
        "\n      - ".join(hits)


@check("author markers are internally consistent")
def _authors():
    bad = []
    for pub in cvdata.all_publications(PUBLIC):
        authors = pub.get("authors") or []
        if pub.get("me") and pub["me"] not in authors:
            bad.append("%s: me=%r not in authors" % (pub["id"], pub["me"]))
        for group in ("equal", "corresponding"):
            for n in pub.get(group) or []:
                if n not in authors:
                    bad.append("%s: %s=%r not in authors" % (pub["id"], group, n))
        if len(authors) != len(set(authors)):
            bad.append("%s: duplicate name in author list" % pub["id"])
    assert not bad, "\n      - ".join(bad)


@check("DOIs are well formed and unique")
def _dois():
    seen: dict[str, str] = {}
    bad = []
    for pub in cvdata.all_publications(PUBLIC):
        doi = pub.get("doi")
        if not doi:
            continue
        if not doi.startswith("10."):
            bad.append("%s: %r does not look like a DOI" % (pub["id"], doi))
        key = doi.lower()
        if key in seen:
            bad.append("%s: DOI duplicated with %s" % (pub["id"], seen[key]))
        seen[key] = pub["id"]
    assert not bad, "\n      - ".join(bad)


@check("no grant is presented as funded without status: awarded")
def _grants():
    valid = {"awarded", "applied", "in_review", "not_funded"}
    bad = [g.get("title_kr") or g.get("title_en") or "?"
           for g in PUBLIC.get("grants") or [] if g.get("status") not in valid]
    assert not bad, "invalid status on: %s" % ", ".join(bad)


@check("JSON artifacts are serializable and complete")
def _json():
    resume = render_json.json_resume(PUBLIC)
    feed = render_json.publications_feed(PUBLIC)
    json.dumps(resume, ensure_ascii=False)
    json.dumps(feed, ensure_ascii=False)
    n = len(cvdata.all_publications(PUBLIC))
    assert feed["count"] == n, "feed says %d publications, cv.yaml has %d" % (feed["count"], n)
    assert len(resume["publications"]) == n


@check("web CV escapes HTML and declares both themes")
def _html_safety():
    html = render_html.web_cv(PUBLIC)
    assert html.startswith("<!doctype html>")
    assert 'name="viewport"' in html
    assert "prefers-color-scheme:dark" in html
    assert '[data-theme="dark"]' in html
    assert "@media print" in html
    # A stray unescaped angle bracket from data would break the document.
    body = html.split("<body>", 1)[1]
    assert body.count("<") == body.count(">"), "unbalanced angle brackets in body"


@check("private overlay actually supplies the 이력서 fields")
def _private_overlay():
    if not os.path.exists(cvdata.PRIVATE_PATH):
        return
    full = cvdata.load()
    assert cvdata.has_private(full)
    person = full["person"]
    assert person.get("birth"), "private.yaml did not supply person.birth"
    assert person.get("address_kr"), "private.yaml did not supply person.address_kr"
    assert (person.get("phones") or {}).get("mobile"), "private.yaml did not supply mobile"
    kr = render_markdown.cv_kr(full)
    assert person["address_kr"] in kr, "address missing from the private 이력서"


def main() -> int:
    for name in PASSED:
        print("  ok    %s" % name)
    for f in FAILED:
        print("  FAIL  %s" % f)
    print("\n%d passed, %d failed" % (len(PASSED), len(FAILED)))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
