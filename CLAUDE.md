# ☠️ DEAD REPO. DO NOT BUILD OR DEPLOY HERE.

**This is the orphan.** The live site is served from the repo with **no `.com`**:

- ✅ LIVE: `connorwithhonor/scv123`
- ☠️ THIS: `connorwithhonor/scv123.com`

## Evidence (measured 2026-07-22 against the live homepage)

| repo | index.html | delta vs live | homepage title |
|---|---|---|---|
| `scv123` | 31969 | **745 bytes** | matches live |
| `scv123.com` (this) | 47025 | 14311 bytes | different |

## Why your instincts fail here

This is the third instance of the same trap on this account (see
`santaclaritaartificialintelligence.com`, now archived). In that case the DEAD repo
had the NEWER commit date, so "most recently updated" pointed at the wrong repo.
Repo name, title, and recency are all unreliable. **Byte-compare `index.html`
against the live homepage. That is the only check that has ever worked.**

Full context: `claude-memory/scai-repo-topology-trap.md`
