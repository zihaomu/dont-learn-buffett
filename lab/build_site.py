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
RAW_DATA_GITHUB_URL = "https://github.com/zihaomu/dont-learn-buffett/tree/main/raw_data"
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


DECISION_PROFILES = [
    {
        "start": 1957,
        "end": 1964,
        "category": "partnership",
        "title": "合伙企业年度选择",
        "actual": "用相对收益和长期评价体系管理合伙资本",
        "thesis": "先定义什么叫正确表现，再让仓位、回撤和机会成本服从这个评价体系。",
        "temptation": "把短期战胜市场当成唯一目标",
        "temptation_risk": "短期排名会诱导更高换手和更高杠杆，反而破坏长期评价体系。",
        "macro": "战后美国扩张早期，消费社会、制造业利润和证券市场仍在重新定价。",
        "dollar": "布雷顿森林体系下美元仍锚定黄金，美元资产是战后资本秩序中心。",
        "tailwind": "美国本土企业、分散市场和信息效率不足，给小规模合伙资本留下了可挖掘空间。",
        "shock": "冷战、衰退和市场下跌让投资者持续面对周期风险。",
        "letter": "重点不是预测指数，而是用多年周期衡量相对表现、work-outs 和低估证券。",
    },
    {
        "start": 1965,
        "end": 1969,
        "category": "structure",
        "title": "载体与退出年度选择",
        "actual": "把资本载体从合伙企业推向 Berkshire，并在机会变少时收紧甚至退出",
        "thesis": "当环境不再适合原策略，真正重要的不是硬做，而是改变资本结构和机会标准。",
        "temptation": "为了维持过往收益继续扩大合伙企业",
        "temptation_risk": "资金规模和市场估值会吞掉早期优势，继续扩张反而会稀释判断质量。",
        "macro": "美国市场经历战后繁荣后估值上升，越战和通胀压力开始抬头。",
        "dollar": "布雷顿森林体系仍在，但美元外部约束和黄金兑换压力越来越明显。",
        "tailwind": "美国资本市场深度继续扩大，Berkshire 这样的公司载体开始承接长期资本配置。",
        "shock": "越战、财政压力和市场投机让长期资本开始面对更复杂的宏观环境。",
        "letter": "重点转向资本结构、机会稀缺、控制型投资和是否继续接受外部资金。",
    },
    {
        "start": 1970,
        "end": 1979,
        "category": "float",
        "title": "通胀与浮存金年度选择",
        "actual": "把重心从纺织和普通股票选择，转向保险浮存金、低估证券和资本再配置",
        "thesis": "通胀和熊市不是简单的买入信号，关键是能否拥有低成本、长期、可再配置的资金。",
        "temptation": "因为通胀恐惧追逐硬资产和热门宏观交易",
        "temptation_risk": "宏观交易看似解释一切，却很容易让投资者用价格波动代替企业价值判断。",
        "macro": "高通胀、石油冲击和熊市让美国投资者重新审视股票、债券和现金的真实购买力。",
        "dollar": "1971 年美元停止兑换黄金后，美元信用进入法币时代，通胀成为投资核心变量。",
        "tailwind": "美国仍拥有深厚资本市场和可收购企业，危机中低估资产开始出现。",
        "shock": "石油冲击、布雷顿森林瓦解和滞胀改变了投资者对安全资产的理解。",
        "letter": "重点是保险浮存金、低估证券、纺织业务困境和通胀对企业经济性的侵蚀。",
    },
    {
        "start": 1980,
        "end": 1989,
        "category": "franchise",
        "title": "品牌与特许经营年度选择",
        "actual": "用保险资金买入更持久的消费、媒体和金融特许经营权",
        "thesis": "从便宜资产进化到好生意合理价，核心是企业能否在通胀和竞争后仍保持定价权。",
        "temptation": "只按低市净率继续寻找烟蒂股",
        "temptation_risk": "便宜但衰退的资产可能长期吞噬资本，账面便宜不等于真实复利。",
        "macro": "Volcker 高利率压住通胀后，美国进入新一轮资本市场扩张。",
        "dollar": "强美元和全球资本回流强化了美国金融资产的中心地位。",
        "tailwind": "美国消费品牌、媒体网络和金融市场给高质量企业提供更长的复利跑道。",
        "shock": "高利率、1987 年股灾和全球资本流动让投资者反复面对估值与流动性冲击。",
        "letter": "重点是内在价值、特许经营权、保险浮存金成本，以及从烟蒂股向好公司的转变。",
    },
    {
        "start": 1990,
        "end": 1999,
        "category": "discipline",
        "title": "全球化与泡沫年度选择",
        "actual": "在全球化和科技泡沫中坚持能力圈，承认看不懂的高增长也可以不买",
        "thesis": "能力圈不是行业标签，而是能否解释现金流、竞争优势和价格之间的关系。",
        "temptation": "为了不落后纳斯达克而追逐科技叙事",
        "temptation_risk": "相对落后会制造强烈心理压力，但为了跟上泡沫而买入看不懂资产，可能破坏整个体系。",
        "macro": "冷战结束、全球化加速和互联网兴起改变了利润池和市场叙事。",
        "dollar": "美元资产在全球化中继续吸收资本，美国资本市场成为全球风险资产定价中心。",
        "tailwind": "美国企业开始从全球消费者、供应链和金融市场中获取更大范围的利润。",
        "shock": "日本泡沫破裂、亚洲金融危机和互联网泡沫让全球资本快速轮动。",
        "letter": "重点是能力圈、保险风险、并购纪律，以及在科技泡沫中承受相对落后的压力。",
    },
    {
        "start": 2000,
        "end": 2009,
        "category": "crisis",
        "title": "危机资本年度选择",
        "actual": "在泡沫破裂和金融危机中用 Berkshire 资产负债表提供稀缺资本",
        "thesis": "危机中真正稀缺的不是观点，而是长期信誉、流动性和可以迅速部署的资本。",
        "temptation": "在危机中彻底离场，等媒体确认安全后再回来",
        "temptation_risk": "等确定性出现时，价格和条款往往已经不再属于长期资本。",
        "macro": "互联网泡沫破裂、低利率、住房信贷扩张和 2008 年金融危机重塑市场。",
        "dollar": "美元体系在危机中承压，但也通过全球避险需求继续保持中心地位。",
        "tailwind": "美国市场允许强资产负债表在恐慌中以优先条款提供资本。",
        "shock": "9/11、次贷危机和全球金融危机让投资者重新认识杠杆、流动性和信用风险。",
        "letter": "重点是衍生品风险、保险承保纪律、现金储备和危机时的资本投放。",
    },
    {
        "start": 2010,
        "end": 2019,
        "category": "scale",
        "title": "规模约束年度选择",
        "actual": "承认规模约束，把全资业务、回购和平台型现金流纳入资本配置工具箱",
        "thesis": "当资本规模变大，能不能复制早期收益不是核心；核心是如何在更少机会中避免坏交易。",
        "temptation": "为了证明仍然灵活，追逐所有新经济热点",
        "temptation_risk": "规模越大，错误越贵；扩展能力圈必须来自商业理解，而不是行业焦虑。",
        "macro": "低利率、科技平台崛起和全球化成熟，让优质现金流资产估值持续抬升。",
        "dollar": "美元低利率和全球资本回流支撑大型美国企业融资、回购和估值。",
        "tailwind": "美国平台公司、消费品牌和资本市场机制把全球利润集中到少数企业。",
        "shock": "欧债危机、贸易摩擦和平台监管压力不断测试全球化利润池。",
        "letter": "重点是规模、现金、回购、全资业务，以及 Apple 这类成熟平台型公司的能力圈边界。",
    },
    {
        "start": 2020,
        "end": 2024,
        "category": "resilience",
        "title": "韧性与传承年度选择",
        "actual": "在疫情、通胀和传承阶段优先资产负债表韧性、现金和资本纪律",
        "thesis": "当世界变化速度超过判断速度，保持可选择性本身就是资本配置的一部分。",
        "temptation": "在极端行情中用全部现金押注单一宏观方向",
        "temptation_risk": "宏观判断即使方向正确，也可能因为时点、杠杆和流动性而失败。",
        "macro": "疫情冲击、财政刺激、通胀回归和高利率改变了资产估值基础。",
        "dollar": "美元在全球冲击中继续承担避险和结算中心角色，但通胀削弱现金购买力。",
        "tailwind": "美国企业盈利能力、能源安全、平台现金流和资本市场深度仍是 Berkshire 的主要土壤。",
        "shock": "疫情、供应链重组、地缘冲突和利率急升让投资者重新审视韧性。",
        "letter": "重点是现金、回购、能源、日本商社、Apple 仓位、Munger 遗产和接班结构。",
    },
]


