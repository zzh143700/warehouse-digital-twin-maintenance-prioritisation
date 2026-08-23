# Dissertation Appendix Guide and Repository Mapping

## Use principle

The dissertation PDF should contain compact evidence needed to understand and assess the study. Large row-level CSV files, executable code and machine-readable audit records should remain in the repository and be referenced through a stable URL and commit hash. Article PDFs and extracted full text must not be placed in either the appendix or the repository.

## Recommended appendix structure

| Appendix | Content to include in the dissertation | Supporting repository files | Status |
|---|---|---|---|
| Appendix A: Literature Search and Study Selection | Search sources and dates, search-string summary, PRISMA flow diagram, screening criteria and final evidence strata | `literature_data/database_search_log.md`; `literature_data/prisma_counts_*.csv`; `literature_data/title_abstract_screening_decisions.csv`; `appendix_materials/prisma_flowchart.*` | Prepared |
| Appendix B: Literature Quality and Citation Audit | Appraisal criteria, score ranges, 64-study quality summary and metadata-verification note | `literature_data/quality_appraisal_all64.csv`; `literature_data/literature_metadata_audit.csv`; `literature_data/literature_screening_public.xlsx`; `literature_data/literature_corpus_64_verified.bib` | Prepared |
| Appendix C: Data Provenance and Preparation | NASA FD001 source, SHA-256 hashes, data structure, integrity checks, RUL-target construction and transfer boundary | `docs/DATA_PROVENANCE.md`; `outputs/data_audit/`; `src/prepare_fd001_data.py` | Prepared |
| Appendix D: RUL Modelling and Validation | Grouped-validation design, candidate configurations, selected parameters, fold metrics and endpoint results | `src/run_fd001_models.py`; `outputs/model_outputs/model_cv_search_results.csv`; `model_cv_fold_metrics.csv`; `model_run_summary.json` | Prepared |
| Appendix E: Warehouse Scenario and Priority Index | Five virtual assets, score anchors, surrogate-input assignment, equations, planning horizon, weights and baselines | `docs/warehouse_scenario_protocol.md`; `outputs/ranking_outputs/warehouse_base_mapping_and_ranking.csv`; `warehouse_controlled_checks.json` | Prepared |
| Appendix F: Sensitivity and Robustness Evidence | Compact summary of score, weight, horizon, assignment-design, ablation and prediction-noise tests | `outputs/ranking_outputs/*summary.csv`; detailed row files in the same directory; `warehouse_ranking_summary.json` | Prepared |
| Appendix G: Interactive Dashboard | One interface screenshot, displayed outputs, user controls and non-live boundary | `dashboard/screenshots/`; `docs/DASHBOARD_SPEC.md`; `dashboard/streamlit_app.py`; `tests/test_dashboard_logic.py` | Prepared |
| Appendix H: Reproducibility and Code Availability | Repository URL, immutable commit hash, software versions, commands, file inventory and verification result | `README.md`; `requirements.txt`; `run_all.ps1`; `run_dashboard.ps1`; `VERIFICATION.md`; `.github/workflows/verify.yml` | Add URL and commit after upload |

## Recommended compact appendix tables

The PDF appendices should include the following tables rather than pasting complete CSV files:

- A1: Search platforms, search dates and recorded result counts.
- A2: Title/abstract and full-text screening counts.
- B1: Quality-appraisal criteria and allowable scores.
- B2: Numbers of core, supporting-method and background/review studies.
- C1: FD001 file names, SHA-256 hashes, rows and engine counts.
- D1: Candidate model settings and the grouped-validation selection rule.
- D2: Fold-level and endpoint MAE/RMSE.
- E1: Five virtual assets and author-assigned consequence parameters.
- E2: Priority equations, base horizon, alternative horizons and weight schemes.
- F1: Baseline, sensitivity, ablation and residual-resampling summary.
- G1: Dashboard controls, outputs and validation boundary.
- H1: Reproduction commands, software versions and verification checks.

## Ready-to-paste code-availability statement

> The reproducibility package is available at [GitHub repository URL], archived at commit `[commit hash]`. It contains the data-integrity checks, RUL modelling scripts, prioritisation simulation, pinned dependencies, recorded seeds, generated summary outputs, Dashboard implementation and automated verification tests. The package uses C-MAPSS FD001 predictions only as surrogate degradation inputs after transfer to the conceptual warehouse scenario. Article PDFs and extracted full text are excluded for copyright compliance.

## Ready-to-paste appendix note for large files

> Detailed row-level simulation outputs and literature-screening records are provided in the accompanying GitHub repository rather than reproduced in full in the dissertation appendix. The appendix reports the criteria, principal summary tables and file inventory required to interpret those materials.

## Final checks before submission

- Replace both placeholders in the code-availability statement with the final repository URL and commit hash.
- Confirm whether the repository will remain private, be shared directly with the supervisor, or become public for examination.
- If made public, confirm NASA FD001 redistribution terms or remove `source_data/` and provide download instructions plus hashes.
- Keep the 80.2% leading-asset result together with the 8.7% complete-order result.
- Do not describe repository verification as real-world warehouse validation.

