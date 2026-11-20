# Frozen evaluator offline replay — 2026-11-20

**Classification:** `LOCAL_OFFLINE_REPLAY_PASS_WITH_HISTORICAL_ARTIFACT_BLOCKERS`

## Provenance
Original `src/v2_evaluator/`, `src/v2_evaluation_contract.py`, `tests/test_v2_evaluator.py`, `tests/test_v2_evaluator_artifacts.py` and the selected frozen fixtures were obtained through the connected private Google Drive source folder `irg_ai-main`. All ten evaluator code/test files independently matched the SHA-256 values in `evaluation/frozen/V2_EVALUATOR_MANIFEST_v1.json`. The source files were copied **only** into an isolated temporary workspace, never this public repository.

## Executed offline tests
- Core replay: `PYTHONPATH=<isolated_workspace> python -m pytest tests/test_v2_evaluator.py -q --disable-warnings --maxfail=1`
  - **17 passed** in ~0.18 seconds (reported by pytest).
- Selected core + artifact replay: `PYTHONPATH=<isolated_workspace> python -m pytest tests/test_v2_evaluator.py tests/test_v2_evaluator_artifacts.py -q --disable-warnings -k 'not frozen_authority_is_unchanged and not every_manifest_bound_file_hash_matches and not builder_reproduces_exact_canonical_artifact_bytes'`
  - **20 passed, 3 deliberately deselected** in ~0.15 seconds.

The first direct invocation failed during collection with `ModuleNotFoundError: No module named src.v2_evaluation_contract` because PYTHONPATH omitted the isolated workspace. The corrected invocation passed. This environment-only import error is not counted as a product regression.

## Deliberately deselected artifact checks
- `test_frozen_authority_is_unchanged`: its `FROZEN` binding demands original `V2_MASTER_REGRESSION_MANIFEST_v1.json` bytes with evaluator SHA-256 `9ddf9eaf...`; the only available current Drive master manifest has SHA-256 `fa6b6291...`.
- `test_every_manifest_bound_file_hash_matches`: requires the complete all-file evaluator dependency closure beyond the selected isolated sources.
- `test_builder_reproduces_exact_canonical_artifact_bytes`: requires complete builder inputs and historical artifact closure, including the missing evaluator-bound revision.

**No tests were modified, omitted from the source files, or relabeled as passing.** Historical focused-test evidence previously reported broader offline 23/23; this replay independently verified only the selected 20 with 3 deselections, not historical 23/23 reproducibility.

## Qualification boundary
Owner approval artifact `V2_EVALUATOR_APPROVAL_v1.json` freezes the evaluator implementation; it explicitly leaves release qualification `NOT_EXECUTED`, the qualification plan `PENDING`, and live execution unauthorized. No OpenAI/Qdrant/MySQL/provider calls or production writes occurred in these tests. `IRG-X001` remains `UNRESOLVED`.

## Follow-up
Recover the evaluator-bound master manifest revision `9ddf9eaf...` and fully recreate the artifact/source closure. Then rerun the three deselected integrity tests in a newly bound isolated environment before any strict qualification claim.
