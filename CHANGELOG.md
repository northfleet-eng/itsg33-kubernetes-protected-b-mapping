# Changelog

## 2026-09-23

- Added [`oscal/`](oscal/): ITSP.10.033 (1,248 controls, activities and enhancements) and the ITSP.10.033-01 Medium profile (384 selected) in OSCAL 1.1.3, built on NIST SP 800-53 Rev. 5.2.0. The 53 Canada-specific controls and enhancements are transcribed in full; every NIST-derived control carries CCCS's statement wording and GC discussion; the 13 parameter values Table 4 suggests are bound to NIST parameters. Every document validates with oscal-cli 3.2.0 and loads in Compliance Trestle 5.1.
- Added this mapping as an OSCAL component definition (upstream Kubernetes and containerized workload), with a computed gap report: selected controls minus claimed controls.
- Added CI: rebuild, validate, and fail on drift on every change; weekly check of the CCCS PDFs against their pinned SHA-256.
- Recorded three places where ITSP.10.033 and ITSP.10.033-01 disagree (SI-2(4), AC-2(10), and SA-15(13), SA-24, SI-2(7)); see [`oscal/README.md`](oscal/README.md).
- Replaced "approximately 385" with the exact count from the transcribed Table 4: 384, one of them withdrawn.

## 2026-09-18

- Corrected the "New in ITSP.10.033-01" section: SI-7(1) at 30 days is carried over from Annex 4A Profile 1, not new; AC-17(400) is AC-17(100) renumbered. Noted that Profile 1 selected no supply chain control (SA-12, SA-19, and all enhancements Not Selected).

## 2026-09-16

- Re-baselined against CCCS ITSP.10.033-01 (Medium impact profile, effective April 2026), which supersedes ITSG-33 Annex 4A Profile 1. Every control previously cited remains selected; the CSV now carries an ITSP.10.033-01 status column.
- Added a "New in ITSP.10.033-01" section covering SA-400 (Sovereignty and jurisdiction), SI-400 (Dedicated administration workstation), AC-17(400), SI-7(1), the SR family, and the not-selected SR-4 and CM-14 that tailored profiles are most likely to add.
- Control titles updated to ITSP.10.033 (NIST SP 800-53 Rev. 5) wording.
- Corrected the profile size. The earlier figure of approximately 295 controls and enhancements was wrong for both Annex 4A Profile 1 and ITSP.10.033-01; both select approximately 385.
- Corrected Kubernetes details: audit policy uses `level`, not stage; `--authorization-mode=Node,RBAC`; bound service-account tokens described by mechanism rather than the retired feature-gate name; SBOMs are generated at build and verified at admission; API Priority and Fairness added under SC-5.
- Added ITSP.10.036 (effective September 14, 2026, supersedes Annex 1) and the July 2026 joint SBOM minimum-elements guidance to the sources.
- Fixed the ITSP.40.111 link (the old path returned 404) and noted the revision effective May 29, 2026.
- Replaced the retired `northfleet.tech` domain with `northfleetsecurity.ca`.
- Demoted the community `PBMM.yaml` baseline from source baseline to convenience reference (last updated 2018, predates ITSP.10.033).

## 2026-05-23

- Initial release: ITSG-33 Annex 4A Profile 1 (Protected B / Medium Integrity / Medium Availability) mapped to Kubernetes mechanisms, bucketed by admin, workload, and external.
