#!/usr/bin/env python3
"""
Build the static Don't Learn Buffett site from raw_data/processed.
"""

from __future__ import annotations

import csv
import html
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw_data"
PROCESSED = RAW / "processed"
OUT = ROOT / "html"
SITE = OUT / "invest"
SITE_NAME = "Don't Learn Buffett"
SITE_NAME_ZH = "别学巴菲特"
SITE_TAGLINE = "回到历史现场，重新做一次决定。"
SITE_TAGLINE_ZH = "回到历史现场，重新做一次决定。"
PROJECT_GITHUB_URL = "https://github.com/zihaomu/dont-learn-buffett"
RAW_LETTERS_GITHUB_URL = (
    "https://github.com/zihaomu/dont-learn-buffett/tree/main/"
    "raw_data/primary/warren_buffett_letters"
)


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def number(value: str | float | int) -> float | None:
    if value == "" or value is None:
        return None
    return float(value)


def format_multiple(value: float) -> str:
    if value >= 10000:
        return f"{value:,.0f}x"
    if value >= 100:
        return f"{value:,.1f}x"
    return f"{value:,.2f}x"


def pct(value: str | float | int) -> str:
    if value == "" or value is None:
        return "n/a"
    return f"{float(value):.1f}%"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def build_index(rows: list[dict], events: list[dict], manifest: dict) -> str:
    clean_rows = []
    for row in rows:
        clean_rows.append(
            {
                "year": int(row["year"]),
                "buffett": number(row["buffett_cumulative"]),
                "sp500": number(row["sp500_price_cumulative"]),
                "dow": number(row["dow_price_cumulative"]),
                "buffettReturn": number(row["buffett_return_pct"]),
                "sp500Return": number(row["sp500_price_return_pct"]),
                "dowReturn": number(row["dow_price_return_pct"]),
                "buffettSource": row["buffett_source"],
            }
        )
    clean_events = []
    for event in events:
        clean_events.append(
            {
                "year": int(event["year"]),
                "slug": event["slug"],
                "title": event["title"],
                "category": event["category"],
                "impact": event["impact"],
                "surfaceStory": event["surface_story"],
                "hiddenCondition": event["hidden_condition"],
                "mislearningRisk": event["mislearning_risk"],
                "realLesson": event["real_lesson"],
                "verdict": event["verdict"],
                "sceneSetting": event["scene_setting"],
                "readerDecision": event["reader_decision"],
                "shuToAvoid": event["shu_to_avoid"],
                "daoToLearn": event["dao_to_learn"],
                "macroRegime": event["macro_regime"],
                "dollarContext": event["dollar_context"],
                "americaTailwind": event["america_tailwind"],
                "globalShock": event["global_shock"],
                "letterFocus": event["letter_focus"],
                "world": event["world"],
                "url": f"events/{event['slug']}.html",
            }
        )

    final = clean_rows[-1]
    first = clean_rows[0]
    biggest_drawdown = min(clean_rows, key=lambda row: row["buffettReturn"] or 0)
    source_links = source_links_html(manifest)
    data_json = json.dumps(clean_rows, ensure_ascii=False)
    events_json = json.dumps(clean_events, ensure_ascii=False)

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{SITE_NAME} / {SITE_NAME_ZH}</title>
  <meta name="description" content="别学巴菲特。用数据、代码、股东信和年报证明：普通人学到的 Buffett 往往是最危险的 Buffett。">
  <style>
{base_css()}
  </style>
