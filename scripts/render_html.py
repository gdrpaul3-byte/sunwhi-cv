#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Web CV: a single self-contained, print-ready HTML page."""
from __future__ import annotations

import html as _html

from cvdata import PUB_KINDS, author_string, daterange, stamp

BOLD = "<strong>%s</strong>"


def esc(s) -> str:
    return _html.escape("" if s is None else str(s), quote=False)


CSS = """
:root{
  --bg:#ffffff; --panel:#f7f7f5; --ink:#16181d; --muted:#5c6270; --faint:#8b91a0;
  --rule:#e3e5ea; --accent:#7a1f2b; --accent-soft:#f3e7e9; --link:#1f4f8b;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,"Noto Serif KR",serif;
  --sans:"Inter",-apple-system,BlinkMacSystemFont,"Segoe UI","Pretendard","Noto Sans KR",sans-serif;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
  --measure:44rem;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --bg:#101216; --panel:#171a20; --ink:#e8eaef; --muted:#a2a9b8; --faint:#767d8d;
    --rule:#272b34; --accent:#e0919c; --accent-soft:#2a1e21; --link:#8fb6e8;
  }
}
:root[data-theme="dark"]{
  --bg:#101216; --panel:#171a20; --ink:#e8eaef; --muted:#a2a9b8; --faint:#767d8d;
  --rule:#272b34; --accent:#e0919c; --accent-soft:#2a1e21; --link:#8fb6e8;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
  font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:52rem;margin:0 auto;padding:3.5rem 1.5rem 5rem}
a{color:var(--link);text-decoration:none;border-bottom:1px solid transparent}
a:hover{border-bottom-color:currentColor}

header.masthead{border-bottom:2px solid var(--ink);padding-bottom:1.25rem;margin-bottom:.5rem}
h1{font-family:var(--serif);font-size:2.6rem;line-height:1.1;margin:0 0 .25rem;
  letter-spacing:-.015em;font-weight:600}
.alt{color:var(--faint);font-size:.85rem;font-style:italic;margin:0 0 .9rem}
.role{font-size:1.02rem;color:var(--muted);margin:0 0 1rem}
.role strong{color:var(--ink);font-weight:600}
.contact{display:flex;flex-wrap:wrap;gap:.4rem 1.1rem;font-size:.85rem;color:var(--muted);
  font-family:var(--mono)}
.contact a{color:var(--muted)}
.idlinks{display:flex;flex-wrap:wrap;gap:.45rem;margin-top:.9rem}
.idlinks a{font-size:.75rem;letter-spacing:.04em;text-transform:uppercase;
  padding:.28rem .6rem;border:1px solid var(--rule);border-radius:999px;
  color:var(--muted);background:var(--panel)}
.idlinks a:hover{border-color:var(--accent);color:var(--accent)}
.updated{font-size:.75rem;color:var(--faint);font-family:var(--mono);margin-top:1rem}

h2{font-family:var(--sans);font-size:.78rem;font-weight:700;letter-spacing:.16em;
  text-transform:uppercase;color:var(--accent);margin:2.8rem 0 .9rem;
  padding-bottom:.4rem;border-bottom:1px solid var(--rule)}

.entry{margin:0 0 1.35rem;display:grid;grid-template-columns:8.5rem 1fr;gap:0 1.4rem}
.entry .when{font-family:var(--mono);font-size:.8rem;color:var(--faint);
  padding-top:.2rem;white-space:nowrap}
.entry .what{min-width:0}
.entry .what .line1{font-weight:600}
.entry .what .line2{color:var(--muted);font-size:.94rem}
.entry .what .sub{color:var(--faint);font-size:.86rem;font-style:italic;margin-top:.15rem}
.entry ul{margin:.4rem 0 0;padding-left:1.1rem}
.entry li{color:var(--muted);font-size:.94rem;margin:.2rem 0}

ol.pubs{list-style:none;counter-reset:p;margin:0;padding:0}
ol.pubs li{counter-increment:p;position:relative;padding-left:2.1rem;margin:0 0 1.05rem;
  font-size:.95rem;line-height:1.55}
ol.pubs li::before{content:counter(p) ".";position:absolute;left:0;top:0;
  font-family:var(--mono);font-size:.8rem;color:var(--faint)}
ol.pubs .title{color:var(--ink)}
ol.pubs .venue{font-style:italic;color:var(--muted)}
ol.pubs .doi{font-family:var(--mono);font-size:.78rem}
.badge{display:inline-block;font-size:.66rem;letter-spacing:.08em;text-transform:uppercase;
  padding:.12rem .42rem;border-radius:3px;background:var(--accent-soft);color:var(--accent);
  margin-left:.35rem;vertical-align:.08em;font-weight:600;white-space:nowrap}

table{width:100%;border-collapse:collapse;font-size:.9rem;margin:.2rem 0 1rem}
th{text-align:left;font-size:.7rem;letter-spacing:.09em;text-transform:uppercase;
  color:var(--faint);font-weight:600;padding:.4rem .6rem .4rem 0;border-bottom:1px solid var(--rule)}
td{padding:.45rem .6rem .45rem 0;border-bottom:1px solid var(--rule);
  color:var(--muted);vertical-align:top}
td.k{font-family:var(--mono);font-size:.82rem;color:var(--faint);white-space:nowrap}
td strong{color:var(--ink);font-weight:600}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}

.metrics{display:flex;gap:1.6rem;flex-wrap:wrap;background:var(--panel);
  border:1px solid var(--rule);border-radius:8px;padding:1rem 1.25rem;margin:.3rem 0 .6rem}
.metrics div{min-width:5rem}
.metrics .n{font-family:var(--serif);font-size:1.7rem;font-weight:600;line-height:1}
.metrics .l{font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--faint);
  margin-top:.25rem}
.note{font-size:.85rem;color:var(--faint);font-style:italic;margin:.4rem 0 1rem}

.tools{position:fixed;top:1rem;right:1rem;display:flex;gap:.4rem;z-index:9}
.tools button{font:inherit;font-size:.75rem;padding:.35rem .7rem;border-radius:6px;
  border:1px solid var(--rule);background:var(--panel);color:var(--muted);cursor:pointer}
.tools button:hover{border-color:var(--accent);color:var(--accent)}

footer{margin-top:3.5rem;padding-top:1.2rem;border-top:1px solid var(--rule);
  font-size:.78rem;color:var(--faint);font-family:var(--mono)}

@media (max-width:640px){
  .wrap{padding:2.25rem 1.1rem 3.5rem}
  h1{font-size:2rem}
  .entry{grid-template-columns:1fr;gap:.15rem}
  .entry .when{padding-top:0}
  .tools{position:static;justify-content:flex-end;margin-bottom:1rem}
}
@media print{
  :root{--bg:#fff;--ink:#000;--muted:#333;--faint:#666;--rule:#ccc;--accent:#000;
    --accent-soft:#eee;--link:#000;--panel:#fff}
  body{font-size:10.2pt;line-height:1.42}
  .wrap{max-width:none;padding:0}
  .tools{display:none}
  h1{font-size:20pt}
  h2{margin:14pt 0 5pt;font-size:8pt;break-after:avoid}
  .entry,ol.pubs li,tr{break-inside:avoid}
  a{color:#000}
  .idlinks a{border-color:#999}
  @page{margin:16mm 15mm}
}
"""

