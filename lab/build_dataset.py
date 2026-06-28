#!/usr/bin/env python3
"""
Collect source files and build normalized data for Don't Learn Buffett.

Outputs live under raw_data/:
- primary/: downloaded primary-source files where stable direct downloads exist
- market_indices_raw/: raw S&P 500 and Dow daily CSV files
- processed/: normalized annual return and event CSV/JSON files
- source_manifest.json / sources.md: source map and known limitations
"""

from __future__ import annotations

import csv
import json
import math
import os
import shutil
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime
from datetime import timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw_data"
PRIMARY = RAW / "primary"
MARKET_RAW = RAW / "market_indices_raw"
PROCESSED = RAW / "processed"

USER_AGENT = "Mozilla/5.0 DontLearnBuffettResearch/1.0"

CANONICAL_LETTERS_DIR = PRIMARY / "warren_buffett_letters"
CANONICAL_LETTERS_GITHUB_URL = (
    "https://github.com/zihaomu/dont-learn-buffett/tree/main/"
    "raw_data/primary/warren_buffett_letters"
)


PARTNERSHIP_RETURNS = {
    1957: 10.4,
    1958: 40.9,
    1959: 25.9,
    1960: 22.8,
    1961: 45.9,
    1962: 13.9,
    1963: 38.7,
    1964: 27.8,
}


BERKSHIRE_RETURNS = {
    1965: 49.5,
    1966: -3.4,
    1967: 13.3,
    1968: 77.8,
    1969: 19.4,
    1970: -4.6,
    1971: 80.5,
    1972: 8.1,
    1973: -2.5,
    1974: -48.7,
    1975: 2.5,
    1976: 129.3,
    1977: 46.8,
    1978: 14.5,
    1979: 102.5,
    1980: 32.8,
    1981: 31.8,
    1982: 38.4,
    1983: 69.0,
    1984: -2.7,
    1985: 93.7,
    1986: 14.2,
    1987: 4.6,
    1988: 59.3,
    1989: 84.6,
    1990: -23.1,
    1991: 35.6,
    1992: 29.8,
    1993: 38.9,
    1994: 25.0,
    1995: 57.4,
    1996: 6.2,
    1997: 34.9,
    1998: 52.2,
    1999: -19.9,
    2000: 26.6,
    2001: 6.5,
    2002: -3.8,
    2003: 15.8,
    2004: 4.3,
    2005: 0.8,
    2006: 24.1,
    2007: 28.7,
    2008: -31.8,
    2009: 2.7,
    2010: 21.4,
    2011: -4.7,
    2012: 16.8,
    2013: 32.7,
    2014: 27.0,
    2015: -12.5,
    2016: 23.4,
    2017: 21.9,
    2018: 2.8,
    2019: 11.0,
    2020: 2.4,
    2021: 29.6,
    2022: 4.0,
    2023: 15.8,
    2024: 25.5,
}


SP500_TOTAL_RETURNS_FROM_BERKSHIRE = {
    1965: 10.0,
    1966: -11.7,
    1967: 30.9,
    1968: 11.0,
    1969: -8.4,
    1970: 3.9,
    1971: 14.6,
    1972: 18.9,
    1973: -14.8,
    1974: -26.4,
    1975: 37.2,
    1976: 23.6,
    1977: -7.4,
    1978: 6.4,
    1979: 18.2,
    1980: 32.3,
    1981: -5.0,
    1982: 21.4,
    1983: 22.4,
    1984: 6.1,
    1985: 31.6,
    1986: 18.6,
    1987: 5.1,
    1988: 16.6,
    1989: 31.7,
    1990: -3.1,
    1991: 30.5,
    1992: 7.6,
    1993: 10.1,
    1994: 1.3,
    1995: 37.6,
    1996: 23.0,
    1997: 33.4,
    1998: 28.6,
    1999: 21.0,
    2000: -9.1,
    2001: -11.9,
    2002: -22.1,
    2003: 28.7,
    2004: 10.9,
    2005: 4.9,
    2006: 15.8,
    2007: 5.5,
    2008: -37.0,
    2009: 26.5,
    2010: 15.1,
    2011: 2.1,
    2012: 16.0,
    2013: 32.4,
    2014: 13.7,
    2015: 1.4,
    2016: 12.0,
    2017: 21.8,
    2018: -4.4,
    2019: 31.5,
    2020: 18.4,
    2021: 28.7,
    2022: -18.1,
    2023: 26.3,
    2024: 25.0,
}


SOURCES = [
    {
        "id": "berkshire_letters_index",
        "kind": "primary",
        "title": "Berkshire Hathaway shareholder letters index",
        "url": "https://www.berkshirehathaway.com/letters/letters.html",
        "local_path": "",
        "note": "Official index for shareholder letters. Local letter PDFs are consolidated in the public raw archive instead of duplicate source folders.",
    },
    {
        "id": "berkshire_2024_annual_report",
        "kind": "primary",
        "title": "Berkshire Hathaway 2024 Annual Report",
        "url": "https://www.berkshirehathaway.com/2024ar/2024ar.pdf",
        "local_path": "primary/berkshire_2024_annual_report.pdf",
        "note": "Source for 1965-2024 Berkshire vs. S&P 500 annual percentage table.",
    },
    {
        "id": "warren_buffett_letters",
        "kind": "primary",
        "title": "Warren Buffett letters raw archive",
        "url": CANONICAL_LETTERS_GITHUB_URL,
        "local_path": "primary/warren_buffett_letters/",
        "note": "Canonical public raw archive. Includes one PDF per year from 1957-2024 plus early partnership H1/midyear letters.",
    },
    {
        "id": "buffett_partnership_letters_ivey",
        "kind": "source_archive_reference",
        "title": "Buffett Partnership Letters PDF",
        "url": "https://www.ivey.uwo.ca/media/2975913/buffett-partnership-letters.pdf",
        "local_path": "",
        "note": "Upstream reference for early partnership letters; canonical local copies live under primary/warren_buffett_letters/.",
    },
    {
        "id": "fenwii_buffett_letters_1957_2018_en",
        "kind": "source_archive_reference",
        "title": "Warren Buffett shareholder letters 1957-2018 English PDF archive",
        "url": "https://github.com/fenwii/WarrenBuffettLetter/tree/main/%E5%B7%B4%E8%8F%B2%E7%89%B9%E8%87%B4%E8%82%A1%E4%B8%9C%E7%9A%84%E4%BF%A1WarrenBuffettLetter/1957-2018%20en",
        "local_path": "",
        "note": "Upstream archive used to build the canonical local by-year archive; duplicate source PDFs are not retained locally.",
    },
    {
        "id": "rbcpa_letters_index",
        "kind": "primary_index",
        "title": "Warren Buffett letters to partners 1959-1975 index",
        "url": "https://www.rbcpa.com/warren-e-buffett/buffett-letters-1959-present/",
        "local_path": "",
        "note": "Useful index for early partner/Berkshire letters not hosted as current official PDFs.",
    },
    {
        "id": "dow_sp500_github",
        "kind": "market_data",
        "title": "Historical time series of Dow Jones Industrial Average and S&P 500",
        "url": "https://github.com/fja05680/dow-sp500-100-years",
        "local_path": "market_indices_raw/",
        "note": "Raw daily CSV files used to compute year-end price-index returns.",
    },
    {
        "id": "britannica_buffett",
        "kind": "secondary",
        "title": "Britannica Money: Warren Buffett biography",
        "url": "https://www.britannica.com/money/Warren-Edward-Buffett",
        "local_path": "",
        "note": "Secondary chronology and biographical context.",
    },
    {
        "id": "britannica_berkshire",
        "kind": "secondary",
        "title": "Britannica Money: Berkshire Hathaway overview",
        "url": "https://www.britannica.com/money/Berkshire-Hathaway",
        "local_path": "",
        "note": "Secondary context on Berkshire's business mix.",
    },
    {
        "id": "novel_investor_partnership_notes",
        "kind": "secondary",
        "title": "Novel Investor notes on Buffett Partnership Letters",
        "url": "https://novelinvestor.com/notes/buffett-partnership-letters-by-warren-buffett/",
        "local_path": "",
        "note": "Secondary summary of partnership period and Dow comparison.",
    },
    {
        "id": "tang_tangshufang_context",
        "kind": "secondary_chinese",
        "title": "唐书房 / 巴芒演义 context",
        "url": "https://10year.wordpress.com/tag/%E5%94%90%E4%B9%A6%E6%88%BF/",
        "local_path": "",
        "note": "Chinese context for 唐朝's Buffett/Munger writing series and 巴芒演义.",
    },
    {
        "id": "tang_weread_books",
        "kind": "secondary_chinese",
        "title": "微信读书: 唐朝作品介绍",
        "url": "https://weread.qq.com/web/search/books?author=%E5%94%90%E6%9C%9D&ii=5383296059b5f3538f97206",
        "local_path": "",
        "note": "Chinese source for 唐朝's value-investing books, including 巴芒演义.",
    },
]


