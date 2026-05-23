# ITSG-33 Profile 1 Protected B to Kubernetes mapping

A working mapping from CCCS ITSG-33 Annex 4A Profile 1 (Protected B / Medium Integrity / Medium Availability) security controls to the Kubernetes mechanisms that address them.

## Scope

Profile 1 (PBMM) selects approximately 295 base controls and enhancements from the ITSG-33 Annex 3A catalogue. This mapping does not enumerate all 295. It enumerates the procurement-relevant subset for an engineering team or procurement officer reviewing a Kubernetes-based platform for Protected B workloads: roughly 30 to 50 controls where the Kubernetes side of the mapping is non-obvious or carries material gap.

For the full Profile 1 enumeration, refer to the canonical sources in [`SOURCES.md`](SOURCES.md).

## Three implementation categories

Controls map into one of three categories depending on where the mechanism lives:

1. **Admin-implemented**: a cluster administrator configures the mechanism using upstream Kubernetes primitives (RBAC, NetworkPolicy, audit policy, admission, etc.). No additional component required.
2. **Workload-implemented**: the application or container image itself provides the mechanism (app-level authentication, app-level logging, app-level field encryption).
3. **External**: upstream Kubernetes alone cannot satisfy the control. An additional component is required (signing infrastructure, runtime security tooling, SIEM, immutable backup destination, etc.).

The third category is the most procurement-relevant. It is where vendor evaluations diverge.

---

## Admin-implemented controls

| Control | Title (paraphrased) | Kubernetes mechanism |
|---|---|---|
| AC-2 | Account management | ServiceAccounts, OIDC integration with corporate identity provider, RBAC RoleBindings |
| AC-3 | Access enforcement | RBAC (Roles, ClusterRoles), `--authorization-mode=RBAC,Node` |
| AC-4 | Information flow enforcement | NetworkPolicy, Gateway API, namespace boundaries |
| AC-5 | Separation of duties | Namespace partitioning combined with RBAC scoping |
| AC-6 | Least privilege | Fine-grained RBAC verbs, no wildcard verbs, controlled `system:masters` membership |
| AC-11 | Session lock | kubectl session timeouts via OIDC identity provider; dashboard idle timeout |
| AC-17 | Remote access | kube-apiserver behind VPN or jump host; bastion patterns |
| AU-2, AU-3 | Audit events and content | kube-apiserver audit policy file; audit webhook |
| AU-4 | Audit storage capacity | Log forwarding to external store; persistent-volume sizing for local audit |
| AU-9 | Audit protection | Read-only audit forwarding; separate audit credentials |
| AU-12 | Audit generation | Audit policy stage set to `RequestResponse` |
| CM-2 | Baseline configuration | Declarative manifests under GitOps (Argo CD, Flux) as the baseline |
| CM-3 | Configuration change control | Pull-request review on infrastructure repository; admission webhooks for runtime enforcement |
| CM-6 | Configuration settings | Pod Security Admission (`restricted` profile), policy engines such as OPA Gatekeeper or Kyverno |
| CM-7 | Least functionality | Pod Security `restricted`, anonymous authentication disabled, insecure ports disabled |
| CM-8 | System component inventory | Cluster inventory via `kubectl get`, inventory CRDs, SBOM generation at admission |
| IA-2 | User identification and authentication | OIDC to identity provider that enforces MFA; short-lived tokens |
| IA-3 | Device identification and authentication | kubelet TLS bootstrap, certificate signing request approval workflow |
| IA-5 | Authenticator management | ServiceAccount token rotation, `BoundServiceAccountTokenVolume` |
| SC-2 | Application partitioning | Namespaces, separation between control-plane and data-plane workloads |
| SC-5 | Denial-of-service protection | ResourceQuotas, LimitRanges, PodDisruptionBudgets |
| SC-7 | Boundary protection | NetworkPolicy default-deny, Ingress controller, egress gateway |
| SC-8 | Transmission confidentiality | TLS on kube-apiserver, etcd peer TLS, service-mesh mTLS |
| SC-12 | Cryptographic key establishment | KMS provider plugin for etcd encryption-at-rest |
| SC-13 | Cryptographic protection | FIPS-validated modules; CSE-approved cryptographic algorithms per ITSP.40.111 |
| SC-23 | Session authenticity | TLS everywhere; mTLS via service mesh; anonymous endpoints disabled |
| SC-28 | Protection of information at rest | etcd encryption-at-rest (`--encryption-provider-config`); CSI driver-level encrypted volumes |
| SI-2 | Flaw remediation | Patch cadence policy; managed control plane; node image rotation |
| SI-4 (partial) | Information system monitoring | kube-apiserver audit logs; metrics-server; cluster monitoring stack |

---

## Workload-implemented controls

