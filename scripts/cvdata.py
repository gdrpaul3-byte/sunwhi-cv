#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Load, validate, and normalize cv.yaml — the single source of truth.

Every renderer imports from here so that formatting rules (author markers,
date ranges, citation strings) are defined exactly once.
"""
from __future__ import annotations

import datetime as _dt
import io
import os
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.stderr.write("PyYAML is required:  pip install -r requirements.txt\n")
    raise

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CV_PATH = os.path.join(ROOT, "cv.yaml")
PRIVATE_PATH = os.path.join(ROOT, "private.yaml")

# Publication buckets, in the order a CV presents them.
PUB_KINDS = ["journal", "preprint", "conference"]


class CVError(Exception):
    pass


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------

def _deep_merge(base: dict, overlay: dict) -> dict:
    """Recursively merge `overlay` into `base`, returning `base`."""
    for k, v in (overlay or {}).items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
    return base


def load(path: str | None = None, private: bool | str | None = None) -> dict:
    """Load cv.yaml, optionally overlaid with private.yaml.

    cv.yaml holds only information that is safe to publish. Home address, date
    of birth, personal mobile number and military-service details live in
    private.yaml, which is git-ignored. Korean 이력서 forms require those fields,
    so the local build merges them in when the file is present; the public
    repository and GitHub Pages never see them.

    private=False forces a public-only build even if private.yaml exists.
    """
    path = path or CV_PATH
    with io.open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise CVError("cv.yaml must contain a top-level mapping")

    if private is not False:
        ppath = private if isinstance(private, str) else PRIVATE_PATH
        if os.path.exists(ppath):
            with io.open(ppath, encoding="utf-8") as fh:
                overlay = yaml.safe_load(fh) or {}
            if not isinstance(overlay, dict):
                raise CVError("%s must contain a top-level mapping" % ppath)
            _deep_merge(data, overlay)
            data.setdefault("meta", {})["_private_overlay"] = True

    _normalize(data)
    return data


def has_private(d: dict) -> bool:
    return bool(d.get("meta", {}).get("_private_overlay"))


def _normalize(d: dict) -> None:
    d.setdefault("meta", {})
    d.setdefault("person", {})
    for key in ("appointments", "education", "grants", "teaching", "invited_talks",
                "posters", "software", "service", "peer_review", "mentoring",
                "awards", "certifications", "media", "outreach", "references"):
        d.setdefault(key, [])
    pubs = d.setdefault("publications", {})
    for kind in PUB_KINDS:
        pubs.setdefault(kind, [])
    d.setdefault("skills", {})

    me = d["person"].get("citation_name")
    for kind in PUB_KINDS:
        for i, p in enumerate(pubs[kind]):
            p.setdefault("kind", kind)
            p.setdefault("authors", [])
            p.setdefault("equal", [])
            p.setdefault("corresponding", [])
            p.setdefault("id", "%s-%02d" % (kind, i + 1))
            if "me" not in p:
                p["me"] = me

    # Sort each bucket newest-first, stable on the order the file already has.
    for kind in PUB_KINDS:
        pubs[kind].sort(key=lambda p: (_year_key(p.get("year")),), reverse=True)


def _year_key(y) -> int:
    try:
        return int(str(y)[:4])
    except (TypeError, ValueError):
        return 0


# --------------------------------------------------------------------------
# validation
# --------------------------------------------------------------------------

def validate(d: dict) -> list[str]:
    """Return a list of human-readable problems. Empty list == clean."""
    problems: list[str] = []
    p = d.get("person", {})

    for field in ("name_en", "name_kr", "citation_name", "orcid"):
        if not p.get(field):
            problems.append("person.%s is missing" % field)

    orcid = str(p.get("orcid", ""))
    if orcid and not re.fullmatch(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", orcid):
        problems.append("person.orcid %r is not a valid ORCID iD" % orcid)

    seen_ids: set[str] = set()
    for kind in PUB_KINDS:
        for pub in d["publications"][kind]:
            pid = pub.get("id")
            where = "publications.%s[%s]" % (kind, pid)
            if pid in seen_ids:
                problems.append("%s: duplicate id" % where)
            seen_ids.add(pid)

            if not pub.get("title"):
                problems.append("%s: no title" % where)
            if not pub.get("year"):
                problems.append("%s: no year" % where)
            authors = pub.get("authors") or []
            if not authors:
                problems.append("%s: no authors" % where)

            me = pub.get("me")
            if me and authors and me not in authors:
                problems.append("%s: own name %r not found in author list %s"
                                % (where, me, authors))
            for group in ("equal", "corresponding"):
                for name in pub.get(group) or []:
                    if name not in authors:
                        problems.append("%s: %s author %r not in author list"
                                        % (where, group, name))
            if kind == "journal" and not pub.get("doi"):
                problems.append("%s: journal article without a DOI" % where)

    for i, t in enumerate(d.get("teaching") or []):
        if not t.get("term"):
            problems.append("teaching[%d]: no term (e.g. '2026-1')" % i)
        if not (t.get("name_kr") or t.get("name_en")):
            problems.append("teaching[%d]: no course name" % i)

    for i, g in enumerate(d.get("grants") or []):
        if g.get("status") not in ("awarded", "applied", "not_funded", "in_review"):
            problems.append(
                "grants[%d] (%s): status must be one of "
                "awarded/applied/in_review/not_funded — a CV must never present "
                "an unfunded application as funded"
                % (i, g.get("title_kr") or g.get("title_en") or "?"))

    for i, a in enumerate(d.get("appointments") or []):
        if not a.get("start"):
            problems.append("appointments[%d]: no start date" % i)

    return problems


# --------------------------------------------------------------------------
# formatting helpers shared by all renderers
# --------------------------------------------------------------------------

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _datepart(v, lang: str) -> str:
    """'2019' -> '2019'; '2019-04' -> 'Apr 2019' (en) / '2019.04' (kr)."""
    s = str(v)
    m = re.fullmatch(r"(\d{4})-(\d{2})", s)
    if not m:
        return s
    year, month = m.group(1), int(m.group(2))
    if lang == "kr":
        return "%s.%02d" % (year, month)
    if 1 <= month <= 12:
        return "%s %s" % (_MONTHS[month - 1], year)
    return year


def daterange(start, end, present_en: str = "present", lang: str = "en") -> str:
    """'2019' + '2024' -> '2019–2024'; open ranges -> '2025–present'.

    Month precision is accepted and rendered idiomatically per language:
    '2019-04' becomes 'Apr 2019' in English and '2019.04' in Korean.
    """
    present = present_en if lang == "en" else "현재"
    s = "" if start is None else _datepart(start, lang)
    if end in (None, "", "present", "현재"):
        e = present
    else:
        e = _datepart(end, lang)
    if not s:
        return e
    if s == e:
        return s
    return "%s–%s" % (s, e)


def author_string(pub: dict, bold_self: str | None = None,
                  markers: bool = True) -> str:
    """Render the author list with * (equal) and dagger (corresponding) markers.

    bold_self: a wrapper format string such as '**%s**' (Markdown) or
    '<strong>%s</strong>' (HTML). None leaves the name unstyled.
    """
    equal = set(pub.get("equal") or [])
    corr = set(pub.get("corresponding") or [])
    me = pub.get("me")
    out = []
    for name in pub.get("authors") or []:
        text = name
        if markers:
            if name in equal:
                text += "*"
            if name in corr:
                text += "†"
        if bold_self and me and name == me:
            text = bold_self % text
        out.append(text)
    return ", ".join(out)


def citation(pub: dict, bold_self: str | None = None, link: bool = False) -> str:
    """One-line reference string, journal style."""
    bits = [author_string(pub, bold_self=bold_self)]
    year = pub.get("year")
    if year:
        bits.append("(%s)" % year)
    title = (pub.get("title") or "").rstrip(".")
    bits.append(title + ".")

    venue = pub.get("venue")
    if venue:
        tail = venue
        vol = pub.get("volume")
        issue = pub.get("issue")
        if vol:
            tail += " %s" % vol
            if issue:
                tail += "(%s)" % issue
        art = pub.get("article") or pub.get("pages")
        if art:
            tail += ", %s" % art
        bits.append(tail + ".")

    doi = pub.get("doi")
    if doi:
        if link:
            bits.append("[doi:%s](https://doi.org/%s)" % (doi, doi))
        else:
            bits.append("doi:%s" % doi)

    note = pub.get("note")
    if note:
        bits.append("(%s)" % note)
    return " ".join(b for b in bits if b)


def all_publications(d: dict) -> list[dict]:
    out = []
    for kind in PUB_KINDS:
        out.extend(d["publications"][kind])
    return out


def today() -> str:
    return _dt.date.today().isoformat()


def stamp(d: dict) -> str:
    """The 'last updated' string, preferring an explicit meta.updated."""
    return str(d.get("meta", {}).get("updated") or today())