EVENTS = [
    {
        "year": 1957,
        "title": "合伙企业第一份成绩单",
        "category": "partnership",
        "impact": "在道指下跌的一年，合伙企业仍实现正收益，确立了熊市相对表现的主线。",
        "letter_focus": "不预测市场，寻找低估证券；坏年份更容易看出相对优势。",
        "detail": "1957 年三只 1956 年成立的合伙企业明显好于整体市场。之后的表格显示合伙企业 1957 年收益为 10.4%，道指含股息为 -8.4%。这不是一条直线增长的开始，而是一个衡量标准的开始：不是绝对每年赚钱，而是长期显著胜过可比市场。",
        "world": "1957-1958 年美国经济衰退期间，道指承压。",
        "source_ids": "buffett_partnership_letters_ivey",
    },
    {
        "year": 1962,
        "title": "合伙企业合并成 Buffett Partnership Ltd.",
        "category": "structure",
        "impact": "分散的合伙结构被统一，投资业绩和资本配置从此有了更清晰的载体。",
        "letter_focus": "用三到五年评估投资表现，年度涨跌不是质量本身。",
        "detail": "1962 年左右，多个合伙企业被整合为 Buffett Partnership Ltd.。这让资金、持仓和业绩口径更集中，也为随后买入 Berkshire Hathaway 打下结构基础。",
        "world": "1962 年古巴导弹危机加剧市场波动，但合伙企业继续强调相对业绩。",
        "source_ids": "buffett_partnership_letters_ivey,britannica_buffett",
    },
    {
        "year": 1965,
        "title": "控制 Berkshire Hathaway",
        "category": "control",
        "impact": "一笔纺织股投资变成控制权交易，后来成为资本配置平台。",
        "letter_focus": "便宜资产不等于好生意，控制权改变了复利路径。",
        "detail": "1965 年 Buffett 取得 Berkshire Hathaway 控制权。按他后来反思，这家纺织公司的商业质量并不好，但这个壳后来承载了保险浮存金、全资收购和长期股权投资。",
        "world": "美国战后扩张进入后期，资本市场估值和商业模式开始分化。",
        "source_ids": "berkshire_2024_annual_report,britannica_buffett,britannica_berkshire",
    },
    {
        "year": 1967,
        "title": "进入保险，建立浮存金引擎",
        "category": "insurance",
        "impact": "National Indemnity 把 Berkshire 从纺织公司推向保险驱动的控股公司。",
        "letter_focus": "保险浮存金让 Berkshire 获得长期、低成本、可投资资金。",
        "detail": "1967 年 Berkshire 进入保险业务，后来浮存金成为 Buffett 复利机器最重要的结构性优势之一。同年 Berkshire 支付了唯一一次每股 10 美分现金股息，之后长期选择留存再投资。",
        "world": "1960 年代后期通胀压力上升，低成本长期资金的价值开始凸显。",
        "source_ids": "berkshire_2024_annual_report,britannica_berkshire",
    },
    {
        "year": 1973,
        "title": "买入 Washington Post，遭遇熊市",
        "category": "bear_market",
        "impact": "在市场情绪低迷时买入高质量媒体资产，是价值投资逆向性的典型案例。",
        "letter_focus": "以企业价值而不是市场报价作为决策锚点。",
        "detail": "1973 年 Berkshire 开始买入 Washington Post。1973-1974 年熊市使账面市值承压，但也提供了以低价买入优质资产的环境。",
        "world": "第一次石油危机、通胀和衰退预期冲击全球市场。",
        "source_ids": "britannica_buffett",
    },
    {
        "year": 1976,
        "title": "GEICO 转折点",
        "category": "insurance",
        "impact": "对 GEICO 的投资把早年理解的保险商业模式转化为 Berkshire 的核心能力。",
        "letter_focus": "优秀保险公司的承保纪律和成本结构可以放大长期投资能力。",
        "detail": "Buffett 早年研究 GEICO，1970 年代中期在 GEICO 困境中大举投资。之后 Berkshire 于 1996 年完成全资收购，GEICO 成为保险业务支柱。",
        "world": "1970 年代中期美国市场从深度熊市恢复。",
        "source_ids": "britannica_buffett,britannica_berkshire",
    },
    {
        "year": 1985,
        "title": "纺织业务关停",
        "category": "mistake",
        "impact": "承认原始业务不可救药，把资本从低回报业务中解放出来。",
        "letter_focus": "管理层必须处理错误，不能把沉没成本包装成坚持。",
        "detail": "1985 年 Berkshire 关闭纺织业务，标志着最初那笔便宜股投资的商业终点。此后公司重心已经实质转为保险、可控企业和长期证券投资。",
        "world": "1980 年代美国资本市场进入长期牛市早期。",
        "source_ids": "britannica_buffett,britannica_berkshire",
    },
    {
        "year": 1988,
        "title": "开始买入 Coca-Cola",
        "category": "quality",
        "impact": "从烟蒂式便宜股进一步转向高质量品牌和长期持有。",
        "letter_focus": "好生意、护城河和长期再投资，比单纯低估更重要。",
        "detail": "1988 年 Berkshire 开始买入 Coca-Cola。这笔投资后来成为 Buffett 从 Graham 式低估资产向 Munger 式优质企业进化的代表案例。",
        "world": "1987 年黑色星期一后，市场恐慌仍未完全消退。",
        "source_ids": "britannica_berkshire,tang_tangshufang_context",
    },
    {
        "year": 1996,
        "title": "全资收购 GEICO",
        "category": "acquisition",
        "impact": "把长期研究和部分持股升级为全资控制，保险浮存金基础更稳。",
        "letter_focus": "当理解足够深、价格足够合理时，控制权能创造额外价值。",
        "detail": "1996 年 Berkshire 完成 GEICO 全资收购。GEICO 的低成本直销模式和承保规模，强化了 Berkshire 保险业务的长期资金来源。",
        "world": "美国进入互联网泡沫前的高速扩张期。",
        "source_ids": "britannica_berkshire",
    },
    {
        "year": 1999,
        "title": "科技泡沫中跑输",
        "category": "discipline",
        "impact": "Berkshire 在泡沫年份显著跑输，但没有改变能力圈纪律。",
        "letter_focus": "不懂的不买，短期相对落后不等于原则失效。",
        "detail": "1999 年 Berkshire 每股市值下跌 19.9%，而 S&P 500 含股息上涨 21.0%。这是全图中最重要的心理压力年份之一：坚持能力圈意味着会在热门资产泡沫中显得落伍。",
        "world": "互联网泡沫推高成长股估值，传统价值股承压。",
        "source_ids": "berkshire_2024_annual_report",
    },
    {
        "year": 2008,
        "title": "金融危机中的资本提供者",
        "category": "crisis",
        "impact": "市场流动性枯竭时，Berkshire 的现金和声誉变成交易优势。",
        "letter_focus": "保持流动性和信用，才能在别人被迫卖出时行动。",
        "detail": "2008 年 Berkshire 股价同样大幅下跌，但公司在危机中向优质金融/工业企业提供资本。对长期投资者而言，这一年同时是回撤测试和机会测试。",
        "world": "全球金融危机冲击银行、信用市场和实体经济。",
        "source_ids": "berkshire_2024_annual_report",
    },
    {
        "year": 2009,
        "title": "宣布收购 BNSF",
        "category": "acquisition",
        "impact": "Berkshire 从证券投资进一步扩展到美国基础设施和铁路现金流。",
        "letter_focus": "在美国经济长期增长上押注，用全资企业承接长期资本。",
        "detail": "2009 年 Berkshire 宣布收购 BNSF，2010 年完成交易。铁路业务让 Berkshire 的收益来源更接近美国实体经济的长期货运网络。",
        "world": "金融危机后，美国进入低利率和复苏周期。",
        "source_ids": "britannica_berkshire",
    },
    {
        "year": 2016,
        "title": "Apple 成为公开股权核心仓位",
        "category": "public_equity",
        "impact": "Berkshire 对消费品牌、生态系统和资本回报的理解延伸到科技巨头。",
        "letter_focus": "能力圈不是行业标签，而是能否理解消费者黏性和长期现金流。",
        "detail": "2016 年 Berkshire 开始买入 Apple，后来 Apple 成为公开股票组合中最重要的仓位之一。这也是 Buffett 投资框架继续演化的标志。",
        "world": "移动互联网进入成熟期，平台型公司现金流能力凸显。",
        "source_ids": "britannica_berkshire",
    },
    {
        "year": 2020,
        "title": "疫情冲击与保守资产负债表",
        "category": "risk",
        "impact": "疫情冲击验证了 Berkshire 对流动性和极端风险的长期偏好。",
        "letter_focus": "现金不是拖累，而是在不确定性爆发时保持选择权的资产。",
        "detail": "2020 年市场经历疫情暴跌和快速反弹。Berkshire 当年每股市值上涨 2.4%，低于 S&P 500 含股息 18.4%，但资产负债表保持了充足防御能力。",
        "world": "COVID-19 改变全球经济活动和货币政策路径。",
        "source_ids": "berkshire_2024_annual_report",
    },
    {
        "year": 2023,
        "title": "Charlie Munger 去世",
        "category": "people",
        "impact": "Berkshire 的投资文化进入传承阶段，Munger 对“好公司合理价”的影响成为核心遗产。",
        "letter_focus": "理性、耐心、反愚蠢，比公式更重要。",
        "detail": "Charlie Munger 于 2023 年去世。对 Berkshire 和全球价值投资者而言，这不只是人物事件，也是投资思想从第一代搭档向下一代管理层传承的节点。",
        "world": "高利率环境重新定价长期资产，市场关注大型科技公司集中度。",
            "source_ids": "warren_buffett_letters,britannica_berkshire",
    },
    {
        "year": 2024,
        "title": "60 年成绩单：5,502,284%",
        "category": "scorecard",
        "impact": "1965-2024 年 Berkshire 总收益 5,502,284%，S&P 500 含股息 39,054%。",
        "letter_focus": "复利来自长期资本配置、留存收益、保险浮存金和美国经济。",
        "detail": "2024 年报列示，Berkshire 1965-2024 年复合年增长 19.9%，S&P 500 含股息为 10.4%；总收益分别为 5,502,284% 和 39,054%。这一页的主图就是把这个结果放回 1957 年的起点，并叠加关键年份。",
        "world": "AI 热潮和高利率并存，Berkshire 继续持有大量现金和美国企业权益。",
            "source_ids": "berkshire_2024_annual_report,warren_buffett_letters",
    },
]


