#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Markdown renderers: full English CV, Korean 이력서, and a one-page résumé."""
from __future__ import annotations

from cvdata import (PUB_KINDS, author_string, citation, daterange, funded_grants,
                    grants, pending_grants, stamp)

BOLD = "**%s**"


# --------------------------------------------------------------------------
# shared building blocks
# --------------------------------------------------------------------------

def _h(level: int, text: str) -> str:
    return "\n%s %s\n" % ("#" * level, text)


def _contact_line(p: dict) -> str:
    bits = []
    if p.get("emails"):
        bits.append(" · ".join(p["emails"]))
    ph = p.get("phones") or {}
    for label, num in ph.items():
        bits.append("%s %s" % (label, num))
    return "  \n".join(bits)


LINK_LABELS = {"lab": "Lab website", "cv": "Web CV", "cv_repo": "CV source",
               "youtube": "YouTube", "github": "GitHub"}


def link_label(key: str) -> str:
    return LINK_LABELS.get(key, key.replace("_", " ").title())


def _idlinks_md(p: dict) -> str:
    links = []
    if p.get("orcid"):
        links.append("[ORCID %s](https://orcid.org/%s)" % (p["orcid"], p["orcid"]))
    ids = p.get("ids") or {}
    if ids.get("scholar"):
        links.append("[Google Scholar](https://scholar.google.com/citations?user=%s)"
                     % ids["scholar"])
    for key, url in (p.get("links") or {}).items():
        links.append("[%s](%s)" % (link_label(key), url))
    return " · ".join(links)


def _pub_section(d: dict, kind: str, heading: str, numbered: bool = True) -> str:
    pubs = d["publications"][kind]
    if not pubs:
        return ""
    out = [_h(2, heading)]
    for i, pub in enumerate(pubs, 1):
        line = citation(pub, bold_self=BOLD, link=True)
        out.append("%s%s" % ("%d. " % i if numbered else "- ", line))
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------
# English academic CV
# --------------------------------------------------------------------------