</head>
<body>
  <header class="topbar">
    <a class="brand" href="./" aria-label="{SITE_NAME} 首页">
      <span class="brand-mark"></span>
      <span>{SITE_NAME}</span>
    </a>
    <nav class="nav">
      <a href="#chart">阅读主线</a>
      <a href="#events">历史章节</a>
      <a href="sources.html">数据来源</a>
      <a href="data/returns.csv">CSV</a>
      {github_link()}
    </nav>
  </header>

  <main>
    <section class="workbench" id="chart" aria-labelledby="chart-title">
      <div class="chart-head">
        <div>
          <p class="eyebrow">1957-2024 / Data, code, letters</p>
          <h1 id="chart-title">{SITE_NAME}</h1>
          <p class="lede">{SITE_TAGLINE}</p>
          <p class="hero-claim">这不是一份研究报表，而是一本活的书。每一章把你带回当时的市场，让你先做判断，再看 Buffett 为什么能做出那个决断。</p>
        </div>
        <div class="controls" aria-label="图表控制">
          <button type="button" id="resetZoom">重置</button>
          <button type="button" id="toggleScale" aria-pressed="true">对数轴</button>
        </div>
      </div>

      <div class="proof-grid" aria-label="核心判断">
        <div class="proof-card">
          <span>命题</span>
          <strong>别急着复制 Buffett，先看清他当时拥有的条件。</strong>
        </div>
        <div class="proof-card">
          <span>读法</span>
          <strong>先回到历史现场，再问：如果我是 Buffett，我会怎么做？</strong>
        </div>
        <div class="proof-card">
          <span>证据</span>
          <strong>用收益曲线、股东信、年报和事件底稿还原每个决断。</strong>
        </div>
      </div>

      <div class="metrics" aria-label="累计收益概要">
        <div class="metric">
          <span>Buffett</span>
          <strong>{format_multiple(final["buffett"])}</strong>
          <small>{first["year"]} 的 1 到 2024</small>
        </div>
        <div class="metric">
          <span>S&P 500 price</span>
          <strong>{format_multiple(final["sp500"])}</strong>
          <small>不含股息，补齐至 2024</small>
        </div>
        <div class="metric">
          <span>Dow price</span>
          <strong>{format_multiple(final["dow"])}</strong>
          <small>不含股息，补齐至 2024</small>
        </div>
        <div class="metric">
          <span>最大单年回撤</span>
          <strong>{biggest_drawdown["year"]}</strong>
          <small>Buffett {biggest_drawdown["buffettReturn"]:.1f}%</small>
        </div>
      </div>

      <div class="chart-shell">
        <svg id="returnChart" role="img" aria-label="Buffett、S&P 500 和 Dow 的累计收益曲线"></svg>
        <div id="tooltip" class="tooltip" hidden></div>
      </div>

      <div class="legend" aria-label="图例">
        <span><i class="swatch buffett"></i>Buffett: 1957-1964 合伙企业，1965-2024 Berkshire 每股市值</span>
        <span><i class="swatch sp500"></i>S&P 500 price index</span>
        <span><i class="swatch dow"></i>Dow Jones price index</span>
        <span><i class="dot"></i>事件节点</span>
      </div>
    </section>

    <section class="notes" aria-labelledby="notes-title">
      <h2 id="notes-title">这本书怎么读</h2>
      <div class="note-grid">
        <p>不要先背结论。先把自己放回当时：信息不完整、市场在波动、别人也不知道未来。</p>
        <p>每一章都问同一个问题：如果你是 Buffett，你有没有同样的判断、资本结构、资金期限和心理承受力？</p>
        <p>最后再分清楚：哪些只是术，哪些才是道。术可以模仿，道必须理解。</p>
      </div>
    </section>

    <section class="macro-section" aria-labelledby="macro-title">
      <div class="section-head">
        <p class="eyebrow">One condition layer</p>
        <h2 id="macro-title">条件链的一环：美国、美元和国际局势</h2>
      </div>
      <div class="macro-grid">
        <div>
          <span>美国消费力</span>
          <p>Coca-Cola、GEICO、Apple、BNSF 背后不是抽象“好公司”，而是美国消费、汽车社会、平台生态和物流网络的长期扩张。</p>
        </div>
        <div>
          <span>美元体系</span>
          <p>美元购买力长期被通胀侵蚀，但美元资产、美元现金和美元信用给资产所有者、资本提供者和控股平台完全不同的位置。</p>
        </div>
        <div>
          <span>资本市场制度</span>
          <p>股东权益、信息披露、并购市场、回购文化、长期资金和全球利润回流，让美国股票不只是股票，而是一套制度红利。</p>
        </div>
        <div>
          <span>国际冲击</span>
          <p>石油危机、冷战、全球化、金融危机、疫情和高利率，不是背景噪音。它们不断改变谁拥有融资权、定价权和安全资产。</p>
        </div>
      </div>
    </section>

    <section class="event-section" id="events" aria-labelledby="events-title">
      <div class="section-head">
        <p class="eyebrow">Living chapters</p>
        <h2 id="events-title">历史章节</h2>
      </div>
      <div class="event-list">
        {events_list_html(events)}
      </div>
    </section>

    <section class="source-strip" aria-labelledby="sources-title">
      <h2 id="sources-title">主要资料</h2>
      <div class="source-links">{source_links}</div>
    </section>
  </main>

  <script>
    const DATA = {data_json};
    const EVENTS = {events_json};
{chart_js()}
  </script>
</body>
</html>
"""


def events_list_html(events: list[dict]) -> str:
    parts = []
    for event in events:
        parts.append(
            f"""<a class="event-row" href="events/{html.escape(event['slug'])}.html" id="year-{event['year']}">
  <span class="event-year">{event['year']}</span>
  <span class="event-copy">
    <strong>{html.escape(event['title'])}</strong>
    <small>{html.escape(event['verdict'])}</small>
  </span>
  <span class="event-category">{html.escape(event['category'])}</span>
</a>"""
        )
    return "\n".join(parts)


def source_links_html(manifest: dict) -> str:
    selected = [
        "warren_buffett_letters",
        "berkshire_2024_annual_report",
        "buffett_partnership_letters_ivey",
        "rbcpa_letters_index",
        "dow_sp500_github",
        "tang_tangshufang_context",
    ]
    sources = {source["id"]: source for source in manifest["sources"]}
    parts = []
    for source_id in selected:
        source = sources[source_id]
        parts.append(f"""<a href="{html.escape(source['url'])}" target="_blank" rel="noreferrer">{html.escape(source['title'])}</a>""")
    return "\n".join(parts)


def github_link() -> str:
    return f"""<a class="github-link" href="{PROJECT_GITHUB_URL}" target="_blank" rel="noreferrer" title="GitHub 项目主页" aria-label="GitHub 项目主页">
  <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
    <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.56 0-.28-.01-1.02-.02-2-3.2.7-3.88-1.54-3.88-1.54-.52-1.31-1.27-1.66-1.27-1.66-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.18 1.76 1.18 1.02 1.75 2.68 1.24 3.33.95.1-.74.4-1.24.73-1.53-2.55-.29-5.23-1.28-5.23-5.68 0-1.25.45-2.28 1.18-3.08-.12-.29-.51-1.46.11-3.04 0 0 .96-.31 3.15 1.18A10.9 10.9 0 0 1 12 5.55c.97 0 1.94.13 2.85.38C17.04 4.44 18 4.75 18 4.75c.62 1.58.23 2.75.11 3.04.73.8 1.18 1.83 1.18 3.08 0 4.42-2.69 5.39-5.25 5.67.41.35.78 1.05.78 2.12 0 1.53-.01 2.76-.01 3.14 0 .31.21.68.8.56A11.51 11.51 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5z"/>
  </svg>
