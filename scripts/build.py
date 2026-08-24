#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build every CV artifact from cv.yaml.

    python scripts/build.py                # build everything into build/
    python scripts/build.py --check        # validate only, non-zero exit on problems
    python scripts/build.py --orcid-diff   # also query the live ORCID record
    python scripts/build.py --docx         # also emit .docx (needs python-docx)
    python scripts/build.py --pdf          # also emit .pdf (needs Chrome or LibreOffice)

Run it from anywhere; paths are resolved relative to the repository root.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cvdata  # noqa: E402
import render_html  # noqa: E402
import render_json  # noqa: E402
import render_markdown  # noqa: E402

ROOT = cvdata.ROOT
OUT = os.path.join(ROOT, "build")
OUT_PRIVATE = os.path.join(ROOT, "build-private")


def write(relpath: str, text: str, out_dir: str | None = None) -> str:
    path = os.path.join(out_dir or OUT, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path


def write_json(relpath: str, obj, out_dir: str | None = None) -> str:
    return write(relpath, json.dumps(obj, ensure_ascii=False, indent=2) + "\n", out_dir)


# --------------------------------------------------------------------------
# optional exporters
# --------------------------------------------------------------------------

def find_chrome() -> str | None:
    for name in ("chrome", "google-chrome", "chromium", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
        if os.path.exists(p):
            return p
    return None


def html_to_pdf(html_path: str, pdf_path: str) -> bool:
    chrome = find_chrome()
    if not chrome:
        sys.stderr.write("  ! no Chrome/Edge found — skipping PDF\n")
        return False
    url = "file:///" + os.path.abspath(html_path).replace("\\", "/")
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
           "--print-to-pdf=" + os.path.abspath(pdf_path), url]
    try:
        subprocess.run(cmd, check=True, timeout=180,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return os.path.exists(pdf_path)
    except Exception as exc:  # pragma: no cover
        sys.stderr.write("  ! PDF export failed: %s\n" % exc)
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Build CV artifacts from cv.yaml")
    ap.add_argument("--check", action="store_true", help="validate only")
    ap.add_argument("--orcid-diff", action="store_true",
                    help="query the live ORCID record and write build/orcid-diff.json")
    ap.add_argument("--docx", action="store_true", help="also emit .docx files")
    ap.add_argument("--pdf", action="store_true", help="also emit .pdf files")
    ap.add_argument("--source", default=None, help="path to cv.yaml")
    ap.add_argument("--public-only", action="store_true",
                    help="skip build-private/ even if private.yaml exists")
    args = ap.parse_args()

    # Everything written to build/ is committed and published, so it is always
    # rendered from the public-only data. private.yaml (home address, date of
    # birth, personal mobile, military service) is merged only for the Korean
    # application documents, which land in the git-ignored build-private/.
    data = cvdata.load(args.source, private=False)
    problems = cvdata.validate(data)
    if problems:
        sys.stderr.write("cv.yaml validation problems (%d):\n" % len(problems))
        for p in problems:
            sys.stderr.write("  - %s\n" % p)
        if args.check:
            return 1
        sys.stderr.write("(continuing anyway; run --check in CI to make these fatal)\n\n")
    else:
        print("cv.yaml: valid")
    if args.check:
        return 0

    os.makedirs(OUT, exist_ok=True)
    made = []

    made.append(write("cv-en.md", render_markdown.cv_en(data)))
    made.append(write("cv-kr.md", render_markdown.cv_kr(data)))
    made.append(write("resume-en.md", render_markdown.resume_en(data)))

    html = render_html.web_cv(data)
    made.append(write("index.html", html))

    made.append(write_json("cv.json", render_json.json_resume(data)))
    made.append(write_json("publications.json", render_json.publications_feed(data)))

    if args.orcid_diff:
        try:
            diff = render_json.orcid_diff(data)
            made.append(write_json("orcid-diff.json", diff))
            n = len(diff["missing_works"])
            print("orcid: %d work(s) present in cv.yaml but missing from ORCID" % n)
            for w in diff["missing_works"]:
                print("   - %s (%s)" % (w["title"], w["doi"]))
            for e in diff["open_ended_education"]:
                print("   ! education '%s' at %s has no end date" % (e["role"], e["org"]))
        except Exception as exc:
            sys.stderr.write("  ! ORCID check failed: %s\n" % exc)

    if args.docx:
        try:
            import render_docx
            made += render_docx.build(data, OUT)
        except ImportError as exc:
            sys.stderr.write("  ! docx export needs python-docx (%s)\n" % exc)

    if args.pdf:
        pdf = os.path.join(OUT, "cv-en.pdf")
        if html_to_pdf(os.path.join(OUT, "index.html"), pdf):
            made.append(pdf)

    print("\nbuilt %d file(s) in %s:" % (len(made), OUT))
    for m in made:
        print("  %-22s %6.1f KB" % (os.path.basename(m), os.path.getsize(m) / 1024.0))

    # -- private variants ---------------------------------------------------
    if os.path.exists(cvdata.PRIVATE_PATH) and not args.public_only:
        full = cvdata.load(args.source)
        os.makedirs(OUT_PRIVATE, exist_ok=True)
        priv = [write("cv-kr.md", render_markdown.cv_kr(full), OUT_PRIVATE),
                write("cv-en.md", render_markdown.cv_en(full), OUT_PRIVATE)]
        if args.docx:
            try:
                import render_docx
                priv += render_docx.build(full, OUT_PRIVATE)
            except ImportError:
                pass
        print("\nbuilt %d private file(s) in %s (git-ignored — contains "
              "address / date of birth / mobile):" % (len(priv), OUT_PRIVATE))
        for m in priv:
            print("  %-22s %6.1f KB" % (os.path.basename(m), os.path.getsize(m) / 1024.0))
    elif not os.path.exists(cvdata.PRIVATE_PATH):
        print("\nnote: no private.yaml — Korean 이력서 built without address, "
              "date of birth, mobile, or military service.\n"
              "      See private.yaml.example to enable those for job applications.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