CONTROVERSY = {
    1957: {
        "surface_story": "Buffett 在熊市里仍然赚钱，所以普通人也应该学习熊市防守和相对收益。",
        "hidden_condition": "早期合伙企业规模小、市场信息效率低，且投资人用多年周期评价他，不是每天看账户波动的散户环境。",
        "mislearning_risk": "把“熊市不亏”理解成个人也应该每年战胜市场，最后在短期波动里频繁换策略。",
        "real_lesson": "可学的是评价周期和相对思维，不是幻想每一年都能绝对赚钱。",
        "verdict": "你能学他的衡量方式，学不了他的早期市场环境。",
    },
    1962: {
        "surface_story": "Buffett 把分散合伙企业整合起来，说明优秀投资人应该集中控制资本。",
        "hidden_condition": "他控制的是愿意长期委托的合伙资本，并且已经用早期业绩建立信任；普通人没有这种资本组织权。",
        "mislearning_risk": "把“集中管理”误学成个人账户高度集中，忽略资金来源、期限和信任结构。",
        "real_lesson": "可学的是用统一口径审视长期业绩，不是模仿他的资本组织能力。",
        "verdict": "Buffett 不是只会选股，他先拥有了能承载策略的资本结构。",
    },
    1965: {
        "surface_story": "买下 Berkshire 是一笔经典便宜股投资，后来变成巨大成功。",
        "hidden_condition": "这不是普通股票买卖，而是控制权交易；控制权让资本配置、并购和现金再分配成为可能。",
        "mislearning_risk": "把便宜股当成 Berkshire 式机会，买入后却没有任何改变企业命运的权力。",
        "real_lesson": "可学的是承认便宜不等于好生意，以及错误资产也要重新配置。",
        "verdict": "你买的是股票代码，Buffett 买到的是资本配置平台。",
    },
    1967: {
        "surface_story": "进入保险后，Buffett 找到了长期复利引擎。",
        "hidden_condition": "保险浮存金是低成本、长期、可投资资金，和个人加杠杆完全不是一回事。",
        "mislearning_risk": "把浮存金误解成“借钱投资”，用短期限、高成本资金模仿长期资本。",
        "real_lesson": "可学的是理解资金成本和资金期限，不是用杠杆冒充浮存金。",
        "verdict": "你能学他的耐心，但你学不了他的资金结构。",
    },
    1973: {
        "surface_story": "Washington Post 说明 Buffett 敢在熊市买入好公司。",
        "hidden_condition": "他有估值能力、资本期限和承受多年账面压力的结构，不需要在短期内向市场证明自己。",
        "mislearning_risk": "看到下跌就加仓，把价格便宜误认为价值便宜。",
        "real_lesson": "可学的是以企业价值作为锚点，不是机械地越跌越买。",
        "verdict": "下跌不是机会，理解价值以后下跌才可能是机会。",
    },
    1976: {
        "surface_story": "GEICO 说明 Buffett 能在困境中发现伟大公司。",
        "hidden_condition": "他对保险商业模式研究多年，早年就理解 GEICO 的成本结构和承保逻辑。",
        "mislearning_risk": "把困境反转当成勇敢，买入自己并不理解的烂公司。",
        "real_lesson": "可学的是长期跟踪一个行业直到真正理解，不是困境里盲目抄底。",
        "verdict": "逆向投资不是站到多数人反面，而是知道多数人错在哪里。",
    },
    1985: {
        "surface_story": "关闭纺织业务说明 Buffett 能承认错误。",
        "hidden_condition": "Berkshire 已经有更好的资本去处，关闭低回报业务不是情绪动作，而是资本再配置。",
        "mislearning_risk": "把“长期持有”误学成永不认错，在低回报资产里消耗时间。",
        "real_lesson": "可学的是处理沉没成本，不是把坚持包装成价值投资。",
        "verdict": "长期主义不是死扛，死扛只是慢速亏损。",
    },
    1988: {
        "surface_story": "Coca-Cola 说明买好公司长期持有就能成功。",
        "hidden_condition": "这是 Buffett 和 Munger 投资框架进化后的结果，背后是几十年商业判断训练、品牌理解和估值纪律。",
        "mislearning_risk": "把“好公司”简化成知名品牌，忽略价格、护城河变化和再投资能力。",
        "real_lesson": "可学的是好生意和合理价格的结合，不是看到消费品牌就长期持有。",
        "verdict": "你学到的是买可乐，没学到的是判断好生意的能力。",
    },
    1996: {
        "surface_story": "全资收购 GEICO 是长期研究后的果断出手。",
        "hidden_condition": "Berkshire 可以从公开股权升级为控制权，把保险业务纳入整个资本机器。",
        "mislearning_risk": "把长期跟踪误学成只要熟悉一个公司就应该重仓，忽略控制权和经营整合价值。",
        "real_lesson": "可学的是深度理解后再行动，不是用熟悉感替代研究。",
        "verdict": "Buffett 的加仓有时买到控制权，你的加仓只是更高仓位。",
    },
    1999: {
        "surface_story": "科技泡沫中跑输，证明 Buffett 坚守能力圈。",
        "hidden_condition": "他能承受舆论和相对业绩压力，因为 Berkshire 的资本基础和信誉足够稳固。",
        "mislearning_risk": "把能力圈当成不学习新事物的借口，在变化中把无知包装成纪律。",
        "real_lesson": "可学的是不买不懂的东西，同时持续扩大真正能懂的范围。",
        "verdict": "能力圈不是护城河，懒惰才需要借口。",
    },
    2008: {
        "surface_story": "金融危机说明 Buffett 能在别人恐惧时贪婪。",
        "hidden_condition": "Berkshire 是危机中的资本提供者，拥有现金、信用和交易声誉，可以拿到普通投资者拿不到的条款。",
        "mislearning_risk": "把危机买入误学成个人账户盲目抄底，忽略流动性、杠杆和收入风险。",
        "real_lesson": "可学的是危机前保留选择权，不是危机中喊口号。",
        "verdict": "你不是危机里的 Buffett，你只是危机里的价格接受者。",
    },
    2009: {
        "surface_story": "BNSF 是 Buffett 对美国长期经济的重下注。",
        "hidden_condition": "Berkshire 能买下整家公司，用全资企业现金流承接长期资本，不是买几股铁路股。",
        "mislearning_risk": "把宏观信念当成投资理由，忽略自己没有控制权和现金流再配置权。",
        "real_lesson": "可学的是把投资和真实经济现金流连接起来，不是用宏大叙事替代估值。",
        "verdict": "Buffett 押注美国时买下基础设施，你押注美国时只是买入波动。",
    },
    2016: {
        "surface_story": "Apple 说明 Buffett 的能力圈也能进化到科技公司。",
        "hidden_condition": "他买的是成熟平台、消费者黏性、现金流和回购能力，不是追逐热门科技叙事。",
        "mislearning_risk": "用 Buffett 买 Apple 证明自己可以买任何科技股，把能力圈扩展误解成追热点。",
        "real_lesson": "可学的是能力圈按商业理解扩展，不是按行业标签扩展。",
        "verdict": "Buffett 买 Apple 不是追科技，是买消费垄断和现金流。",
    },
    2020: {
        "surface_story": "疫情中 Berkshire 保守，说明现金会拖累收益但能防风险。",
        "hidden_condition": "Berkshire 的现金是公司级选择权，背后有保险、全资企业和公开股票组合共同支撑。",
        "mislearning_risk": "把现金管理简化成择时，要么永远满仓，要么永远恐惧。",
        "real_lesson": "可学的是现金的期权价值，不是把现金当作情绪避难所。",
        "verdict": "现金不是仓位，是身份。Berkshire 的现金和你的现金不是同一种资产。",
    },
    2023: {
        "surface_story": "Munger 去世，Buffett 投资思想进入传承阶段。",
        "hidden_condition": "Munger 不是一句“买好公司”的名言，而是几十年反愚蠢、商业判断和人格互补。",
        "mislearning_risk": "摘录 Munger 金句，却没有建立反思错误和避免愚蠢的系统。",
        "real_lesson": "可学的是思维搭档、反证习惯和减少愚蠢，不是收藏格言。",
        "verdict": "你能背 Munger，未必能拥有一个 Munger。",
    },
    2024: {
        "surface_story": "60 年 5,502,284% 的成绩单证明复利和长期主义的力量。",
        "hidden_condition": "这个结果叠加了美国战后增长、保险浮存金、税务递延、控股平台、声誉交易流和极长寿命。",
        "mislearning_risk": "看到最终复利曲线，忽略支撑曲线的资本机器，然后把长期持有当作万能答案。",
        "real_lesson": "可学的是复利需要结构承载，不是时间本身会自动奖励所有人。",
        "verdict": "你看到的是复利，没看到的是机器。",
    },
}