</a>"""


def build_event_page(event: dict, rows: list[dict], manifest: dict) -> str:
    by_year = {int(row["year"]): row for row in rows}
    row = by_year[int(event["year"])]
    source_links = []
    source_map = {source["id"]: source for source in manifest["sources"]}
    for source_id in event["source_ids"].split(","):
        source_id = source_id.strip()
        if source_id and source_id in source_map:
            source = source_map[source_id]
            source_links.append(f"""<a href="{html.escape(source['url'])}" target="_blank" rel="noreferrer">{html.escape(source['title'])}</a>""")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(event['year'])} / {html.escape(event['title'])} / {SITE_NAME}</title>
  <style>
{base_css()}
  </style>
</head>
<body class="event-page">
  <header class="topbar">
    <a class="brand" href="../index.html#year-{event['year']}">
      <span class="brand-mark"></span>
      <span>{SITE_NAME}</span>
    </a>
    <nav class="nav">
      <a href="../index.html#chart">阅读主线</a>
      <a href="../sources.html">资料来源</a>
      {github_link()}
    </nav>
  </header>
  <main class="event-main">
    <article class="event-article">
      <p class="eyebrow">{html.escape(event['category'])} / {event['year']}</p>
      <h1>{html.escape(event['title'])}</h1>
      <p class="event-impact">{html.escape(event['verdict'])}</p>
      <div class="event-stats">
        <div><span>Buffett 当年</span><strong>{pct(row['buffett_return_pct'])}</strong></div>
        <div><span>S&P 500 price</span><strong>{pct(row['sp500_price_return_pct'])}</strong></div>
        <div><span>Dow price</span><strong>{pct(row['dow_price_return_pct'])}</strong></div>
        <div><span>累计倍数</span><strong>{format_multiple(float(row['buffett_cumulative']))}</strong></div>
      </div>
      <section>
        <h2>回到现场</h2>
        <p>{html.escape(event['scene_setting'])}</p>
      </section>
      <section class="decision-box">
        <h2>轮到你做决定</h2>
        <p>{html.escape(event['reader_decision'])}</p>
      </section>
      <section>
        <h2>表面故事</h2>
        <p>{html.escape(event['surface_story'])}</p>
      </section>
      <section>
        <h2>术的陷阱</h2>
        <p>{html.escape(event['shu_to_avoid'])}</p>
        <p>{html.escape(event['mislearning_risk'])}</p>
      </section>
      <section>
        <h2>道的部分</h2>
        <p>{html.escape(event['dao_to_learn'])}</p>
        <p>{html.escape(event['real_lesson'])}</p>
      </section>
      <section class="judgment">
        <h2>判决</h2>
        <p>{html.escape(event['verdict'])}</p>
      </section>
      <section>
        <h2>被隐藏的条件</h2>
        <p>{html.escape(event['hidden_condition'])}</p>
      </section>
      <section>
        <h2>宏观底稿</h2>
        <div class="macro-facts">
          <div>
            <span>宏观时代</span>
            <p>{html.escape(event['macro_regime'])}</p>
          </div>
          <div>
            <span>美元背景</span>
            <p>{html.escape(event['dollar_context'])}</p>
          </div>
          <div>
            <span>美国红利</span>
            <p>{html.escape(event['america_tailwind'])}</p>
          </div>
          <div>
            <span>国际冲击</span>
            <p>{html.escape(event['global_shock'])}</p>
          </div>
        </div>
      </section>
      <section>
        <h2>事实底稿</h2>
        <p>{html.escape(event['detail'])}</p>
      </section>
      <section>
        <h2>信件主线</h2>
        <p>{html.escape(event['letter_focus'])}</p>
      </section>
      <section>
        <h2>当年背景</h2>
        <p>{html.escape(event['world'])}</p>
      </section>
      <section>
        <h2>资料</h2>
        <div class="source-links">{''.join(source_links)}</div>
      </section>
    </article>
  </main>
</body>
</html>
"""


def build_sources_page(manifest: dict) -> str:
    source_items = []
    for source in manifest["sources"]:
        local = f"\n  <small>Local: {html.escape(source['local_path'])}</small>" if source["local_path"] else ""
        source_items.append(
            f"""<li>
  <a href="{html.escape(source['url'])}" target="_blank" rel="noreferrer">{html.escape(source['title'])}</a>
  <span>{html.escape(source['kind'])}</span>
  <p>{html.escape(source['note'])}</p>{local}
</li>"""
        )
    downloads = []
    for item in manifest["downloads"]:
        downloads.append(
            f"""<tr>
  <td>{html.escape(item['status'])}</td>
  <td>{html.escape(item['path'])}</td>
  <td>{html.escape(str(item.get('bytes', '')))}</td>
</tr>"""
        )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>资料来源 / {SITE_NAME}</title>
  <style>
{base_css()}
  </style>
