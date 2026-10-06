# GitLab Failure Lab source register

## Primary source

GitLab, *Postmortem of database outage of January 31*, 10 February 2017. [Official postmortem](https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/). Accessed 5 October 2026 using native web search and primary-page inspection.

## Register

- **S1 — Wrong host and impact scope:** Timeline, around 23:00–23:30 UTC; Root cause analysis, problem 1; opening incident summary; Data loss impact. Supports the accidental clearing of the primary data directory, the reported loss window from about 17:20 to 00:00 UTC, and GitLab’s approximate counts of 5,000 projects, 5,000 comments and 700 new user accounts.
- **S2 — Backup health and recovery testing:** Broken recovery procedures; Database backups using `pg_dump`; Root cause analysis, problem 2. Supports the PostgreSQL version mismatch that stopped the logical backup, rejected failure emails and lack of an owner for regular recovery testing.
- **S3 — Copy freshness and purpose:** Timeline around 17:20 UTC; LVM snapshots; Recovering GitLab.com. Supports the manually created snapshot about six hours before the outage to refresh staging, the snapshots’ staging purpose rather than disaster-recovery design, the nearly day-old alternate copy and GitLab’s choice to use the newer snapshot to reduce data loss.
- **S4 — Restore duration and affected data:** Recovering GitLab.com; Data loss impact. Supports the roughly 18-hour staging-to-production database copy over throttled network disks at around 60 Mbps, and that Git repositories and wikis were unavailable during the outage but were not lost.

## Model boundary

All alternative branches, effort and missing-write units are invented teaching devices and labeled illustrative. Units are not hours, bytes or historical loss estimates. The backup-exposure message appears on every `assume` path as a modeled warning; it does not claim that each such path causes historical loss. Checking recovery pauses deletion; it does not manufacture a working backup. Confirming the secondary preserves the model’s primary copy; it does not guarantee restored replication. The recovery-copy decision is shown only when the model requires restoration, and its two choices change the modelled missing-write window. Equal transfer effort is a simplifying assumption, not a comparison established by GitLab. No fatigue attribution or fast-restore claim is made. No command is executed. No live incident document was needed. No direct quotations are used.
