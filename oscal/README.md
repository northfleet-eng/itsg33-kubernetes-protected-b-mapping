# ITSP.10.033 and the Medium profile in OSCAL

A machine-readable rendering of the Government of Canada's security control catalogue (CCCS ITSP.10.033, effective March 31, 2026) and its Medium impact profile (ITSP.10.033-01, effective April 1, 2026) in [OSCAL](https://pages.nist.gov/OSCAL/) 1.1.3, plus this repository's Kubernetes mapping as an OSCAL component definition.

CCCS publishes both documents as PDF only. This directory transcribes them, validates every file with the NIST reference tooling, and rebuilds the whole set in CI on every change. It is unofficial and has not been reviewed or endorsed by CCCS. Where anything here disagrees with the PDFs, the PDFs are right, and an issue is welcome.

## What is here

| Path | What it is |
|---|---|
| [`resolved/itsp.10.033-01-medium.json`](resolved/itsp.10.033-01-medium.json) | **Start here.** The Medium profile resolved to a single catalog: the 384 controls, activities and enhancements Table 4 marks Selected, in CCCS's wording, with the profile's suggested parameter values and notes. |
| [`resolved/itsp.10.033-01-medium.csv`](resolved/itsp.10.033-01-medium.csv) | The same, one row per control, for spreadsheets. |
| [`resolved/itsp.10.033.json`](resolved/itsp.10.033.json), [`.csv`](resolved/itsp.10.033.csv) | The full ITSP.10.033 catalogue: all 1,248 controls, activities and enhancements, including the 189 withdrawn. |
| [`catalogs/itsp.10.033-canadian-controls.json`](catalogs/itsp.10.033-canadian-controls.json) | The 53 controls and enhancements that NIST SP 800-53 does not define: the 400 series (SA-400, SI-400, AC-17(400), PE-400, and the rest) and SC-19, which NIST withdrew and CCCS kept. Transcribed in full: statement, parameters, discussion, GC discussion, related controls, references. |
| [`profiles/itsp.10.033/profile.json`](profiles/itsp.10.033/profile.json) | The catalogue as a profile: NIST SP 800-53 Rev. 5.2.0 plus the Canadian catalog, with CCCS's statement wording and GC discussion attached to each of the 1,014 active NIST-derived controls. |
| [`profiles/itsp.10.033-01-medium/profile.json`](profiles/itsp.10.033-01-medium/profile.json) | The Medium profile: selections, parameter values, notes. |
| [`component-definitions/upstream-kubernetes.json`](component-definitions/upstream-kubernetes.json) | The repository's mapping as a component definition: what upstream Kubernetes and a containerized workload can implement against the Medium profile. |
| [`reports/gap-upstream-kubernetes.md`](reports/gap-upstream-kubernetes.md) | Selected controls minus claimed controls, computed. |
| [`reports/diff-aws-cccs-oscal-samples.md`](reports/diff-aws-cccs-oscal-samples.md) | This rendering of the Medium profile against the other public one. |
| [`src/`](src/) | Transcribed sources: Table 4 of ITSP.10.033-01 as CSV (every row of the 139-page table), CCCS's wording for every control, and the pinned inputs with their SHA-256. |
| [`scripts/`](scripts/) | Extraction, build, and report tools. |

## OSCAL in one paragraph

OSCAL is NIST's schema family for compliance documents as data, in JSON, XML or YAML. A **catalog** is a rulebook: every control, its statement, its parameters. A **profile** selects and tailors controls from one or more catalogs; the Medium profile is one. **Resolving** a profile flattens it and everything it imports into a single catalog, which is what tooling consumes. A **component definition** records which controls a component can implement, and how. If you know Kubernetes: the catalog is the API, the profile is an overlay, resolution is the build, and the component definition is the manifest.

## How it is built

```
CCCS PDFs ──extract (by hand, reviewed)──▶ src/, catalogs/
NIST 800-53 5.2.0 (pinned) ─┐
src/, catalogs/ ────────────┴─build_profiles──▶ profiles/ ──oscal-cli resolve──▶ resolved/
itsg33-kubernetes-mapping.csv ──▶ component-definitions/ ──gap.py──▶ reports/
```

- **Extraction** (`extract_table4.py`, `extract_canadian.py`, `extract_cccs_wording.py`) reads the PDFs by position and text. Its output is committed and reviewed against the PDFs; CI does not run it. Re-running it against the pinned PDFs reproduces the committed files byte for byte.
- **Build** (`build.sh`) regenerates the profiles, resolves them with oscal-cli 3.2.0, normalizes the result, exports CSV, rebuilds the component definition and the gap report, and validates every OSCAL document. It is deterministic: CI rebuilds on every push and fails if the output differs from what is committed.
- **Normalization** (`normalize.py`) exists because oscal-cli's as-is merge keeps each import's groups separate. It folds the Canadian controls into their families, nests each Canada-specific enhancement under its base control (AC-17(400) under AC-17), and replaces per-run identifiers and timestamps with content-derived ones.
- **Pinned inputs** are in [`src/sources.json`](src/sources.json). A weekly CI job re-fetches the two CCCS PDFs and fails if either has changed, which is how a silent revision of the rulebook shows up here.

