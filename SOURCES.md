# Canonical sources

The following Canadian Centre for Cyber Security (CCCS) pages are the authoritative texts behind the controls in this repository.

## CCCS — ITSG-33 master and annexes

- **Master document — IT security risk management: A lifecycle approach (ITSG-33):** <https://www.cyber.gc.ca/en/guidance/it-security-risk-management-lifecycle-approach-itsg-33>
- **Annex 1 — Departmental IT security risk management activities:** <https://www.cyber.gc.ca/en/guidance/annex-1-departmental-it-security-risk-management-activities-itsg-33>
- **Annex 3A — Security Control Catalogue:** <https://www.cyber.gc.ca/en/guidance/annex-3a-security-control-catalogue-itsg-33>
- **Annex 4A Profile 1 (Protected B / Medium Integrity / Medium Availability):** <https://www.cyber.gc.ca/en/guidance/annex-4a-profile-1-protected-b-medium-integrity-medium-availability-itsg-33>
- **Annex 4A Profile 1 PDF (1.73 MB):** <https://www.cyber.gc.ca/sites/default/files/cyber/publications/itsg33-ann4a-1-eng.pdf>
- **Suggested security controls and control enhancements:** <https://www.cyber.gc.ca/en/guidance/suggested-security-controls-and-control-enhancements-itsg-33>

CCCS distributes an Excel version of the Profile 1 selections on request via `itsclientservices@cse-cst.gc.ca`. The Excel is useful as an authoritative cross-check against the machine-readable baseline noted below.

## CCCS — cryptographic and algorithm guidance

- **ITSP.40.111 (cryptographic algorithms):** <https://www.cyber.gc.ca/en/guidance/cryptographic-algorithms-unclassified-protected-information-itsp40111>
- **ITSP.40.062 (guidance on securely configuring network protocols):** <https://www.cyber.gc.ca/en/guidance/guidance-securely-configuring-network-protocols-itsp40062>

## Government of Canada — cloud-specific overlay

- **Government of Canada Security Control Profile for Cloud-based IT Services:** <https://www.canada.ca/en/government/system/digital-government/digital-government-innovations/cloud-services/government-canada-security-control-profile-cloud-based-it-services.html>

## Community machine-readable baseline

- **cds-snc/ITSG-33-baselines `PBMM.yaml`** (Canadian Digital Service maintains, sourced from CCCS): <https://github.com/cds-snc/ITSG-33-baselines/blob/master/PBMM.yaml>

This repository's mapping uses the community baseline as the machine-readable enumeration of Profile 1 controls. Where the community baseline diverges from the CCCS-authored Excel, the CCCS version is authoritative.

## Cross-references and adjacent mappings

These external publications cover similar mapping work. Use them as cross-checks, not source-of-truth.

- **NSA / CISA Kubernetes Hardening Guidance v1.2 (August 2022):** <https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220829.PDF>
- **CIS Kubernetes Benchmark:** <https://www.cisecurity.org/benchmark/kubernetes>
- **CIS Controls v8.1 mapping to NIST SP 800-53 Rev 5:** <https://www.cisecurity.org/insights/white-papers/cis-controls-v8-1-mapping-to-nist-sp-800-53-rev-5>
- **Google Kubernetes Engine Policy Controller — NIST SP 800-53 Rev 5 constraints:** <https://cloud.google.com/kubernetes-engine/enterprise/policy-controller/docs/how-to/using-nist-sp-800-53-r5>
- **Kubernetes SIG-Security policy management paper:** <https://github.com/kubernetes/sig-security/blob/main/sig-security-docs/papers/policy/kubernetes-policy-management.md>

## NIST SP 800-53 relationship

ITSG-33 Annex 3A is structurally derived from NIST SP 800-53 (Rev 4 lineage with Rev 5 alignment underway). Same 17 families, same two-letter family codes, same numbering convention.

Canadian-tailored additions are identifiable by enhancement number 100 or higher (for example `AC-17(100)`, `AC-19(100)`, `IA-8(100)`, `PE-2(100)`). These have no NIST SP 800-53 equivalent and require Canadian-specific implementation guidance.

Profile 1 (PBMM) approximates the NIST SP 800-53 Moderate baseline in selection density, though it is not identical. A vendor with a FedRAMP Moderate authorization has done a significant portion of the work; gaps remain in Canadian-tailored enhancements and in CSE-approved cryptography requirements.

## What this repository is not

This mapping is not a CCCS-endorsed assessment instrument. It is a community starting point for engineering teams and procurement officers reasoning about the gap between upstream Kubernetes and the Protected B control catalogue.

A formal security control assessment for a Protected B accreditation must be performed by a qualified Canadian accreditor against the customer's specific deployment. The output of that assessment is the authoritative document.
