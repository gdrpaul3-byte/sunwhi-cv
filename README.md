# sunwhi-cv

The CV of **Sunwhi Kim, Ph.D.** (김선휘) as data, not as a pile of Word files.

Everything lives in one file — [`cv.yaml`](cv.yaml). A build step turns it into an
English academic CV, a Korean 이력서, a one-page résumé, a web page, and machine-readable
JSON. Edit the YAML; never edit anything in `build/` by hand.

**Live CV:** https://gdrpaul3-byte.github.io/sunwhi-cv/

---

## Why this exists

Before this repo the CV existed as ~8 divergent `.docx` files, a Korean 이력서, a lab
website, an ORCID record, and a Google Scholar profile — each with a different idea of
what was true. A publication added in one place stayed missing in the other four.

Now there is one source of truth, and the drift is detected mechanically:

| Surface | How it stays current |
|---|---|
| English CV / 이력서 / résumé | regenerated from `cv.yaml` on every push |
| Web CV (GitHub Pages) | regenerated and deployed on every push to `main` |
| Lab website publication list | `scripts/sync_labpage.py` rewrites one delimited block |
| ORCID | `--orcid-diff` reports what ORCID is missing (writing is still manual — ORCID has no unattended write path) |
| Google Scholar | read-only; citation metrics are copied into `cv.yaml` under `metrics:` |

---

## Quick start

```bash
pip install -r requirements.txt
python scripts/build.py
```

Artifacts land in `build/`:

| File | What it is |
|---|---|
| `index.html` | web CV — responsive, dark-mode aware, prints to a clean PDF |
| `cv-en.md` | full English academic CV |
| `cv-kr.md` | Korean 이력서 |
| `resume-en.md` | one-page résumé |
| `cv.json` | [JSON Resume](https://jsonresume.org) — feeds third-party tools |
| `publications.json` | the feed the lab website consumes |
| `CV_SunwhiKim.docx`, `이력서_김선휘.docx` | Word versions (`--docx`) |
| `cv-en.pdf` | print-quality PDF (`--pdf`) |

### Other commands

```bash
python scripts/build.py --check
```
Validate `cv.yaml` without building. Exits non-zero on problems — this is what CI runs.

```bash
python scripts/build.py --orcid-diff
```
Fetch the live ORCID record and write `build/orcid-diff.json` listing every work in
`cv.yaml` that ORCID does not have, plus structural problems such as a degree with no
end date.

```bash
python scripts/build.py --docx --pdf --orcid-diff
```
Everything.

```bash
python scripts/sync_labpage.py --lab ../sunwhikim_lab_page
```
Rewrite the publication block in the lab site's `index.html`. Add `--check` to fail
instead of writing — useful in the lab repo's own CI.

---

## Editing `cv.yaml`

### Adding a publication

```yaml
publications:
  journal:
    - id: natcomm2025            # stable slug; used as an anchor
      year: 2025
      authors: [Kim YE, Kim M, Kim S, Lee R]   # full list, in order
      equal: [Kim M, Kim S, Lee R]             # rendered with *
      corresponding: [Park C, Kim IH]          # rendered with †
      me: Kim S                                # bolded in every output
      title: Endothelial SHANK3 regulates tight junctions ...
      venue: Nature Communications
      volume: 16
      issue: 1
      article: 1407
      doi: 10.1038/s41467-025-56720-1
      role_kr: 공동 제1저자        # only used by the Korean 이력서
      note: Cover article          # rendered as a badge
      featured: true               # promotes it in the one-page résumé
```

`authors`, `equal`, `corresponding`, and `me` are cross-checked: if `me` or an
equal/corresponding name is not in `authors`, `--check` fails. That is the single most
common way a hand-edited CV goes wrong.

Buckets are `journal`, `preprint`, and `conference`. Each is sorted newest-first
automatically, so insert anywhere.

### Adding a grant

```yaml
grants:
  - title_kr: 과제명
    funder_kr: 지원기관
    period: 2026.03–2027.02
    role: PI
    amount: ₩10,000,000
    status: awarded     # awarded | in_review | applied | not_funded
```

`status` is **required and validated**. A CV must never present an application as
funded, so the build refuses any other value. Only `awarded` grants appear under
"Research Funding"; `applied` and `in_review` render under a separate
"Grants Under Review" heading; `not_funded` is kept for the record and printed nowhere.

### Adding a course

```yaml
teaching:
  - term: 2026-1        # YYYY-S
    name_kr: 뇌과학개론
    name_en: Introduction to Neuroscience
    code: "500387"      # quote it — a bare number loses leading zeros
    credits: 3
    institution_kr: 화성의과학대학교
    institution_en: Hwasung Medi-Science University
```

### Bilingual fields

Anything ending in `_en` / `_kr` is language-paired. English outputs prefer `_en` and
fall back to `_kr`; the Korean 이력서 does the reverse. Fill in both when you have both.

---

## Repository layout

```
cv.yaml                    the source of truth — this is the file you edit
scripts/
  cvdata.py                load, validate, and normalize; shared formatting rules
  build.py                 CLI entry point
  render_markdown.py       cv-en.md, cv-kr.md, resume-en.md
  render_html.py           index.html (web CV)
  render_json.py           cv.json, publications.json, ORCID reconciliation
  render_docx.py           optional .docx export
  sync_labpage.py          push publications into the lab website
build/                     generated — committed so Pages can serve it
.github/workflows/build.yml
```

`build/` is committed on purpose: GitHub Pages serves it, and the lab site fetches
`build/publications.json` from this repo. Do not add it to `.gitignore`.

---

## Continuing this work in another tool

The repo is deliberately plain: Python 3.9+, one required dependency (PyYAML), no
build system, no framework, no lockfile. Cursor, a Grok agent, Claude Code, or a person
with a text editor can all pick it up the same way:

```bash
git clone https://github.com/gdrpaul3-byte/sunwhi-cv
cd sunwhi-cv
pip install -r requirements.txt
python scripts/build.py --check
```

The validator is the contract. If `--check` passes, every renderer will produce
sensible output — so an agent can edit `cv.yaml`, run `--check`, and know whether it
broke anything without reading a single renderer.

CI runs on every push and on the 1st of each month: it validates `cv.yaml`, runs the
tests, rebuilds everything, deploys Pages from what it just built, and posts the ORCID
drift table to the job summary. It does **not** commit `build/` — you do, along with
your `cv.yaml` edit. CI fails if the committed `build/` is stale, so run
`python scripts/build.py` before pushing.

---

## Maintenance rhythm

- **When a paper is accepted** — add it to `publications.journal`, push. Then add it to
  ORCID by hand (`build/orcid-diff.json` will keep reminding you until you do).
- **Each semester** — add courses to `teaching`.
- **When a grant result arrives** — flip `status` from `in_review` to `awarded` or
  `not_funded`.
- **Yearly** — refresh `metrics:` from Google Scholar and bump `meta.updated`.