def profile_for_year(year: int) -> dict:
    for profile in DECISION_PROFILES:
        if profile["start"] <= year <= profile["end"]:
            return profile
    return DECISION_PROFILES[-1]


def letter_pdf_url(year: int) -> str:
    return f"{RAW_DATA_GITHUB_URL}/primary/warren_buffett_letters/{year}.pdf"


def years_forward_summary(rows_by_year: dict[int, dict], year: int, key: str, label: str, horizon: int = 5) -> str:
    current = rows_by_year[year]
    end_year = min(year + horizon, max(rows_by_year))
    if end_year == year:
        return f"{label}的长期后验仍要等后续年报确认。"
    start_value = number(current[key])
    end_value = number(rows_by_year[end_year][key])
    if not start_value or not end_value:
        return f"{label}在 {year}-{end_year} 的可比数据不足。"
    gain = (end_value / start_value - 1) * 100
    return f"到 {end_year} 年，{label}路径约累计 {gain:.1f}%。"


def relative_sentence(row: dict) -> str:
    buffett = number(row["buffett_return_pct"])
    sp500 = number(row["sp500_price_return_pct"])
    if buffett is None or sp500 is None:
        return "相对收益没有完整可比数据。"
    diff = buffett - sp500
    direction = "领先" if diff >= 0 else "落后"
    return f"Buffett 当年 {pct(buffett)}，S&P 500 price {pct(sp500)}，{direction} {abs(diff):.1f} 个百分点。"


