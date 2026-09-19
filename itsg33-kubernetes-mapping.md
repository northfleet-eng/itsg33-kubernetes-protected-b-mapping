# ITSG-33 Protected B to Kubernetes mapping

A working mapping from the Government of Canada Protected B / Medium control profile to the Kubernetes mechanisms that address each control. The profile is CCCS ITSP.10.033-01 (Medium impact), effective April 2026, which supersedes ITSG-33 Annex 4A Profile 1 (Protected B / Medium Integrity / Medium Availability). Control identifiers and titles follow ITSP.10.033.

## Scope

ITSP.10.033-01 selects approximately 385 controls and enhancements from the ITSP.10.033 catalogue (this repository's count from the published PDF tables). This mapping does not enumerate all of them. It enumerates the procurement-relevant subset for an engineering team or procurement officer reviewing a Kubernetes-based platform for Protected B workloads: roughly 50 controls where the Kubernetes side of the mapping is non-obvious or carries a material gap.

Every control in the three tables below is selected in ITSP.10.033-01. Controls that are new since Annex 4A Profile 1, or that a tailored profile is likely to add, are in the final section.

For the full enumeration, refer to the canonical sources in [`SOURCES.md`](SOURCES.md).

## Three implementation categories

Controls map into one of three categories depending on where the mechanism lives:

1. **Admin-implemented**: a cluster administrator configures the mechanism using upstream Kubernetes primitives (RBAC, NetworkPolicy, audit policy, admission, and so on). No additional component required.
2. **Workload-implemented**: the application or container image itself provides the mechanism (app-level authentication, app-level logging, app-level field encryption).
3. **External**: upstream Kubernetes alone cannot satisfy the control. An additional component is required (signing infrastructure, runtime security tooling, SIEM, immutable backup destination, and so on).

The third category is the most procurement-relevant. It is where vendor evaluations diverge.

---

## Admin-implemented controls

| Control | Title | Kubernetes mechanism |
|---|---|---|
| AC-2 | Account management | ServiceAccounts; OIDC integration with the corporate identity provider; RBAC RoleBindings |
| AC-3 | Access enforcement | RBAC (Roles, ClusterRoles); `--authorization-mode=Node,RBAC` |
| AC-4 | Information flow enforcement | NetworkPolicy; Gateway API; namespace boundaries |
| AC-5 | Separation of duties | Namespace partitioning combined with RBAC scoping |
| AC-6 | Least privilege | Fine-grained RBAC verbs; no wildcard verbs; controlled `system:masters` membership |
| AC-11 | Device lock | Short OIDC token lifetimes enforced by the identity provider; dashboard idle timeout |
| AC-17 | Remote access | kube-apiserver reachable only through a VPN or bastion; pair with SI-400 and AC-17(400) below |
| AU-2, AU-3 | Event logging; Content of audit records | kube-apiserver audit policy file; audit log or webhook backend |
| AU-4 | Audit log storage capacity | Log forwarding to an external store; persistent-volume sizing for local audit |
| AU-9 | Protection of audit information | Read-only audit forwarding; separate audit credentials |
| AU-12 | Audit record generation | Audit policy rules with `level: RequestResponse` for security-relevant resources; `Metadata` elsewhere |
| CM-2 | Baseline configuration | Declarative manifests under GitOps (Argo CD, Flux) as the baseline |
| CM-3 | Configuration change control | Pull-request review on the infrastructure repository; admission webhooks for runtime enforcement |
| CM-6 | Configuration settings | Pod Security Admission (`restricted` profile); policy engines such as OPA Gatekeeper or Kyverno |
| CM-7 | Least functionality | Pod Security `restricted`; anonymous authentication disabled; insecure ports disabled |
| CM-8 | System component inventory | Cluster inventory via the API; inventory CRDs; SBOMs attached to images and checked at admission |
| IA-2 | Identification and authentication (organizational users) | OIDC to an identity provider that enforces MFA; short-lived tokens |
| IA-3 | Device identification and authentication | kubelet TLS bootstrap; certificate signing request approval workflow |
| IA-5 | Authenticator management | Projected service-account tokens with audience and expiry; token rotation |
| SC-2 | Separation of system and user functionality | Namespaces; separation between control-plane and data-plane workloads |
| SC-5 | Denial-of-service protection | ResourceQuotas; LimitRanges; API Priority and Fairness on the apiserver |
| SC-7 | Boundary protection | NetworkPolicy default-deny; Ingress controller; egress gateway |
| SC-8 | Transmission confidentiality and integrity | TLS on kube-apiserver; etcd peer TLS; service-mesh mTLS |
| SC-12 | Cryptographic key establishment and management | KMS provider plugin for etcd encryption at rest |
| SC-13 | Cryptographic protection | FIPS-validated modules; CSE-approved cryptographic algorithms per ITSP.40.111 |
| SC-23 | Session authenticity | TLS everywhere; mTLS via service mesh; anonymous endpoints disabled |
| SC-28 | Protection of information at rest | etcd encryption at rest (`--encryption-provider-config`); CSI driver-level encrypted volumes |
| SI-2 | Flaw remediation | Patch cadence policy; managed control plane; node image rotation |
| SI-4 (partial) | System monitoring | kube-apiserver audit logs; metrics-server; cluster monitoring stack |

---

## Workload-implemented controls

| Control | Kubernetes mechanism |
|---|---|
| AC-3 (workload RBAC) | Application-level RBAC inside the workload, distinct from cluster RBAC |
| AU-3, AU-12 (workload audit) | Structured application logging to stdout, picked up by node-level log collectors |
| IA-2 (end-user auth) | Application-level OIDC or SAML for end-user identity, distinct from cluster-operator identity |
| SC-8 (in-app TLS) | Application-level TLS termination when a service mesh is not present |
| SC-13, SC-28 (in-app crypto) | Application-level field encryption or envelope encryption for sensitive fields |
| SI-10 | Information input validation in application code |
| SI-11 | Sanitized error handling in application code |

---

## External controls (upstream Kubernetes alone is insufficient)

This is the gap analysis. For each control below, upstream Kubernetes cannot satisfy the requirement without an additional component. The choice of component is left to the implementing organization. Examples are listed for orientation, not endorsement.

| Control | Why upstream Kubernetes is insufficient | Category of external mechanism |
|---|---|---|
| CM-5 | No built-in image-signature verification on the admission path. ValidatingAdmissionPolicy can pin digests but cannot check signatures | Image-signing verification at admission (e.g. sigstore policy-controller, Connaisseur, Kyverno verify-images) |
| CM-8(3) | No native verification of software composition against an authoritative inventory | SBOM generation at build and verification at admission (e.g. Syft, Grype) |
| SA-10(1) | No native build-provenance attestation | Build-attestation framework (e.g. in-toto, SLSA provenance, Rekor transparency log) |
| SA-11 | No native vulnerability or threat analysis of running workloads | Vulnerability scanner (e.g. Trivy, Grype, commercial alternatives) |
| SA-15 | The control sits in the development pipeline, not the cluster | CI/CD pipeline with signed builds and recorded provenance |
| SI-3 | Kubernetes has no built-in malicious-code detection at runtime. The profile's suggested parameters call for definition updates at least every 30 days and quarantine on detection | Runtime detection (e.g. Falco, Tetragon, commercial alternatives) |
| SI-4 (runtime monitoring) | apiserver audit captures control-plane activity, not workload-level behaviour | Runtime observability and detection (e.g. Falco, Cilium Hubble, eBPF-based tooling) |
| SI-7 | No native file-integrity monitoring | Runtime integrity monitoring or immutable root filesystem patterns |
| AU-6 | Audit log emission is not the same as review, analysis, or correlation | Security information and event management (SIEM) ingestion |
| AU-9(2) | Local audit destinations are not separation-of-duty compliant | Forwarder to immutable write-once storage on a separate system |
| IR-4 | No native incident-handling or response workflow | Security orchestration, automation, and response (SOAR) tooling |
| CA-7 | Continuous monitoring spans multiple capabilities | Continuous compliance scanner (e.g. Kubescape, Trivy, Compliance Operator) |
| CP-9 | etcd snapshot covers cluster state, not application state | Workload backup (e.g. Velero, Kasten K10) plus offsite or air-gapped retention |
| CP-10 | Recovery within RTO requires application-state replication | Replicated storage; database clustering |
| SC-12(1) | The KMS itself is an external system | KMS or HSM (e.g. Vault, cloud KMS, on-premise HSM) |
| SC-17 | The Kubernetes cluster CA signs kubelet certificates, not workload certificates | cert-manager integrated with a corporate or private public-key infrastructure |

---

## New in ITSP.10.033-01

These controls did not exist in Annex 4A Profile 1, exist under a new number, or carry over with a parameter worth restating. Profile 1 selected no supply chain control at all (SA-12, SA-19, and every enhancement were Not Selected), so the SR rows are the largest change. Status is as published in ITSP.10.033-01; a department's tailored profile may differ.

| Control | Status | What it asks | Kubernetes relevance |
|---|---|---|---|
| SA-400 | Selected | Sovereignty and jurisdiction: the organization conducts a sovereignty and jurisdiction threat and risk assessment covering injury from external legal compulsion, jurisdiction-specific threat, vulnerability, and risk | Organizational, not a cluster mechanism. The assessment needs evidence about where images are built, signed, and hosted, where the KMS and registry sit, and under whose law each counterparty operates. A vendor's delivery chain should be able to answer those questions in writing |
| SA-400(1) to SA-400(7) | Not selected | Enhancements on data at rest, in transit, in use, extraterritorial protection, and legal or contractual assessment | Departments with higher-value data may select these. Each one maps to where a registry, KMS, signing service, or backup destination is allowed to reside |
| SI-400 | Selected | Dedicated administration workstation: administrative or superuser actions are performed from a physical workstation dedicated to those tasks, isolated from other functions and networks, and from any form of internet access | Admin. Cluster-admin `kubectl` access, GitOps repository writes, and KMS administration should be possible only from such a workstation. Design the bastion or jump-host pattern under AC-17 around it |
| AC-17(400) | Selected (renumbered from AC-17(100), which Profile 1 also selected) | Privileged accounts remote access: remote access to privileged accounts only from dedicated management consoles | Admin. Restrict `system:masters` and cluster-admin bindings to identities that can only originate from the SI-400 workstation |
| SI-7(1) | Selected; carried over from Profile 1 with the same parameter, integrity-check frequency at no longer than 30 days | Integrity checks at startup, on transitional states or security-relevant events, and on a frequency | External. Image digest pinning, signature verification at admission, and a periodic re-verification of running images and manifests against the signed baseline |
| SR-3, SR-5, SR-6, SR-8, SR-10, SR-11, SR-11(2) | Selected | Supply chain controls and processes; acquisition strategies; supplier assessments and reviews; notification agreements for supply chain compromise; inspection of components for tampering; component authenticity and configuration control for components in service or repair | Organizational and external. SBOMs, build provenance, signature verification, and a tamper-evident record of what was delivered and applied are the evidence these controls consume. SR-8 in particular expects a written notification agreement with every supplier in the chain |
| SR-4, SR-4(3), SR-4(4) | Not selected | Provenance: document, monitor, and maintain provenance; validate as genuine and not altered; supply chain integrity pedigree | The Rev. 5 home for build provenance and attestation. Not in the Medium profile, but the most likely tailoring addition for a software supply chain, and the control that SLSA-style provenance answers directly |
| CM-14 | Not selected | Signed components: prevent installation of software without verification of a digital signature under an organization-approved certificate | The Rev. 5 home for image-signature enforcement. Not in the Medium profile; this mapping keeps CM-5 as the selected control that admission-time signature verification supports |

---

## Notes on the mapping

**This mapping is a starting point, not a substitute for a formal security control assessment.** A qualified Canadian assessor performs the actual assessment against the customer's specific deployment. This document is for engineering teams reasoning about the gap between upstream Kubernetes and the Protected B control profile, and for procurement officers reasoning about what external tooling a vendor offering must bring.

**Canadian-specific controls are numbered from 400.** Under Annex 3A the same convention started at 100 (AC-17(100), IA-8(100), PE-2(100)). ITSP.10.033-01 selects SA-400, SI-400, AC-17(400), AC-21(400), and several PE-400-series physical controls; the ones relevant to a Kubernetes platform are in the table above.

**ITSP.10.033-01 is comparable to the NIST SP 800-53 Moderate baseline in selection density.** A vendor with a FedRAMP Moderate authorization has done a significant portion of the work; gaps remain in the 400-series controls and in the CSE-approved cryptography requirements of ITSP.40.111.

**Security assurance levels.** Annex 4A Profile 1 suggested SAL2 for the majority of controls and SAL3 for critical controls, with criticality determined by the project. ITSP.10.033-01 carries its own assurance guidance in section 3.1. Neither is enumerated in this mapping.

## Companion files

- [`itsg33-kubernetes-mapping.csv`](itsg33-kubernetes-mapping.csv): same content as CSV for spreadsheet import, with an ITSP.10.033-01 status column
- [`SOURCES.md`](SOURCES.md): canonical CCCS source URLs for the current and superseded series
- [`CHANGELOG.md`](CHANGELOG.md): what changed between releases
- [`README.md`](README.md): repository overview
- [`LICENSE`](LICENSE): Apache License 2.0