def cv_en(d: dict) -> str:
    p = d["person"]
    L: list[str] = []

    L.append("# %s, %s" % (p.get("name_en"), p.get("degree", "Ph.D.")))
    alts = p.get("name_en_alt") or []
    if alts:
        L.append("\n*Also published as %s*" % ", ".join(alts))
    L.append("\n%s, %s  \n%s" % (p.get("title_en"), p.get("dept_en"),
                                 p.get("institution_en")))
    L.append("\n" + _contact_line(p))
    L.append("\n" + _idlinks_md(p))
    L.append("\n*Last updated: %s*\n" % stamp(d))
    L.append("\n---")

    if d["appointments"]:
        L.append(_h(2, "Professional Appointments"))
        for a in d["appointments"]:
            L.append("**%s** — %s  " % (daterange(a.get("start"), a.get("end")),
                                        a.get("role_en", "")))
            org = a.get("org_en", "")
            if a.get("dept_en"):
                org = "%s, %s" % (a["dept_en"], org)
            L.append("%s%s" % (org, ", " + a["country"] if a.get("country") else ""))
            if a.get("advisor"):
                L.append("  \n*Advisor: %s*" % a["advisor"])
            for b in a.get("bullets") or []:
                L.append("- %s" % b)
            L.append("")

    if d["education"]:
        L.append(_h(2, "Education"))
        for e in d["education"]:
            L.append("**%s** — %s  " % (daterange(e.get("start"), e.get("end")),
                                        e.get("degree_en", "")))
            L.append("%s, %s" % (e.get("dept_en", ""), e.get("org_en", "")))
            if e.get("advisor"):
                L.append("  \n*Advisor: %s*" % e["advisor"])
            if e.get("thesis"):
                L.append("  \n*Dissertation: %s*" % e["thesis"])
            L.append("")

    note = d.get("meta", {}).get("author_note_en")
    if note:
        L.append(_h(2, "Publications"))
        L.append("*%s*" % note)
        L.append(_pub_section(d, "journal", "Peer-Reviewed Journal Articles").lstrip("\n"))
    else:
        L.append(_pub_section(d, "journal", "Peer-Reviewed Journal Articles"))
    L.append(_pub_section(d, "preprint", "Preprints & Manuscripts"))
    L.append(_pub_section(d, "conference", "Conference Proceedings"))

    if d.get("metrics"):
        m = d["metrics"]
        L.append(_h(2, "Citation Metrics"))
        L.append("Citations %s · h-index %s · i10-index %s  \n*(Google Scholar, %s)*"
                 % (m.get("citations"), m.get("h_index"), m.get("i10_index"),
                    m.get("as_of", stamp(d))))

    funded = funded_grants(d)
    other = pending_grants(d)
    if funded or other:
        L.append(_h(2, "Research Funding"))
        for g in funded:
            L.append("**%s** — %s  " % (g.get("period", ""),
                                        g.get("title_en") or g.get("title_kr")))
            L.append("%s%s%s" % (g.get("funder_en") or g.get("funder_kr") or "",
                                 " · Role: %s" % g["role"] if g.get("role") else "",
                                 " · %s" % g["amount"] if g.get("amount") else ""))
            L.append("")
        if other:
            L.append("*Submitted / under review*\n")
            for g in other:
                L.append("- %s — %s (%s)" % (g.get("period", ""),
                                             g.get("title_en") or g.get("title_kr"),
                                             g.get("status")))
            L.append("")

    if d["teaching"]:
        L.append(_h(2, "Teaching"))
        L.append("| Term | Course | Code | Credits | Institution |")
        L.append("|---|---|---|---|---|")
        for t in d["teaching"]:
            name = t.get("name_en") or t.get("name_kr")
            if t.get("name_en") and t.get("name_kr"):
                name = "%s (%s)" % (t["name_en"], t["name_kr"])
            L.append("| %s | %s | %s | %s | %s |" % (
                t.get("term", ""), name, t.get("code", ""),
                t.get("credits", ""), t.get("institution_en") or t.get("institution_kr") or ""))
        L.append("")

    if d["invited_talks"]:
        L.append(_h(2, "Invited Talks & Guest Lectures"))
        for t in d["invited_talks"]:
            L.append("- **%s** “%s.” %s%s" % (
                t.get("year", ""), (t.get("title") or "").rstrip("."),
                t.get("venue", ""),
                ", " + t["location"] if t.get("location") else ""))
        L.append("")

    if d["posters"]:
        L.append(_h(2, "Conference Presentations"))
        for t in d["posters"]:
            authors = ", ".join(t.get("authors") or [])
            L.append("- %s. “%s.” *%s*, %s%s." % (
                authors, (t.get("title") or "").rstrip("."), t.get("venue", ""),
                t.get("year", ""), ", " + t["location"] if t.get("location") else ""))
        L.append("")

    if d["software"]:
        L.append(_h(2, "Software & Registered Programs"))
        reg = [s for s in d["software"] if s.get("registration")]
        opensrc = [s for s in d["software"] if not s.get("registration")]
        if reg:
            L.append("*Copyright-registered software (Korea Copyright Commission)*\n")
            for s in reg:
                L.append("- **%s** — %s (%s). %s" % (
                    s.get("name_en") or s.get("name_kr"), s["registration"],
                    s.get("year", ""), s.get("description_en") or s.get("description_kr") or ""))
            L.append("")
        if opensrc:
            L.append("*Open-source research & teaching tools*\n")
            for s in opensrc:
                url = " — %s" % s["url"] if s.get("url") else ""
                L.append("- **%s** (%s). %s%s" % (
                    s.get("name_en") or s.get("name_kr"), s.get("year", ""),
                    s.get("description_en") or s.get("description_kr") or "", url))
            L.append("")

    if d["consulting"]:
        L.append(_h(2, "AI Agent Onboarding & Consulting"))
        for c in d["consulting"]:
            when = c.get("period") or c.get("year", "")
            org = c.get("org_en") or c.get("org_kr", "")
            if c.get("org_en") and c.get("org_kr") and c["org_en"] != c["org_kr"]:
                org = "%s (%s)" % (c["org_en"], c["org_kr"])
            L.append("**%s** — %s  " % (when, org))
            detail = " · ".join(filter(None, [c.get("kind_en"), c.get("topic_en")]))
            if detail:
                L.append(detail)
            if c.get("note"):
                L.append("  \n*%s*" % c["note"])
            L.append("")

    if d["mentoring"]:
        L.append(_h(2, "Mentoring & Advising"))
        for m in d["mentoring"]:
            L.append("- **%s** — %s%s" % (m.get("period", ""), m.get("name", ""),
                                          ", " + m["role"] if m.get("role") else ""))
        L.append("")

    if d["service"]:
        L.append(_h(2, "Institutional & Professional Service"))
        for s in d["service"]:
            L.append("- **%s** — %s%s" % (s.get("period") or s.get("year", ""),
                                          s.get("role_en") or s.get("role_kr"),
                                          ", " + s["org"] if s.get("org") else ""))
        L.append("")

    if d["peer_review"]:
        L.append(_h(2, "Peer Review"))
        for r in d["peer_review"]:
            L.append("- %s (%s)%s" % (r.get("journal", ""), r.get("years", ""),
                                      " — %s" % r["note"] if r.get("note") else ""))
        L.append("")

    if d["awards"]:
        L.append(_h(2, "Awards & Honors"))
        for a in d["awards"]:
            L.append("- **%s** — %s%s" % (a.get("year", ""),
                                          a.get("name_en") or a.get("name_kr"),
                                          ", " + a["org"] if a.get("org") else ""))
        L.append("")

    if d["certifications"]:
        L.append(_h(2, "Certifications & Training"))
        for c in d["certifications"]:
            L.append("- **%s** — %s%s" % (c.get("date", ""),
                                          c.get("name_en") or c.get("name_kr"),
                                          ", " + c["issuer"] if c.get("issuer") else ""))
        L.append("")

    if d["media"]:
        L.append(_h(2, "Media Coverage"))
        for m in d["media"]:
            L.append("- **%s** — %s, *%s*" % (m.get("year", ""), m.get("title", ""),
                                              m.get("outlet", "")))
        L.append("")

    if d["outreach"]:
        L.append(_h(2, "Outreach"))
        for o in d["outreach"]:
            name = o.get("name_en") or o.get("name_kr")
            if o.get("url"):
                name = "[%s](%s)" % (name, o["url"])
            L.append("- **%s** — %s. %s" % (o.get("period") or o.get("year", ""),
                                            name,
                                            o.get("description_en") or o.get("description_kr") or ""))
        L.append("")

    if d["skills"]:
        L.append(_h(2, "Technical Skills"))
        for group, items in d["skills"].items():
            L.append("- **%s:** %s" % (group.replace("_", " ").title(),
                                       ", ".join(items)))
        L.append("")

    if d["references"]:
        L.append(_h(2, "References"))
        for r in d["references"]:
            L.append("- **%s** — %s, %s (%s)" % (r.get("name", ""), r.get("title", ""),
                                                 r.get("org", ""), r.get("email", "")))
        L.append("")

    return "\n".join(L).replace("\n\n\n", "\n\n").strip() + "\n"