LIVING_BOOK = {
    1957: {
        "scene_setting": "你刚开始管理合伙资本，美国经济进入衰退，市场下跌。外界不会因为你年轻就降低评价标准，合伙人真正关心的是：坏年份里，你到底有没有一套可执行的判断方式。",
        "reader_decision": "如果你是 Buffett，你会追求短期绝对收益，还是把目标定为长期、相对市场更好的表现？你能不能忍受用三到五年证明自己？",
        "shu_to_avoid": "把巴菲特的早期成绩误读成每年都要赢，最后被短期排名牵着走。",
        "dao_to_learn": "道在评价体系：先定义什么叫正确表现，再让策略为这个评价体系服务。",
    },
    1962: {
        "scene_setting": "你已经有多个合伙企业，也有了早期业绩。现在的问题不只是买什么股票，而是资本如何被组织、如何被信任、如何被长期评价。",
        "reader_decision": "如果你是 Buffett，你会继续分散管理多个小结构，还是把资本、口径和责任集中起来？你能不能让别人把长期资金交给你？",
        "shu_to_avoid": "把集中管理误学成个人账户集中持仓，却没有长期资本和委托信任。",
        "dao_to_learn": "道在结构：投资能力需要合适的载体，否则好判断也会被坏资金期限毁掉。",
    },
    1965: {
        "scene_setting": "你买到一家便宜的纺织公司，但它不是好生意。市场给了你价格，现实给了你一个低回报业务。你要面对的是：便宜和优秀不是一回事。",
        "reader_decision": "如果你是 Buffett，你会继续证明自己买得便宜，还是承认原始判断不完美，把控制权变成资本配置平台？",
        "shu_to_avoid": "只学买便宜股，却没有控制权，也没有改变企业资本用途的能力。",
        "dao_to_learn": "道在纠错：真正厉害的不是从不犯错，而是把错误资产重新放进更好的结构里。",
    },
    1967: {
        "scene_setting": "你控制了 Berkshire，但纺织业务不是未来。保险业务出现了，它带来的不是一只股票，而是一种长期、低成本、可投资的资金来源。",
        "reader_decision": "如果你是 Buffett，你会把保险当作普通生意看，还是看见浮存金能改变整个资本机器？你能不能区分长期资金和危险杠杆？",
        "shu_to_avoid": "把浮存金误学成借钱投资，用短钱模仿长钱。",
        "dao_to_learn": "道在资金性质：同样是钱，期限、成本和稳定性不同，投资命运就完全不同。",
    },
    1973: {
        "scene_setting": "市场恐慌，通胀高企，媒体资产被压低估值。Washington Post 看起来便宜，但你必须判断它是真便宜，还是时代正在毁掉它。",
        "reader_decision": "如果你是 Buffett，你敢不敢在账面继续下跌时持有？你买的是市场下跌，还是企业价值和定价权？",
        "shu_to_avoid": "把下跌当机会，越跌越买，却没有企业价值判断。",
        "dao_to_learn": "道在锚点：不是逆市场就是对，只有价值判断能把逆向和固执分开。",
    },
    1976: {
        "scene_setting": "GEICO 陷入困境，但它不是你第一次听说的公司。你早年研究过它，理解成本结构和保险模型。现在市场给了你一次压力测试后的价格。",
        "reader_decision": "如果你是 Buffett，你会把它当作困境股回避，还是基于多年理解判断它能否活下来？你真的懂这个生意吗？",
        "shu_to_avoid": "把困境投资理解成胆子大，买入自己并不理解的烂公司。",
        "dao_to_learn": "道在准备：机会出现时的果断，来自机会出现前很多年的理解。",
    },
    1985: {
        "scene_setting": "Berkshire 的纺织业务终于走到终点。继续经营可以维持体面，关停则承认最初那笔便宜股不是好生意。",
        "reader_decision": "如果你是 Buffett，你会继续讲长期主义，还是停止向低回报业务投入新的资本？你能不能亲手处理自己的旧判断？",
        "shu_to_avoid": "把长期持有误学成永不认错。",
        "dao_to_learn": "道在资本去处：长期主义不是死守，而是让资本持续流向更高回报的地方。",
    },
    1988: {
        "scene_setting": "Coca-Cola 是人人知道的品牌，但人人知道不等于值得买。你要判断的是品牌、分销、定价权和价格之间是否仍有足够空间。",
        "reader_decision": "如果你是 Buffett，你会因为它是好公司就买，还是要求好公司、好价格和长期再投资逻辑同时成立？",
        "shu_to_avoid": "把买好公司简化成买知名公司。",
        "dao_to_learn": "道在商业质量：好公司不是标签，而是长期现金流、定价权和资本回报的组合。",
    },
    1996: {
        "scene_setting": "你已经研究 GEICO 很久，也曾在它困难时下注。现在可以全资收购，把一项长期理解变成 Berkshire 内部的保险引擎。",
        "reader_decision": "如果你是 Buffett，你会满足于持股收益，还是在理解足够深时买下控制权？你有能力经营和配置这家公司吗？",
        "shu_to_avoid": "把加仓理解成信心，却忽略 Buffett 的加仓有时是在买控制权。",
        "dao_to_learn": "道在能力边界：当理解、价格、结构和控制权同时出现时，行动才有意义。",
    },
    1999: {
        "scene_setting": "互联网股票暴涨，Berkshire 跑输，外界质疑 Buffett 老了。你面对的不只是市场价格，还有声誉压力和时代叙事。",
        "reader_decision": "如果你是 Buffett，你会为了不落伍而买不懂的科技股，还是接受短期难看，坚持能力圈？同时你会不会继续学习新生意？",
        "shu_to_avoid": "把能力圈当成拒绝学习的借口。",
        "dao_to_learn": "道在诚实：不懂就是不懂，但真正的能力圈也必须能被持续扩展。",
    },
    2008: {
        "scene_setting": "全球金融体系冻结，所有人都在抢美元流动性。Berkshire 股价也跌，但它手里有现金、信用和可以被信任的名字。",
        "reader_decision": "如果你是 Buffett，你会先保命还是出手提供资本？如果没有永久资本和信用，你是否仍然敢说别人恐惧我贪婪？",
        "shu_to_avoid": "把危机买入理解成抄底口号。",
        "dao_to_learn": "道在位置：危机中重要的不是勇气，而是你到底是资本提供者还是价格接受者。",
    },
    2009: {
        "scene_setting": "金融危机刚过，美国经济还没有恢复信心。BNSF 代表铁路、物流、能源、农业和美国实体经济底盘。",
        "reader_decision": "如果你是 Buffett，你会等待宏观数据好看，还是在恐惧未散时买下美国经济的基础设施？你能承受这笔长期押注吗？",
        "shu_to_avoid": "用宏大叙事替代估值和现金流。",
        "dao_to_learn": "道在连接：伟大投资不是喊相信未来，而是把未来落实到可拥有、可计价的现金流资产。",
    },
    2016: {
        "scene_setting": "Apple 已经不是早期科技创业公司，而是成熟平台、消费品牌、现金流机器和回购机器。Buffett 的能力圈开始改变边界。",
        "reader_decision": "如果你是 Buffett，你会因为科技标签拒绝它，还是重新判断它是不是一个消费者生意？你能否说清楚自己懂的到底是什么？",
        "shu_to_avoid": "用 Buffett 买 Apple 证明自己可以追任何科技热点。",
        "dao_to_learn": "道在重新定义：能力圈不是行业标签，而是你能否理解现金流和用户黏性。",
    },
    2020: {
        "scene_setting": "疫情让市场暴跌又快速反弹。Berkshire 没有像很多人期待那样大举抄底，保守资产负债表显得不够刺激。",
        "reader_decision": "如果你是 Buffett，你会为了证明自己还敢出手而行动，还是承认极端不确定性下现金本身就是选择权？",
        "shu_to_avoid": "把现金管理变成情绪择时。",
        "dao_to_learn": "道在选择权：有些时候不行动不是怯懦，而是保留未来行动的权利。",
    },
    2023: {
        "scene_setting": "Munger 去世，市场开始回顾“好公司合理价”的思想遗产。但真正的问题是：这些思想如何从金句变成决策系统。",
        "reader_decision": "如果你是 Buffett，你如何在失去最重要的思维搭档后继续保持判断质量？你有自己的反愚蠢机制吗？",
        "shu_to_avoid": "背诵 Munger 金句，把智慧变成社交平台语录。",
        "dao_to_learn": "道在反愚蠢：减少大错，比追求每次聪明更重要。",
    },
    2024: {
        "scene_setting": "60 年成绩单摆在面前：Berkshire 复利惊人。但这条曲线背后不只有耐心，还有美国、美元、保险、控制权、税务、声誉和寿命。",
        "reader_decision": "如果你是 Buffett，你能不能在 60 年里反复做少数正确决定，并让结构保护这些决定？如果不能，你到底应该学什么？",
        "shu_to_avoid": "只看最终曲线，把长期持有当作万能答案。",
        "dao_to_learn": "道在系统：复利不是时间自动给的奖励，而是正确判断被正确结构长期承载的结果。",
    },
}