| Control | Kubernetes mechanism |
|---|---|
| AC-3 (workload RBAC) | Application-level RBAC inside the workload, distinct from cluster RBAC |
| AU-3, AU-12 (workload audit) | Structured application logging to stdout, picked up by node-level log collectors |
| IA-2 (end-user auth) | Application-level OIDC or SAML for end-user identity, distinct from cluster-operator identity |
| SC-8 (in-app TLS) | Application-level TLS termination when a service mesh is not present |
| SC-13, SC-28 (in-app crypto) | Application-level field encryption or envelope encryption for sensitive fields |
| SI-10 | Input validation in application code |
| SI-11 | Sanitized error handling in application code |

---

## External controls (upstream Kubernetes alone is insufficient)

This is the gap analysis. For each control below, upstream Kubernetes cannot satisfy the requirement without an additional component. The choice of component is left to the implementing organization. Examples are listed for orientation, not endorsement.

| Control | Why upstream Kubernetes is insufficient | Category of external mechanism |
|---|---|---|
| CM-5 | No native image-signing enforcement on the admission path | Image-signing verification at admission (e.g. sigstore policy-controller, Connaisseur, Kyverno verify-images) |
| CM-8(3) | No native verification of software composition against an authoritative inventory | SBOM generation and verification (e.g. Syft, Grype) plus admission-time checks |
| SA-10(1) | No native build-provenance attestation | Build-attestation framework (e.g. in-toto, SLSA provenance, Rekor transparency log) |
| SA-11 | No native vulnerability or threat analysis of running workloads | Vulnerability scanner (e.g. Trivy, Grype, commercial alternatives) |
| SA-15 | The control sits in the development pipeline, not the cluster | CI/CD pipeline with signed builds and recorded provenance |
| SI-3 | Kubernetes has no built-in malicious-code detection at runtime | Runtime detection (e.g. Falco, Tetragon, commercial alternatives) |
| SI-4 (runtime monitoring) | apiserver audit captures control-plane activity, not workload-level behaviour | Runtime observability and detection (e.g. Falco, Cilium Hubble, eBPF-based tooling) |
| SI-7 | No native file-integrity monitoring | Runtime integrity monitoring or immutable root filesystem patterns |
| AU-6 | Audit log emission is not the same as analysis or correlation | Security information and event management (SIEM) ingestion |
| AU-9(2) | Local audit destinations are not separation-of-duty compliant | Forwarder to immutable write-once storage |
| IR-4 | No native incident-handling or response workflow | Security orchestration, automation, and response (SOAR) tooling |
| CA-7 | Continuous monitoring spans multiple capabilities | Continuous compliance scanner (e.g. Kubescape, Trivy, Compliance Operator) |
| CP-9 | etcd snapshot covers cluster state, not application state | Workload backup (e.g. Velero, Kasten K10) plus offsite or air-gapped retention |
| CP-10 | Recovery within RTO requires application-state replication | Replicated storage; database clustering |
| SC-12(1) | The KMS itself is an external system | KMS or HSM (e.g. Vault, cloud KMS, on-premise HSM) |
| SC-17 | The Kubernetes cluster CA signs kubelet certificates, not workload certificates | cert-manager integrated with a corporate or private public-key infrastructure |

---

## Notes on the mapping

**This mapping is a starting point, not a substitute for a formal security control assessment.** A qualified Canadian accreditor performs the actual assessment against the customer's specific deployment. This document is for engineering teams reasoning about the gap between upstream Kubernetes and the Protected B control catalogue, and for procurement officers reasoning about what external tooling a vendor offering must bring.

**Profile 1 includes Canadian-tailored controls.** Any enhancement number ≥ 100 (for example `AC-17(100)`, `IA-8(100)`, `PE-2(100)`) is CCCS-authored and has no NIST SP 800-53 equivalent. The full Profile 1 enumeration is in the canonical sources; this mapping focuses on the procurement-relevant subset and notes Canadian-tailored items where they are relevant to a Kubernetes platform.

**Profile 1 is approximately equivalent to FedRAMP Moderate in selection density.** A vendor with a FedRAMP Moderate authorization has done a significant portion of the work; gaps remain in the Canadian-tailored enhancements and in CSE-approved cryptography requirements (ITSP.40.111).

**Security assurance levels.** Profile 1 is SAL2 baseline with SAL3 on critical controls. The selection of SAL3 controls is in the Profile 1 PDF and is out of scope for this mapping.

## Companion files

- [`itsg33-kubernetes-mapping.csv`](itsg33-kubernetes-mapping.csv) — same content as CSV for spreadsheet import
- [`SOURCES.md`](SOURCES.md) — canonical CCCS source URLs and the community PBMM baseline reference
- [`README.md`](README.md) — repository overview
- [`LICENSE`](LICENSE) — Apache License 2.0