# --------------------------------------------------------------------------
# Korean 이력서
# --------------------------------------------------------------------------

def cv_kr(d: dict) -> str:
    p = d["person"]
    L: list[str] = []
    L.append("# 이 력 서")
    L.append("\n*최종 수정: %s*\n" % stamp(d))

    L.append("\n## 1. 인적사항\n")
    L.append("| 항목 | 내용 |")
    L.append("|---|---|")
    rows = [
        ("성명(한글)", p.get("name_kr", "")),
        ("성명(영문)", "%s (%s)" % (p.get("name_en", ""),
                                 ", ".join(p.get("name_en_alt") or []))
         if p.get("name_en_alt") else p.get("name_en", "")),
        ("생년월일", p.get("birth", "")),
        ("이메일", ", ".join(p.get("emails") or [])),
        ("핸드폰", (p.get("phones") or {}).get("mobile", "")),
        ("ORCID", p.get("orcid", "")),
        ("주소", p.get("address_kr", "")),
    ]
    for k, v in rows:
        if v:
            L.append("| %s | %s |" % (k, v))

    L.append("\n## 2. 학력사항\n")
    L.append("| 기간 | 학교명 | 학위 | 전공(학과) | 지도교수 | 학위논문 |")
    L.append("|---|---|---|---|---|---|")
    for e in d["education"]:
        L.append("| %s | %s | %s | %s | %s | %s |" % (
            daterange(e.get("start"), e.get("end"), lang="kr"),
            e.get("org_kr", ""), e.get("degree_kr", ""), e.get("dept_kr", ""),
            e.get("advisor_kr", ""), e.get("thesis", "")))

    L.append("\n## 3. 경력사항\n")
    L.append("| 기간 | 기관명 | 부서 | 직위 |")
    L.append("|---|---|---|---|")
    for a in d["appointments"]:
        org = a.get("org_kr") or a.get("org_en", "")
        # Show both names only when they actually differ.
        if a.get("org_kr") and a.get("org_en") and a["org_kr"] != a["org_en"]:
            org = "%s / %s" % (a["org_kr"], a["org_en"])
        L.append("| %s | %s | %s | %s |" % (
            daterange(a.get("start"), a.get("end"), lang="kr"), org,
            a.get("dept_kr") or a.get("dept_en", ""),
            a.get("role_kr") or a.get("role_en", "")))

    L.append("\n## 4. 논문 실적\n")
    L.append("| 출간연도 | 학술지 | 권·호 | 제목 | 기여도 | 특이사항 |")
    L.append("|---|---|---|---|---|---|")
    for kind in PUB_KINDS:
        for pub in d["publications"][kind]:
            vol = ""
            if pub.get("volume"):
                vol = str(pub["volume"])
                if pub.get("issue"):
                    vol += "(%s)" % pub["issue"]
            if pub.get("article"):
                vol += (", " if vol else "") + str(pub["article"])
            L.append("| %s | %s | %s | %s | %s | %s |" % (
                pub.get("year", ""), pub.get("venue", ""), vol,
                pub.get("title", ""), pub.get("role_kr", ""),
                pub.get("note_kr") or pub.get("note") or ""))

    shown_grants = grants(d)
    if shown_grants:
        L.append("\n## 5. 연구비 수혜 실적\n")
        L.append("| 기간 | 과제명 | 지원기관 | 역할 | 연구비 | 상태 |")
        L.append("|---|---|---|---|---|---|")
        status_kr = {"awarded": "선정", "applied": "신청", "in_review": "심사중"}
        for g in shown_grants:
            L.append("| %s | %s | %s | %s | %s | %s |" % (
                g.get("period", ""), g.get("title_kr") or g.get("title_en", ""),
                g.get("funder_kr") or g.get("funder_en", ""), g.get("role_kr") or g.get("role", ""),
                g.get("amount", ""), status_kr.get(g.get("status"), g.get("status", ""))))

    L.append("\n## 6. 강의 실적\n")
    L.append("| 연도·학기 | 강의명 | 교과코드 | 학점 | 학교명 |")
    L.append("|---|---|---|---|---|")
    for t in d["teaching"]:
        L.append("| %s | %s | %s | %s | %s |" % (
            t.get("term", ""), t.get("name_kr") or t.get("name_en", ""),
            t.get("code", ""), t.get("credits", ""),
            t.get("institution_kr") or t.get("institution_en", "")))

    if d["software"]:
        L.append("\n## 7. 프로그램 개발 실적\n")
        L.append("| 연도 | 프로그램명 | 등록번호 | 내용 |")
        L.append("|---|---|---|---|")
        for s in d["software"]:
            L.append("| %s | %s | %s | %s |" % (
                s.get("year", ""), s.get("name_kr") or s.get("name_en", ""),
                s.get("registration", ""),
                s.get("description_kr") or s.get("description_en", "")))
        L.append("\n\\* 요청 시 등록 증명서 제공")

    if d["consulting"]:
        L.append("\n## 8. 외부 강연·워크샵·컨설팅\n")
        L.append("| 기간 | 기관 | 형태 | 주제 |")
        L.append("|---|---|---|---|")
        for c in d["consulting"]:
            L.append("| %s | %s | %s | %s |" % (
                c.get("period") or c.get("year", ""),
                c.get("org_kr") or c.get("org_en", ""),
                c.get("kind_kr") or c.get("kind_en", ""),
                c.get("topic_kr") or c.get("topic_en", "")))

    if d["service"]:
        L.append("\n## 9. 교내·학회 활동\n")
        L.append("| 기간 | 활동 | 기관 |")
        L.append("|---|---|---|")
        for s in d["service"]:
            L.append("| %s | %s | %s |" % (s.get("period") or s.get("year", ""),
                                           s.get("role_kr") or s.get("role_en", ""),
                                           s.get("org", "")))

    if d["certifications"]:
        L.append("\n## 10. 교육 이수 및 자격\n")
        L.append("| 일자 | 명칭 | 발급기관 |")
        L.append("|---|---|---|")
        for c in d["certifications"]:
            L.append("| %s | %s | %s |" % (c.get("date", ""),
                                           c.get("name_kr") or c.get("name_en", ""),
                                           c.get("issuer", "")))

    if d["media"]:
        L.append("\n## 11. 언론 보도\n")
        L.append("| 연도 | 언론사 | 기사 제목 |")
        L.append("|---|---|---|")
        for m in d["media"]:
            L.append("| %s | %s | %s |" % (m.get("year", ""), m.get("outlet", ""),
                                           m.get("title", "")))

    mil = d.get("military")
    if mil:
        L.append("\n## 12. 병역사항\n")
        L.append("| 항목 | 내용 |")
        L.append("|---|---|")
        for k, v in mil.items():
            L.append("| %s | %s |" % (k, v))

    L.append("\n\n본 이력서에 기재한 사항은 사실과 다름없음을 확인합니다.\n")
    L.append("작성일 : %s" % stamp(d))
    L.append("\n지원자 : %s (인)\n" % p.get("name_kr", ""))
    return "\n".join(L)