MACRO_CONTEXT = {
    1957: {
        "macro_regime": "战后美国扩张早期，消费社会和股票市场仍在重新定价工业化后的企业利润。",
        "dollar_context": "布雷顿森林体系下美元仍锚定黄金，美元信用是战后资本秩序的中心。",
        "america_tailwind": "Buffett 的早期机会来自美国本土企业、分散市场和仍不充分的信息效率。",
        "global_shock": "1957-1958 年美国经济衰退提醒投资者：国际秩序稳定不等于商业周期消失。",
    },
    1962: {
        "macro_regime": "冷战高压期，美国企业利润和资本市场在地缘风险中继续扩张。",
        "dollar_context": "美元仍是战后体系核心货币，资本以美元资产作为安全和收益的共同锚点。",
        "america_tailwind": "合伙企业能以美国证券为主要猎场，本身就是美元资产深度和法治市场的红利。",
        "global_shock": "古巴导弹危机把核战争风险推到市场面前，但美国资本市场没有失去长期定价功能。",
    },
    1965: {
        "macro_regime": "美国战后繁荣进入后期，传统制造业和资本市场估值开始分化。",
        "dollar_context": "美元黄金锚仍在，但美国财政和国际收支压力已经为 1971 年转折埋下伏笔。",
        "america_tailwind": "控制 Berkshire 之所以有价值，是因为美国允许股东控制权、并购和资本再配置长期发挥作用。",
        "global_shock": "越战和战后财政压力逐渐改变美元体系，也改变未来通胀和资产定价环境。",
    },
    1967: {
        "macro_regime": "通胀压力上升，美国金融体系开始进入更复杂的利率和信用周期。",
        "dollar_context": "低成本长期资金在美元体系里开始变得更稀缺，也更有价值。",
        "america_tailwind": "保险浮存金能投资美国优质资产，把家庭、汽车、企业风险转化为 Berkshire 的长期资金来源。",
        "global_shock": "1960 年代后期的财政压力、战争支出和通胀预期让资金成本成为决定长期胜负的变量。",
    },
    1973: {
        "macro_regime": "布雷顿森林体系结束后，美国进入高通胀、低增长和估值压缩的年代。",
        "dollar_context": "美元脱离黄金后，现金购买力更容易被通胀侵蚀，优质资产的定价权变得更重要。",
        "america_tailwind": "即使在熊市，美国仍有能长期把通胀转嫁给消费者和广告市场的优质企业。",
        "global_shock": "第一次石油危机把地缘政治、能源价格和美国通胀直接压到投资者账户上。",
    },
    1976: {
        "macro_regime": "美国从 1973-1974 年深熊中恢复，但通胀和利率仍然支配资产定价。",
        "dollar_context": "高通胀环境惩罚现金和固定收益，也奖励能够调整价格、控制成本的商业模式。",
        "america_tailwind": "GEICO 绑定美国汽车社会和中产家庭风险池，这不是抽象好公司，而是美国生活方式的金融化。",
        "global_shock": "石油冲击后的经济恢复证明：宏观危机不会平均伤害所有企业，成本结构决定谁能活下来。",
    },
    1985: {
        "macro_regime": "Volcker 高利率之后，美国重新压住通胀，资本市场进入长期牛市早期。",
        "dollar_context": "强美元和高利率重建美元信用，也让低回报传统制造业承压。",
        "america_tailwind": "Berkshire 能退出纺织，把资本投向美国更高回报部门，这依赖一个足够深的资本市场。",
        "global_shock": "1980 年代全球制造业竞争加剧，传统美国纺织业务不再享有战后保护性红利。",
    },
    1988: {
        "macro_regime": "美国消费品牌全球化，美国企业开始更充分收割全球市场。",
        "dollar_context": "通胀被压制后，长期权益资产重新获得估值空间，品牌定价权变成抗通胀资产。",
        "america_tailwind": "Coca-Cola 是美国消费文化全球扩张的符号，Buffett 买到的是品牌、分销和美元利润流。",
        "global_shock": "黑色星期一后市场恐慌仍在，但美国消费品牌的全球需求没有随股价一起崩掉。",
    },
    1996: {
        "macro_regime": "冷战后美国全球化红利扩大，金融市场深度和企业并购活动增强。",
        "dollar_context": "美元资产在全球资本流动中继续占据中心位置，优质美国企业享受更低融资成本。",
        "america_tailwind": "GEICO 全资并入 Berkshire，把美国汽车保险市场和低成本直销模式变成内部资本机器。",
        "global_shock": "全球化和互联网前夜扩大了美国企业利润池，也强化了资本市场给赢家的估值溢价。",
    },
    1999: {
        "macro_regime": "互联网泡沫把美国成长股推到极端估值，传统价值股短期失去叙事优势。",
        "dollar_context": "强美元、资本流入和科技乐观主义共同推高美国风险资产。",
        "america_tailwind": "即使 Berkshire 跑输，美国资本市场仍允许不同风格长期共存并接受最终业绩检验。",
        "global_shock": "亚洲金融危机后全球资本回流美元资产，强化了美国市场中心地位，也放大了泡沫。",
    },
    2008: {
        "macro_regime": "全球金融危机暴露美元信用体系的脆弱性，也显示美联储和美国资产的中心地位。",
        "dollar_context": "危机中全世界抢美元流动性，Berkshire 手里的美元现金变成稀缺交易筹码。",
        "america_tailwind": "Buffett 能以美国信用和 Berkshire 声誉成为资本提供者，普通投资者只是价格接受者。",
        "global_shock": "美国次贷危机变成全球危机，说明美国金融体系的问题会外溢到所有投资者。",
    },
    2009: {
        "macro_regime": "金融危机后美国进入低利率、量化宽松和缓慢复苏时代。",
        "dollar_context": "低利率降低长期资产折现率，也让拥有稳定现金流的实体资产更稀缺。",
        "america_tailwind": "BNSF 是美国货运、能源、农业和消费供应链的基础设施，直接绑定美国经济底盘。",
        "global_shock": "危机后的政策托底改变资产价格路径，长期资本能买到被恐慌压低的基础设施资产。",
    },
    2016: {
        "macro_regime": "移动互联网成熟，美国平台公司成为全球利润池的中心。",
        "dollar_context": "低利率和全球美元利润回流支撑大型科技公司的回购、现金流和估值。",
        "america_tailwind": "Apple 把全球消费力、美国品牌、软件生态和资本回报机制集中到一家企业。",
        "global_shock": "全球化供应链和智能手机普及让美国平台公司赚取全球消费者和开发者的利润。",
    },
    2020: {
        "macro_regime": "疫情冲击后，美国用财政和货币扩张托底资产和消费。",
        "dollar_context": "美元体系先经历流动性挤兑，再经历大规模宽松，现金既是防御也是等待再定价的选择权。",
        "america_tailwind": "美国政策能力、资本市场深度和大型企业利润恢复速度，让长期资产迅速重新定价。",
        "global_shock": "COVID-19 同时冲击供应链、消费和货币政策，把宏观风险直接推到每个投资者面前。",
    },
    2023: {
        "macro_regime": "高利率、AI 热潮和地缘摩擦并存，美国资产重新按资本成本和技术垄断定价。",
        "dollar_context": "高利率强化美元吸引力，也提高普通投资者犯错的机会成本。",
        "america_tailwind": "Berkshire 继续持有大量美元现金和美国企业权益，仍站在美国资产体系内部。",
        "global_shock": "俄乌战争后能源、供应链和地缘安全重估，全球资本更关注安全资产和定价权。",
    },
    2024: {
        "macro_regime": "美国进入高利率与 AI 资本开支并行阶段，少数大公司主导指数收益。",
        "dollar_context": "美元购买力长期被通胀侵蚀，但美元资产和全球储备货币地位仍支撑美国资本市场深度。",
        "america_tailwind": "60 年成绩单背后是美国消费、股东制度、企业利润、美元资产和资本市场共同提供的顺风。",
        "global_shock": "去全球化、地缘冲突和高利率没有终结美国资产中心地位，反而让安全资产溢价更明显。",
    },
}