</head>
<body>
  <header class="topbar">
    <a class="brand" href="index.html"><span class="brand-mark"></span><span>{SITE_NAME}</span></a>
    <nav class="nav">
      <a href="data/returns.csv">returns.csv</a>
      <a href="data/events.csv">events.csv</a>
      {github_link()}
    </nav>
  </header>
  <main class="sources-main">
    <section>
      <p class="eyebrow">Raw data</p>
      <h1>资料来源与数据口径</h1>
      <div class="note-grid">
        {''.join(f'<p>{html.escape(item)}</p>' for item in manifest['data_policy'])}
      </div>
      <h2>限制</h2>
      <ul class="plain-list">
        {''.join(f'<li>{html.escape(item)}</li>' for item in manifest['limitations'])}
      </ul>
      <h2>来源</h2>
      <ul class="source-list">{''.join(source_items)}</ul>
      <h2>本地下载</h2>
      <table class="download-table">
        <thead><tr><th>状态</th><th>路径</th><th>字节</th></tr></thead>
        <tbody>{''.join(downloads)}</tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


def base_css() -> str:
    return r"""
:root {
  --paper: #f6f6f3;
  --ink: #171717;
  --muted: #666b73;
  --line: #d4d8dd;
  --panel: #ffffff;
  --green: #147a63;
  --rust: #c1121f;
  --blue: #2457a6;
  --gold: #a97700;
  --black: #111111;
  --focus: #c1121f;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background:
    linear-gradient(90deg, rgba(193,18,31,.07), transparent 32%),
    var(--paper);
  color: var(--ink);
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
a { color: inherit; }
.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 62px;
  padding: 0 28px;
  border-bottom: 1px solid rgba(28, 26, 21, .16);
  background: rgba(246, 246, 243, .92);
  backdrop-filter: blur(14px);
}
.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  font-weight: 800;
}
.brand-mark {
  width: 18px;
  height: 18px;
  border: 3px solid var(--black);
  border-radius: 50%;
  box-shadow: 8px 0 0 var(--green), 16px 0 0 var(--rust);
}
.nav { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
.nav a {
  padding: 8px 10px;
  border-radius: 7px;
  text-decoration: none;
  font-size: 14px;
  color: var(--muted);
}
.nav a:hover, .nav a:focus-visible { background: rgba(28,26,21,.08); color: var(--ink); outline: none; }
.nav a.github-link {
  display: inline-flex;
  align-items: center;
  width: 38px;
  min-width: 38px;
  height: 38px;
  justify-content: center;
  padding: 0;
  border: 1px solid rgba(28,26,21,.18);
  background: rgba(255,255,255,.74);
  color: var(--ink);
}
.github-link svg {
  display: block;
  width: 20px;
  height: 20px;
  fill: currentColor;
}
.nav a.github-link:hover,
.nav a.github-link:focus-visible {
  border-color: rgba(28,26,21,.36);
  background: #fff;
  color: var(--ink);
}
main { width: min(1480px, 100%); margin: 0 auto; }
.workbench { padding: 34px 28px 18px; }
.chart-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 20px;
  align-items: end;
  margin-bottom: 18px;
}
.eyebrow {
  margin: 0 0 8px;
  color: var(--rust);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .08em;
  text-transform: uppercase;
}
h1, h2 {
  margin: 0;
  line-height: 1.05;
  letter-spacing: 0;
}
h1 { font-size: clamp(32px, 6vw, 82px); max-width: 1120px; }
h2 { font-size: clamp(24px, 3vw, 42px); }
.lede {
  margin: 14px 0 0;
  color: var(--ink);
  font-size: clamp(15px, 1.7vw, 20px);
  font-weight: 800;
  max-width: 780px;
}
.hero-claim {
  max-width: 880px;
  margin: 16px 0 0;
  color: var(--muted);
  font-size: clamp(17px, 2vw, 24px);
  line-height: 1.42;
}
.hero-claim.strong {
  color: var(--rust);
  font-weight: 900;
}
.proof-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin: 22px 0 18px;
}
.proof-card {
  min-height: 118px;
  padding: 16px;
  border: 1px solid var(--line);
  border-top: 4px solid var(--rust);
  border-radius: 8px;
  background: var(--panel);
}
.proof-card span {
  display: block;
  margin-bottom: 10px;
  color: var(--rust);
  font-size: 12px;
  font-weight: 900;
  text-transform: uppercase;
}
.proof-card strong {
  display: block;
  font-size: clamp(16px, 1.5vw, 20px);
  line-height: 1.35;
}
.controls { display: flex; gap: 8px; align-items: center; }
button {
  appearance: none;
  border: 1px solid rgba(28,26,21,.2);
  border-radius: 7px;
  background: var(--panel);
  color: var(--ink);
  min-height: 38px;
  padding: 0 13px;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}
button:hover, button:focus-visible { border-color: var(--focus); outline: none; }
.metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  margin: 18px 0;
}
.metric {
  padding: 14px 16px;
  min-width: 0;
  border-right: 1px solid var(--line);
}
.metric:last-child { border-right: 0; }
.metric span, .metric small { display: block; color: var(--muted); }
.metric span { font-size: 12px; font-weight: 800; text-transform: uppercase; }
.metric strong { display: block; margin: 4px 0; font-size: clamp(24px, 3vw, 40px); line-height: 1; }
.metric small { font-size: 13px; }
.chart-shell {
  position: relative;
  min-height: 520px;
  height: min(70vh, 720px);
  border: 1px solid rgba(28,26,21,.18);
  border-radius: 8px;
  background: linear-gradient(180deg, #ffffff 0%, #eef1f4 100%);
  overflow: hidden;
  touch-action: none;
}
#returnChart { display: block; width: 100%; height: 100%; cursor: grab; }
#returnChart.dragging { cursor: grabbing; }
.axis text { fill: var(--muted); font-size: 12px; }
.axis line, .axis path { stroke: rgba(28,26,21,.2); }
.grid line { stroke: rgba(28,26,21,.08); }
.series { fill: none; stroke-width: 3; stroke-linejoin: round; stroke-linecap: round; }
.series.buffett { stroke: var(--green); stroke-width: 4; }
.series.sp500 { stroke: var(--blue); }
.series.dow { stroke: var(--rust); }
.event-dot { fill: #111; stroke: #ffffff; stroke-width: 2; cursor: pointer; }
.event-dot:hover, .event-dot:focus { stroke: var(--gold); stroke-width: 4; outline: none; }
.tooltip {
  position: absolute;
  width: min(320px, calc(100vw - 42px));
  padding: 12px 14px;
  border: 1px solid rgba(28,26,21,.18);
  border-radius: 8px;
  background: #111111;
  color: #ffffff;
  pointer-events: none;
  box-shadow: 0 14px 28px rgba(28,26,21,.2);
}
.tooltip strong { display: block; font-size: 16px; margin-bottom: 5px; }
.tooltip span { display: inline-block; margin-bottom: 6px; color: #cbbd9c; font-size: 12px; text-transform: uppercase; }
.tooltip p { margin: 0; color: #eee6d4; font-size: 13px; line-height: 1.45; }
.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 18px;
  margin-top: 13px;
  color: var(--muted);
  font-size: 13px;
}
.legend span { display: inline-flex; align-items: center; gap: 7px; }
.swatch { display: inline-block; width: 20px; height: 3px; border-radius: 3px; }
.swatch.buffett { background: var(--green); }
.swatch.sp500 { background: var(--blue); }
.swatch.dow { background: var(--rust); }
.dot { width: 9px; height: 9px; border-radius: 50%; background: #111; display: inline-block; }
.notes, .macro-section, .event-section, .source-strip, .sources-main, .event-main {
  padding: 34px 28px;
}
.note-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
  margin-top: 16px;
}
.note-grid p {
  margin: 0;
  padding-top: 14px;
  border-top: 2px solid var(--line);
  color: var(--muted);
  line-height: 1.6;
}
.macro-section {
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}
.macro-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  margin-top: 18px;
  background: var(--line);
  border: 1px solid var(--line);
}
.macro-grid div,
.macro-facts div {
  background: var(--panel);
  padding: 16px;
}
.macro-grid span,
.macro-facts span {
  display: block;
  margin-bottom: 10px;
  color: var(--rust);
  font-size: 12px;
  font-weight: 900;
  text-transform: uppercase;
}
.macro-grid p,
.macro-facts p {
  margin: 0;
  color: var(--muted);
  line-height: 1.65;
}
.section-head { margin-bottom: 16px; }
.event-list {
  display: grid;
  border-top: 1px solid var(--line);
}
.event-row {
  display: grid;
  grid-template-columns: 86px minmax(0, 1fr) 132px;
  gap: 16px;
  align-items: center;
  min-height: 78px;
  padding: 14px 0;
  border-bottom: 1px solid var(--line);
  text-decoration: none;
}
.event-row:hover .event-copy strong, .event-row:focus-visible .event-copy strong { color: var(--green); }
.event-row:focus-visible { outline: 2px solid var(--focus); outline-offset: 3px; }
.event-year { font-size: 28px; font-weight: 900; }
.event-copy strong { display: block; font-size: 18px; margin-bottom: 4px; }
.event-copy small { color: var(--muted); line-height: 1.5; }
.event-category {
  justify-self: end;
  padding: 5px 8px;
  border: 1px solid rgba(28,26,21,.2);
  border-radius: 6px;
  color: var(--muted);
  font-size: 12px;
  text-transform: uppercase;
}
.source-strip {
  border-top: 1px solid var(--line);
  margin-bottom: 40px;
}
.source-links { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.source-links a {
  display: inline-flex;
  align-items: center;
  min-height: 36px;
  padding: 7px 10px;
  border: 1px solid rgba(28,26,21,.16);
  border-radius: 7px;
  color: var(--muted);
  text-decoration: none;
  background: rgba(255,255,255,.72);
}
.source-links a:hover, .source-links a:focus-visible { color: var(--ink); border-color: var(--focus); outline: none; }
.event-main, .sources-main { width: min(1040px, 100%); }
.event-article {
  padding-top: 28px;
}
.event-article h1 { font-size: clamp(38px, 7vw, 86px); }
.event-impact {
  max-width: 760px;
  color: var(--rust);
  font-size: 21px;
  font-weight: 850;
  line-height: 1.45;
}
.event-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  margin: 26px 0;
  background: var(--line);
  border: 1px solid var(--line);
}
.event-stats div {
  background: var(--paper);
  padding: 14px;
}
.event-stats span { display: block; color: var(--muted); font-size: 12px; font-weight: 800; text-transform: uppercase; }
.event-stats strong { display: block; margin-top: 5px; font-size: 28px; }
.event-article section {
  border-top: 1px solid var(--line);
  padding: 24px 0;
}
.event-article section.decision-box {
  padding: 26px 20px;
  border: 2px solid var(--ink);
  border-radius: 8px;
  background: #fff;
}
.event-article section.decision-box h2 {
  color: var(--ink);
}
.event-article section.decision-box p {
  color: var(--ink);
  font-size: 21px;
  font-weight: 850;
  line-height: 1.5;
}
.event-article section.judgment {
  padding: 26px 20px;
  border: 2px solid var(--rust);
  border-radius: 8px;
  background: #fff;
}
.event-article section.judgment h2 {
  color: var(--rust);
}
.event-article section.judgment p {
  color: var(--ink);
  font-size: 22px;
  font-weight: 900;
  line-height: 1.45;
}
.macro-facts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1px;
  background: var(--line);
  border: 1px solid var(--line);
}
.event-article section h2, .sources-main h2 { font-size: 24px; margin-bottom: 12px; }
.event-article section p, .plain-list, .source-list p {
  color: var(--muted);
  line-height: 1.7;
  font-size: 17px;
}
.plain-list { padding-left: 20px; }
.source-list {
  list-style: none;
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--line);
}
.source-list li {
  padding: 16px 0;
  border-bottom: 1px solid var(--line);
}
.source-list a { font-weight: 800; }
.source-list span {
  display: inline-flex;
  margin-left: 8px;
  color: var(--rust);
  font-size: 12px;
  text-transform: uppercase;
}
.source-list small { display: block; color: var(--muted); }
.download-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.download-table th, .download-table td {
  text-align: left;
  padding: 9px 8px;
  border-bottom: 1px solid var(--line);
  vertical-align: top;
}
.download-table th { color: var(--muted); font-size: 12px; text-transform: uppercase; }
@media (max-width: 860px) {
  .topbar { align-items: flex-start; gap: 10px; flex-direction: column; padding: 12px 18px; }
  .nav { justify-content: flex-start; }
  .workbench, .notes, .macro-section, .event-section, .source-strip, .sources-main, .event-main { padding-left: 18px; padding-right: 18px; }
  .chart-head { grid-template-columns: 1fr; }
  .proof-grid { grid-template-columns: 1fr; }
  .macro-grid { grid-template-columns: 1fr; }
  .macro-facts { grid-template-columns: 1fr; }
  .controls { justify-content: flex-start; }
  .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .metric:nth-child(2) { border-right: 0; }
  .metric:nth-child(1), .metric:nth-child(2) { border-bottom: 1px solid var(--line); }
  .chart-shell { min-height: 460px; height: 62vh; }
  .note-grid { grid-template-columns: 1fr; }
  .event-row { grid-template-columns: 72px minmax(0, 1fr); }
  .event-category { grid-column: 2; justify-self: start; }
  .event-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 520px) {
  h1 { font-size: 38px; }
  .metrics, .event-stats { grid-template-columns: 1fr; }
  .metric { border-right: 0; border-bottom: 1px solid var(--line); }
  .metric:last-child { border-bottom: 0; }
  .event-row { grid-template-columns: 1fr; gap: 6px; }
  .event-category { grid-column: 1; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
}
"""


