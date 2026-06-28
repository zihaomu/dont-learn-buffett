#!/usr/bin/env python3
"""
Historical rebuild helper for the normalized by-year/by-period Buffett archive.

Normal data builds read the canonical archive under:

    raw_data/primary/warren_buffett_letters/

This script is only needed if that archive must be regenerated from upstream
source files. Restore the source archives locally first:

    raw_data/primary/berkshire_letters_fenwii/1957-2018_en/
    raw_data/primary/berkshire_letters/

Those duplicate source folders are intentionally not retained in the cleaned
workspace after the canonical archive has been built.

Rules:
- 1957-1970: split the early partnership compilation into source-sequence
  year packages. Each package starts at that year's annual/performance letter
  where available, then includes source-order follow-up letters before the
  next annual/performance letter.
- 1961-1968: also expose standalone first-half reports as YYYY-h1.pdf.
- 1969: expose the May wind-down letter as YYYY-midyear.pdf because Buffett
  describes it as being written in lieu of the mid-year letter.
- 1971-2006: copy fenwii's single-year English PDFs.
- 2007-2024: prefer Berkshire Hathaway official shareholder-letter PDFs.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
except ImportError as exc:  # pragma: no cover - local environment guard.
    raise SystemExit("Missing dependency: install pypdf with `python3 -m pip install --user pypdf`.") from exc


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw_data"
PRIMARY = RAW / "primary"
FENWII_DIR = PRIMARY / "berkshire_letters_fenwii" / "1957-2018_en"
OFFICIAL_DIR = PRIMARY / "berkshire_letters"
OUTPUT_DIR = PRIMARY / "warren_buffett_letters"

FENWII_ARCHIVE_BASE_URL = (
    "https://raw.githubusercontent.com/fenwii/WarrenBuffettLetter/main/"
    "%E5%B7%B4%E8%8F%B2%E7%89%B9%E8%87%B4%E8%82%A1%E4%B8%9C%E7%9A%84%E4%BF%A1"
    "WarrenBuffettLetter/1957-2018%20en"
)
BERKSHIRE_LETTERS_BASE_URL = "https://www.berkshirehathaway.com/letters"

PARTNERSHIP_SOURCE = FENWII_DIR / "1957-1970.pdf"
PARTNERSHIP_SOURCE_REFERENCE = f"{FENWII_ARCHIVE_BASE_URL}/1957-1970.pdf"
PARTNERSHIP_PAGE_RANGES = [
    {
        "year": 1957,
        "period": "year",
        "document_kind": "annual_letter",
        "document_id": "1957",
        "filename": "1957.pdf",
        "page_start": 1,
        "page_end": 3,
        "note": "1957 annual partnership letter.",
    },
    {
        "year": 1958,
        "period": "year",
        "document_kind": "annual_letter",
        "document_id": "1958",
        "filename": "1958.pdf",
        "page_start": 4,
        "page_end": 6,
        "note": "1958 annual partnership letter.",
    },
    {
        "year": 1959,
        "period": "year",
        "document_kind": "annual_letter",
        "document_id": "1959",
        "filename": "1959.pdf",
        "page_start": 7,
        "page_end": 8,
        "note": "1959 annual partnership letter.",
    },
    {
        "year": 1960,
        "period": "year",
        "document_kind": "year_package",
        "document_id": "1960",
        "filename": "1960.pdf",
        "page_start": 9,
        "page_end": 16,
        "note": "1960 source-sequence package beginning with the 1960 annual partnership letter.",
    },
    {
        "year": 1961,
        "period": "year",
        "document_kind": "year_package",
        "document_id": "1961",
        "filename": "1961.pdf",
        "page_start": 17,
        "page_end": 31,
        "note": "1961 source-sequence package beginning with the 1961 annual performance letter.",
    },
    {
        "year": 1962,
        "period": "year",
        "document_kind": "year_package",
        "document_id": "1962",
        "filename": "1962.pdf",
        "page_start": 32,
        "page_end": 50,
        "note": "1962 source-sequence package beginning with the 1962 annual performance letter.",
    },
    {
        "year": 1963,
        "period": "year",
        "document_kind": "year_package",
        "document_id": "1963",
        "filename": "1963.pdf",
        "page_start": 51,
        "page_end": 66,
        "note": "1963 source-sequence package beginning with the 1963 annual performance letter.",
    },
    {
        "year": 1964,
        "period": "year",
        "document_kind": "year_package",
        "document_id": "1964",
        "filename": "1964.pdf",
        "page_start": 67,
        "page_end": 84,
        "note": "1964 source-sequence package beginning with the 1964 annual performance letter.",
    },
    {
        "year": 1965,
        "period": "year",
        "document_kind": "year_package",
        "document_id": "1965",
        "filename": "1965.pdf",
        "page_start": 85,
        "page_end": 99,
        "note": "1965 source-sequence package beginning with the 1965 annual performance letter.",
    },
    {
        "year": 1966,
        "period": "year",
        "document_kind": "year_package",
        "document_id": "1966",
        "filename": "1966.pdf",
        "page_start": 100,
        "page_end": 114,
        "note": "1966 source-sequence package beginning with the 1966 annual performance letter.",
    },
    {
        "year": 1967,
        "period": "year",
        "document_kind": "year_package",
        "document_id": "1967",
        "filename": "1967.pdf",
        "page_start": 115,
        "page_end": 122,
        "note": "1967 source-sequence package beginning with the 1967 annual performance letter.",
    },
    {
        "year": 1968,
        "period": "year",
        "document_kind": "year_package",
        "document_id": "1968",
        "filename": "1968.pdf",
        "page_start": 123,
        "page_end": 128,
        "note": "1968 source-sequence package beginning with the 1968 annual performance letter.",
    },
    {
        "year": 1969,
        "period": "year",
        "document_kind": "year_package",
        "document_id": "1969",
        "filename": "1969.pdf",
        "page_start": 129,
        "page_end": 144,
        "note": "1969 package: partnership wind-down and controlled-company material.",
    },
    {
        "year": 1970,
        "period": "year",
        "document_kind": "year_package",
        "document_id": "1970",
        "filename": "1970.pdf",
        "page_start": 145,
        "page_end": 152,
        "note": "1970 package: partnership liquidation bond-purchase letter.",
    },
]

PARTNERSHIP_EXTRA_DOCUMENTS = [
    {
        "year": 1961,
        "period": "h1",
        "document_kind": "first_half_report",
        "document_id": "1961-h1",
        "filename": "1961-h1.pdf",
        "page_start": 14,
        "page_end": 16,
        "note": "Standalone first-half 1961 partnership letter dated July 1961.",
    },
    {
        "year": 1962,
        "period": "h1",
        "document_kind": "first_half_report",
        "document_id": "1962-h1",
        "filename": "1962-h1.pdf",
        "page_start": 26,
        "page_end": 29,
        "note": "Standalone first-half 1962 partnership letter dated July 6, 1962.",
    },
    {
        "year": 1963,
        "period": "h1",
        "document_kind": "first_half_report",
        "document_id": "1963-h1",
        "filename": "1963-h1.pdf",
        "page_start": 42,
        "page_end": 48,
        "note": "Standalone first-half 1963 partnership letter dated July 10, 1963.",
    },
    {
        "year": 1964,
        "period": "h1",
        "document_kind": "first_half_report",
        "document_id": "1964-h1",
        "filename": "1964-h1.pdf",
        "page_start": 63,
        "page_end": 66,
        "note": "Standalone first-half 1964 partnership letter dated July 8, 1964.",
    },
    {
        "year": 1965,
        "period": "h1",
        "document_kind": "first_half_report",
        "document_id": "1965-h1",
        "filename": "1965-h1.pdf",
        "page_start": 79,
        "page_end": 82,
        "note": "Standalone first-half 1965 partnership letter dated July 9, 1965.",
    },
    {
        "year": 1966,
        "period": "h1",
        "document_kind": "first_half_report",
        "document_id": "1966-h1",
        "filename": "1966-h1.pdf",
        "page_start": 95,
        "page_end": 99,
        "note": "Standalone first-half 1966 partnership letter dated July 12, 1966.",
    },
    {
        "year": 1967,
        "period": "h1",
        "document_kind": "first_half_report",
        "document_id": "1967-h1",
        "filename": "1967-h1.pdf",
        "page_start": 108,
        "page_end": 110,
        "note": "Standalone first-half 1967 partnership letter dated July 12, 1967.",
    },
    {
        "year": 1968,
        "period": "h1",
        "document_kind": "first_half_report",
        "document_id": "1968-h1",
        "filename": "1968-h1.pdf",
        "page_start": 120,
        "page_end": 122,
        "note": "Standalone first-half 1968 partnership letter dated July 11, 1968.",
    },
    {
        "year": 1969,
        "period": "midyear",
        "document_kind": "midyear_wind_down_letter",
        "document_id": "1969-midyear",
        "filename": "1969-midyear.pdf",
        "page_start": 129,
        "page_end": 131,
        "note": "Standalone May 29, 1969 wind-down letter, written in lieu of the mid-year letter.",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_page_count(path: Path) -> int:
    return len(PdfReader(str(path)).pages)


def split_pages(source: Path, destination: Path, page_start: int, page_end: int) -> int:
    reader = PdfReader(str(source))
    writer = PdfWriter()
    for page_index in range(page_start - 1, page_end):
        writer.add_page(reader.pages[page_index])
    with destination.open("wb") as file:
        writer.write(file)
    return page_end - page_start + 1


def copy_pdf(source: Path, destination: Path) -> int:
    shutil.copy2(source, destination)
    return pdf_page_count(destination)


def build_split_record(item: dict) -> dict:
    output = OUTPUT_DIR / item["filename"]
    pages = split_pages(PARTNERSHIP_SOURCE, output, item["page_start"], item["page_end"])
    return {
        "document_id": item["document_id"],
        "year": item["year"],
        "period": item["period"],
        "document_kind": item["document_kind"],
        "output_path": str(output.relative_to(RAW)),
        "source_path": PARTNERSHIP_SOURCE_REFERENCE,
        "source_preference": "fenwii_split",
        "source_pages": f"{item['page_start']}-{item['page_end']}",
        "pages": pages,
        "bytes": output.stat().st_size,
        "sha256": sha256(output),
        "note": item["note"],
    }


def write_outputs() -> list[dict]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []

    for item in PARTNERSHIP_PAGE_RANGES:
        records.append(build_split_record(item))

    for item in PARTNERSHIP_EXTRA_DOCUMENTS:
        records.append(build_split_record(item))

    for year in range(1971, 2025):
        official = OFFICIAL_DIR / f"{year}ltr.pdf"
        fenwii = FENWII_DIR / f"{year}.pdf"
        if official.exists():
            source = official
            source_reference = f"{BERKSHIRE_LETTERS_BASE_URL}/{year}ltr.pdf"
            source_preference = "official_berkshire"
            note = "Official Berkshire Hathaway shareholder-letter PDF preferred when available."
        elif fenwii.exists():
            source = fenwii
            source_reference = f"{FENWII_ARCHIVE_BASE_URL}/{year}.pdf"
            source_preference = "fenwii_archive"
            note = "Fenwii English PDF archive used where no local official direct PDF is stored."
        else:
            raise FileNotFoundError(f"Missing source PDF for {year}")

        output = OUTPUT_DIR / f"{year}.pdf"
        pages = copy_pdf(source, output)
        records.append(
            {
                "document_id": str(year),
                "year": year,
                "period": "year",
                "document_kind": "shareholder_letter",
                "output_path": str(output.relative_to(RAW)),
                "source_path": source_reference,
                "source_preference": source_preference,
                "source_pages": "all",
                "pages": pages,
                "bytes": output.stat().st_size,
                "sha256": sha256(output),
                "note": note,
            }
        )

    period_order = {"year": 0, "h1": 1, "midyear": 2}
    records.sort(key=lambda record: (int(record["year"]), period_order.get(record["period"], 99), record["document_id"]))
    return records


def write_index(records: list[dict]) -> None:
    index_path = PRIMARY / "warren_buffett_letters_index.csv"
    with index_path.open("w", newline="", encoding="utf-8") as file:
        fields = [
            "document_id",
            "year",
            "period",
            "document_kind",
            "output_path",
            "source_path",
            "source_preference",
            "source_pages",
            "pages",
            "bytes",
            "sha256",
            "note",
        ]
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)

    manifest = {
        "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "scope": "Normalized Buffett shareholder-letter archive by year and period.",
        "output_dir": str(OUTPUT_DIR.relative_to(RAW)),
        "index_path": str(index_path.relative_to(RAW)),
        "policy": [
            "The canonical archive is the retained local source of truth; duplicate upstream source folders are not retained after cleanup.",
            "1957-1970 is split from the early partnership compilation into year packages.",
            "Standalone first-half letters are also exposed as YYYY-h1.pdf when present.",
            "The May 29, 1969 wind-down letter is exposed as 1969-midyear.pdf because Buffett described it as written in lieu of the mid-year letter.",
            "1971-2006 uses fenwii's English PDF archive where local official direct PDFs are not stored.",
            "2007-2024 prefers Berkshire Hathaway official shareholder-letter PDFs.",
            "The 2024 full annual report remains separate; this archive standardizes shareholder-letter PDFs.",
        ],
        "records": records,
    }
    with (PRIMARY / "warren_buffett_letters_manifest.json").open("w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)


def main() -> None:
    if not PARTNERSHIP_SOURCE.exists() or not FENWII_DIR.exists() or not OFFICIAL_DIR.exists():
        raise SystemExit(
            "Missing restored source archives. Normal builds use raw_data/primary/warren_buffett_letters; "
            "only run this helper after restoring raw_data/primary/berkshire_letters_fenwii/1957-2018_en/ "
            "and raw_data/primary/berkshire_letters/."
        )
    records = write_outputs()
    write_index(records)
    print(f"Wrote {len(records)} normalized PDFs to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