JS = """
(function(){
  var root=document.documentElement, K='cv-theme';
  try{var s=localStorage.getItem(K); if(s) root.setAttribute('data-theme',s);}catch(e){}
  var t=document.getElementById('theme');
  if(t) t.addEventListener('click',function(){
    var cur=root.getAttribute('data-theme');
    if(!cur) cur = matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light';
    var next = cur==='dark' ? 'light' : 'dark';
    root.setAttribute('data-theme',next);
    try{localStorage.setItem(K,next);}catch(e){}
  });
  var p=document.getElementById('print');
  if(p) p.addEventListener('click',function(){window.print();});
})();
"""


def _entry(when: str, line1: str, line2: str = "", sub: str = "",
           bullets: list[str] | None = None) -> str:
    out = ['<div class="entry"><div class="when">%s</div><div class="what">' % esc(when)]
    out.append('<div class="line1">%s</div>' % line1)
    if line2:
        out.append('<div class="line2">%s</div>' % line2)
    if sub:
        out.append('<div class="sub">%s</div>' % sub)
    if bullets:
        out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % esc(b) for b in bullets))
    out.append("</div></div>")
    return "".join(out)


def _pub_li(pub: dict) -> str:
    authors = author_string(pub, bold_self=BOLD)
    parts = ['%s (%s). <span class="title">%s.</span>'
             % (authors, esc(pub.get("year")), esc((pub.get("title") or "").rstrip(".")))]
    venue = pub.get("venue")
    if venue:
        v = esc(venue)
        if pub.get("volume"):
            v += " %s" % esc(pub["volume"])
            if pub.get("issue"):
                v += "(%s)" % esc(pub["issue"])
        if pub.get("article") or pub.get("pages"):
            v += ", %s" % esc(pub.get("article") or pub.get("pages"))
        parts.append('<span class="venue">%s.</span>' % v)
    if pub.get("doi"):
        parts.append('<a class="doi" href="https://doi.org/%s">doi:%s</a>'
                     % (esc(pub["doi"]), esc(pub["doi"])))
    elif pub.get("url"):
        parts.append('<a class="doi" href="%s">%s</a>'
                     % (esc(pub["url"]), esc(pub.get("url_label") or "link")))
    if pub.get("note"):
        parts.append('<span class="badge">%s</span>' % esc(pub["note"]))
    return "<li>%s</li>" % " ".join(parts)