def build_annual_decisions(rows: list[dict], events: list[dict]) -> list[dict]:
    events_by_year = {int(event["year"]): event for event in events}
    rows_by_year = {int(row["year"]): row for row in rows}
    decisions = []
    for row in rows:
        year = int(row["year"])
        event = events_by_year.get(year)
        profile = profile_for_year(year)
        title = event["title"] if event else f"{year}：{profile['title']}"
        category = event["category"] if event else profile["category"]
        actual_title = event["title"] if event else profile["actual"]
        actual_thesis = event["real_lesson"] if event else profile["thesis"]
        verdict = event["verdict"] if event else f"这一年的核心不是照抄动作，而是在「{profile['title']}」中重新判断资本、价格和能力圈。"
        scene = event["scene_setting"] if event else (
            f"你站在 {year} 年末，只能看到当年的年报、市场价格和宏观压力，"
            f"不知道后面几年会发生什么。{relative_sentence(row)}"
        )
        reader_prompt = event["reader_decision"] if event else (
            "如果你负责 Berkshire 或一笔长期资本，你会追随市场、退回现金，"
            "还是继续按可解释的企业价值配置资本？"
        )
        hidden_condition = event["hidden_condition"] if event else profile["tailwind"]
        letter_focus = event["letter_focus"] if event else profile["letter"]
        world = event["world"] if event else profile["shock"]
        detail = event["detail"] if event else (
            f"{year} 年 Buffett 线收益为 {pct(row['buffett_return_pct'])}，"
            f"S&P 500 price 为 {pct(row['sp500_price_return_pct'])}，"
            f"Dow price 为 {pct(row['dow_price_return_pct'])}。"
        )
        actual_immediate = f"后验看，当年实际路径的结果是：{relative_sentence(row)}"
        actual_later = years_forward_summary(rows_by_year, year, "buffett_cumulative", "Buffett 实际")
        sp500_later = years_forward_summary(rows_by_year, year, "sp500_price_cumulative", "S&P 500 price")
        dow_later = years_forward_summary(rows_by_year, year, "dow_price_cumulative", "Dow price")
        options = [
            {
                "id": "actual",
                "title": actual_title,
                "thesis": actual_thesis,
                "immediate": actual_immediate,
                "later": actual_later,
                "actual": True,
            },
            {
                "id": "sp500",
                "title": "直接买入 S&P 500，放弃主动判断",
                "thesis": "这是一条普通人最容易执行的路线：承认自己无法复制 Buffett，把美国大盘作为默认选择。",
                "immediate": f"当年 S&P 500 price 收益为 {pct(row['sp500_price_return_pct'])}。",
                "later": sp500_later,
                "actual": False,
            },
            {
                "id": "cash",
                "title": "退回现金，等待更清晰的信号",
                "thesis": "当市场和宏观都不确定时，现金看起来最安全，但它也会持续暴露在通胀和机会成本下。",
                "immediate": "当年现金路径大致避免了股票波动，但也放弃了企业价值变化带来的收益。",
                "later": f"对照后验，{actual_later} 现金路径的机会成本取决于你能否在之后重新进入市场。",
                "actual": False,
            },
            {
                "id": "temptation",
                "title": profile["temptation"],
                "thesis": profile["temptation_risk"],
                "immediate": f"这条路短期可能更接近市场情绪；同年 Dow price 收益为 {pct(row['dow_price_return_pct'])}。",
                "later": dow_later,
                "actual": False,
            },
        ]
        rotate = year % len(options)
        options = options[rotate:] + options[:rotate]
        decisions.append(
            {
                "year": year,
                "slug": f"{year}-decision",
                "title": title,
                "category": category,
                "url": f"decisions/{year}.html",
                "key": bool(event),
                "verdict": verdict,
                "scene": scene,
                "reader_prompt": reader_prompt,
                "actual_title": actual_title,
                "actual_thesis": actual_thesis,
                "hidden_condition": hidden_condition,
                "letter_focus": letter_focus,
                "detail": detail,
                "world": world,
                "macro": event["macro_regime"] if event else profile["macro"],
                "dollar": event["dollar_context"] if event else profile["dollar"],
                "tailwind": event["america_tailwind"] if event else profile["tailwind"],
                "shock": event["global_shock"] if event else profile["shock"],
                "letter_url": letter_pdf_url(year),
                "event": event,
                "options": options,
            }
        )
    return decisions


