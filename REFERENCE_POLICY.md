# Reference policy — precedence and conflict handling
Snapshot: 2026-11-20. Authority is attached to *individual claims and scoped runs*, not headings or whole files.

## Order (highest first)
1. Immutable, hash-verified empirical run artifact **for that exact experiment/population**.
2. Bound source + executable tests at a specific revision.
3. Accepted decision record/contract, for its accepted scope.
4. Current source-linked synthesis, which remains revisable.
5. Historical runtime descriptions.
6. Research/proposed designs and unactivated policy.
7. Superseded roadmap and archive.

A frozen result establishes *what happened under its configuration*, not universal architecture. Later synthesis can supersede a historical interpretation, never rewrite a frozen source.

## Conflict procedure
Record claim IDs, the exact conflicting statements, source locator, revision, date and scope. Distinguish (a) factual contradiction, (b) configuration/period difference, (c) incompatible metrics/denominators, (d) proposed vs active behavior. Resolve using directly bound evidence; otherwise mark UNRESOLVED, block promotion and preserve both sources. 'CURRENT', 'V2', 'FINAL' or 'PRODUCTION' filenames give no privilege.

## Evidence handling
A transfer must be byte-identical to original or labeled excerpt/curation. Keep original URL, provenance, version/hash where known, source confidence, sensitivity screening, and explicit immutable-vs-mutable status. No guessed hashes. For a public repo use sanitized summaries or links when source data may be sensitive; never treat a pointer as a copied frozen artifact.

## Promotion
An experiment moves to a clean build only via [governance/EXPERIMENT_PROMOTION_POLICY.md](governance/EXPERIMENT_PROMOTION_POLICY.md), with valid holdout and downstream utility, not ranking movement alone. Negative evidence remains discoverable. Release claims must bind source, corpus, config, model, evaluator, prompt, population, run, metrics and validity.