def ensure_dirs() -> None:
    for directory in [
        CANONICAL_LETTERS_DIR,
        MARKET_RAW,
        PROCESSED,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def request(url: str, timeout: int = 30) -> urllib.request.Request:
    return urllib.request.Request(url, headers={"User-Agent": USER_AGENT})


def download(url: str, destination: Path, timeout: int = 30, retries: int = 2) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0:
        return {
            "url": url,
            "path": str(destination.relative_to(RAW)),
            "status": "downloaded",
            "bytes": destination.stat().st_size,
            "http_status": "cached",
        }
    last_error = ""
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request(url, timeout), timeout=timeout) as response:
                tmp = destination.with_suffix(destination.suffix + ".tmp")
                with tmp.open("wb") as out:
                    shutil.copyfileobj(response, out)
                tmp.replace(destination)
                return {
                    "url": url,
                    "path": str(destination.relative_to(RAW)),
                    "status": "downloaded",
                    "bytes": destination.stat().st_size,
                    "http_status": response.status,
                }
        except Exception as exc:  # noqa: BLE001 - keep failure detail in manifest.
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < retries:
                time.sleep(1 + attempt)
    return {
        "url": url,
        "path": str(destination.relative_to(RAW)),
        "status": "failed",
        "bytes": 0,
        "error": last_error,
    }