def build_index(rows: list[dict], events: list[dict], manifest: dict) -> str:
    decisions = build_annual_decisions(rows, events)
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
    clean_decisions = []
    for decision in decisions:
        clean_decisions.append(
            {
                "year": decision["year"],
                "slug": decision["slug"],
                "title": decision["title"],
                "category": decision["category"],
                "verdict": decision["verdict"],
                "url": decision["url"],
                "key": decision["key"],
            }
        )

    final = clean_rows[-1]
    first = clean_rows[0]
    biggest_drawdown = min(clean_rows, key=lambda row: row["buffettReturn"] or 0)
    source_links = source_links_html(manifest)
    data_json = json.dumps(clean_rows, ensure_ascii=False)
    decisions_json = json.dumps(clean_decisions, ensure_ascii=False)

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
        <p class="hero-claim">这不是一份研究报表，而是一本活的书。每一年都把你带回当时的市场，让你先做选择，再看 Buffett 当时实际怎么做。</p>
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
        <p class="eyebrow">Decision rooms</p>
        <h2 id="events-title">年度决策现场</h2>
      </div>
      <div class="event-list">
        {events_list_html(decisions)}
      </div>
    </section>

    <section class="source-strip" aria-labelledby="sources-title">
      <h2 id="sources-title">主要资料</h2>
      <div class="source-links">{source_links}</div>
    </section>
  </main>

  <script>
    const DATA = {data_json};
    const EVENTS = {decisions_json};
{chart_js()}
  </script>
