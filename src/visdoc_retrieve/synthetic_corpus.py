"""Deterministic synthetic technical corpus generation for Phase 1."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz  # type: ignore[import-untyped]
from reportlab.lib import colors  # type: ignore[import-untyped]
from reportlab.lib.pagesizes import letter  # type: ignore[import-untyped]
from reportlab.pdfgen import canvas  # type: ignore[import-untyped]

from visdoc_retrieve.data_schema import (
    file_sha256,
    load_jsonl,
    page_content_hash,
    validate_family_split_consistency,
    validate_pages,
    validate_queries,
    write_jsonl,
)


@dataclass(frozen=True, slots=True)
class CorpusConfig:
    """Configuration for the default synthetic smoke corpus."""

    logical_root: str = "data/synthetic-smoke"
    render_zoom: float = 1.5


@dataclass(frozen=True, slots=True)
class FamilySpec:
    family_id: str
    title: str
    split: str
    domain: str
    cn_label: str


@dataclass(frozen=True, slots=True)
class PageBlueprint:
    section: str
    signal: str
    query_types: tuple[str, str, str]


@dataclass(frozen=True, slots=True)
class PageSpec:
    page_id: str
    page_number: int
    title: str
    signal: str
    query_types: tuple[str, str, str]
    text_lines: tuple[str, ...]


DEFAULT_FAMILIES: tuple[FamilySpec, ...] = (
    FamilySpec(
        family_id="manual-a",
        title="Pump Controller Field Manual",
        split="train",
        domain="pump controller",
        cn_label="泵站控制",
    ),
    FamilySpec(
        family_id="manual-b",
        title="Optical Switch Service Manual",
        split="dev",
        domain="optical switch",
        cn_label="光交换机",
    ),
    FamilySpec(
        family_id="manual-c",
        title="Robotic Arm Calibration Manual",
        split="test",
        domain="robotic arm",
        cn_label="机械臂校准",
    ),
)

PAGE_BLUEPRINTS: tuple[PageBlueprint, ...] = (
    PageBlueprint("calibration table", "table", ("table", "text", "layout")),
    PageBlueprint(
        "exploded component figure",
        "figure",
        ("figure", "text", "ocr_failure"),
    ),
    PageBlueprint("startup flow diagram", "flow", ("layout", "text", "figure")),
    PageBlueprint("torque specification", "specification", ("text", "table", "layout")),
    PageBlueprint(
        "fault troubleshooting",
        "troubleshooting",
        ("text", "table", "ocr_failure"),
    ),
    PageBlueprint("control panel layout", "layout", ("layout", "figure", "text")),
    PageBlueprint(
        "faint scanned label",
        "ocr_failure",
        ("ocr_failure", "text", "layout"),
    ),
    PageBlueprint("中英 mixed checklist", "mixed", ("text", "ocr_failure", "table")),
)


def generate_default_corpus(
    output_dir: Path,
    config: CorpusConfig | None = None,
) -> dict[str, object]:
    """Generate the deterministic Phase 1 smoke corpus and return its summary."""

    corpus_config = config or CorpusConfig()
    output_dir.mkdir(parents=True, exist_ok=True)

    page_records: list[dict[str, object]] = []
    query_records: list[dict[str, object]] = []

    for family in DEFAULT_FAMILIES:
        page_specs = _build_page_specs(family)
        pdf_path = output_dir / "pdfs" / f"{family.family_id}.pdf"
        _write_family_pdf(pdf_path, family, page_specs)
        _write_text_artifacts(output_dir, family, page_specs)
        _render_family_pdf(pdf_path, output_dir, family, corpus_config)

        for page in page_specs:
            image_path = (
                output_dir
                / "pages"
                / family.family_id
                / f"p{page.page_number:02d}.png"
            )
            text_path = (
                output_dir
                / "text"
                / family.family_id
                / f"p{page.page_number:02d}.txt"
            )
            page_records.append(
                {
                    "page_id": page.page_id,
                    "doc_id": family.family_id,
                    "page_number": page.page_number,
                    "image_path": _logical_path(
                        corpus_config,
                        "pages",
                        family.family_id,
                        f"p{page.page_number:02d}.png",
                    ),
                    "text_path": _logical_path(
                        corpus_config,
                        "text",
                        family.family_id,
                        f"p{page.page_number:02d}.txt",
                    ),
                    "family_id": family.family_id,
                    "split": family.split,
                    "content_hash": page_content_hash(image_path, text_path),
                }
            )
            query_records.extend(_build_query_records(family, page))

    pages_manifest = output_dir / "pages.jsonl"
    queries_manifest = output_dir / "queries.jsonl"
    write_jsonl(pages_manifest, page_records)
    write_jsonl(queries_manifest, query_records)

    pages = validate_pages(load_jsonl(pages_manifest))
    queries = validate_queries(load_jsonl(queries_manifest), pages)
    validate_family_split_consistency(pages, queries)

    summary = _build_summary(corpus_config, pages_manifest, queries_manifest)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _build_page_specs(family: FamilySpec) -> tuple[PageSpec, ...]:
    specs: list[PageSpec] = []
    for index, blueprint in enumerate(PAGE_BLUEPRINTS, start=1):
        page_id = f"{family.family_id}-p{index:02d}"
        title = f"{family.title}: {blueprint.section.title()}"
        text_lines = _build_text_lines(family, index, blueprint)
        specs.append(
            PageSpec(
                page_id=page_id,
                page_number=index,
                title=title,
                signal=blueprint.signal,
                query_types=blueprint.query_types,
                text_lines=text_lines,
            )
        )
    return tuple(specs)


def _build_text_lines(
    family: FamilySpec,
    page_number: int,
    blueprint: PageBlueprint,
) -> tuple[str, ...]:
    section_code = f"{family.family_id.upper()}-{page_number:02d}"
    return (
        f"{family.title} / {blueprint.section}",
        f"Document family: {family.family_id}; split: {family.split}.",
        f"Technical domain: {family.domain}; bilingual signal: {family.cn_label}.",
        f"Reference code {section_code} links the page image to OCR-like text.",
        "Table signal: operating limit "
        f"{20 + page_number} psi and ΔT {page_number + 3} C.",
        f"Figure signal: callout F{page_number} labels sensor, valve, "
        "and service port.",
        "Layout signal: top-left panel, center warning band, and footer revision box.",
        "OCR-failure-style signal: S0L-1 may be confused with SOL-I in scans.",
        f"中文/English mixed note: 检查 {family.cn_label} before reset sequence.",
    )


def _write_family_pdf(
    pdf_path: Path,
    family: FamilySpec,
    page_specs: tuple[PageSpec, ...],
) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(
        str(pdf_path),
        pagesize=letter,
        pageCompression=0,
        invariant=1,
    )
    pdf.setTitle(f"{family.title} synthetic smoke corpus")
    pdf.setAuthor("VisDoc-Retrieve Phase 1")
    cjk_font = _register_cjk_font()
    for page in page_specs:
        _draw_pdf_page(pdf, family, page, cjk_font)
        pdf.showPage()
    pdf.save()


def _write_text_artifacts(
    output_dir: Path,
    family: FamilySpec,
    page_specs: tuple[PageSpec, ...],
) -> None:
    for page in page_specs:
        text_path = (
            output_dir
            / "text"
            / family.family_id
            / f"p{page.page_number:02d}.txt"
        )
        text_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.write_text("\n".join(page.text_lines) + "\n", encoding="utf-8")


def _render_family_pdf(
    pdf_path: Path,
    output_dir: Path,
    family: FamilySpec,
    config: CorpusConfig,
) -> None:
    pages_dir = output_dir / "pages" / family.family_id
    pages_dir.mkdir(parents=True, exist_ok=True)
    matrix = fitz.Matrix(config.render_zoom, config.render_zoom)
    with fitz.open(pdf_path) as document:
        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            pixmap.save(str(pages_dir / f"p{page_index + 1:02d}.png"))


def _draw_pdf_page(
    pdf: Any,
    family: FamilySpec,
    page: PageSpec,
    cjk_font: str,
) -> None:
    width, height = letter
    margin = 48
    pdf.setFillColor(colors.HexColor("#111827"))
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(margin, height - 54, family.title)
    pdf.setFont("Helvetica", 9)
    pdf.drawString(
        margin,
        height - 70,
        f"{family.family_id} | split={family.split} | page={page.page_number:02d}",
    )
    pdf.setStrokeColor(colors.HexColor("#64748b"))
    pdf.line(margin, height - 82, width - margin, height - 82)

    text = pdf.beginText(margin, height - 112)
    text.setFont(cjk_font, 10)
    for line in page.text_lines:
        text.textLine(line)
    pdf.drawText(text)
    _draw_signal_panel(pdf, page.signal, margin, 132)


def _draw_signal_panel(pdf: Any, signal: str, left: int, bottom: int) -> None:
    pdf.setStrokeColor(colors.HexColor("#334155"))
    pdf.setFillColor(colors.HexColor("#f8fafc"))
    pdf.rect(left, bottom, 500, 190, stroke=1, fill=1)
    if signal == "table":
        _draw_table(pdf, left + 34, bottom + 42)
    elif signal == "figure":
        _draw_figure(pdf, left + 250, bottom + 95)
    elif signal == "flow":
        _draw_flow(pdf, left + 40, bottom + 50)
    elif signal == "layout":
        _draw_layout(pdf, left + 40, bottom + 36)
    elif signal == "ocr_failure":
        _draw_ocr_failure(pdf, left + 42, bottom + 62)
    else:
        _draw_mixed_panel(pdf, left + 38, bottom + 54)


def _draw_table(pdf: Any, left: int, bottom: int) -> None:
    pdf.setFont("Helvetica", 8)
    for row in range(5):
        pdf.line(left, bottom + row * 24, left + 420, bottom + row * 24)
    for column in range(4):
        pdf.line(left + column * 140, bottom, left + column * 140, bottom + 96)
    for index, label in enumerate(("limit", "nominal", "alarm"), start=1):
        pdf.drawString(left + index * 140 + 8, bottom + 72, label)


def _draw_figure(pdf: Any, center_x: int, center_y: int) -> None:
    pdf.setFillColor(colors.HexColor("#dbeafe"))
    pdf.circle(center_x, center_y, 42, stroke=1, fill=1)
    pdf.setFillColor(colors.HexColor("#fee2e2"))
    pdf.rect(center_x - 95, center_y - 24, 52, 48, stroke=1, fill=1)
    pdf.setFillColor(colors.HexColor("#dcfce7"))
    pdf.rect(center_x + 44, center_y - 24, 52, 48, stroke=1, fill=1)
    pdf.line(center_x - 43, center_y, center_x + 43, center_y)


def _draw_flow(pdf: Any, left: int, bottom: int) -> None:
    labels = ("scan", "verify", "reset")
    for index, label in enumerate(labels):
        x = left + index * 145
        pdf.roundRect(x, bottom + 46, 92, 42, 6, stroke=1, fill=0)
        pdf.drawString(x + 20, bottom + 62, label)
        if index < len(labels) - 1:
            pdf.line(x + 92, bottom + 67, x + 145, bottom + 67)


def _draw_layout(pdf: Any, left: int, bottom: int) -> None:
    pdf.rect(left, bottom, 130, 120, stroke=1, fill=0)
    pdf.rect(left + 154, bottom, 130, 120, stroke=1, fill=0)
    pdf.rect(left + 308, bottom, 130, 120, stroke=1, fill=0)
    pdf.drawString(left + 18, bottom + 96, "left panel")
    pdf.drawString(left + 172, bottom + 54, "warning band")
    pdf.drawString(left + 326, bottom + 18, "revision box")


def _draw_ocr_failure(pdf: Any, left: int, bottom: int) -> None:
    pdf.setFont("Helvetica", 18)
    pdf.drawString(left, bottom + 74, "S0L-1 / SOL-I / 5O1")
    pdf.setFont("Helvetica", 10)
    for offset in (0, 18, 36):
        pdf.drawString(left + offset, bottom + 34 - offset // 2, "faint label scan")


def _draw_mixed_panel(pdf: Any, left: int, bottom: int) -> None:
    pdf.setFont("Helvetica", 12)
    pdf.drawString(left, bottom + 72, "EN reset -> CN 检查 -> verify")
    pdf.drawString(left, bottom + 38, "A/B columns, footer map, table note")


def _build_query_records(
    family: FamilySpec,
    page: PageSpec,
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for query_index, query_type in enumerate(page.query_types, start=1):
        records.append(
            {
                "query_id": f"{page.page_id}-q{query_index:02d}",
                "query": _query_text(family, page, query_type, query_index),
                "positive_page_ids": [page.page_id],
                "family_id": family.family_id,
                "split": family.split,
                "query_type": query_type,
                "source": {
                    "doc_id": family.family_id,
                    "page_id": page.page_id,
                    "page_number": page.page_number,
                    "description": f"{page.signal} synthetic signal {query_index}",
                },
            }
        )
    return records


def _query_text(
    family: FamilySpec,
    page: PageSpec,
    query_type: str,
    query_index: int,
) -> str:
    if query_type == "table":
        return (
            f"Which table limit is listed on {family.domain} "
            f"page {page.page_number}?"
        )
    if query_type == "figure":
        return (
            f"Find the figure callout for {family.cn_label} "
            f"component F{page.page_number}."
        )
    if query_type == "layout":
        return f"Where is the warning band in the layout for {page.title}?"
    if query_type == "ocr_failure":
        return f"Which faint OCR label like S0L-1 appears on {family.family_id}?"
    return f"What technical domain note appears on {page.title} query {query_index}?"


def _build_summary(
    config: CorpusConfig,
    pages_manifest: Path,
    queries_manifest: Path,
) -> dict[str, object]:
    return {
        "corpus_id": "synthetic-smoke",
        "version": 1,
        "logical_root": config.logical_root,
        "counts": {"families": 3, "pages": 24, "queries": 72},
        "splits": {
            "train": ["manual-a"],
            "dev": ["manual-b"],
            "test": ["manual-c"],
        },
        "query_types": ["figure", "layout", "ocr_failure", "table", "text"],
        "manifests": {
            "pages": _logical_path(config, "pages.jsonl"),
            "queries": _logical_path(config, "queries.jsonl"),
        },
        "manifest_digests": {
            "pages": file_sha256(pages_manifest),
            "queries": file_sha256(queries_manifest),
        },
        "content_hash_algorithm": "sha256(image_bytes + nul + text_bytes)",
        "phase_boundary": "data-format-and-artifacts-only",
    }


def _logical_path(config: CorpusConfig, *parts: str) -> str:
    return "/".join((config.logical_root, *parts))


def _register_cjk_font() -> str:
    try:
        from reportlab.pdfbase import pdfmetrics  # type: ignore[import-untyped]
        from reportlab.pdfbase.cidfonts import (  # type: ignore[import-untyped]
            UnicodeCIDFont,
        )

        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    except Exception:
        return "Helvetica"
    return "STSong-Light"
