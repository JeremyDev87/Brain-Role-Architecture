# Soft technical preview measurement ledger template

This public file is an unpopulated template. Before an owner-approved preview post, copy it to an approved private
operational store and populate only that private copy. Never commit collected values, post/channel URLs, account or
profile identifiers, conversation references, event identifiers, private messages, or raw prompts to the public
repository. Public reporting may use sanitized aggregates only; evidence stays behind opaque, non-identifying
receipt labels in the private ledger.

## Frozen preview identity

| Field | Value |
| --- | --- |
| Audience | AI platform and agent-harness engineers |
| Channel | Not selected; requires owner approval immediately before posting |
| Call to action | Reproduce the controlled-mutation proof or open one technical integration-fit question |
| Repository revision | Template only; freeze exact public `main` SHA in the private copy |
| Private post receipt | Template only; use an opaque receipt label, never a URL or account identifier |
| T0 | Template only; verified post timestamp in ISO 8601 with `+09:00` offset |
| Measurement window | Cumulative elapsed windows `[T0,T0+24h]`, `[T0,T0+7d]`, and `[T0,T0+14d]` |

Changing the audience, channel, call to action, repository revision, or post starts a new private measurement
record. Do not overwrite a prior record. Use elapsed time from T0 rather than calendar-day boundaries.

## Checkpoint ledger

| Checkpoint | Collected at | Reach | Engagement | Qualified conversion | Private evidence receipt | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `[T0,T0+24h]` | Template only | Cumulative views/impressions and referrer availability | Not evaluated | Not evaluated | Opaque receipt label | Continue, correct, or contain |
| `[T0,T0+7d]` | Template only | Cumulative views/impressions | Cumulative repository, README, tutorial, or release engagement attributable to the frozen channel | Early qualified events, reported separately | Opaque receipt label | Continue unchanged or revise copy/channel |
| `[T0,T0+14d]` | Template only | Final cumulative reach | Final cumulative engagement | Deduplicated external qualified events attributable to the frozen experiment | Opaque receipt label | Stop, revise, or approve a separately scoped next experiment |

## Attribution, deduplication, and late events

- Attribute an event only through the frozen channel/referrer or an explicit participant statement recorded in the
  private evidence store.
- Build a private unique-event key from the platform plus its native event/conversation identifier. Hashing does
  not make an identifier suitable for this public repository; keep both the source and derived key private.
- Count the same external participant and technical boundary once per window unless a later event establishes a
  distinct adapter/integration boundary.
- Recalculate cumulative checkpoints from T0 so the 7-day value includes the 24-hour interval and the 14-day value
  includes both earlier intervals.
- Events first observed after `T0+14d` are late observations. Record them outside the frozen experiment and do not
  backfill or revise its qualified-conversion count.

## Metric definitions

### Reach

Reach includes channel impressions/views and referrer availability. Stars, watchers, clones, release downloads, and
repository traffic may supplement the record when GitHub exposes them, but they remain attention signals.

### Engagement

Engagement requires observable interaction with the repository, README, controlled-mutation tutorial, or GitHub
Pre-release attributable through the frozen channel/referrer or explicit participant statement. Do not infer
engagement from reach alone.

### Qualified conversion

Count only:

1. an independently reported successful or failed reproduction from an external non-owner/non-maintainer
   participant, with enough technical detail to investigate;
2. an external adapter or integration issue naming the boundary under evaluation; or
3. a technical conversation with an external non-owner/non-maintainer participant that identifies a concrete
   conformance or adoption question.

Every qualified conversion must be attributable to the frozen experiment and pass the private unique-event-key
deduplication rule.

Do not count generic praise, stars, follows, views, automated traffic, or download totals as qualified conversion.

## Decision rules

- **Contain:** any privacy, rights, claim, release-state, anonymous-access, or public-security drift.
- **Revise:** reach is present but qualified conversion is zero at 14 days; change copy or channel, not both at once.
- **Continue:** evidence remains consistent and a qualified event warrants the existing window.
- **Expand:** requires a separate owner-approved experiment after the 14-day review; this ledger does not authorize
  additional channels, registry publication, deployment, or production claims.

## Final interpretation

Summarize what the evidence supports, what it does not support, and the next independently approved experiment.
Keep `PRE_RELEASE`, registry availability, deployment, runtime authority, security certification, and market demand
as separate factual axes.
