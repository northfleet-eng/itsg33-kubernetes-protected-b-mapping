# Canonical sources

The Canadian Centre for Cyber Security (CCCS) pages and PDFs below are the authoritative texts behind the controls in this repository. The ITSP.10.033 series is current. The ITSG-33 annexes are superseded but still published, and still referenced by accreditation packages written before spring 2026.

## CCCS: ITSP.10.033 series (current)

- **Cyber security and privacy risk management: A lifecycle approach (series landing page):** <https://www.cyber.gc.ca/en/guidance/cyber-security-privacy-risk-management>
- **Security and privacy controls and assurance activities catalogue (ITSP.10.033), foreword, overview, and introduction:** <https://www.cyber.gc.ca/en/guidance/cyber-security-privacy-risk-management/itsp10033/foreword-overview-introduction>. Supersedes ITSG-33 Annex 3A. Effective March 31, 2026. Aligned to NIST SP 800-53 Rev. 5.
- **Suggested organizational security and privacy control and activity profile, Medium impact (ITSP.10.033-01):** <https://www.cyber.gc.ca/en/guidance/cyber-security-privacy-risk-management/suggested-organizational-security-privacy-control-activity-profile-medium-impact-itsp10033-01>. Supersedes Annex 4A Profile 1. Effective April 2026.
- **ITSP.10.033-01 PDF (catalogue number D97-3/10-033-01-2026E-PDF):** <https://www.cyber.gc.ca/sites/default/files/itsp.10.033-01-e.pdf>
- **Organizational cyber security and privacy risk management activities (ITSP.10.036):** <https://www.cyber.gc.ca/en/guidance/cyber-security-privacy-risk-management/organizational-cyber-security-privacy-risk-management-activities-itsp10036>. Supersedes ITSG-33 Annex 1. Effective September 14, 2026. Covers the assessment and authorization framework, control profiles, and continuous authorization, with commercial service providers named in its audience.

CCCS distributes a spreadsheet of the ITSP.10.033-01 selections on request from <contact@cyber.gc.ca>. It is the authoritative cross-check for any machine-readable list, including the CSV in this repository.

## CCCS: ITSG-33 (superseded, still published)

- **IT security risk management: A lifecycle approach (ITSG-33), master document:** <https://www.cyber.gc.ca/en/guidance/it-security-risk-management-lifecycle-approach-itsg-33>
- **Annex 1, Departmental IT security risk management activities** (superseded by ITSP.10.036 on September 14, 2026): <https://www.cyber.gc.ca/en/guidance/annex-1-departmental-it-security-risk-management-activities-itsg-33>
- **Annex 3A, Security control catalogue** (superseded by ITSP.10.033 on March 31, 2026): <https://www.cyber.gc.ca/en/guidance/annex-3a-security-control-catalogue-itsg-33>
- **Annex 4A Profile 1, Protected B / Medium Integrity / Medium Availability** (superseded by ITSP.10.033-01): <https://www.cyber.gc.ca/en/guidance/annex-4a-profile-1-protected-b-medium-integrity-medium-availability-itsg-33>
- **Annex 4A Profile 1 PDF:** <https://www.cyber.gc.ca/sites/default/files/cyber/publications/itsg33-ann4a-1-eng.pdf>
- **Suggested security controls and control enhancements:** <https://www.cyber.gc.ca/en/guidance/suggested-security-controls-and-control-enhancements-itsg-33>

The legacy Annex 4A page still directs spreadsheet requests to the former CSE IT Security Client Services address. Use <contact@cyber.gc.ca> for the current series.

## CCCS: cryptographic and protocol guidance

- **Cryptographic algorithms for UNCLASSIFIED, PROTECTED A, and PROTECTED B information (ITSP.40.111):** <https://www.cyber.gc.ca/en/guidance/cryptographic-algorithms-unclassified-protected-protected-b-information-itsp40111>. Current revision effective May 29, 2026.
- **Guidance on securely configuring network protocols (ITSP.40.062):** <https://www.cyber.gc.ca/en/guidance/guidance-securely-configuring-network-protocols-itsp40062>

## Government of Canada: cloud-specific overlay

- **Government of Canada Security Control Profile for Cloud-based IT Services:** <https://www.canada.ca/en/government/system/digital-government/digital-government-innovations/cloud-services/government-canada-security-control-profile-cloud-based-it-services.html>

## Machine-readable renderings

