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
| 长白毛是发霉还是开花？ | 引 Cigar Capitol 的判据，离线可答 |
| 这盒能不能和其他茄放一起？ | 按茄衣判气味组和湿度目标 |
| 我的柜子里有多少支、该怎么安排？ | 需先配置 `personal-ledger.md`，见下 |

Bilingual output is the default: 「Plasencia Alma Fuerte Sixto II Hexagono（六边形）」，not just「普拉森西亚 六边形」。Cigar names do not translate cleanly and losing the English string makes the cigar unsearchable.

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
cd ~/.workbuddy/skills/cigar-skill
python3 scripts/build_index.py
```

That downloads the sitemap and writes `data/brands.txt` (4,757 brands) and
`data/cigars.txt` (19,191 cigars). The indexes are gitignored — they are derived
data and go stale.

## 用法

```bash
# 查型号
python3 scripts/lookup.py --brand "奥利瓦 Oliva" --model "Serie V Melanio Robusto"

# 抓已知型号的完整参数
python3 scripts/lookup.py --url "https://www.cigarcentury.com/en/cigars/oliva-serie-v-melanio-robusto"

# 检查索引是否就绪
python3 scripts/lookup.py --check
```

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
| [Cigar Century](https://www.cigarcentury.com) | Primary | 19,191 型号参数库 |
| [Cigar Capitol](https://cigarcapitol.com) | Primary | 329 术语 · 26 产区 · 每条标注置信度 |
| [Cigar Aficionado](https://www.cigaraficionado.com) | Secondary | 权威 100 分制评分与品鉴笔记 |
| [雪茄 123](https://www.xuejia123.com) | Secondary | 唯一中文源；国产茄唯一去处（须过滤 SEO 稿） |
| [halfwheel](https://halfwheel.com) | Secondary | 行业新品与官方定价动态 |
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

有一处例外值得知道：`references/flavour-groups.md` 含作者的 7 组分盒方法论，
包括每组的盒数。这是刻意要分享的部分，而非泄漏。若你希望它也私有，把那几张表
移进 `references/personal-ledger.md` —— 该文件已被 gitignored。

Before pushing, read `git diff` and check what actually ships.

If you fork this, keep that boundary. Do not commit your own ledger path.

---

## 边界

这个 Skill 不做以下事情：

- **不提供购买建议、商家或链接** — `lookup.py` 主动剔除价格字段
- **不出具真伪结论** — 只给判据和可观察检查
- **不写你的台账** — 只出建议草稿，由你决定
- **不猜型号** — 匹配失败就说失败

Smoking harms health. Reference material for adults only.

---

## 目录结构

```
cigar-skill/
├── SKILL.md                              主入口
├── scripts/
│   ├── build_index.py                    从 sitemap 生成索引
│   ├── lookup.py                         三段式查型号 + 抓参数
│   └── fetch_capitol.py                  刷新离线术语库
├── references/
│   ├── matching-rules.md                 匹配铁律与失败案例
│   ├── data-sources.md                   七站评估
│   ├── flavour-groups.md                 气味组分盒
│   ├── storage-terms.md                  19 条养护术语（离线）
│   ├── terroir.md                        14 个产区（离线）
│   └── personal-ledger.example.md        个人层模板
└── .gitignore
```

## License

MIT — see [LICENSE](LICENSE). Data belongs to the original publishers and is
reproduced only for lookup offline.
