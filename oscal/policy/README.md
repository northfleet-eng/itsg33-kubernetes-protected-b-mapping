# Evidence from the component definition: Kyverno and compliance-to-policy

The component definition in [`../component-definitions/`](../component-definitions/) says which ITSP.10.033-01 controls upstream Kubernetes can implement. This directory turns eight of those claims into automated checks: each becomes a Kyverno policy, the policies are evaluated offline against sample manifests, and the verdicts are published as OSCAL assessment results.

Start with the two summaries: [`results/compliant/summary.md`](results/compliant/summary.md) and [`results/noncompliant/summary.md`](results/noncompliant/summary.md).

## What a pass means

A pass here means the manifests in `samples/compliant/` meet the rule. It is not an assessment of any system. The component definition says what upstream Kubernetes can implement; these results show that the rules checking it work, on manifests written to pass and manifests written to fail. Your cluster's evidence comes from running the same rules against your own manifests or cluster.

## The two tools

- **compliance-to-policy** (C2P), a CNCF project in the OSCAL Compass family, reads an OSCAL component definition and selects the policy for each rule it names. After the policy engine has run, C2P turns the engine's reports back into OSCAL assessment results. This pipeline uses compliance-to-policy-go 1.0.0.
- **Kyverno** is the policy engine. Its CLI evaluates policies against manifests on disk, without a cluster. This pipeline uses Kyverno CLI 1.19.1.

`scripts/install-tools.sh` installs both at those versions into `../vendor/bin/`. The Kyverno archive is checked against its published SHA-256. compliance-to-policy-go is built from a git checkout of the `v1.0.0` tag, verified against the tag's commit, because the Go module proxy cannot serve that version (its test data has file names containing `:`).

## Who implements, who checks

The component definition has three components:

| Component | Type | Role |
|---|---|---|
| Upstream Kubernetes | software | Implements the controls in the mapping's Admin rows, and carries the rules that check them |
| Containerized workload | software | Implements the application's share (the Workload rows); no rules |
| Kyverno | validation | Checks the Upstream Kubernetes component's configuration; implements nothing |

Kyverno is a separate validation component on purpose. It is not upstream Kubernetes. If the component definition said Kyverno enforced a control, that control would stop being something upstream Kubernetes satisfies on its own, and the mapping's External bucket (the gap) would quietly shrink. So Kyverno checks and Kubernetes implements.

The rules use the OSCAL Compass convention C2P reads:

- `Rule_Id` and `Rule_Description` props on the Upstream Kubernetes component, one pair per rule, grouped by `remarks` (`rule_set_00`, `rule_set_01`, ...);
- a `Rule_Id` prop on the statement (`<control>_smt`) of each implemented requirement a rule checks;
- `Rule_Id`, `Check_Id`, and `Check_Description` props on the Kyverno component.

The rule id is the Kyverno policy's `metadata.name` and the name of its directory under `kyverno/policies/`. C2P relies on all three matching, and the build refuses a rule whose names disagree.

## How it runs

```
src/rules.csv ──build_component_definition.py──▶ component definition (rules + Kyverno validation component)
                                                        │
                            c2pcli kyverno oscal2policy ─┴─▶ generated/ (the policies the rules name)
samples/<sample>/ ──kyverno apply (offline)──▶ reports ──report_adapter.py──▶ the four files C2P reads
                            c2pcli kyverno result2oscal ─┬─▶ results/<sample>/assessment-results.json
                                                        ├─ normalize_ar.py ─▶ oscal-cli validate
                                                        ├─ summary.py ─▶ results/<sample>/summary.md
                                                        └─ check_verdicts.py against samples/expected.json
```

`scripts/evaluate.sh` runs these steps:

0. **Plan.** `build_plan.py` writes a minimal assessment plan and system security plan to `results/plan/` and validates both. OSCAL assessment results must import an assessment plan, which imports a system security plan, and oscal-cli loads that whole chain when it validates the results. A sample evaluation has no real system, so both documents describe the sample manifests and nothing else, and say "Not a real system". `results/plan/` sits at the same depth as each `results/<sample>/`, because oscal-cli resolves the links inside an imported document against the importing results file; at equal depth each relative link resolves the same from either place.
1. **Select.** `c2pcli kyverno oscal2policy` reads the component definition and copies the policy directory for each rule into `generated/`.
2. **Evaluate.** `sample_guard.py` first refuses a sample directory that still holds Kustomize or Helm sources (a `kustomization.yaml`, a Kustomization or Component object, or a `Chart.yaml`): the Kyverno CLI would evaluate the unpatched base or the raw templates and could pass over manifests that are never deployed. The Kyverno CLI then applies every generated policy to the manifests in `samples/<sample>/`. No cluster is involved.
3. **Adapt.** Kyverno 1.19 writes its reports in the OpenReports format (`openreports.io/v1alpha1`). compliance-to-policy-go 1.0.0 reads the older policy-report API (`wgpolicyk8s.io/v1beta1`), which OpenReports copied field for field, so `report_adapter.py` renames the API and kind. C2P-Go 1.0.0 also takes verdicts only from namespaced reports and ignores cluster-scoped ones, which would silently drop every ClusterRoleBinding check; the adapter files all results as namespaced reports so none are lost. If the Kyverno output contains no reports at all (malformed or empty manifests), the adapter stops the run instead of letting nothing pass.
4. **Report.** `c2pcli kyverno result2oscal` writes the assessment results. `normalize_ar.py` then makes them valid and stable (see below).
5. **Validate.** oscal-cli validates the results.
6. **Summarize and check.** `summary.py` writes `results/<sample>/summary.md`. Then `check_verdicts.py` fails the run if any rule's verdict is `error` (Kyverno could not evaluate it), and compares every rule's verdict with `samples/expected.json`, the test oracle: every rule must pass on the compliant set and fail on the non-compliant set.

`../scripts/build.sh` runs the unit tests and then this script as part of the whole OSCAL build, and CI fails if any output differs from what is committed.

## Coverage

Only controls the Upstream Kubernetes component claims get rules. External controls stay external.

| Control | Rules | What it evidences |
|---|---|---|
| CM-6 Configuration settings | The Pod Security Standards restricted profile as upstream Kyverno composes it: 11 baseline policies and 6 restricted ones | The mapping's claim is "Pod Security restricted profile"; only the whole profile passing supports it. One limit: the upstream AppArmor rule checks the AppArmor annotation, not the `securityContext.appArmorProfile` field (Kubernetes 1.30 and later), so an unconfined profile set in that field passes |
| CM-7 Least functionality | `disallow-privileged-containers`, `disallow-host-namespaces`, `disallow-host-ports`, `disallow-capabilities-strict`, `disallow-host-path` | Privileged and host-level functions removed |
| AC-6 Least privilege | `restrict-wildcard-verbs`, `restrict-binding-system-groups`, `restrict-automount-sa-token` | No wildcard RBAC; nothing bound to `system:anonymous`, `system:unauthenticated`, or `system:masters`; no stray service-account tokens |
| AC-17(400) Privileged remote access from dedicated consoles | `restrict-clusteradmin-subjects` (custom) | Only the designated administrator group holds cluster-admin. It cannot show where that group's identities connect from; the dedicated administration workstation itself (SI-400) needs configuration review |
| IA-5 Authenticator management | `restrict-automount-sa-token` | Service-account tokens mounted only where declared |
| SC-5 Denial-of-service protection | `require-requests-limits` | CPU and memory requests and a memory limit on every container |
| SC-2 Separation of system and user functionality | `disallow-default-namespace` | Workloads kept out of `default` |
| CM-2 Baseline configuration | `disallow-latest-tag` | Supporting evidence only: an image tagged `latest` leaves the baseline undefined, but pinned tags alone do not make a baseline |

The full rule list, with the controls each one evidences, is [`src/rules.csv`](src/rules.csv).

