## ADDED Requirements

### Requirement: Configured retrieval candidate universe
The system SHALL distinguish the evaluated query split from the candidate page
universe used for ranking.

#### Scenario: Evaluated-split universe preserves current smoke behavior
- **WHEN** a text diagnostic config selects `dev` as the evaluated split and
           `evaluated_split_pages` as the candidate universe
- **THEN** the report ranks dev queries only against dev pages and records the
           candidate universe as evaluated-split pages

#### Scenario: Non-train universe uses non-train candidate pages
- **WHEN** a text diagnostic config selects `dev` as the evaluated split and
           `non_train_pages` as the candidate universe
- **THEN** the report ranks dev queries against non-train pages while still
           recording final test query evaluation as `not_run`

#### Scenario: All-pages universe is explicit
- **WHEN** a text diagnostic config selects `all_pages` as the candidate
           universe
- **THEN** the report ranks evaluated queries against all manifest pages and
           labels the run as all-pages diagnostic retrieval

### Requirement: Candidate universe report support
The system SHALL report candidate page support, candidate split counts, and
evaluated query support for every retrieval diagnostic report.

#### Scenario: Candidate support is present in the report
- **WHEN** a retrieval diagnostic report is generated
- **THEN** it includes the candidate universe name, candidate page count,
           candidate split counts, evaluated split list, and evaluated query
           count

#### Scenario: Candidate universe changes are not model improvements
- **WHEN** two reports use different candidate universes
- **THEN** the reports do not describe metric differences as retrieval
           improvement, model superiority, or final benchmark results

### Requirement: Candidate universe boundary
The candidate universe layer SHALL NOT create new corpus data, hard-negative
triples, final-test query evaluation, model downloads, embedding caches, or
benchmark result claims.

#### Scenario: Wider candidate pool remains diagnostic
- **WHEN** a non-train or all-pages candidate universe is configured
- **THEN** the report remains diagnostic-only and records no hard-negative
           output, no final-test evaluation, no training run, and no benchmark
           claim
