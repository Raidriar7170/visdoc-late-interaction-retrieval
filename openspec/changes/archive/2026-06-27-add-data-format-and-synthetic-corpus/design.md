## Context

Phase 0 created a Python skeleton with OpenSpec as the source of truth and no data
surfaces. Phase 1 needs the first page-level retrieval data contract so future text,
visual, hard-negative, and training phases can work from stable manifests instead of ad
hoc files.

This change introduces a small synthetic technical corpus for smoke testing only. It is
not a benchmark result surface, and it must not introduce retrieval, ranking metrics,
model inference, hard-negative mining, or training.

## Goals / Non-Goals

**Goals:**

- Define page and query manifest records with deterministic validation.
- Generate a small synthetic technical PDF corpus with 3 document families, 24 pages,
  and 72 query relevance records.
- Render every PDF page to a deterministic page image and text fixture.
- Split by family so train/dev/test page leakage can be checked cheaply.
- Record content hashes for generated page artifacts and manifests.
- Keep tests local, deterministic, and CPU-only.

**Non-Goals:**

- No BM25, dense, hybrid, ColPali, ColQwen, reranker, embedding, or retrieval scoring
  implementation.
- No Recall@k, MRR, NDCG, latency, index size, or benchmark report generation.
- No hard-negative triple mining; only the leakage guard needed by future mining phases
  is introduced.
- No LoRA/QLoRA training or model download.
- No final result table or improvement claim.

## Decisions

1. Generate a fixed smoke corpus instead of checking in large hand-authored fixtures.

   The generator will materialize `data/synthetic-smoke/` with PDFs, rendered PNG page
   images, OCR-like text files, page/query manifests, and a summary. Tests can also
   generate the corpus in a temporary directory and compare digests. The alternative,
   committing only static fixtures, would make determinism harder to prove and would not
   exercise the generation path.

2. Use `reportlab` for PDF generation and `PyMuPDF` for page rendering.

   These are document-processing dependencies, not retrieval/model dependencies. They
   support true PDF and PNG outputs while keeping the phase CPU-only. The alternative,
   SVG-only pseudo-pages, would be lighter but less faithful to the future visual
   retrieval path.

3. Keep schemas as typed Python validators plus JSONL manifests.

   The page and query manifests are stored as JSONL so future retrieval phases can
   stream them easily. Validators use standard Python types and explicit checks rather
   than introducing Pydantic or a separate schema runtime. The alternative, JSON Schema
   files only, would document shape but leave Python callers without a canonical
   validation path.

4. Split by family.

   The smoke corpus uses one train family, one dev family, and one test family. This is
   intentionally conservative for leakage checks and future hard-negative mining. The
   alternative, random per-query splits, would make family/topic leakage more likely.

5. Keep generated corpus size small and deterministic.

   The default corpus is 3 families x 8 pages and 3 queries per page. This lands inside
   the project brief's smoke range while keeping tests fast and local.

## Risks / Trade-offs

- PDF renderer differences across library versions -> Tests compare manifest-level
  hashes and generated file inventory, not pixel-level screenshots across platforms.
- Binary generated artifacts can add repository weight -> Keep the materialized smoke
  corpus small and deterministic.
- Synthetic data may look too clean -> Include tables, figures, flow diagrams,
  specification pages, troubleshooting pages, Chinese labels, and OCR-failure-style
  queries, but leave realism expansion to later changes.
- Leakage guard could be mistaken for hard-negative mining -> Name and document it as
  validation-only; it must not emit training triples.
