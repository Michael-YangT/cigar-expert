# Setup and degradation

Two dependencies, neither of which needs an account. No key, token, MCP server
or CLI to install: the skill is meant to work on a machine that has just cloned
the repository.

## python-runtime

| Field | Value |
|---|---|
| Required | yes |
| Auth | none |
| Minimum version | Python 3.8 |
| Official site | https://www.python.org/ |
| Documentation | https://docs.python.org/3/ |
| Downloads | https://www.python.org/downloads/ |

Steps:

1. `python3 --version`, expecting 3.8 or newer.
2. Install nothing else. All six scripts import only the standard library.
3. `python3 scripts/check_environment.py` and read the `status` field.

Verify: the command exits 0 and reports `ready` or `partial`.

Security: no package installation is required, and none should be added to
satisfy this skill. Stdlib-only is deliberate — a clone runs as-is, and a
third-party dependency would add a supply-chain surface for no benefit.

If Python is missing, nothing script-based runs. Storage, terminology and
flavour-group answers survive, because they read markdown rather than execute
code. Do not describe a cigar from memory to cover the gap.

## reference-sites

| Field | Value |
|---|---|
| Required | no |
| Auth | none |
| Primary site | https://www.cigarcentury.com/ |
| Machine-readable index | https://www.cigarcentury.com/sitemap.xml |

Five hosts, all HTTPS, all read-only, all without credentials:

| Site | Used by | Needs | If unreachable |
|---|---|---|---|
| Cigar Century | `build_index.py`, `lookup.py` | nothing, plain GET | `lookup.py` exits 2. Answer from the Chinese index or say the catalogue is unreachable. Never invent a vitola. |
| 雪茄 123 | `fetch_domestic.py` | nothing | Chinese domestic brands have no other source. Say so rather than guessing. |
| Cigar Capitol | `fetch_capitol.py` | nothing | Irrelevant at answer time: all 329 entries are already cached in `references/`. |
| Cigar Aficionado | `fetch_rating.py` | nothing, but one page per request | No other authoritative source. Say the rating could not be retrieved; never estimate one. |
| halfwheel | `fetch_news.py` | a browser-capable fetcher | Expected. The script returns `status: blocked` by design and prints the date-archive URLs for the built-in web-fetch tool. Do not retry it. |

Verify: `python3 scripts/check_environment.py --online` lists HTTP 200 for Cigar
Century, and 200 or 403 for halfwheel.

Security: only these five hosts are contacted. No credential exists to store,
rotate or revoke; the skill never contacts a retailer and never sends a price.

## First run

```bash
python3 scripts/build_index.py                    # ~10 s, 4,757 brands + 19,191 models
python3 scripts/fetch_domestic.py --build-index    # ~80 s, ~1,770 Chinese pages
```

Both write into `data/`, which is gitignored — derived data goes stale, and a
stale index is worse than none. Rebuild rather than patch.

Skipping either leaves the skill in `partial`: storage, terminology and
flavour-group answers still work from `references/`; catalogue lookup does not.

## Degradation by function

| Function | Breaks when | What still works | What to tell the user |
|---|---|---|---|
| Cigar lookup | no index, or Cigar Century down | Chinese index, all cached references | which of the two, and the one command that fixes it |
| Chinese domestic lookup | no `xuejia-index.tsv` | everything else | run `--build-index`; about 80 s |
| Storage and terminology | never, once installed | — | — |
| Flavour-group assignment | wrapper unknown or ambiguous | the full wrapper-to-group table | ask which wrapper, then map it |
| Published score | no rating page found | tasting notes from 雪茄 123 | "no published rating found", not a guess |
| New releases | always, from a script | the date archive via the web-fetch tool | that the site blocks scripts, and where to look instead |

## When a site changes layout

The parsers key off stable structure: `<loc>` entries in the sitemap, the
`SCORE / LENGTH / GAUGE / STRENGTH` label block on a rating page, and the
label-then-value pattern on a Chinese detail page. Each parser fails with a
specific message rather than returning empty fields, so a layout change shows up
as an error on the next run instead of as a wrong answer.

If an index build reports zero entries, check the sitemap by hand before
touching a regex — the usual cause is the site, not the code.

## Verification

```bash
python3 scripts/check_environment.py     # expect ready
python3 scripts/lookup.py --check        # expect ok for both indexes
python3 scripts/lookup.py --brand "奥利瓦 Oliva" --model "Serie V Melanio Robusto"
```

A working install resolves the last command to `oliva-serie-v-melanio-robusto`
with confidence `high`.

## CI / 回归检查清单

每次克隆、拉取更新或修改脚本后，按顺序运行：

```bash
# 1. 环境自检（本地 + 网络）
python3 scripts/check_environment.py               # 期望 ready 或 partial
python3 scripts/check_environment.py --online      # 五站可达性：Cigar Century 200，halfwheel 200 或 403

# 2. 索引完整性
python3 scripts/lookup.py --check                  # 两个索引均报 ok

# 3. 单元测试（stdlib-only，无网络）
python3 -m unittest tests.test_lookup              # 全部通过

# 4. 端到端一次查型号
python3 scripts/lookup.py --brand "奥利瓦 Oliva" --model "Serie V Melanio Robusto"   # 期望 confidence: high

# 5. 索引时效性（data/ 是 gitignored 的派生数据，会过期）
# 若 data/brands.txt / cigars.txt 修改时间超过 30 天，执行重建：
#   python3 scripts/build_index.py
#   python3 scripts/fetch_domestic.py --build-index
```

任何一步失败，先解决当前步骤再进入下一步；不要在索引缺失或过期时直接断言“这支雪茄不存在”。