</body>
</html>
"""


def events_list_html(events: list[dict]) -> str:
    parts = []
    for event in events:
        marker = "重点年份" if event.get("key") else "年度现场"
        parts.append(
            f"""<a class="event-row" href="{html.escape(event['url'])}" id="year-{event['year']}">
  <span class="event-year">{event['year']}</span>
  <span class="event-copy">
    <strong>{html.escape(event['title'])}</strong>
    <small>{html.escape(event['verdict'])}</small>
  </span>
  <span class="event-category">{html.escape(marker)} / {html.escape(event['category'])}</span>
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


def decision_source_links(decision: dict, manifest: dict) -> str:
    links = [
        f"""<a href="{html.escape(decision['letter_url'])}" target="_blank" rel="noreferrer">{decision['year']} shareholder letter PDF</a>""",
        f"""<a href="{RAW_DATA_GITHUB_URL}" target="_blank" rel="noreferrer">完整 raw_data 原始资料库</a>""",
    ]
    event = decision.get("event")
    if event:
        source_map = {source["id"]: source for source in manifest["sources"]}
        for source_id in event["source_ids"].split(","):
            source_id = source_id.strip()
            if source_id and source_id in source_map:
                source = source_map[source_id]
                links.append(f"""<a href="{html.escape(source['url'])}" target="_blank" rel="noreferrer">{html.escape(source['title'])}</a>""")
    return "\n".join(links)


def choice_cards_html(options: list[dict]) -> str:
    cards = []
    labels = ["A", "B", "C", "D"]
    for label, option in zip(labels, options):
        actual = "true" if option["actual"] else "false"
        badge = '<span class="choice-badge">Buffett 实际选择</span>' if option["actual"] else '<span class="choice-badge muted">未选择路径</span>'
        cards.append(
            f"""<button class="choice-card" type="button" data-choice="{html.escape(option['id'])}" data-actual="{actual}" aria-pressed="false">
  <span class="choice-label">Option {label}</span>
  <strong>{html.escape(option['title'])}</strong>
  <p>{html.escape(option['thesis'])}</p>
  {badge}
  <span class="choice-result">
    <em>一年视角</em>{html.escape(option['immediate'])}
    <em>多年后验</em>{html.escape(option['later'])}
  </span>
</button>"""
        )
    return "\n".join(cards)


def phrase_spans(text: str) -> str:
    parts = []
    current = ""
    for char in text:
        current += char
        if char in "，。！？；":
            parts.append(current)
            current = ""
    if current:
        parts.append(current)
    return "".join(f"<span>{html.escape(part)}</span>" for part in parts)


def build_decision_page(decision: dict, row: dict, manifest: dict) -> str:
    source_links = decision_source_links(decision, manifest)
    option_cards = choice_cards_html(decision["options"])
    selected_note = "先选择一个方案。页面不会立即告诉你 Buffett 做了什么。"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{decision['year']} / {html.escape(decision['title'])} / {SITE_NAME}</title>
  <style>
{base_css()}
  </style>
