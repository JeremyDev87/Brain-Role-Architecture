# Soft technical preview runbook

This runbook prepares a bounded technical preview for AI platform and harness engineers. It does not authorize
repository publication, a release mutation, registry publication, deployment, or an external post.

## Positioning and evidence boundary

Brain-Role Architecture is a policy-as-code and conformance toolkit for AI-agent responsibility, authority, and
change contracts. The preview demonstrates the repository's deterministic controlled-mutation proof. It does not
claim production readiness, runtime authorization, security certification, hosted execution, deployment safety,
or proven market demand.

The repository's normative source of truth is `SPEC.md`. The allowed and forbidden preview wording is maintained
in `docs/launch/claim-matrix.md`. A GitHub Pre-release asset is not evidence of registry availability, and a green
verification run is not publication authority.

## Preview contract

- **Audience:** AI platform and agent-harness engineers evaluating conformance boundaries.
- **Channel:** one owner-approved technical channel selected immediately before posting.
- **Call to action:** reproduce `docs/tutorials/controlled-mutation-demo.md` or open one technical integration-fit
  question with the adapter/runtime boundary that needs evaluation.
- **Source path:** source checkout only until a registry readback proves another installation path.
- **Measurement template:** `docs/launch/soft-preview-ledger.md`; copy it to an approved private operational store
  before recording metrics or evidence. Never commit a populated ledger to the public repository.

Do not add a second audience, channel, or call to action during the first 14-day measurement window. This keeps
attribution interpretable and prevents reach from being mistaken for qualified demand.

## Pre-publication gates

All gates are fail-closed. Record the exact command output or GitHub URL used for each decision.

1. Freeze the intended public repository ID, exact `main` commit and tree, tag target, release state, asset
   digests, branch/ref inventory, and current Actions/security settings.
2. Verify the intended public history contains no secret, personal email, absolute operator path, private host,
   or unapproved collaboration surface. Current-tree scanning alone is insufficient.
3. Confirm license, NOTICE, contributor, generated-image provenance, and redistribution-right evidence. Keep the
   generated poster only under the owner-confirmed rights path.
4. Run `make verify`, the full-history secret scan, the public-boundary scan, exact diff/untracked review, and an
   independent Critical/High blocker review on the frozen candidate.
5. Keep repository metadata, review redaction, archive/cutover, tag/release migration, visibility, public security
   controls, registry publication, deployment, and external posting as separate approval lanes.

Stop before any external mutation if the target repository ID, exact revision, rights evidence, rollback boundary,
or owner authorization is ambiguous.

## External mutation protocol

For every approved GitHub mutation:

1. Record the expected immutable target and the one mutation being attempted.
2. Execute the mutation without appending a fragile assertion or follow-up mutation.
3. Save the mutation receipt without secret or personal values.
4. Perform an authoritative readback in a separate command.
5. If the result is ambiguous, inspect state and stop; never blindly retry a non-idempotent operation.

`PRIVATE` to `PUBLIC` is a disclosure boundary. Returning to private can contain future access but cannot recall
existing clones, caches, Git objects, pull-request views, or downloaded release assets.

## Publication and security sequence

1. Freeze all controlled writers. Record each checkout and prohibit pushes until its remote migration is verified.
2. Rename only the historical private repository. In a separate readback, require its original immutable ID,
   private visibility, expected historical head, and the approved archive slug.
3. Repoint every controlled old-history checkout to the archive URL. For each checkout, separately verify the
   configured URL, archive immutable ID, and remote head; do not trust a same-slug redirect.
4. Only after all known writers target the archive, create the clean replacement at the original slug. In a
   separate readback, require a new immutable ID, private visibility, and zero remote heads.
5. Configure least-privilege Actions policy, push only the approved clean history without force, and require
   exact-head hosted CI.
6. Preserve `v0.4.0` in immutable-copy mode: create a clean noreply root whose tree exactly equals the frozen
   original `v0.4.0` tag tree, point the new annotated tag to that clean root, and attach only the exact original
   wheel/sdist bytes with their frozen digests. Do not move the tag to the current preview tree, rebuild assets from
   the preview candidate, or replace release bytes without a new, separately authorized release plan.
7. After the clean repository and remotes are verified, disable Actions on the historical repository and archive it.
   Read back its original immutable ID, private visibility, archived state, and expected historical head.
8. Under a fresh visibility authorization, change only repository visibility and then verify anonymous clone,
   default HEAD, README, tag, release, and asset access.
9. In separate mutations, configure and read back branch/ruleset protection, required checks, CodeQL default
   setup, Dependabot alerts/security updates, secret scanning/push protection, private vulnerability reporting,
   and Actions policy.
10. Do not announce the preview until anonymous access and public security readbacks pass.

Registry publication, deployment, production adoption, and additional launch channels remain outside this sequence.

## Preview post and verification

The post must link directly to the repository and controlled-mutation tutorial, use only claims allowed by the
claim matrix, and retain `PRE_RELEASE`/experimental wording. Immediately after posting:

- verify the rendered post and links from an anonymous context;
- record the verified post timestamp and a private opaque receipt identifier in the private operational ledger;
- verify the call to action still points to reproduction or a technical integration-fit question;
- stop distribution if a claim, link, release state, or security readback has drifted.

## Measurement and decision points

- **24 hours — reach:** record cumulative `[T0,T0+24h]` impressions/views and referrer availability without
  treating them as demand.
- **7 days — engagement:** record cumulative `[T0,T0+7d]` repository/demo/release engagement attributable to the
  frozen channel.
- **14 days — qualified conversion:** record cumulative `[T0,T0+14d]` independent reproduction, an
  adapter/integration issue, or a technical conversation from an external non-owner/non-maintainer participant.

If reach exists but qualified conversion remains zero, revise the copy or channel before expanding distribution.
Do not convert stars, views, downloads, or rank into a production-readiness or market-demand claim.

## Containment and rollback

- Before public visibility, abort the cutover and restore names/remotes only from frozen immutable-ID evidence.
- After public visibility, rollback means containment: return to private if needed, disable affected automation,
  remove the external post when authorized, and publish a correction. Never claim prior disclosure was recalled.
- A release correction, tag replacement, registry action, or deployment rollback requires its own authorization
  and evidence ledger.
