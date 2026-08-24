#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""JSON renderers.

`cv.json`           — JSON Resume (jsonresume.org) for third-party tooling.
`publications.json` — the feed the lab website consumes, so the site and the
                      CV can never drift apart.
`orcid-diff.json`   — what ORCID is missing relative to cv.yaml.
"""
from __future__ import annotations

import json
import urllib.request

from cvdata import PUB_KINDS, author_string, citation, daterange, stamp


def json_resume(d: dict) -> dict:
    p = d["person"]
    profiles = []
    ids = p.get("ids") or {}
    if p.get("orcid"):
        profiles.append({"network": "ORCID", "username": p["orcid"],
                         "url": "https://orcid.org/%s" % p["orcid"]})
    if ids.get("scholar"):
        profiles.append({"network": "Google Scholar", "username": ids["scholar"],
                         "url": "https://scholar.google.com/citations?user=%s" % ids["scholar"]})
    if ids.get("github"):
        profiles.append({"network": "GitHub", "username": ids["github"],
                         "url": "https://github.com/%s" % ids["github"]})

    emails = p.get("emails") or []
    return {
        "$schema": "https://raw.githubusercontent.com/jsonresume/resume-schema/v1.0.0/schema.json",
        "meta": {"lastModified": stamp(d), "source": "cv.yaml",
                 "canonical": (p.get("links") or {}).get("cv")},
        "basics": {
            "name": p.get("name_en"),
            "label": "%s, %s" % (p.get("title_en", ""), p.get("dept_en", "")),
            "email": emails[0] if emails else None,
            "phone": (p.get("phones") or {}).get("mobile"),
            "url": (p.get("links") or {}).get("lab"),
            "summary": (d.get("meta", {}).get("resume", {}) or {}).get("summary_en"),
            "location": {"countryCode": "KR", "region": p.get("region", "Gyeonggi-do")},
            "profiles": profiles,
        },
        "work": [{
            "name": a.get("org_en"),
            "position": a.get("role_en"),
            "department": a.get("dept_en"),
            "startDate": str(a.get("start", "")),
            "endDate": None if a.get("end") in (None, "present") else str(a.get("end")),
            "highlights": a.get("bullets") or [],
        } for a in d["appointments"]],
        "education": [{
            "institution": e.get("org_en"),
            "area": e.get("dept_en"),
            "studyType": e.get("degree_en"),
            "startDate": str(e.get("start", "")),
            "endDate": None if e.get("end") in (None, "present") else str(e.get("end")),
        } for e in d["education"]],
        "publications": [{
            "name": pub.get("title"),
            "publisher": pub.get("venue"),
            "releaseDate": str(pub.get("year", "")),
            "url": "https://doi.org/%s" % pub["doi"] if pub.get("doi") else pub.get("url"),
            "summary": author_string(pub),
        } for kind in PUB_KINDS for pub in d["publications"][kind]],
        "awards": [{"title": a.get("name_en") or a.get("name_kr"),
                    "date": str(a.get("year", "")),
                    "awarder": a.get("org")} for a in d["awards"]],
        "certificates": [{"name": c.get("name_en") or c.get("name_kr"),
                          "date": str(c.get("date", "")),
                          "issuer": c.get("issuer")} for c in d["certifications"]],
        "skills": [{"name": g.replace("_", " ").title(), "keywords": items}
                   for g, items in (d.get("skills") or {}).items()],
    }


def publications_feed(d: dict) -> dict:
    """Compact, display-ready feed for the lab website."""
    items = []
    for kind in PUB_KINDS:
        for pub in d["publications"][kind]:
            items.append({
                "id": pub.get("id"),
                "kind": kind,
                "year": pub.get("year"),
                "title": pub.get("title"),
                "venue": pub.get("venue"),
                "volume": pub.get("volume"),
                "issue": pub.get("issue"),
                "article": pub.get("article"),
                "doi": pub.get("doi"),
                "url": ("https://doi.org/%s" % pub["doi"]) if pub.get("doi") else pub.get("url"),
                "authors": pub.get("authors"),
                "authors_display": author_string(pub),
                "role_kr": pub.get("role_kr"),
                "note": pub.get("note_kr") or pub.get("note"),
                "featured": bool(pub.get("featured")),
                "citation": citation(pub),
            })
    items.sort(key=lambda x: (int(str(x["year"])[:4] or 0),), reverse=True)
    return {
        "generated": stamp(d),
        "source": "https://github.com/%s/sunwhi-cv" % ((d["person"].get("ids") or {}).get("github", "")),
        "count": len(items),
        "publications": items,
    }


# --------------------------------------------------------------------------
# ORCID reconciliation
# --------------------------------------------------------------------------

ORCID_API = "https://pub.orcid.org/v3.0/%s/record"


def fetch_orcid(orcid: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(ORCID_API % orcid,
                                 headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _orcid_dois(record: dict) -> set[str]:
    dois = set()
    groups = ((record.get("activities-summary") or {}).get("works") or {}).get("group") or []
    for g in groups:
        for s in g.get("work-summary") or []:
            for x in ((s.get("external-ids") or {}).get("external-id") or []):
                if (x.get("external-id-type") or "").lower() == "doi":
                    dois.add((x.get("external-id-value") or "").lower())
    return dois


def orcid_diff(d: dict, record: dict | None = None) -> dict:
    """What cv.yaml knows that the live ORCID record does not."""
    orcid = d["person"].get("orcid")
    record = record or fetch_orcid(orcid)
    have = _orcid_dois(record)

    missing_works = []
    for kind in PUB_KINDS:
        for pub in d["publications"][kind]:
            doi = (pub.get("doi") or "").lower()
            if not doi:
                continue
            if doi not in have:
                missing_works.append({"title": pub.get("title"), "doi": pub.get("doi"),
                                      "year": pub.get("year"), "venue": pub.get("venue")})

    acts = record.get("activities-summary") or {}

    def _summaries(section, key):
        out = []
        for g in (acts.get(section) or {}).get("affiliation-group") or []:
            for s in g.get("summaries") or []:
                out.append(list(s.values())[0])
        return out

    edu = _summaries("educations", "education-summary")
    open_edu = []
    for e in edu:
        if not e.get("end-date"):
            open_edu.append({
                "role": e.get("role-title"),
                "org": (e.get("organization") or {}).get("name"),
                "start": ((e.get("start-date") or {}).get("year") or {}).get("value"),
                "problem": "no end date — shows as ongoing",
            })

    cv_edu_count = len(d["education"])
    return {
        "orcid": orcid,
        "checked": stamp(d),
        "missing_works": missing_works,
        "open_ended_education": open_edu,
        "counts": {
            "orcid_education": len(edu),
            "cv_education": cv_edu_count,
            "orcid_employment": len(_summaries("employments", "employment-summary")),
            "cv_appointments": len(d["appointments"]),
            "orcid_fundings": len((acts.get("fundings") or {}).get("group") or []),
            "cv_grants_awarded": len([g for g in d["grants"] if g.get("status") == "awarded"]),
            "orcid_distinctions": len(_summaries("distinctions", "distinction-summary")),
            "cv_awards": len(d["awards"]),
            "orcid_services": len(_summaries("services", "service-summary")),
            "cv_service": len(d["service"]),
        },
        "researcher_urls": [
            (u.get("url-name"), ((u.get("url") or {}).get("value")))
            for u in (((record.get("person") or {}).get("researcher-urls") or {})
                      .get("researcher-url") or [])
        ],
    }
