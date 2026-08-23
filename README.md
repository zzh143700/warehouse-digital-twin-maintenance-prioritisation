# Warehouse Digital Twin Maintenance Prioritisation

This repository contains the reproducibility package and public literature-audit materials for a Warwick MSc dissertation addressing the following research question:

> Can AI-predicted Remaining Useful Life generate risk-based maintenance priority rankings in a conceptual warehouse digital twin?

The project combines C-MAPSS FD001 Remaining Useful Life (RUL) modelling with an author-developed urgency--consequence index for five virtual warehouse assets. After transfer, C-MAPSS predictions are used only as **surrogate degradation inputs**. They are not warehouse-asset RUL estimates.

## Scope and interpretation boundary

The implementation is a digital-twin-inspired decision-support simulation, not a live warehouse Digital Twin. It has no live sensors, warehouse-management-system connection, work-order feedback or intervention outcomes. The repository supports reproducibility, internal logic checks and controlled sensitivity analysis. It does not validate warehouse failure timing, operational risk, maintenance effectiveness, cost savings or an optimal schedule.

## Repository contents

```text
.
├─ src/                    Data preparation, modelling, simulation and verification
├─ dashboard/              Streamlit interface and verified screenshots
├─ tests/                  Deterministic Dashboard regression tests
├─ source_data/            C-MAPSS FD001 text files used by the workflow
├─ input_data/             Reproducibly generated modelling CSV files
├─ outputs/                Recorded data-audit, model and ranking outputs
├─ docs/                   Data provenance, output dictionary and scenario protocol
├─ literature_data/        Screening decisions, appraisal, metadata and BibTeX files
├─ appendix_materials/     PRISMA files and an appendix-to-repository guide
├─ run_all.ps1             End-to-end Windows workflow
├─ run_dashboard.ps1       Dashboard launcher
└─ requirements.txt        Pinned Python dependencies
```

## Quick verification

Requirements: Windows 10/11, 64-bit Python 3.11--3.13, PowerShell and approximately 2 GB of free disk space.

To create a local virtual environment, install the pinned dependencies and reproduce all analytical outputs:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_all.ps1 -InstallDependencies
```

To verify the recorded outputs without retraining:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_all.ps1 -VerifyOnly
```

To run the deterministic Dashboard tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Dashboard

First launch:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_dashboard.ps1 -InstallDependencies
```

Later launches:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_dashboard.ps1
```

The default address is `http://localhost:8501`. Editing a surrogate input or planning horizon immediately recalculates the current scenario ranking. This interface refresh is not operational real-time synchronisation.

## Reproducible reference results

| Check | Recorded value |
|---|---:|
| Gradient Boosting endpoint MAE | 18.157983 |
| Gradient Boosting endpoint RMSE | 24.868127 |
| Adjacent-score exact-order agreement | 0.935607 |
| Adjacent-score top-ranked agreement | 0.963964 |
| Prediction-noise top-ranked agreement | 0.802000 |
| Prediction-noise exact-order agreement | 0.087000 |

The favourable `0.802` top-ranked result must be interpreted together with the much lower `0.087` complete-order result.

## Literature and appendix materials

`literature_data/literature_screening_public.xlsx` provides a sanitised, human-readable workbook covering the 64-study evidence matrix, quality appraisal, title/abstract screening, PRISMA counts and metadata audit. Machine-readable CSV files and the verified BibTeX library are stored alongside it. Article PDFs, full abstracts, extracted full-text passages and local file paths are deliberately excluded.

See [APPENDIX_GUIDE.md](appendix_materials/APPENDIX_GUIDE.md) for the recommended dissertation appendix structure and exact file mapping.

## Data and software notes

FD001 is a simulated turbofan degradation dataset from the NASA Prognostics Center of Excellence repository. File hashes and the transfer boundary are recorded in [DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md). Before changing a private repository to public, confirm the current NASA redistribution and attribution terms. No journal article PDFs are included.

No open-source licence is granted by this repository unless a licence file is added later. Fitted `joblib` files should be loaded only from a trusted copy of this repository.