def collect_canonical_letter_files() -> list[dict]:
    records: list[dict] = []
    pdfs = sorted(
        CANONICAL_LETTERS_DIR.glob("*.pdf"),
        key=lambda path: (
            int(path.stem[:4]),
            {"year": 0, "h1": 1, "midyear": 2}.get(letter_period(path.stem), 99),
            path.stem,
        ),
    )
    if not pdfs:
        return [
            {
                "url": CANONICAL_LETTERS_GITHUB_URL,
                "path": str(CANONICAL_LETTERS_DIR.relative_to(RAW)),
                "status": "failed",
                "bytes": 0,
                "error": "Missing canonical Buffett letters PDFs. Restore raw_data/primary/warren_buffett_letters before running build_dataset.py.",
                "source_id": "warren_buffett_letters",
            }
        ]
    for path in pdfs:
        document_id = path.stem
        period = letter_period(document_id)
        records.append(
            {
                "url": CANONICAL_LETTERS_GITHUB_URL,
                "path": str(path.relative_to(RAW)),
                "status": "downloaded",
                "bytes": path.stat().st_size,
                "http_status": "canonical",
                "source_id": "warren_buffett_letters",
                "document_id": document_id,
                "period": period,
                "document_kind": letter_document_kind(period),
            }
        )
    return records


def letter_period(document_id: str) -> str:
    if document_id.endswith("-h1"):
        return "h1"
    if document_id.endswith("-midyear"):
        return "midyear"
    return "year"


def letter_document_kind(period: str) -> str:
    if period == "h1":
        return "first_half_report"
    if period == "midyear":
        return "midyear_wind_down_letter"
    return "shareholder_letter"


def collect_primary_files() -> list[dict]:
    records: list[dict] = []
    downloads = [
        (
            "https://www.berkshirehathaway.com/2024ar/2024ar.pdf",
            PRIMARY / "berkshire_2024_annual_report.pdf",
        ),
    ]

    for url, destination in downloads:
        records.append(download(url, destination, timeout=45, retries=1))

    records.extend(collect_canonical_letter_files())

    return records


def collect_market_files() -> list[dict]:
    base = "https://raw.githubusercontent.com/fja05680/dow-sp500-100-years/master/"
    records = [
        download(base + "SP500.csv", MARKET_RAW / "SP500.csv", timeout=45, retries=2),
        download(base + "DJA.csv", MARKET_RAW / "DJA.csv", timeout=45, retries=2),
    ]
    yahoo_path = MARKET_RAW / "yahoo_2019_2024_year_end.json"
    yahoo_payload = collect_yahoo_recent_closes()
    yahoo_path.write_text(json.dumps(yahoo_payload, indent=2), encoding="utf-8")
    records.append(
        {
            "url": "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC and %5EDJI",
            "path": str(yahoo_path.relative_to(RAW)),
            "status": "downloaded",
            "bytes": yahoo_path.stat().st_size,
            "note": "Supplemental year-end closes for 2019-2024 because the GitHub raw CSVs end in December 2019.",
        }
    )
    return records


def collect_yahoo_recent_closes() -> dict:
    symbols = {"sp500": "%5EGSPC", "dow": "%5EDJI"}
    # Start before 2019 year-end so the 2020 return can use the same source for 2019 close.
    period1 = int(datetime(2019, 12, 20, tzinfo=timezone.utc).timestamp())
    period2 = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp())
    payload = {"generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z", "series": {}}
    for label, symbol in symbols.items():
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={period1}&period2={period2}&interval=1d"
        with urllib.request.urlopen(request(url), timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]
        by_year: dict[str, dict] = {}
        for stamp, close in zip(timestamps, closes):
            if close is None:
                continue
            date = datetime.utcfromtimestamp(stamp).strftime("%Y-%m-%d")
            year = date[:4]
            if "2019" <= year <= "2024":
                by_year[year] = {"date": date, "close": close}
        payload["series"][label] = {"url": url, "year_end": by_year}
    return payload


def annual_closes(csv_path: Path) -> dict[int, float]:
    by_year: dict[int, tuple[str, float]] = {}
    with csv_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        date_field = "Date" if "Date" in (reader.fieldnames or []) else ""
        for row in reader:
            date = row.get(date_field) or row.get("") or ""
            if len(date) < 10:
                continue
            year = int(date[:4])
            if year < 1956 or year > 2024:
                continue
            close_text = row.get("Adj Close") or row.get("Close")
            if not close_text:
                continue
            try:
                close = float(close_text)
            except ValueError:
                continue
            if year not in by_year or date > by_year[year][0]:
                by_year[year] = (date, close)
    return {year: close for year, (date, close) in by_year.items()}


def add_recent_yahoo_closes(spx: dict[int, float], dow: dict[int, float]) -> None:
    supplement_path = MARKET_RAW / "yahoo_2019_2024_year_end.json"
    if not supplement_path.exists():
        return
    data = json.loads(supplement_path.read_text(encoding="utf-8"))
    for year, item in data["series"].get("sp500", {}).get("year_end", {}).items():
        spx[int(year)] = float(item["close"])
    for year, item in data["series"].get("dow", {}).get("year_end", {}).items():
        dow[int(year)] = float(item["close"])


def pct_change(current: float, previous: float) -> float:
    return (current / previous - 1.0) * 100.0


