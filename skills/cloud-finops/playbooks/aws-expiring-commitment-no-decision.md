---
name: aws-expiring-commitment-no-decision
scope: aws
service: AWS Savings Plans / Reserved Instances
waste_category: commitment-mismatch
confidence: obvious
---

# AWS Expiring Commitment Without a Renewal Decision

## Problem

Every Savings Plan and Reserved Instance has a hard end date, and AWS does
not auto-renew either instrument. When a commitment lapses with no decision
made, the covered usage silently reverts to on-demand rates - typically a
30-60% cost increase on that usage overnight - and the increase hides
inside normal billing variance until someone asks why the bill grew. The
opposite failure is just as common: a panicked same-shape renewal bought on
expiry day, locking in coverage for a workload that has since shrunk,
moved region, or migrated to Graviton. The waste is not the commitment
itself; it is the absence of a decision while the clock runs out.

## Symptoms

- A Savings Plan or RI end date lands within the next 90 days and no owner
  can name the renewal decision for it
- Savings Plan or RI coverage percentage drops in a step function in Cost
  Explorer with no corresponding usage change
- On-demand spend rises in a month where usage was flat
- Expiration email alerts from AWS go to a mailbox nobody reads (the
  default: the root account email)
- The commitment inventory lives in someone's head or a stale spreadsheet
  rather than a reviewed register

## Detection

```bash
# Runnable with read-only IAM (ec2:DescribeReservedInstances,
# savingsplans:DescribeSavingsPlans). Run from the management account or
# per linked account.

# Reserved Instances ending within 90 days, still active
aws ec2 describe-reserved-instances \
  --filters "Name=state,Values=active" \
  --query "ReservedInstances[?End<='$(date -u -d '+90 days' +%Y-%m-%dT%H:%M:%S)'].{id:ReservedInstancesId,type:InstanceType,az:AvailabilityZone,count:InstanceCount,end:End}" \
  --output table

# Savings Plans ending within 90 days
aws savingsplans describe-savings-plans \
  --states active \
  --query "savingsPlans[?end<='$(date -u -d '+90 days' +%Y-%m-%dT%H:%M:%S)'].{id:savingsPlanId,type:savingsPlanType,commitment:commitment,end:end}" \
  --output table
```

Cost Explorer > Reservations > Expiration alerts (and the equivalent
Savings Plans alerts) can push the same signal by email or SNS up to 60
days ahead - turn them on and route them to the FinOps channel, not the
root mailbox. The classification is single-signal (`obvious`): a
commitment inside its expiry window with no recorded decision always
warrants action, because the action is *making the decision*, not
automatically buying a replacement.

## Fix

1. Build (or refresh) the commitment register: every RI and SP with end
   date, commitment value, covering scope, and a named decision owner.
2. For each commitment entering its 90-day window, run the renewal
   decision against current usage, not against the original purchase
   rationale: has the workload grown, shrunk, changed instance family, or
   moved region since purchase? `references/finops-aws-commitments.md`
   carries the full decision framework.
3. Decide one of three outcomes and record it: renew resized (usually a
   smaller or different-shape block), let lapse deliberately (workload is
   shrinking or migrating), or replace with a different instrument (e.g.
   an expiring EC2 Instance SP replaced by a Compute SP if flexibility now
   matters more than depth).
4. Where several commitments expire in the same quarter, use the renewal
   round to move the portfolio towards staggered expiry - phased blocks so
   no more than roughly a quarter of total commitment expires in any
   single quarter.
5. Put the register on a standing review cadence (monthly is enough) so
   the 90-day window is never discovered late.

## Anti-pattern

- Auto-renewing the same shape "to be safe" on expiry day. The renewal
  moment is the cheapest point to fix a shape mismatch; a same-shape
  renewal under time pressure locks the old estate's shape onto the new
  estate for another 1-3 years.
- Letting a commitment lapse as the *default* outcome rather than a
  decision. Lapse is sometimes right, but it should be chosen, priced
  (coverage gap x on-demand premium), and dated.
- Treating expiry alerts as the fix. Alerts without a named decision owner
  and a register just move the surprise from the bill to an inbox.

## See also

- `references/finops-aws-commitments.md` - commitment decision framework,
  staggered-expiry portfolio design, phased purchasing cadence
- `playbooks/azure-unused-reservation.md` - the Azure member of the
  commitment-mismatch family
- `playbooks/gcp-cud-mismatch.md` - the GCP member of the family
- `references/finops-waste-detection-playbooks.md` - the eight-category
  taxonomy this pattern fits ("commitment-mismatch")

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
