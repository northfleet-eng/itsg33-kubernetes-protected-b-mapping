# ITSG-33 to Kubernetes Protected B mapping

An open-source mapping of CCCS ITSG-33 Annex 4A Profile 1 (Protected B / Medium Integrity / Medium Availability) security controls to the Kubernetes mechanisms that address them.

## What this is

A working reference (Markdown for diff-friendliness, with companion `.csv` for spreadsheet import) that pairs Protected B-applicable ITSG-33 controls with the Kubernetes mechanisms that address each one. Controls are bucketed by where the mechanism lives:

- **Admin-implemented** — cluster administrator configures upstream Kubernetes primitives (RBAC, NetworkPolicy, audit policy, etc.)
- **Workload-implemented** — the application or container image itself provides the mechanism
- **External** — upstream Kubernetes alone is insufficient and an additional component is required

The third category is the gap analysis. It is where vendor evaluations diverge.

## Why this exists

ITSG-33 is the canonical Canadian IT security risk management guidance, published by the Canadian Centre for Cyber Security. The Annex 4A Profile 1 catalogue applies to federal and defence workloads classified at Protected B with Medium integrity and availability requirements. Every Canadian defence-tech vendor, accreditation consultant, and procurement officer evaluating a Kubernetes-based platform produces some version of this mapping internally. This repository publishes one openly so that the procurement vocabulary is shared.

## Files in this repository

- [`itsg33-kubernetes-mapping.md`](itsg33-kubernetes-mapping.md) — the main mapping. Controls bucketed by admin / workload / external, with K8s mechanism for each.
- [`itsg33-kubernetes-mapping.csv`](itsg33-kubernetes-mapping.csv) — same content as CSV for spreadsheet import.
- [`SOURCES.md`](SOURCES.md) — canonical CCCS source URLs, cross-reference mappings, and the NIST SP 800-53 relationship.
- [`LICENSE`](LICENSE) — Apache License 2.0.

## Scope

This repository covers the procurement-relevant subset of Profile 1: approximately 30 to 50 controls where the Kubernetes side of the mapping is non-obvious or carries material gap. Profile 1 in full contains approximately 295 base controls and enhancements; the full enumeration is in the canonical sources linked in [`SOURCES.md`](SOURCES.md).

This repository is a starting point, not a substitute for a formal security control assessment. A qualified Canadian accreditor performs the actual assessment against the customer's specific deployment.

## How to use

1. Open [`itsg33-kubernetes-mapping.md`](itsg33-kubernetes-mapping.md) or import [`itsg33-kubernetes-mapping.csv`](itsg33-kubernetes-mapping.csv) into a spreadsheet.
2. Walk the **Admin-implemented** table to confirm each upstream Kubernetes feature is configured correctly.
3. Walk the **Workload-implemented** table to confirm each application meets its share of the control.
4. Walk the **External** table to identify which additional components your environment requires and which vendor is responsible for each.

## Methodology

- **Source baseline**: the community-maintained `cds-snc/ITSG-33-baselines/PBMM.yaml`, cross-referenced against CCCS canonical sources. Where the two diverge, the CCCS version (Annex 4A Profile 1 PDF and Excel) is authoritative.
- **Selection of priority controls**: bias toward controls where upstream Kubernetes alone does not satisfy the requirement, or where the K8s mechanism is non-obvious to engineering teams.
- **External-component examples**: listed for orientation. The choice of specific component (which signing infrastructure, which runtime-security tool, which SIEM, etc.) is intentionally left to the implementing organization.

## Open items

- One pass of cross-checking the community baseline `PBMM.yaml` against the CCCS-distributed Excel (available on request via `itsclientservices@cse-cst.gc.ca`) before treating this mapping as authoritative for procurement decisions.
- Canadian-tailored enhancements (any enhancement number ≥ 100) are noted where they appear in the priority subset but are not enumerated comprehensively. A separate pass enumerating only the ≥ 100 enhancements would be a useful follow-up artifact.

Issues and pull requests welcome.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).

## Maintained by

Northfleet (`https://northfleet.tech`). Issues and pull requests welcome.

## Disclaimer

This mapping is provided as-is for evaluation and planning use. It is not a CCCS-endorsed assessment instrument. For authoritative guidance, refer to the source documents in [`SOURCES.md`](SOURCES.md).