def build_returns() -> list[dict]:
    spx = annual_closes(MARKET_RAW / "SP500.csv")
    dow = annual_closes(MARKET_RAW / "DJA.csv")
    add_recent_yahoo_closes(spx, dow)
    rows: list[dict] = []

    buffett_cumulative = 1.0
    spx_cumulative = 1.0
    dow_cumulative = 1.0
    spx_total_cumulative = ""

    for year in range(1957, 2025):
        if year in PARTNERSHIP_RETURNS:
            buffett_return = PARTNERSHIP_RETURNS[year]
            source = "Buffett Partnership gain"
        else:
            buffett_return = BERKSHIRE_RETURNS[year]
            source = "Berkshire per-share market value"
        buffett_cumulative *= 1.0 + buffett_return / 100.0

        spx_return = pct_change(spx[year], spx[year - 1]) if year in spx and (year - 1) in spx else math.nan
        dow_return = pct_change(dow[year], dow[year - 1]) if year in dow and (year - 1) in dow else math.nan
        if not math.isnan(spx_return):
            spx_cumulative *= 1.0 + spx_return / 100.0
        if not math.isnan(dow_return):
            dow_cumulative *= 1.0 + dow_return / 100.0

        spx_total_return = SP500_TOTAL_RETURNS_FROM_BERKSHIRE.get(year)
        if spx_total_return is None:
            spx_total_cumulative = ""
        else:
            prev = 1.0 if spx_total_cumulative == "" else float(spx_total_cumulative)
            spx_total_cumulative = prev * (1.0 + spx_total_return / 100.0)

        rows.append(
            {
                "year": year,
                "buffett_return_pct": round(buffett_return, 4),
                "buffett_cumulative": round(buffett_cumulative, 8),
                "buffett_source": source,
                "sp500_price_return_pct": "" if math.isnan(spx_return) else round(spx_return, 4),
                "sp500_price_cumulative": round(spx_cumulative, 8),
                "sp500_close": "" if year not in spx else round(spx[year], 6),
                "dow_price_return_pct": "" if math.isnan(dow_return) else round(dow_return, 4),
                "dow_price_cumulative": round(dow_cumulative, 8),
                "dow_close": "" if year not in dow else round(dow[year], 6),
                "sp500_total_return_from_berkshire_pct": "" if spx_total_return is None else spx_total_return,
                "sp500_total_cumulative_from_1965": "" if spx_total_cumulative == "" else round(float(spx_total_cumulative), 8),
            }
        )

    output = PROCESSED / "returns.csv"
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return rows


def build_events() -> list[dict]:
    source_by_id = {source["id"]: source for source in SOURCES}
    rows = []
    for event in EVENTS:
        source_ids = [item.strip() for item in event["source_ids"].split(",") if item.strip()]
        urls = [source_by_id[item]["url"] for item in source_ids if item in source_by_id]
        controversy = CONTROVERSY[event["year"]]
        living_book = LIVING_BOOK[event["year"]]
        macro = MACRO_CONTEXT[event["year"]]
        row = {
            **event,
            **controversy,
            **living_book,
            **macro,
            "slug": f"{event['year']}-{slugify(event['title'])}",
            "source_urls": " | ".join(urls),
        }
        rows.append(row)

    csv_path = PROCESSED / "events.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        fields = [
            "year",
            "slug",
            "title",
            "category",
            "impact",
            "surface_story",
            "hidden_condition",
            "mislearning_risk",
            "real_lesson",
            "verdict",
            "scene_setting",
            "reader_decision",
            "shu_to_avoid",
            "dao_to_learn",
            "macro_regime",
            "dollar_context",
            "america_tailwind",
            "global_shock",
            "letter_focus",
            "detail",
            "world",
            "source_ids",
            "source_urls",
        ]
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    with (PROCESSED / "events.json").open("w", encoding="utf-8") as file:
        json.dump(rows, file, ensure_ascii=False, indent=2)
    return rows


def slugify(text: str) -> str:
    mapping = {
        "合伙企业第一份成绩单": "partnership-first-scorecard",
        "合伙企业合并成 Buffett Partnership Ltd.": "partnership-consolidation",
        "控制 Berkshire Hathaway": "berkshire-control",
        "进入保险，建立浮存金引擎": "insurance-float",
        "买入 Washington Post，遭遇熊市": "washington-post-bear-market",
        "GEICO 转折点": "geico-turning-point",
        "纺织业务关停": "textile-shutdown",
        "开始买入 Coca-Cola": "coca-cola",
        "全资收购 GEICO": "geico-acquisition",
        "科技泡沫中跑输": "dotcom-discipline",
        "金融危机中的资本提供者": "financial-crisis-capital",
        "宣布收购 BNSF": "bnsf",
        "Apple 成为公开股权核心仓位": "apple",
        "疫情冲击与保守资产负债表": "covid-balance-sheet",
        "Charlie Munger 去世": "munger",
        "60 年成绩单：5,502,284%": "sixty-year-scorecard",
    }
    if text in mapping:
        return mapping[text]
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(part for part in cleaned.split("-") if part)


def write_sources(download_records: list[dict], market_records: list[dict]) -> None:
    manifest = {
        "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "scope": "Buffett investor letters and return/event data through 2024.",
        "data_policy": [
            "1957-1964 Buffett line uses partnership gain before partner allocation.",
            "1965-2024 Buffett line uses Berkshire per-share market value from the 2024 annual report.",
            "S&P 500 and Dow comparison lines use price-index year-end closes from raw daily CSV files.",
            "Berkshire's official S&P 500 total-return comparison is also preserved for 1965-2024 in processed/returns.csv.",
        ],
        "limitations": [
            "Shareholder-letter PDFs are consolidated under primary/warren_buffett_letters/; duplicate upstream PDF folders are not retained locally.",
            "Dow and S&P price-index series exclude dividends. Use sp500_total_return_from_berkshire_pct for the official 1965-2024 total-return benchmark.",
            "唐朝/唐书房 source collection is represented by public context pages and book descriptions, not full WeChat article archives.",
        ],
        "sources": SOURCES,
        "downloads": download_records + market_records,
    }
    with (RAW / "source_manifest.json").open("w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)

    lines = [
        "# Source Notes",
        "",
        f"Generated: {manifest['generated_at']}",
        "",
        "## Data Policy",
    ]
    lines += [f"- {item}" for item in manifest["data_policy"]]
    lines += ["", "## Limitations"]
    lines += [f"- {item}" for item in manifest["limitations"]]
    lines += ["", "## Sources"]
    for source in SOURCES:
        local = f" Local: `{source['local_path']}`." if source["local_path"] else ""
        lines.append(f"- **{source['id']}** ({source['kind']}): {source['title']} - {source['url']}.{local} {source['note']}")
    lines += ["", "## Download Results"]
    for record in manifest["downloads"]:
        if record["status"] == "downloaded":
            if record.get("http_status") == "canonical":
                lines.append(f"- canonical `{record['path']}` ({record['bytes']} bytes)")
            else:
                lines.append(f"- downloaded `{record['path']}` ({record['bytes']} bytes) from {record['url']}")
        else:
            lines.append(f"- failed `{record['path']}` from {record['url']}: {record.get('error', 'unknown error')}")
    (RAW / "sources.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    download_records = collect_primary_files()
    market_records = collect_market_files()
    build_returns()
    build_events()
    write_sources(download_records, market_records)
    print(f"Wrote data to {RAW}")


if __name__ == "__main__":
    main()