</head>
<body class="decision-page">
  <header class="topbar">
    <a class="brand" href="../index.html#year-{decision['year']}">
      <span class="brand-mark"></span>
      <span>{SITE_NAME}</span>
    </a>
    <nav class="nav">
      <a href="../index.html#events">年度现场</a>
      <a href="../sources.html">资料来源</a>
      {github_link()}
    </nav>
  </header>
  <main class="decision-main">
    <section class="decision-hero">
      <p class="eyebrow">{html.escape(decision['category'])} / {decision['year']}</p>
      <h1>{html.escape(decision['title'])}</h1>
      <p class="event-impact">{phrase_spans(decision['scene'])}</p>
      <div class="event-stats">
        <div><span>Buffett 当年</span><strong>{pct(row['buffett_return_pct'])}</strong></div>
        <div><span>S&P 500 price</span><strong>{pct(row['sp500_price_return_pct'])}</strong></div>
        <div><span>Dow price</span><strong>{pct(row['dow_price_return_pct'])}</strong></div>
        <div><span>累计倍数</span><strong>{format_multiple(float(row['buffett_cumulative']))}</strong></div>
      </div>
    </section>
    <section class="decision-workspace" aria-labelledby="decision-title">
      <aside class="factor-panel">
        <p class="eyebrow">Known then</p>
        <h2>当时你能看到的因素</h2>
        <div class="factor-list">
          <div><span>宏观时代</span><p>{html.escape(decision['macro'])}</p></div>
          <div><span>美元背景</span><p>{html.escape(decision['dollar'])}</p></div>
          <div><span>美国红利</span><p>{html.escape(decision['tailwind'])}</p></div>
          <div><span>国际冲击</span><p>{html.escape(decision['shock'])}</p></div>
          <div><span>信件主线</span><p>{html.escape(decision['letter_focus'])}</p></div>
        </div>
        <div class="source-links decision-sources">{source_links}</div>
      </aside>
      <section class="choice-panel">
        <p class="eyebrow">Your move</p>
        <h2 id="decision-title">如果你站在 {decision['year']} 年，你会怎么选？</h2>
        <p class="choice-prompt">{html.escape(decision['reader_prompt'])}</p>
        <p class="choice-status" id="choiceStatus">{html.escape(selected_note)}</p>
        <div class="choice-grid">
          {option_cards}
        </div>
        <section class="reveal-panel" id="actualReveal" hidden>
          <p class="eyebrow">After your choice</p>
          <h2>Buffett 当时实际选择</h2>
          <strong>{html.escape(decision['actual_title'])}</strong>
          <p>{html.escape(decision['actual_thesis'])}</p>
          <h3>被隐藏的条件</h3>
          <p>{html.escape(decision['hidden_condition'])}</p>
          <h3>后验事实</h3>
          <p>{html.escape(decision['detail'])}</p>
          <h3>世界没有站在原地</h3>
          <p>{html.escape(decision['world'])}</p>
        </section>
      </section>
    </section>
  </main>
  <script>
{decision_js()}
  </script>
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
      <a href="index.html">阅读主线</a>
      {github_link()}
    </nav>
  </header>
  <main class="sources-main">
    <section>
      <p class="eyebrow">Raw data</p>
      <h1>资料来源与数据口径</h1>
      <a class="raw-data-link" href="{RAW_DATA_GITHUB_URL}" target="_blank" rel="noreferrer">
        <span>完整原始资料库</span>
        <strong>github.com/zihaomu/dont-learn-buffett/tree/main/raw_data</strong>
      </a>
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
  overflow-x: hidden;
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
  overflow-wrap: anywhere;
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
  overflow-wrap: anywhere;
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
.event-dot { fill: #111; stroke: #ffffff; stroke-width: 2; cursor: pointer; opacity: .78; }
.event-dot.key { fill: var(--rust); opacity: 1; }
.event-dot:hover, .event-dot:focus { stroke: var(--gold); stroke-width: 4; opacity: 1; outline: none; }
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
.notes, .macro-section, .event-section, .source-strip, .sources-main, .event-main, .decision-main {
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
  grid-template-columns: 86px minmax(0, 1fr) 172px;
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
.decision-main { width: min(1400px, 100%); }
.decision-main,
.decision-hero,
.decision-workspace,
.factor-panel,
.choice-panel {
  min-width: 0;
  max-width: 100%;
}
.raw-data-link {
  display: block;
  margin: 18px 0 22px;
  padding: 14px 0;
  border-top: 2px solid var(--ink);
  border-bottom: 1px solid var(--line);
  text-decoration: none;
}
.raw-data-link span {
  display: block;
  margin-bottom: 6px;
  color: var(--rust);
  font-size: 12px;
  font-weight: 900;
  text-transform: uppercase;
}
.raw-data-link strong {
  display: block;
  color: var(--ink);
  font-size: clamp(15px, 2vw, 20px);
  overflow-wrap: anywhere;
}
.raw-data-link:hover strong,
.raw-data-link:focus-visible strong {
  color: var(--green);
}
.raw-data-link:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 4px;
}
.event-article {
  padding-top: 28px;
}
.event-article h1 { font-size: clamp(38px, 7vw, 86px); }
.decision-hero h1 { font-size: clamp(36px, 6vw, 78px); }
.event-impact {
  width: 100%;
  max-width: 760px;
  color: var(--rust);
  font-size: 21px;
  font-weight: 850;
  line-height: 1.45;
  overflow-wrap: anywhere;
  word-break: break-word;
}
.event-impact span { display: inline; }
.decision-workspace {
  display: grid;
  grid-template-columns: minmax(280px, .92fr) minmax(0, 1.35fr);
  gap: 18px;
  align-items: start;
  margin-top: 22px;
}
.factor-panel,
.choice-panel {
  border-top: 1px solid var(--line);
  padding-top: 18px;
}
.factor-panel {
  position: sticky;
  top: 86px;
}
.factor-list {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}
.factor-list div {
  padding: 14px;
  border: 1px solid rgba(28,26,21,.14);
  border-radius: 8px;
  background: rgba(255,255,255,.64);
}
.factor-list span {
  display: block;
  margin-bottom: 8px;
  color: var(--rust);
  font-size: 12px;
  font-weight: 900;
  text-transform: uppercase;
}
.factor-list p,
.choice-prompt,
.choice-status {
  margin: 0;
  color: var(--muted);
  line-height: 1.6;
  overflow-wrap: anywhere;
}
.decision-sources { margin-top: 14px; }
.choice-panel h2 { font-size: clamp(24px, 3vw, 42px); }
.choice-prompt { margin-top: 10px; max-width: 780px; }
.choice-status {
  margin-top: 12px;
  color: var(--ink);
  font-weight: 800;
}
.choice-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}
.choice-card {
  display: block;
  width: 100%;
  min-height: 210px;
  padding: 15px;
  text-align: left;
  border: 1px solid rgba(28,26,21,.18);
  border-radius: 8px;
  background: var(--panel);
}
.choice-card:hover,
.choice-card:focus-visible {
  border-color: var(--focus);
  outline: none;
}
.choice-card.selected {
  border-color: var(--ink);
  box-shadow: inset 0 0 0 1px var(--ink);
}
.choice-card[data-actual="true"].selected,
body.choice-revealed .choice-card[data-actual="true"] {
  border-color: var(--green);
}
.choice-label,
.choice-badge,
.choice-result em {
  display: block;
  font-size: 12px;
  font-weight: 900;
  text-transform: uppercase;
}
.choice-label { color: var(--rust); margin-bottom: 8px; }
.choice-card strong {
  display: block;
  font-size: 18px;
  line-height: 1.32;
}
.choice-card p {
  margin: 10px 0 0;
  color: var(--muted);
  line-height: 1.55;
  overflow-wrap: anywhere;
}
.choice-badge {
  display: none;
  margin-top: 12px;
  color: var(--green);
}
.choice-badge.muted { color: var(--muted); }
.choice-result {
  display: none;
  margin-top: 12px;
  color: var(--ink);
  line-height: 1.55;
}
.choice-result em {
  margin: 10px 0 4px;
  color: var(--rust);
  font-style: normal;
}
body.choice-revealed .choice-badge,
body.choice-revealed .choice-result {
  display: block;
}
.reveal-panel {
  margin-top: 18px;
  padding: 18px;
  border: 1px solid rgba(20,122,99,.34);
  border-top: 4px solid var(--green);
  border-radius: 8px;
  background: rgba(255,255,255,.72);
}
.reveal-panel strong {
  display: block;
  margin-top: 8px;
  font-size: clamp(20px, 2.4vw, 32px);
  line-height: 1.2;
}
.reveal-panel h3 {
  margin: 18px 0 6px;
  font-size: 16px;
}
.reveal-panel p {
  margin: 8px 0 0;
  color: var(--muted);
  line-height: 1.65;
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
  .workbench, .notes, .macro-section, .event-section, .source-strip, .sources-main, .event-main, .decision-main { padding-left: 18px; padding-right: 18px; }
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
  .decision-workspace, .choice-grid { grid-template-columns: 1fr; }
  .factor-panel { position: static; }
}
@media (max-width: 520px) {
  h1 { font-size: 38px; }
  .event-impact { max-width: 100%; font-size: 18px; word-break: break-all; }
  .event-impact span { display: block; }
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


def decision_js() -> str:
    return r"""
    const cards = Array.from(document.querySelectorAll('.choice-card'));
    const reveal = document.getElementById('actualReveal');
    const status = document.getElementById('choiceStatus');

    for (const card of cards) {
      card.addEventListener('click', () => {
        document.body.classList.add('choice-revealed');
        for (const item of cards) {
          item.classList.toggle('selected', item === card);
          item.setAttribute('aria-pressed', item === card ? 'true' : 'false');
        }
        const selected = card.querySelector('strong')?.textContent || '这个方案';
        const actual = card.dataset.actual === 'true';
        status.textContent = actual
          ? `你选中了 Buffett 当时走的路：${selected}。`
          : `你选择的是另一条可能路径：${selected}。现在对照 Buffett 的实际选择。`;
        reveal.hidden = false;
      });
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
        const circle = make('circle', { class: event.key ? 'event-dot key' : 'event-dot', cx: x, cy: y, r: event.key ? 6 : 4, tabindex: 0, role: 'link', 'data-url': event.url, 'aria-label': `${event.year} ${event.title}` });
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
    decisions = build_annual_decisions(rows, events)
    rows_by_year = {int(row["year"]): row for row in rows}

    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "events").mkdir(parents=True, exist_ok=True)
    (SITE / "decisions").mkdir(parents=True, exist_ok=True)
    (SITE / "data").mkdir(parents=True, exist_ok=True)

    (SITE / "index.html").write_text(build_index(rows, events, manifest), encoding="utf-8")
    for event in events:
        (SITE / "events" / f"{event['slug']}.html").write_text(build_event_page(event, rows, manifest), encoding="utf-8")
    for decision in decisions:
        row = rows_by_year[decision["year"]]
        (SITE / "decisions" / f"{decision['year']}.html").write_text(build_decision_page(decision, row, manifest), encoding="utf-8")
    (SITE / "sources.html").write_text(build_sources_page(manifest), encoding="utf-8")

    shutil.copy2(PROCESSED / "returns.csv", SITE / "data" / "returns.csv")
    shutil.copy2(PROCESSED / "events.csv", SITE / "data" / "events.csv")
    (SITE / "data" / "decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.copy2(RAW / "source_manifest.json", SITE / "data" / "source_manifest.json")

    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(f"""<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=invest/"><title>{SITE_NAME}</title><a href="invest/">{SITE_NAME}</a>""", encoding="utf-8")
    print(f"Wrote static site to {SITE}")


if __name__ == "__main__":
    write_files()