Eight of the 34 controls the component definition claims have offline checks. The other 26 depend on apiserver configuration, TLS, key management, network behaviour, change process, inventory, or application code, and no rule here checks them:

AC-2, AC-3, AC-4, AC-5, AC-11, AC-17, AU-2, AU-3, AU-4, AU-9, AU-12, CM-3, CM-8, IA-2, IA-3, SC-7, SC-8, SC-12, SC-13, SC-23, SC-28, SI-2, SI-4, SI-10, SI-11, SI-400.

They need configuration review or live evidence. SC-7 and AC-4 are the notable gap: checking that every namespace has a default-deny NetworkPolicy needs lookups against a live cluster (Kyverno's `require-netpol` makes an API call), which an offline evaluation cannot make.

## Reading an assessment-results file

Each `results/<sample>/assessment-results.json` holds one `result`. Inside it:

- `reviewed-controls` lists the controls the rules covered (the eight above);
- `observations` holds one entry per rule;
- `local-definitions.inventory-items` lists every Kubernetes object the Kyverno CLI evaluated;
- `findings` holds one entry per reviewed control.

Here is one observation from [`results/noncompliant/assessment-results.json`](results/noncompliant/assessment-results.json), trimmed:

```json
{
  "props": [
    {"name": "assessment-rule-id", "ns": "https://northfleetsecurity.ca/ns/oscal/cccs", "value": "restrict-clusteradmin-subjects"},
    {"name": "controls", "ns": "https://northfleetsecurity.ca/ns/oscal/cccs", "value": "ac-17.400"}
  ],
  "methods": ["TEST"],
  "subjects": [
    {
      "type": "inventory-item",
      "subject-uuid": "cf803ad5-45a1-5cae-bd3a-eed128c4a227",
      "title": "ApiVersion: rbac.authorization.k8s.io/v1, Kind: ClusterRoleBinding, Namespace: , Name: legacy-admin",
      "props": [
        {"name": "result", "ns": "https://northfleetsecurity.ca/ns/oscal/cccs", "value": "fail"},
        {"name": "reason", "ns": "https://northfleetsecurity.ca/ns/oscal/cccs", "value": "cluster-admin may be bound only to the group itsp:daw-admins."}
      ]
    },
    {
      "type": "inventory-item",
      "subject-uuid": "50e93c98-c5a3-57f7-ad95-1d2348b544b8",
      "title": "ApiVersion: rbac.authorization.k8s.io/v1, Kind: ClusterRoleBinding, Namespace: , Name: masters-view",
      "props": [
        {"name": "result", "ns": "https://northfleetsecurity.ca/ns/oscal/cccs", "value": "skip"},
        {"name": "reason", "ns": "https://northfleetsecurity.ca/ns/oscal/cccs", "value": "preconditions not met"}
      ]
    }
  ]
}
```

- `assessment-rule-id` names the rule, and `controls` names the controls it evidences.
- Each subject is one Kubernetes object the rule evaluated. `result` is `pass`, `fail`, `warn`, `error`, or `skip`, and `reason` is Kyverno's message.
- `subject-uuid` points at the object's entry in `local-definitions.inventory-items`.

In this example the ClusterRoleBinding `legacy-admin` binds cluster-admin to a service account and fails. `masters-view` binds a different role, so the rule's precondition skipped it; the binding to `system:masters` fails a different rule, `restrict-binding-system-groups`.

A rule's verdict is computed from its subjects: `error` if any errored, `fail` if any failed or warned, `pass` if at least one was evaluated and all passed, and `none` if nothing was evaluated. `none` is never reported as a pass. A control is satisfied for a sample only if every rule mapped to it passed.

Each finding carries that control-level verdict where OSCAL tools look for it:

- `target` points at the control's statement (`type: statement-id`, for example `ac-17.400_smt`).
- `target.status.state` is `satisfied` or `not-satisfied`.
- `target.status.reason` is `pass` or `fail`, or `other` when a rule evaluated nothing or errored.
- `related-observations` links the observations of the rules behind the finding.

In the summaries, a satisfied control whose rules carry a limit reads "satisfied, with limits", and the limit is spelled out under "What the evidence does not show".

`normalize_ar.py` changes what C2P writes, in these ways, so the file validates and rebuilds byte for byte:

- random uuids become ones derived from the content;
- every timestamp becomes the release date;
- the method becomes `TEST` (C2P writes `TEST-AUTOMATED`, which OSCAL does not allow);
- C2P's props get this repository's namespace;
- `reviewed-controls` becomes one object naming only the controls the rules observed (C2P writes a list of every claimed control);
- one finding is added per reviewed control (C2P writes none);
- statement ids become control ids;
- zero-value expiry dates and null values are dropped;
- `import-ap` points at the sample plan in `results/plan/`.

## Running it

From the `oscal/` directory:

```bash
policy/scripts/install-tools.sh                                   # Kyverno CLI and c2pcli into vendor/bin
OSCAL_CLI=/path/to/oscal-cli policy/scripts/evaluate.sh           # both samples; needs oscal-cli 3.2.0 and Java 17+
python3 -m unittest discover -s policy/tests                      # the unit tests
OSCAL_CLI=/path/to/oscal-cli scripts/build.sh                     # everything, as CI runs it
```

`install-tools.sh` needs Go 1.22 or later and git. `evaluate.sh` installs the tools itself if they are missing.

## Running it against your own manifests

1. Render your manifests first: Helm charts and Kustomize overlays must be expanded to plain YAML (`helm template`, `kustomize build`). The run refuses a directory that still holds their sources.
2. Put the YAML in a new directory, for example `samples/mine/`.
3. From `oscal/policy/`, run `SAMPLES=mine OSCAL_CLI=/path/to/oscal-cli scripts/evaluate.sh`.

The results land in `results/mine/`. `samples/expected.json` has no entry for your directory, so the verdicts are reported as not checked rather than compared. A rule that errors still fails the run, after the summary is written. The summary is evidence about those manifests, which is closer to your system than the samples are, but it is still not an assessment of a running cluster.

## Adding a rule

1. Add the Kyverno policy as `kyverno/policies/<rule-id>/<rule-id>.yaml`, with `metadata.name: <rule-id>`. It must run offline: no `apiCall`, `imageRegistry`, `configMap`, or `verifyImages` context. The tests reject policies that use them.
2. Record it in `kyverno/vendor.lock`: as `custom`, or with its upstream path and the pinned commit (then `scripts/vendor-policies.sh` fetches it).
3. Add a row to `src/rules.csv`. Name only controls the Upstream Kubernetes component claims; the build refuses anything else.
4. Add the rule's expected verdicts to `samples/expected.json`, and make sure the compliant samples pass it and the non-compliant samples fail it.
5. Run `scripts/build.sh` from `oscal/`, and commit what it regenerates.

## Provenance

- **Library policies.** The 23 policies copied from [kyverno/policies](https://github.com/kyverno/policies) are byte-identical to upstream at commit `2716f4a26a3c27590a1d6d960dee4ce043e4fa4a`. [`kyverno/vendor.lock`](kyverno/vendor.lock) records the source path of each, and `scripts/vendor-policies.sh` re-fetches them. One upstream file, `require-pod-requests-limits.yaml`, declares the policy name `require-requests-limits`, so that is its rule id here.
- **Custom policy.** `restrict-clusteradmin-subjects` was written for this repository. No library policy expresses AC-17(400)'s intent, which is that cluster-admin is held only by the group reserved for dedicated administration workstations. `itsp:daw-admins` is an example group name.
- **Licences.** The library policies are under the Apache License 2.0 ([`kyverno/LICENSE-kyverno-policies`](kyverno/LICENSE-kyverno-policies)); the repository's [`NOTICE`](../../NOTICE) carries the attribution.
