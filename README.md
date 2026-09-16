# ITSG-33 to Kubernetes Protected B mapping

An open-source mapping of the Government of Canada Protected B / Medium security control profile to the Kubernetes mechanisms that address each control.

The profile is CCCS **ITSP.10.033-01**, *Suggested organizational security and privacy control and activity profile, Medium impact*, in force since April 2026. It supersedes ITSG-33 Annex 4A Profile 1 (Protected B / Medium Integrity / Medium Availability), the profile this mapping was originally written against. The repository keeps the ITSG-33 name because that is still what accreditation packages, RFPs, and search queries call it.

## What this is

A working reference (Markdown for diff-friendliness, with a companion `.csv` for spreadsheet import) that pairs Protected B-applicable controls with the Kubernetes mechanisms that address each one. Controls are bucketed by where the mechanism lives:

- **Admin-implemented**: a cluster administrator configures upstream Kubernetes primitives (RBAC, NetworkPolicy, audit policy, and so on).
- **Workload-implemented**: the application or container image itself provides the mechanism.
- **External**: upstream Kubernetes alone is insufficient and an additional component is required.

The third category is the gap analysis. It is where vendor evaluations diverge.

## Why this exists

ITSG-33 is the Canadian IT security risk management framework published by the Canadian Centre for Cyber Security (CCCS). Its control catalogue and profiles were replaced in spring 2026 by the ITSP.10.033 series, aligned to NIST SP 800-53 Rev. 5. Anyone evaluating a Kubernetes-based platform for Protected B workloads ends up producing some version of this mapping internally. This repository publishes one openly so that the procurement vocabulary is shared.

## The 2026 transition from ITSG-33 to ITSP.10.033

- **March 31, 2026:** ITSP.10.033, *Security and privacy controls and assurance activities catalogue*, superseded ITSG-33 Annex 3A. It is aligned to NIST SP 800-53 Rev. 5 and adds three families: PM (Program management), PT (Personal information and transparency), and SR (Supply chain risk management).
- **April 2026:** ITSP.10.033-01 superseded Annex 4A Profile 1. The PDF gives an effective date of April 1, 2026; the web page says April 2.
- **September 14, 2026:** ITSP.10.036, *Organizational cyber security and privacy risk management activities*, superseded ITSG-33 Annex 1. The ITSG-33 master document and its remaining annexes are being replaced piece by piece under the same series.
- **Canadian-specific controls were renumbered.** Enhancements that previously started at 100 now start at 400. AC-17(100) is now AC-17(400).
- **Base control identifiers did not change.** Every control in this mapping keeps its ID, and every one of them is selected in ITSP.10.033-01. The CSV carries the status column.
- **New selected controls that touch a Kubernetes platform** (SA-400, SI-400, AC-17(400), SI-7(1), and the SR family) are covered in the mapping's [New in ITSP.10.033-01](itsg33-kubernetes-mapping.md#new-in-itsp10033-01) section.

## Files in this repository

- [`itsg33-kubernetes-mapping.md`](itsg33-kubernetes-mapping.md): the main mapping. Controls bucketed by admin / workload / external, with the Kubernetes mechanism for each, plus the ITSP.10.033-01 additions.
- [`itsg33-kubernetes-mapping.csv`](itsg33-kubernetes-mapping.csv): same content as CSV, one row per control and category, with an ITSP.10.033-01 status column.
- [`SOURCES.md`](SOURCES.md): canonical CCCS source URLs for the current ITSP.10.033 series and the superseded ITSG-33 annexes, cross-reference mappings, and the NIST SP 800-53 relationship.
- [`CHANGELOG.md`](CHANGELOG.md): what changed between releases of this mapping.
- [`LICENSE`](LICENSE): Apache License 2.0.

## Scope

This repository covers the procurement-relevant subset of the profile: roughly 50 controls where the Kubernetes side of the mapping is non-obvious or carries a material gap. ITSP.10.033-01 selects approximately 385 controls and enhancements in total (this repository's count from the published PDF tables; Annex 4A Profile 1 selected a similar number). The full enumeration is in the canonical sources linked in [`SOURCES.md`](SOURCES.md).

ITSP.10.033-01 is a *suggested organizational* profile. Departments and agencies tailor it, and a tailored profile can select controls this one does not. SR-4 (Provenance) and CM-14 (Signed components) are the two most likely additions for a software supply chain. Confirm against the customer's tailored profile before relying on any selection status here.

This repository is a starting point, not a substitute for a formal security control assessment. A qualified Canadian assessor performs the actual assessment against the customer's specific deployment.

## How to use

1. Open [`itsg33-kubernetes-mapping.md`](itsg33-kubernetes-mapping.md) or import [`itsg33-kubernetes-mapping.csv`](itsg33-kubernetes-mapping.csv) into a spreadsheet.
2. Walk the **Admin-implemented** table to confirm each upstream Kubernetes feature is configured correctly.
3. Walk the **Workload-implemented** table to confirm each application meets its share of the control.
4. Walk the **External** table to identify which additional components your environment requires and which vendor is responsible for each.
5. Walk the **New in ITSP.10.033-01** table to catch the controls that did not exist under Annex 4A Profile 1.

## Methodology

- **Source of truth:** the CCCS-published PDFs. ITSP.10.033-01 for current selection status; Annex 4A Profile 1 for the original selection this mapping was built from. Where any secondary source diverges, the CCCS PDF is authoritative.
- **Community baseline:** the `cds-snc/ITSG-33-baselines/PBMM.yaml` file is a convenient machine-readable list, but it was last updated in 2018, predates ITSP.10.033, and does not match the Annex 4A PDF row for row. It is referenced for convenience only.
- **Selection of priority controls:** bias toward controls where upstream Kubernetes alone does not satisfy the requirement, or where the Kubernetes mechanism is non-obvious to engineering teams.
- **External-component examples:** listed for orientation, not endorsement. The choice of specific component (which signing infrastructure, which runtime-security tool, which SIEM) is left to the implementing organization.
- **Control titles** follow ITSP.10.033 (Rev. 5 wording), so AC-11 reads "Device lock" rather than the Annex 3A "Session lock".

## Open items

- Cross-check this mapping against the CCCS spreadsheet of ITSP.10.033-01 (available on request from contact@cyber.gc.ca) before treating it as authoritative for a procurement decision.
- Extend the New in ITSP.10.033-01 section to the full 400-series enumeration once departmental tailoring practice is visible.
- A Secret-level companion (Annex 4A Profile 3 and whatever succeeds it in the ITSP.10.033 series) is out of scope here.

Issues and pull requests welcome.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).

## Maintained by

Northfleet (`https://northfleetsecurity.ca`). Issues and pull requests welcome.

## Disclaimer

This mapping is provided as-is for evaluation and planning use. It is not a CCCS-endorsed assessment instrument. For authoritative guidance, refer to the source documents in [`SOURCES.md`](SOURCES.md).
