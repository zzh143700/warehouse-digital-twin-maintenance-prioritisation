# Verification Record

Verification date: 23 August 2026  
Platform: Windows 11, 64-bit Python 3.13.9

## Tests performed

The curated repository directory was tested after reorganisation, rather than relying only on results from the source working directory.

| Test | Command | Result |
|---|---|---|
| End-to-end reconstruction | `powershell -ExecutionPolicy Bypass -File .\run_all.ps1 -PythonPath <verified-python>` | PASS |
| Recorded-output verification | `powershell -ExecutionPolicy Bypass -File .\run_all.ps1 -VerifyOnly -PythonPath <verified-python>` | PASS |
| Dashboard regression tests | `python -m unittest discover -s tests -v` | PASS: 5 of 5 tests |
| Literature-workbook formula scan | Search for `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?` and `#N/A` | PASS: 0 matches |

`<verified-python>` denotes the existing isolated project environment used for the release audit. A new user can create an equivalent local `.venv` and install the pinned dependencies by running `run_all.ps1 -InstallDependencies`.

## Verified analytical outputs

| Check | Result |
|---|---:|
| FD001 training engines | 100 |
| FD001 test engines | 100 |
| Seeded asset rows | 5,000 |
| Assignment repetitions | 1,000 |
| Adjacent-score comparisons | 28,000 |
| Gradient Boosting endpoint MAE | 18.157983 |
| Gradient Boosting endpoint RMSE | 24.868127 |
| Adjacent-score exact-order agreement | 0.935607 |
| Adjacent-score top-ranked agreement | 0.963964 |
| Prediction-noise top-ranked agreement | 0.802000 |
| Prediction-noise exact-order agreement | 0.087000 |

The automated verifier also confirmed five assets and five RUL quintiles in every assignment, weights summing to one, all controlled mathematical checks, and the surrogate-only transfer boundary.

## Interpretation boundary

These tests establish that the recorded computational workflow is internally consistent and reproducible in the tested environment. They do not constitute validation of warehouse RUL estimates, operational risk, maintenance effectiveness or a live Digital Twin.
