# Literature Data Package

This folder contains the machine-readable audit trail used to support the dissertation literature review and citation checking.

| File | Rows or scope | Purpose |
|---|---:|---|
| `literature_screening_public.xlsx` | Six worksheets | Sanitised workbook combining the main screening, evidence, appraisal and metadata records |
| `title_abstract_screening_decisions.csv` | 85 records | Include, Maybe or Exclude decisions with recorded reasons |
| `prisma_counts_title_abstract.csv` | 12 recorded metrics | Historical title/abstract-stage PRISMA counts |
| `prisma_counts_full_text.csv` | 7 recorded metrics | Completed full-text-stage counts and evidence strata |
| `quality_appraisal_all64.csv` | 64 studies | Criterion-level appraisal scores and concise quality notes |
| `literature_metadata_audit.csv` | 64 studies | Title, year and DOI verification audit |
| `literature_corpus_64_verified.bib` | 64 records | Verified BibTeX library |
| `database_search_log.md` | Search log | Recorded enrichment searches and result counts |

## Publication boundary

The public workbook excludes direct article excerpts, full abstracts, PDF file names, extracted-text paths and local filesystem paths. The repository does not contain downloaded article PDFs or extracted full-text files. Screening and appraisal statements are researcher-produced audit records, not substitutes for reading and citing the original studies.

The initial `6,416` identification figure is a recorded sum of displayed platform result counts and includes cross-database overlap, including an approximate Google Scholar count. It must not be interpreted as 6,416 unique records.