# --------------------------------------------------------------------------
# one-page résumé
# --------------------------------------------------------------------------

def resume_en(d: dict) -> str:
    p = d["person"]
    cfg = d.get("meta", {}).get("resume", {}) or {}
    n_pubs = int(cfg.get("max_publications", 6))

    L: list[str] = []
    L.append("# %s, %s" % (p.get("name_en"), p.get("degree", "Ph.D.")))
    L.append("\n%s · %s, %s" % (p.get("title_en"), p.get("dept_en"),
                                p.get("institution_en")))
    L.append("\n" + _contact_line(p))
    L.append("\n" + _idlinks_md(p))

    if cfg.get("summary_en"):
        L.append(_h(2, "Summary"))
        L.append(cfg["summary_en"])

    L.append(_h(2, "Appointments"))
    for a in d["appointments"]:
        L.append("- **%s** %s, %s" % (daterange(a.get("start"), a.get("end")),
                                      a.get("role_en", ""), a.get("org_en", "")))

    L.append(_h(2, "Education"))
    for e in d["education"]:
        L.append("- **%s** %s, %s" % (daterange(e.get("start"), e.get("end")),
                                      e.get("degree_en", ""), e.get("org_en", "")))

    L.append(_h(2, "Selected Publications"))
    ranked = sorted(
        [q for q in d["publications"]["journal"] + d["publications"]["preprint"]],
        key=lambda q: (0 if q.get("featured") else 1, -int(str(q.get("year", 0))[:4] or 0)))
    for pub in ranked[:n_pubs]:
        L.append("- %s" % citation(pub, bold_self=BOLD, link=True))
    total = len(d["publications"]["journal"])
    if total > n_pubs:
        L.append("\n*Full list: %d peer-reviewed articles — see full CV.*" % total)

    if d.get("metrics"):
        m = d["metrics"]
        L.append("\nCitations %s · h-index %s · i10-index %s (Google Scholar, %s)"
                 % (m.get("citations"), m.get("h_index"), m.get("i10_index"),
                    m.get("as_of", stamp(d))))

    funded = funded_grants(d)
    if funded:
        L.append(_h(2, "Funding"))
        for g in funded:
            L.append("- **%s** %s — %s%s" % (
                g.get("period", ""), g.get("title_en") or g.get("title_kr"),
                g.get("funder_en") or g.get("funder_kr", ""),
                " (%s)" % g["amount"] if g.get("amount") else ""))

    if d["teaching"]:
        L.append(_h(2, "Teaching"))
        terms = sorted({t.get("term", "") for t in d["teaching"] if t.get("term")},
                       reverse=True)
        names = []
        for t in d["teaching"]:
            n = t.get("name_en") or t.get("name_kr")
            if n and n not in names:
                names.append(n)
        L.append("%d courses across %s at %s: %s"
                 % (len(d["teaching"]), ", ".join(terms[:6]),
                    p.get("institution_en", ""), ", ".join(names[:10])))

    if d["consulting"]:
        L.append(_h(2, "AI Agent Onboarding & Consulting"))
        orgs, years = [], set()
        for c in d["consulting"]:
            o = c.get("org_en") or c.get("org_kr")
            if o and o not in orgs:
                orgs.append(o)
            # Accept either `year: 2026` or `period: 2026.07–`.
            for token in str(c.get("year") or c.get("period") or "").split("–"):
                token = token.strip()[:4]
                if token.isdigit():
                    years.add(int(token))
        span = ""
        if years:
            lo, hi = min(years), max(years)
            span = " (%s)" % (lo if lo == hi else "%s–%s" % (lo, hi))
        L.append("Lectures, workshops and advisory engagements on AI-agent adoption%s: %s"
                 % (span, ", ".join(orgs)))

    if d["skills"]:
        L.append(_h(2, "Skills"))
        for group, items in d["skills"].items():
            L.append("- **%s:** %s" % (group.replace("_", " ").title(),
                                       ", ".join(items)))

    return "\n".join(L).strip() + "\n"