def chart_js() -> str:
    return r"""
    const svg = document.getElementById('returnChart');
    const tooltip = document.getElementById('tooltip');
    const resetButton = document.getElementById('resetZoom');
    const scaleButton = document.getElementById('toggleScale');
    const state = {
      xDomain: [1957, 2024],
      yDomain: [0.65, Math.max(...DATA.map(d => d.buffett)) * 1.18],
      log: true,
      dragging: false,
      last: null
    };
    const ns = 'http://www.w3.org/2000/svg';
    const rowByYear = new Map(DATA.map(d => [d.year, d]));
    const eventByYear = new Map(EVENTS.map(d => [d.year, d]));

    function clearSvg() {
      while (svg.firstChild) svg.removeChild(svg.firstChild);
    }

    function dims() {
      const box = svg.getBoundingClientRect();
      const width = Math.max(340, box.width);
      const height = Math.max(420, box.height);
      const margin = { top: 28, right: 28, bottom: 46, left: width < 640 ? 54 : 76 };
      return { width, height, margin, innerW: width - margin.left - margin.right, innerH: height - margin.top - margin.bottom };
    }

    function xScale(year, d) {
      return d.margin.left + (year - state.xDomain[0]) / (state.xDomain[1] - state.xDomain[0]) * d.innerW;
    }

    function yTransform(value) {
      return state.log ? Math.log10(Math.max(value, 0.0001)) : value;
    }

    function yUntransform(value) {
      return state.log ? Math.pow(10, value) : value;
    }

    function yScale(value, d) {
      const min = yTransform(state.yDomain[0]);
      const max = yTransform(state.yDomain[1]);
      const current = yTransform(value);
      return d.margin.top + (max - current) / (max - min) * d.innerH;
    }

    function make(tag, attrs = {}) {
      const el = document.createElementNS(ns, tag);
      for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
      return el;
    }

    function pathFor(key, d) {
      const points = DATA.filter(row => row[key] && row.year >= state.xDomain[0] - 1 && row.year <= state.xDomain[1] + 1)
        .map(row => [xScale(row.year, d), yScale(row[key], d)]);
      return points.map((point, idx) => `${idx === 0 ? 'M' : 'L'}${point[0].toFixed(2)},${point[1].toFixed(2)}`).join(' ');
    }

    function xTicks() {
      const span = state.xDomain[1] - state.xDomain[0];
      const step = span <= 12 ? 1 : span <= 28 ? 4 : span <= 48 ? 8 : 10;
      const start = Math.ceil(state.xDomain[0] / step) * step;
      const ticks = [];
      for (let year = start; year <= state.xDomain[1]; year += step) ticks.push(year);
      return ticks;
    }

    function yTicks() {
      if (!state.log) {
        const max = state.yDomain[1];
        const raw = [1, 10, 100, 1000, 10000, 100000, 500000].filter(v => v >= state.yDomain[0] && v <= max);
        return raw.length ? raw : [state.yDomain[0], state.yDomain[1]];
      }
      const minPow = Math.floor(Math.log10(state.yDomain[0]));
      const maxPow = Math.ceil(Math.log10(state.yDomain[1]));
      const ticks = [];
      for (let p = minPow; p <= maxPow; p++) {
        for (const m of [1, 2, 5]) {
          const value = m * Math.pow(10, p);
          if (value >= state.yDomain[0] && value <= state.yDomain[1]) ticks.push(value);
        }
      }
      return ticks;
    }

    function tickLabel(value) {
      if (value >= 100000) return `${Math.round(value / 1000)}k`;
      if (value >= 1000) return `${Math.round(value).toLocaleString()}`;
      if (value >= 10) return `${Math.round(value)}`;
      if (value >= 1) return value.toFixed(value < 2 ? 1 : 0);
      return value.toFixed(1);
    }

    function renderAxes(d) {
      const grid = make('g', { class: 'grid' });
      for (const year of xTicks()) {
        const x = xScale(year, d);
        grid.appendChild(make('line', { x1: x, x2: x, y1: d.margin.top, y2: d.margin.top + d.innerH }));
      }
      for (const value of yTicks()) {
        const y = yScale(value, d);
        grid.appendChild(make('line', { x1: d.margin.left, x2: d.margin.left + d.innerW, y1: y, y2: y }));
      }
      svg.appendChild(grid);

      const axis = make('g', { class: 'axis' });
      axis.appendChild(make('line', { x1: d.margin.left, x2: d.margin.left + d.innerW, y1: d.margin.top + d.innerH, y2: d.margin.top + d.innerH }));
      axis.appendChild(make('line', { x1: d.margin.left, x2: d.margin.left, y1: d.margin.top, y2: d.margin.top + d.innerH }));
      for (const year of xTicks()) {
        const x = xScale(year, d);
        axis.appendChild(make('line', { x1: x, x2: x, y1: d.margin.top + d.innerH, y2: d.margin.top + d.innerH + 6 }));
        const text = make('text', { x, y: d.margin.top + d.innerH + 24, 'text-anchor': 'middle' });
        text.textContent = String(year);
        axis.appendChild(text);
      }
      for (const value of yTicks()) {
        const y = yScale(value, d);
        axis.appendChild(make('line', { x1: d.margin.left - 6, x2: d.margin.left, y1: y, y2: y }));
        const text = make('text', { x: d.margin.left - 10, y: y + 4, 'text-anchor': 'end' });
        text.textContent = `${tickLabel(value)}x`;
        axis.appendChild(text);
      }
      const label = make('text', { x: d.margin.left, y: 18, fill: '#6f675a', 'font-size': 12 });
      label.textContent = '累计倍数';
      axis.appendChild(label);
      svg.appendChild(axis);
    }

    function renderLines(d) {
      const group = make('g');
      group.appendChild(make('path', { class: 'series buffett', d: pathFor('buffett', d) }));
      group.appendChild(make('path', { class: 'series sp500', d: pathFor('sp500', d) }));
      group.appendChild(make('path', { class: 'series dow', d: pathFor('dow', d) }));
      svg.appendChild(group);
    }

    function renderEvents(d) {
      const group = make('g');
      for (const event of EVENTS) {
        const row = rowByYear.get(event.year);
        if (!row || event.year < state.xDomain[0] || event.year > state.xDomain[1]) continue;
        const x = xScale(event.year, d);
        const y = yScale(row.buffett, d);
        const circle = make('circle', { class: 'event-dot', cx: x, cy: y, r: 6, tabindex: 0, role: 'link', 'data-url': event.url, 'aria-label': `${event.year} ${event.title}` });
        circle.addEventListener('mouseenter', () => showTooltip(event, row, x, y, d));
        circle.addEventListener('mouseleave', hideTooltip);
        circle.addEventListener('focus', () => showTooltip(event, row, x, y, d));
        circle.addEventListener('blur', hideTooltip);
        circle.addEventListener('click', () => { window.location.href = event.url; });
        circle.addEventListener('keydown', e => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            window.location.href = event.url;
          }
        });
        group.appendChild(circle);
      }
      svg.appendChild(group);
    }

    function showTooltip(event, row, x, y, d) {
      tooltip.hidden = false;
      tooltip.innerHTML = `<span>${event.year} / ${event.category}</span><strong>${event.title}</strong><p>${event.verdict}</p><p>Buffett 当年 ${row.buffettReturn.toFixed(1)}%，累计 ${tickLabel(row.buffett)}x</p>`;
      const box = svg.getBoundingClientRect();
      const tip = tooltip.getBoundingClientRect();
      let left = x + 18;
      let top = y - tip.height - 16;
      if (left + tip.width > box.width) left = x - tip.width - 18;
      if (top < 10) top = y + 18;
      tooltip.style.left = `${Math.max(10, left)}px`;
      tooltip.style.top = `${Math.max(10, top)}px`;
    }

    function hideTooltip() {
      tooltip.hidden = true;
    }

    function render() {
      const d = dims();
      svg.setAttribute('viewBox', `0 0 ${d.width} ${d.height}`);
      clearSvg();
      renderAxes(d);
      renderLines(d);
      renderEvents(d);
    }

    function clampDomains() {
      const span = state.xDomain[1] - state.xDomain[0];
      if (span < 3) {
        const center = (state.xDomain[0] + state.xDomain[1]) / 2;
        state.xDomain = [center - 1.5, center + 1.5];
      }
      if (span > 68) state.xDomain = [1957, 2024];
      if (state.xDomain[0] < 1957) {
        state.xDomain[1] += 1957 - state.xDomain[0];
        state.xDomain[0] = 1957;
      }
      if (state.xDomain[1] > 2024) {
        state.xDomain[0] -= state.xDomain[1] - 2024;
        state.xDomain[1] = 2024;
      }
      state.yDomain[0] = Math.max(0.08, state.yDomain[0]);
      state.yDomain[1] = Math.min(Math.max(...DATA.map(d => d.buffett)) * 4, state.yDomain[1]);
      if (state.yDomain[1] / state.yDomain[0] < 1.4) {
        const mid = Math.sqrt(state.yDomain[0] * state.yDomain[1]);
        state.yDomain = [mid / 1.2, mid * 1.2];
      }
    }

    svg.addEventListener('wheel', e => {
      e.preventDefault();
      const d = dims();
      const rect = svg.getBoundingClientRect();
      const px = Math.min(1, Math.max(0, (e.clientX - rect.left - d.margin.left) / d.innerW));
      const py = Math.min(1, Math.max(0, (e.clientY - rect.top - d.margin.top) / d.innerH));
      const factor = e.deltaY > 0 ? 1.16 : 0.86;
      const xAt = state.xDomain[0] + px * (state.xDomain[1] - state.xDomain[0]);
      state.xDomain = [
        xAt - (xAt - state.xDomain[0]) * factor,
        xAt + (state.xDomain[1] - xAt) * factor
      ];
      const yMin = yTransform(state.yDomain[0]);
      const yMax = yTransform(state.yDomain[1]);
      const yAt = yMax - py * (yMax - yMin);
      const nextMin = yAt - (yAt - yMin) * factor;
      const nextMax = yAt + (yMax - yAt) * factor;
      state.yDomain = [yUntransform(nextMin), yUntransform(nextMax)];
      clampDomains();
      hideTooltip();
      render();
    }, { passive: false });

    svg.addEventListener('pointerdown', e => {
      state.dragging = true;
      state.last = { x: e.clientX, y: e.clientY };
      svg.classList.add('dragging');
      svg.setPointerCapture(e.pointerId);
    });

    svg.addEventListener('pointermove', e => {
      if (!state.dragging) return;
      const d = dims();
      const dx = e.clientX - state.last.x;
      const dy = e.clientY - state.last.y;
      state.last = { x: e.clientX, y: e.clientY };
      const xSpan = state.xDomain[1] - state.xDomain[0];
      const xMove = -dx / d.innerW * xSpan;
      state.xDomain = [state.xDomain[0] + xMove, state.xDomain[1] + xMove];
      const yMin = yTransform(state.yDomain[0]);
      const yMax = yTransform(state.yDomain[1]);
      const ySpan = yMax - yMin;
      const yMove = dy / d.innerH * ySpan;
      state.yDomain = [yUntransform(yMin + yMove), yUntransform(yMax + yMove)];
      clampDomains();
      hideTooltip();
      render();
    });

    svg.addEventListener('pointerup', e => {
      state.dragging = false;
      state.last = null;
      svg.classList.remove('dragging');
      try { svg.releasePointerCapture(e.pointerId); } catch (_) {}
    });

    resetButton.addEventListener('click', () => {
      state.xDomain = [1957, 2024];
      state.yDomain = [0.65, Math.max(...DATA.map(d => d.buffett)) * 1.18];
      hideTooltip();
      render();
    });

    scaleButton.addEventListener('click', () => {
      state.log = !state.log;
      scaleButton.textContent = state.log ? '对数轴' : '线性轴';
      scaleButton.setAttribute('aria-pressed', String(state.log));
      state.yDomain = state.log ? [0.65, Math.max(...DATA.map(d => d.buffett)) * 1.18] : [0, Math.max(...DATA.map(d => d.buffett)) * 1.06];
      hideTooltip();
      render();
    });

    const resizeObserver = new ResizeObserver(render);
    resizeObserver.observe(svg.parentElement);
    render();
"""


def write_files() -> None:
    rows = read_csv(PROCESSED / "returns.csv")
    events = read_csv(PROCESSED / "events.csv")
    manifest = json.loads((RAW / "source_manifest.json").read_text(encoding="utf-8"))

    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "events").mkdir(parents=True, exist_ok=True)
    (SITE / "data").mkdir(parents=True, exist_ok=True)

    (SITE / "index.html").write_text(build_index(rows, events, manifest), encoding="utf-8")
    for event in events:
        (SITE / "events" / f"{event['slug']}.html").write_text(build_event_page(event, rows, manifest), encoding="utf-8")
    (SITE / "sources.html").write_text(build_sources_page(manifest), encoding="utf-8")

    shutil.copy2(PROCESSED / "returns.csv", SITE / "data" / "returns.csv")
    shutil.copy2(PROCESSED / "events.csv", SITE / "data" / "events.csv")
    shutil.copy2(RAW / "source_manifest.json", SITE / "data" / "source_manifest.json")

    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(f"""<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=invest/"><title>{SITE_NAME}</title><a href="invest/">{SITE_NAME}</a>""", encoding="utf-8")
    print(f"Wrote static site to {SITE}")


if __name__ == "__main__":
    write_files()