CCCS publishes ITSP.10.033 and ITSP.10.033-01 as PDF only. The Open Government Portal lists both under the Open Government Licence – Canada: [ITSP.10.033](https://open.canada.ca/data/en/dataset/ddad8760-bf9b-47aa-890d-67da202aca6a), [ITSP.10.033-01](https://open.canada.ca/data/en/dataset/06179c95-a0e0-446f-8f53-9208f8b41eb9).

- **This repository, [`oscal/`](oscal/):** the catalogue and the Medium profile in OSCAL 1.1.3, transcribed from the April 2026 PDFs, pinned by SHA-256.
- **NIST SP 800-53 Rev. 5.2.0 in OSCAL:** <https://github.com/usnistgov/oscal-content>. The base the rendering here imports.
- **aws-samples/cccs-oscal-samples:** <https://github.com/aws-samples/cccs-oscal-samples>. Unofficial, maintained by AWS; its ITSP.10.033-01 profile is dated April 28, 2025. The differences from the rendering here are in [`oscal/reports/diff-aws-cccs-oscal-samples.md`](oscal/reports/diff-aws-cccs-oscal-samples.md).
- **cds-snc/ITSG-33-baselines `PBMM.yaml`:** <https://github.com/cds-snc/ITSG-33-baselines/blob/master/PBMM.yaml>. Last updated in 2018; predates ITSP.10.033 and does not match the Annex 4A Profile 1 PDF row for row. Historical reference only.
- **For comparison, an official OSCAL publication:** the Australian Signals Directorate publishes the Information Security Manual in OSCAL with each release, <https://www.cyber.gov.au/business-government/asds-cyber-security-frameworks/ism/ism-oscal-releases>.

The CCCS PDFs are authoritative over every rendering listed here, including this repository's.

## Cross-references and adjacent mappings

These external publications cover similar mapping work. Use them as cross-checks, not source of truth.

- **2026 Minimum Elements for a Software Bill of Materials (SBOM), joint guidance co-sealed by CCCS (July 2026):** <https://www.cyber.gc.ca/en/news-events/joint-guidance-minimum-elements-software-bill-materials>. Replaces the 2021 NTIA minimum elements; the reference for what an SBOM under CM-8 and CM-8(3) should contain.
- **NSA / CISA Kubernetes Hardening Guidance v1.2 (August 2022):** <https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220829.PDF> (the host refuses automated fetches; open in a browser)
- **CIS Kubernetes Benchmark:** <https://www.cisecurity.org/benchmark/kubernetes>
- **CIS Controls v8.1 mapping to NIST SP 800-53 Rev. 5:** <https://www.cisecurity.org/insights/white-papers/cis-controls-v8-1-mapping-to-nist-sp-800-53-rev-5>
- **Google Kubernetes Engine Policy Controller, NIST SP 800-53 Rev. 5 constraints:** <https://cloud.google.com/kubernetes-engine/enterprise/policy-controller/docs/how-to/using-nist-sp-800-53-r5>
- **Kubernetes SIG-Security policy management paper:** <https://github.com/kubernetes/sig-security/blob/main/sig-security-docs/papers/policy/kubernetes-policy-management.md>

## NIST SP 800-53 relationship

ITSP.10.033 is an adapted version of NIST SP 800-53 Rev. 5, reflecting Canadian business and legislative requirements. Its predecessor, ITSG-33 Annex 3A, was derived from NIST SP 800-53 Rev. 4. Base control identifiers are unchanged across the transition. Some Rev. 4 enhancements were withdrawn or moved in Rev. 5, and ITSP.10.033-01 records those (for example, SI-7(14) moved to CM-7(8)).

Canadian-specific controls and enhancements are numbered from 400 in ITSP.10.033. Examples selected in the Medium profile include SA-400 (Sovereignty and jurisdiction), SI-400 (Dedicated administration workstation), AC-17(400), and PE-400. Under Annex 3A the same convention started at 100 (AC-17(100), AC-19(100), AC-21(100), IA-8(100), PE-2(100)). These have no NIST SP 800-53 equivalent and require Canadian-specific implementation guidance.

Annex 3A carried 17 families. ITSP.10.033 adds PM (Program management), PT (Personal information and transparency), and SR (Supply chain risk management), the last of which is directly relevant to any software delivery chain.

ITSP.10.033-01 is comparable to the NIST SP 800-53 Moderate baseline in selection density, though not identical. A vendor with a FedRAMP Moderate authorization has done a significant portion of the work; gaps remain in the 400-series controls and in the CSE-approved cryptography requirements of ITSP.40.111.

## What this repository is not

This mapping is not a CCCS-endorsed assessment instrument. It is a community starting point for engineering teams and procurement officers reasoning about the gap between upstream Kubernetes and the Protected B control profile.

A formal security control assessment for a Protected B authorization must be performed by a qualified Canadian assessor against the customer's specific deployment. The output of that assessment is the authoritative document.
