# Cigar Expert · 雪茄顾问

一个面向 WorkBuddy / Claude 的雪茄参考 Skill。查型号参数、解养护问题、按气味组分盒，中文作答并保留英文原名。

Two layers:

- **通用层** — anyone can use it. Look up a vitola, explain *plume vs. mould*, describe what San Andrés leaf tastes like.
- **个人层** — optional. Point it at your own ledger CSV and it helps identify unknown cigars and calibrate doubtful rows.

The personal layer ships switched off and empty, so this repository contains no
collection data. See [Privacy](#隐私设计).

---

## 它能做什么

| 问它 | 它做 |
|---|---|
| 这支茄什么参数？ | 输出尺寸、环径、强度、茄衣/茄套/茄芯、风味标签、评分，附来源链接 |
| 这支我不认识、没法确定型号 | 三段式比对资料库，给候选 + 置信度；不确定就明说不确定 |
| 国产茄（长城/黄鹤楼/王冠/泰山）什么型号？ | 查雪茄 123 中文库，按长度 + 环径给候选，中英双语名 |
| 这支在权威评分里多少分？ | 引 Cigar Aficionado 百分制与历次复评，`price_reference` 只给站点公布原值 |
| 最近出了什么新款？有没有我手里这支的信息？ | 查 halfwheel 动态与日期归档 |
| 长白毛是发霉还是开花？ | 引 Cigar Capitol 的判据，离线可答 |
| 这盒能不能和其他茄放一起？ | 按茄衣判气味组和湿度目标 |
| 我的柜子里有多少支、该怎么安排？ | 需先配置 `personal-ledger.md`，见下 |

Bilingual output is the default: 「Arturo Fuente Hemingway Classic（海明威经典）」，not just「阿图罗·富恩特 海明威」。Cigar names do not translate cleanly and losing the English string makes the cigar unsearchable.

---

## 安装

The folder name must match the skill name `cigar-expert`, because that is how
the frontmatter resolves:

```bash
git clone <your-repo-url> cigar-expert
cp -r cigar-expert ~/.workbuddy/skills/
```

Then build the catalogue index (takes seconds):

```bash
cd ~/.workbuddy/skills/cigar-expert
python3 scripts/check_environment.py               # 期望 partial，属正常
python3 scripts/build_index.py       # Cigar Century 型号库，约 7 秒
python3 scripts/fetch_domestic.py --build-index   # 雪茄 123 中文库，约 80 秒
```

只装不建索引也能用：养护、术语、气味组三块走 `references/` 离线缓存，`check_environment.py` 会报 `partial` 并点出缺哪一份。**`partial` 不是错误**，但索引缺失时不许把查不到说成「这支不存在」。

That writes `data/brands.txt` (4,757 brands) and `data/cigars.txt` (19,191
non-Chinese models), plus `data/xuejia-index.tsv` (1,767 Chinese-facing pages:
国产 143 · 古巴 1,084 · 非古 540). Indexes are gitignored — derived data, and
they go stale.

## 用法

```bash
# 查型号（非国产）
python3 scripts/lookup.py --brand "奥利瓦 Oliva" --model "Serie V Melanio Robusto"

# 抓已知型号的完整参数
python3 scripts/lookup.py --url "https://www.cigarcentury.com/en/cigars/oliva-serie-v-melanio-robusto"

# 查国产茄 —— Cigar Century 完全没有国产型号，必须走这里
python3 scripts/fetch_domestic.py --find 长城
python3 scripts/fetch_domestic.py --detail https://www.xuejia123.com/baike1/guochan/changcheng/132/91932.html

# 查权威百分制评分（价格只转述站点原值，不推算区间）
python3 scripts/fetch_rating.py --find "Tatuaje Cabinet Tainos"     # 先拿到检索式
python3 scripts/fetch_rating.py --url https://www.cigaraficionado.com/ratings/27174/name/tatuaje-cabinet-tainos-double-corona

# 检查环境
python3 scripts/check_environment.py
python3 scripts/lookup.py --check
```

`--find` 只打印检索式与下一步命令，本身不发请求，输出里的 `status: needs_web_search` 就是提醒别把它当结果。`--url` 只接受单条评分页，索引页会被直接拒掉——否则解析出一片空字段，看起来像「这支没有评分」。

New releases come from halfwheel, which blocks scripts behind a Cloudflare
challenge. `fetch_news.py` detects that and prints the date-archive URLs to use
with a normal web-fetch tool instead — treat its `blocked` output as the answer,
not as a bug to retry past.

Optional personal layer:

```bash
cp references/personal-ledger.example.md references/personal-ledger.md
# 编辑它，填入你的台账路径
```

---

## 为什么匹配规则写得这么严

Because the loose version was tried first and produced wrong answers. All three
failures below were reproduced against a real ledger:

| 输入 | 朴素子串搜索的结果 | 实际应为 |
|---|---|---|
| 黄鹤楼 雪之梦**6** | `262`-allegiance-corona | 找不到（国产茄不在此库） |
| 金特罗 Quintero **Brevas** | arturo-fuente-...-brevas-royal-i | `quintero-brevas` |
| Macanudo Inspirado Red **Robusto** | ...-red-**toro** | `...-red-robusto` |

所以匹配必须是三段，**缺一不可**：

1. **锁品牌** — 品牌 slug 至少含 3 个拉丁字母（防止 `Undercrown 10` 被锁到品牌 `10`；`1502`、`1845` 又是真品牌，不能一刀切过滤）
2. **配产品线** — 数字按整 token 比对，`6` 不会藏进 `262`
3. **验尺寸** — 尺寸词是身份的一部分，不是停用词；缺失就降级为待复核

Full reasoning and all reproduced cases: [`references/matching-rules.md`](references/matching-rules.md).

Confidence is always reported. `high` means present it; `review` means present it
but say what did not match; `no_product_match` means say nothing was found rather
than substituting a lookalike. A wrong answer written into a real ledger is
worse than no answer.

---

## 数据源

Seven sites were fetched and inspected before any was adopted. Verdicts are what
the fetches showed, not reputation.

| Site | Verdict | What it is for |
|---|---|---|
| [Cigar Century](https://www.cigarcentury.com) | Primary | 19,191 型号参数库（无国产） |
| [雪茄 123](https://www.xuejia123.com) | Primary，国产唯一 | 1,767 中文条目；国产茄唯一去处（须过滤 SEO 稿） |
| [Cigar Capitol](https://cigarcapitol.com) | Primary | 329 术语 · 33 产区 · 每条标注置信度 |
| [Cigar Aficionado](https://www.cigaraficionado.com) | Secondary | 权威 100 分制评分与品鉴笔记；单页取用，禁止爬取与脚本搜索 |
| [halfwheel](https://halfwheel.com) | Secondary | 行业新品动态；脚本被 Cloudflare 拦截，需走网页抓取工具 |
| [Cigar Sense](https://www.cigarsense.com) | Restricted | 方法论可参考；核心功能需账号 |
| ~~Cigar Directory~~ | **Rejected** | 榜单前十并列 5.0 无区分度；178mm 写成 178 英寸 |

Full assessment including reproduced defects: [`references/data-sources.md`](references/data-sources.md).

`build_index.py` follows the sitemap declared in the site's `robots.txt`, which
permits the ordinary content paths and disallows only `/es/ajax`, `/en/ajax` and
`/scripts/`.

---

## 隐私设计

公开仓库里**不含任何个人收藏数据**：

- `references/personal-ledger.md` 记录你的台账路径与个人收藏细节 —— 已 gitignored
- 仓库只 ship `personal-ledger.example.md`，一份空模板
- 未配置该文件时，Skill 只回答通用问题，不会假设你有收藏
- 型号举例为市面常见款，不含总数、行数或台账路径

Nothing here refers to any particular collection. Examples use ordinary retail
models and carry no ownership meaning.

Before pushing, read `git diff` and check what actually ships. No personal or
commercial information belongs in this repository.

If you fork this, keep that boundary. Do not commit your own ledger path.

---

## 边界

这个 Skill 不做以下事情：

- **不提供商家、链接或购买引导** — `price_reference` 只转述站点公布的数字，不推算区间、不换算币种、不指向任何卖家
- **不爬取** — Cigar Aficionado 明确禁止脚本访问其搜索；halfwheel 有风控。按仓库规定的单页 / 网页工具方式取用
- **不出具真伪结论** — 只给判据和可观察检查
- **不写你的台账** — 只出建议草稿，由你决定
- **不猜型号** — 匹配失败就说失败

Smoking harms health. Reference material for adults only.

---

## 目录结构

```
cigar-skill/
├── SKILL.md                              主入口
├── skill-dependencies.json               依赖与功能降级清单
├── scripts/
│   ├── check_environment.py              环境自检：ready / partial / needs_setup
│   ├── build_index.py                    从 sitemap 生成 Cigar Century 索引
│   ├── lookup.py                         三段式查型号 + 抓参数
│   ├── fetch_domestic.py                 雪茄 123：中文库索引 / 检索 / 详情
│   ├── fetch_rating.py                   Cigar Aficionado：单页评分（价格原值转述）
│   ├── fetch_news.py                     halfwheel：新品，遇拦截则给出取用路径
│   └── fetch_capitol.py                  刷新离线术语库
├── references/
│   ├── capitol-index.md               全部 329 术语索引（含释义，供检索）
│   ├── storage-terms.md               19 · 养护与老化
│   ├── terroir.md                     33 · 产区与叶子特性
│   ├── leaf-varieties.md              39 · 茄衣/茄芯品种
│   ├── production-curing.md           36 · 发酵与生产（含 Plume vs Mold）
│   ├── anatomy.md                     36 · 结构：茄衣/茄套/茄芯
│   ├── flavour-tasting.md             20 · 强度、口感、余味
│   ├── setup-guide.md                 环境要求、五个站点、降级与恢复
│   ├── matching-rules.md              匹配铁律与失败案例
│   ├── data-sources.md                七站评估
│   ├── flavour-groups.md              气味组分盒
│   ├── defect-diagnosis.md           燃烧与结构故障：斜烧、隧道、堵塞
│   ├── drink-pairing.md              酒食搭配：按强度与风味组
│   └── personal-ledger.example.md     个人层模板
└── .gitignore
```

## License

MIT — see [LICENSE](LICENSE). Data belongs to the original publishers and is
reproduced only for lookup offline.