Compliance Trestle 5.1 reads every file in this directory, and its independent profile resolver produces the same 384 controls as oscal-cli. Trestle resolves relative import paths against the working directory rather than the profile's location, so run it from the profile's directory.

## Using it

```bash
# Build and validate everything (needs python3, Java 17+, oscal-cli on PATH)
scripts/build.sh

# What does the profile ask for that a component definition does not claim?
python3 scripts/gap.py resolved/itsp.10.033-01-medium.json your-component-definition.json

# What changed between two resolved catalogues (a vendor's rendering, or two revisions of this one)?
python3 scripts/diff_resolved.py resolved/itsp.10.033-01-medium.json other-resolved.json

# Re-run the transcription from the PDFs
scripts/fetch.sh --pdfs && pip install -r scripts/requirements.txt
python3 scripts/extract_table4.py vendor/itsp.10.033-01-e.pdf src/itsp.10.033-01-table4.csv
```

A system security plan built on the Medium profile imports `profiles/itsp.10.033-01-medium/profile.json` (or the resolved catalog) as its baseline; `gap.py` runs against any component definition, including your platform's.

## How CCCS's text is carried

- **Canada-specific controls** are transcribed in full into `catalogs/`, with their parameters as OSCAL parameters.
- **NIST-derived controls** keep NIST's statement, parameters, and SP 800-53A assessment objectives, because that structure is what tooling binds to. CCCS rewords many of them (Orders in Council for executive orders, Canada for the Nation, and in the PT family whole statements rewritten for the Privacy Act). Each carries CCCS's statement verbatim in a `cccs-statement` part, its GC discussion in a `gc-guidance` part, and its CCCS title and control-or-activity type as props. Read the `cccs-statement` part, not the NIST statement, for the Canadian requirement. The CSV exports use the CCCS wording.
- **Parameter values** from Table 4 are bound to the NIST parameter each fills. Where CCCS gives a value per statement item and NIST has one parameter for all of them (AC-2(3)), the value names the item. The 13 values and their bindings are listed in `build_profiles.py`.
- Custom parts and props use the namespace `https://northfleetsecurity.ca/ns/oscal/cccs`.

## Where the two CCCS documents disagree

Transcribing both documents side by side surfaced these. Each is carried as published and noted here rather than silently resolved.

- **SI-2(4), Automated patch management tools.** Active, with a statement, in the catalogue; "Withdrawn: Incorporated into SI-02" in the profile's Table 4. Active in the full catalogue here; not selected in the Medium profile.
- **AC-2(10), Shared and group account credential change.** Withdrawn in both documents (incorporated into AC-2), but Table 4 marks it Selected. Selected here as published; it resolves as a withdrawn stub, so the Medium profile has 383 active controls plus that one.
- **SA-15(13), SA-24 and SI-2(7).** In the catalogue (all three arrived with NIST SP 800-53 Rev. 5.2.0), absent from Table 4 altogether. In the full catalogue here; not in the Medium profile.

## Scope and limits

- The Medium profile's own tailoring guidance applies: departments tailor it, and a tailored profile can select controls this one does not.
- The component definition covers the controls in the repository's mapping, which is the procurement-relevant subset. It states what upstream Kubernetes can do, not what any cluster does.
- Canadian-added statement items inside NIST controls (the "AA." items, for example CP-9 AA.) are in the `cccs-statement` text but are not yet separate statement parts with their own identifiers.
- The discussion sections of NIST-derived controls are NIST's. CCCS's general discussion is largely NIST's text; its GC discussion is carried in full.
- English only. The French editions are not transcribed.

## Licence and attribution

The repository's own structure, scripts, and component definition are under the Apache License 2.0 ([`../LICENSE`](../LICENSE)).

The CCCS text in `catalogs/`, `src/`, `profiles/`, and `resolved/` is transcribed from ITSP.10.033 and ITSP.10.033-01, which the Government of Canada publishes under the Open Government Licence – Canada ([ITSP.10.033](https://open.canada.ca/data/en/dataset/ddad8760-bf9b-47aa-890d-67da202aca6a), [ITSP.10.033-01](https://open.canada.ca/data/en/dataset/06179c95-a0e0-446f-8f53-9208f8b41eb9)). Contains information licensed under the Open Government Licence – Canada.

NIST SP 800-53 content, imported at build time from [usnistgov/oscal-content](https://github.com/usnistgov/oscal-content) and present in `resolved/`, is a work of the United States Government and is not subject to copyright in the United States.