def _table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return ""
    h = "".join("<th>%s</th>" % esc(x) for x in headers)
    body = []
    for r in rows:
        cells = []
        for i, c in enumerate(r):
            cls = ' class="k"' if i == 0 else ""
            cells.append("<td%s>%s</td>" % (cls, c))
        body.append("<tr>%s</tr>" % "".join(cells))
    return ('<div class="scroll"><table><thead><tr>%s</tr></thead><tbody>%s</tbody>'
            "</table></div>" % (h, "".join(body)))


def web_cv(d: dict) -> str:
    p = d["person"]
    S: list[str] = []

    # -- masthead ---------------------------------------------------------
    S.append('<div class="tools"><button id="theme">◐ theme</button>'
             '<button id="print">⎙ print / PDF</button></div>')
    S.append('<header class="masthead">')
    S.append("<h1>%s, %s</h1>" % (esc(p.get("name_en")), esc(p.get("degree", "Ph.D."))))
    if p.get("name_kr"):
        S.append('<p class="alt">%s%s</p>' % (
            esc(p["name_kr"]),
            " · also published as %s" % esc(", ".join(p.get("name_en_alt") or []))
            if p.get("name_en_alt") else ""))
    S.append('<p class="role"><strong>%s</strong>, %s<br>%s</p>'
             % (esc(p.get("title_en")), esc(p.get("dept_en")), esc(p.get("institution_en"))))

    contact = []
    for e in p.get("emails") or []:
        contact.append('<a href="mailto:%s">%s</a>' % (esc(e), esc(e)))
    for label, num in (p.get("phones") or {}).items():
        contact.append("%s %s" % (esc(label), esc(num)))
    S.append('<div class="contact">%s</div>' % "".join("<span>%s</span>" % c for c in contact))

    links = []
    if p.get("orcid"):
        links.append(("ORCID", "https://orcid.org/%s" % p["orcid"]))
    ids = p.get("ids") or {}
    if ids.get("scholar"):
        links.append(("Google Scholar",
                      "https://scholar.google.com/citations?user=%s" % ids["scholar"]))
    if ids.get("github"):
        links.append(("GitHub", "https://github.com/%s" % ids["github"]))
    import render_markdown
    for key, url in (p.get("links") or {}).items():
        links.append((render_markdown.link_label(key), url))
    S.append('<div class="idlinks">%s</div>'
             % "".join('<a href="%s">%s</a>' % (esc(u), esc(l)) for l, u in links))
    S.append('<p class="updated">last updated %s · generated from cv.yaml</p>' % esc(stamp(d)))
    S.append("</header>")

    # -- appointments / education ----------------------------------------
    if d["appointments"]:
        S.append("<h2>Professional Appointments</h2>")
        for a in d["appointments"]:
            org = esc(a.get("org_en"))
            if a.get("dept_en"):
                org = "%s, %s" % (esc(a["dept_en"]), org)
            if a.get("country"):
                org += ", %s" % esc(a["country"])
            S.append(_entry(daterange(a.get("start"), a.get("end")),
                            esc(a.get("role_en")), org,
                            "Advisor: %s" % esc(a["advisor"]) if a.get("advisor") else "",
                            a.get("bullets")))

    if d["education"]:
        S.append("<h2>Education</h2>")
        for e in d["education"]:
            S.append(_entry(daterange(e.get("start"), e.get("end")),
                            esc(e.get("degree_en")),
                            "%s, %s" % (esc(e.get("dept_en")), esc(e.get("org_en"))),
                            " · ".join(filter(None, [
                                "Advisor: %s" % esc(e["advisor"]) if e.get("advisor") else "",
                                "Dissertation: %s" % esc(e["thesis"]) if e.get("thesis") else ""]))))

    # -- metrics ----------------------------------------------------------
    if d.get("metrics"):
        m = d["metrics"]
        S.append("<h2>Citation Metrics</h2>")
        S.append('<div class="metrics">%s</div>' % "".join(
            '<div><div class="n">%s</div><div class="l">%s</div></div>' % (esc(v), esc(k))
            for k, v in [("citations", m.get("citations")), ("h-index", m.get("h_index")),
                         ("i10-index", m.get("i10_index"))]))
        S.append('<p class="note">Google Scholar, as of %s</p>' % esc(m.get("as_of", stamp(d))))

    # -- publications -----------------------------------------------------
    titles = {"journal": "Peer-Reviewed Journal Articles",
              "preprint": "Preprints &amp; Manuscripts",
              "conference": "Conference Proceedings"}
    note = d.get("meta", {}).get("author_note_en")
    for kind in PUB_KINDS:
        pubs = d["publications"][kind]
        if not pubs:
            continue
        S.append("<h2>%s</h2>" % titles[kind])
        if kind == "journal" and note:
            S.append('<p class="note">%s</p>' % esc(note))
        S.append('<ol class="pubs">%s</ol>' % "".join(_pub_li(x) for x in pubs))

    # -- funding ----------------------------------------------------------
    if d["grants"]:
        funded = [g for g in d["grants"] if g.get("status") == "awarded"]
        pending = [g for g in d["grants"] if g.get("status") in ("applied", "in_review")]
        if funded:
            S.append("<h2>Research Funding</h2>")
            for g in funded:
                S.append(_entry(g.get("period", ""),
                                esc(g.get("title_en") or g.get("title_kr")),
                                " · ".join(filter(None, [
                                    esc(g.get("funder_en") or g.get("funder_kr") or ""),
                                    "Role: %s" % esc(g["role"]) if g.get("role") else "",
                                    esc(g.get("amount") or "")]))))
        if pending:
            S.append("<h2>Grants Under Review</h2>")
            for g in pending:
                S.append(_entry(g.get("period", ""),
                                esc(g.get("title_en") or g.get("title_kr")),
                                esc(g.get("funder_en") or g.get("funder_kr") or "")))

    # -- teaching ---------------------------------------------------------
    if d["teaching"]:
        S.append("<h2>Teaching</h2>")
        rows = []
        for t in d["teaching"]:
            name = esc(t.get("name_en") or t.get("name_kr"))
            if t.get("name_en") and t.get("name_kr"):
                name = "<strong>%s</strong><br><span style='font-size:.85em'>%s</span>" % (
                    esc(t["name_en"]), esc(t["name_kr"]))
            else:
                name = "<strong>%s</strong>" % name
            rows.append([esc(t.get("term", "")), name, esc(t.get("code", "")),
                         esc(t.get("credits", "")),
                         esc(t.get("institution_en") or t.get("institution_kr") or "")])
        S.append(_table(["Term", "Course", "Code", "Cr.", "Institution"], rows))

    # -- talks / posters --------------------------------------------------
    if d["invited_talks"]:
        S.append("<h2>Invited Talks &amp; Guest Lectures</h2>")
        for t in d["invited_talks"]:
            S.append(_entry(str(t.get("year", "")),
                            "“%s”" % esc((t.get("title") or "").rstrip(".")),
                            " · ".join(filter(None, [esc(t.get("venue", "")),
                                                     esc(t.get("location", ""))]))))
    if d["posters"]:
        S.append("<h2>Conference Presentations</h2>")
        for t in d["posters"]:
            S.append(_entry(str(t.get("year", "")),
                            "“%s”" % esc((t.get("title") or "").rstrip(".")),
                            " · ".join(filter(None, [
                                esc(", ".join(t.get("authors") or [])),
                                esc(t.get("venue", "")), esc(t.get("location", ""))]))))

    # -- software ---------------------------------------------------------
    if d["software"]:
        reg = [s for s in d["software"] if s.get("registration")]
        opensrc = [s for s in d["software"] if not s.get("registration")]
        S.append("<h2>Software &amp; Registered Programs</h2>")
        if reg:
            S.append(_table(["Year", "Program", "Registration", "Description"],
                            [[esc(s.get("year", "")),
                              "<strong>%s</strong>" % esc(s.get("name_en") or s.get("name_kr")),
                              esc(s.get("registration", "")),
                              esc(s.get("description_en") or s.get("description_kr") or "")]
                             for s in reg]))
        if opensrc:
            S.append('<p class="note">Open-source research and teaching tools</p>')
            S.append(_table(["Year", "Project", "Description"],
                            [[esc(s.get("year", "")),
                              ('<a href="%s"><strong>%s</strong></a>' % (esc(s["url"]), esc(s.get("name_en") or s.get("name_kr"))))
                               if s.get("url") else "<strong>%s</strong>" % esc(s.get("name_en") or s.get("name_kr")),
                              esc(s.get("description_en") or s.get("description_kr") or "")]
                             for s in opensrc]))

    # -- the rest ---------------------------------------------------------
    simple = [
        ("mentoring", "Mentoring &amp; Advising",
         lambda m: (m.get("period", ""), esc(m.get("name", "")), esc(m.get("role", "")))),
        ("service", "Institutional &amp; Professional Service",
         lambda s: (s.get("period") or s.get("year", ""),
                    esc(s.get("role_en") or s.get("role_kr") or ""), esc(s.get("org", "")))),
        ("awards", "Awards &amp; Honors",
         lambda a: (a.get("year", ""), esc(a.get("name_en") or a.get("name_kr") or ""),
                    esc(a.get("org", "")))),
        ("certifications", "Certifications &amp; Training",
         lambda c: (c.get("date", ""), esc(c.get("name_en") or c.get("name_kr") or ""),
                    esc(c.get("issuer", "")))),
        ("media", "Media Coverage",
         lambda m: (m.get("year", ""), esc(m.get("title", "")), esc(m.get("outlet", "")))),
        ("outreach", "Outreach",
         lambda o: (o.get("period") or o.get("year", ""),
                    esc(o.get("name_en") or o.get("name_kr") or ""),
                    esc(o.get("description_en") or o.get("description_kr") or ""))),
    ]
    for key, heading, fn in simple:
        if not d.get(key):
            continue
        S.append("<h2>%s</h2>" % heading)
        for item in d[key]:
            when, l1, l2 = fn(item)
            S.append(_entry(str(when), l1, l2))

    if d["peer_review"]:
        S.append("<h2>Peer Review</h2>")
        for r in d["peer_review"]:
            S.append(_entry(str(r.get("years", "")), esc(r.get("journal", "")),
                            esc(r.get("note", ""))))

    if d["skills"]:
        S.append("<h2>Technical Skills</h2>")
        S.append(_table(["Area", "Detail"],
                        [[esc(g.replace("_", " ").title()), esc(", ".join(items))]
                         for g, items in d["skills"].items()]))

    if d["references"]:
        S.append("<h2>References</h2>")
        for r in d["references"]:
            S.append(_entry("", "<strong>%s</strong>" % esc(r.get("name", "")),
                            " · ".join(filter(None, [esc(r.get("title", "")), esc(r.get("org", "")),
                                                     esc(r.get("email", ""))]))))

    S.append('<footer>%s · CV generated from <a href="%s">cv.yaml</a> on %s</footer>'
             % (esc(p.get("name_en")),
                esc((p.get("links") or {}).get("cv_repo", "#")), esc(stamp(d))))

    title = "%s — CV" % p.get("name_en", "CV")
    desc = "Academic CV of %s, %s, %s." % (p.get("name_en"), p.get("title_en"),
                                           p.get("institution_en"))
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n"
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            "<title>%s</title>\n"
            '<meta name="description" content="%s">\n'
            '<meta name="author" content="%s">\n'
            "<style>%s</style>\n</head>\n<body>\n"
            '<main class="wrap">\n%s\n</main>\n'
            "<script>%s</script>\n</body>\n</html>\n"
            % (esc(title), esc(desc), esc(p.get("name_en")), CSS,
               "\n".join(S), JS))
