---
name: azure-snapshot-sprawl
scope: azure
service: Azure Managed Disk Snapshots
waste_category: orphaned
confidence: likely
---

# Azure Snapshot Sprawl

## Problem

Managed disk snapshots bill per GB-month for as long as they exist, and
nothing in Azure expires them: there is no native retention setting on a
manually created snapshot. They accumulate through three channels -
pre-change safety copies nobody deletes afterwards, scripted snapshot
jobs whose cleanup half was never written, and snapshots orphaned when
their source disk (or the whole VM) was deleted. A **full** snapshot
bills the used size of the disk on every copy; **incremental** snapshots
bill only the delta since the previous one, so a full-snapshot job on a
schedule is the expensive variant of the pattern. Two signals are needed
before deleting - age plus a gone source disk, or age plus a superseding
backup - because an old snapshot can be the only restore point something
still depends on.

## Symptoms

- Snapshot count grows month over month while the VM count does not
- Snapshots named `pre-upgrade`, `before-migration`, `temp`, or
  date-stamped by a script that clearly ran on a schedule
- Snapshots whose source disk no longer exists
- Storage cost in the subscription rising with no matching data growth
  on live disks
- Full (non-incremental) snapshots of large disks recurring daily

## Detection

Two signals in one query - age, and whether the source disk still
exists:

```kusto
// Azure Resource Graph - snapshots older than 90 days, flagging those
// whose source disk is gone (sourceGone == true is the strongest signal)
resources
| where type =~ "microsoft.compute/snapshots"
| extend sourceId    = tolower(tostring(properties.creationData.sourceResourceId))
| extend sizeGB      = toint(properties.diskSizeGB)
| extend incremental = tobool(properties.incremental)
| extend created     = todatetime(properties.timeCreated)
| extend ageDays     = datetime_diff('day', now(), created)
| where ageDays > 90
| join kind=leftouter (
    resources
    | where type =~ "microsoft.compute/disks"
    | extend diskId = tolower(id)
    | project diskId
  ) on $left.sourceId == $right.diskId
| extend sourceGone = isempty(diskId)
| project subscriptionId, resourceGroup, name, sizeGB, incremental, ageDays, sourceGone
| order by sourceGone desc, sizeGB desc
```

Resource Graph carries inventory, not cost: `sizeGB` ranks full
snapshots correctly, but an incremental snapshot's billed size is its
delta, which ARG does not expose - price incrementals through the Cost
Management / FOCUS export joined on the lowercased resource ID.

Before deleting anything, check the snapshot is not a restore point a
backup system counts on: Azure Backup keeps its own recovery points in
the vault (not as standalone snapshots you would see here), but
third-party backup tools often do their work through exactly these
snapshot objects. `az snapshot show` and the creating identity in the
activity log tell you which tool made it.

## Fix

1. Delete snapshots where `sourceGone == true` and no backup tool claims
   them - the disk they would restore no longer exists, so their only
   remaining value is as a template, which is rare and identifiable by
   name.
2. For aged snapshots with a living source, confirm with the owner that
   a newer restore point supersedes them, then delete beyond an agreed
   retention window.
3. Replace scripted snapshot jobs with **Azure Backup** policies, which
   carry retention and expiry natively - the job that creates without
   deleting is the root cause, not the snapshots themselves.
4. Where snapshot jobs must remain, switch them to **incremental**
   (`az snapshot create --incremental`) - the recurring cost drops from
   full disk size to daily delta.
5. Add an Azure Policy audit on snapshot age so the estate does not
   regrow silently.

## Anti-pattern

- Deleting the only restore point of a disk that still exists because
  "it is old". Age alone is one signal; this pattern is `likely`, not
  `obvious`, precisely because an old snapshot can still be the backup.
- Deleting snapshots created by a backup product from underneath it.
  The product's catalogue now references a recovery point that is gone,
  and the failure surfaces at restore time - the worst possible moment.
- Keeping full-snapshot schedules "because incremental sounds riskier".
  An incremental chain restores identically; Azure resolves the chain
  server-side, and the first incremental of a disk is a full copy
  anyway.

## See also

- `playbooks/aws-snapshot-sprawl.md` - the AWS twin of this pattern,
  same two-signal logic over EBS
- `playbooks/azure-orphan-disks.md` - the upstream orphan: a deleted
  VM's disk today is an orphaned snapshot's gone source next quarter
- `references/finops-azure.md` - Azure storage billing mechanics
- `references/finops-waste-detection-playbooks.md` - "orphaned"
  category rubric

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
