---
name: finops-on-prem-hybrid
fcp_domain: "Understand Usage & Cost"
fcp_capability: "Allocation"
fcp_capabilities_secondary: ["Invoicing & Chargeback", "Data Ingestion", "Architecting & Workload Placement", "Licensing & SaaS", "KPIs & Benchmarking"]
fcp_phases: ["Inform", "Optimize"]
fcp_personas_primary: ["FinOps Practitioner", "Platform Engineering", "Finance"]
fcp_personas_collaborating: ["Engineering", "Procurement", "ITAM", "Leadership"]
fcp_maturity_entry: "Crawl"
---

# FinOps for On-Premises and Hybrid Estates

> How to run FinOps on capacity the organisation owns or commits to, next to the cloud it
> rents: turning a data centre into an internal bill, getting its usage into the same
> data as the cloud, changing behaviour when there is no invoice to point at, how the
> hybrid platforms (AWS Outposts, Azure Local, Azure Arc, Exadata Cloud@Customer, VMware
> Cloud Foundation) are billed, and what it costs to move a workload out of a cloud.

---

## Scope of this file

This file covers owned and colocated data centres and the vendor platforms that put
cloud-style billing on hardware in the customer's own site. It does not yet cover the
accounting side of owned capacity (depreciation policy, capital against operating
expenditure, colocation lease treatment), capacity planning lead times and headroom,
Google Distributed Cloud billing, or mainframe and edge estates. For those, say that
the library does not cover them rather than improvise. Several on-premises topics already live
elsewhere, and this file points to them rather than repeating them:

| If the question is about | Go to |
|---|---|
| Building the data-centre rate card and mapping on-premises rows to FOCUS | `finops-focus.md`, "Beyond the three clouds" |
| Comparing the data centre and a cloud on one unit cost; the utilisation crossover | `finops-kpis-benchmarking.md`, "Unit economics" section (paragraph "Comparing environments") |
| Migrating a workload from on-premises: baselines, network cost model, double-bubble cost | `finops-onboarding-workloads.md` |
| BYOL, licence mobility and Azure Hybrid Benefit in the cloud | `finops-itam.md`, `finops-azure-commitments.md` |
| Self-hosting AI inference against a managed API, hybrid model routing | `finops-ai-self-hosted-vs-managed.md` |
| Chargeback design, ERP readiness, transfer pricing | `finops-chargeback.md` |
| Power, PUE and carbon of owned facilities | `greenops-cloud-carbon.md` |

The Framework's 2026 revision lists Data Center as one of its Technology Categories,
with a page on how the same capabilities apply to it; `finops-framework.md` carries
the category and Scope definitions and the State of FinOps data on how many
practices now manage data centres and private cloud.

---

## Why owned capacity needs a bill before it needs optimisation

A cloud sends an invoice. A data centre sends nothing: the hardware was bought, the
power is paid by Facilities, and the people sit in an IT budget. Until someone turns
that into a price per unit consumed, there is nothing for a team to allocate, compare
or reduce, and every on-premises workload looks free next to its cloud equivalent.

Capacity also exists before it is consumed. Servers, storage, network gear and cooling
are bought and installed before workloads fill them, so every data centre carries idle
capacity by design. The FinOps Foundation's data-centre paper makes that the defining
difference from cloud and asks for idle capacity to be reported as its own line, not
hidden in the rates
([FinOps for Data Center: Practical Cost Modeling and FOCUS Alignment](https://www.finops.org/wg/finops-for-data-center-practical-cost-modeling-focus-alignment/),
FinOps Foundation working group, last updated 12 March 2026).

The order of work therefore differs from cloud: rate card first (`finops-focus.md`),
then the internal bill (below), then usage data in the shared pipeline, then
behaviour. Optimisation without the first two produces savings nobody can see.

---

## Setting the rate: what the rate card section does not say

The rate-card method (asset cost, service chargeback, consumable units, a steady
utilisation assumption, a fixed review cycle) is in `finops-focus.md`. Three points
from practice complete it.

**Split a bundled host into CPU and memory meters by borrowing a published ratio.**
On-premises hosts are bought as one unit, but workloads are sized in vCPU and memory,
and a single "per VM" rate charges a memory-heavy database the same as a CPU-heavy
batch job. Target's FinOps team split the rate using the CPU-to-memory price ratio of a
public cloud (Ron Tatro and Alex Kadavil, FinOps X 2026). A documented ratio to borrow
exists: Google Cloud bills custom machine types on vCPUs and memory hours separately
([Google Cloud, custom machine types](https://cloud.google.com/compute/docs/instances/creating-instance-with-custom-machine-type),
read 20 October 2026). Note that the same page applies a premium to custom types over
predefined ones; borrow the ratio between the vCPU and memory rates, not the absolute
rates.

**A rate built on depreciation looks backwards.** A rate averaged over the five-year
cost of hardware already bought lags hardware price changes in both directions. Target
sets its rates from five years of capital and operating cost averaged per year and
revises them quarterly or half-yearly; its speakers said they were considering a
forward-looking rate based on replacement cost (the speakers' view, not an established
practice). The Foundation paper offers two options as assets age: let the rate fall,
or keep it and report the difference as an amortisation benefit line. Pick one and
write it down before the first reprice.

**Keep the rate history.** A reprice that rewrites past months breaks every trend line
and every comparison with the cloud. Store the price as its own dimension with an
effective date, so a new rate applies forward only.

---

## Running the internal bill

Once rates exist, someone has to produce the bill every month. The pattern Target
described (Ron Tatro and Alex Kadavil, FinOps X 2026) puts the work with the teams that
run the platforms, not with FinOps:

1. **Service owners define their services.** Each internal provider (compute, storage,
   network, databases) names its services and chooses the lowest grain at which usage
   can be measured: a VM, a volume, a database instance.
2. **They register meters per resource.** Two kinds: what the consumer requested
   (allocated cores, provisioned gigabytes) and what it used. The bill can charge on
   either; reporting both makes overprovisioning visible.
3. **They set and revise the price per meter** on the fixed cycle the rate card
   defines, with history kept.
4. **Services form a graph.** Hardware feeds infrastructure services, which feed
   platform services (a managed database cluster, a message bus), which feed
   applications. Cost flows up through shared identifiers and is charged only at the
   consuming application, while each layer stays visible to its owner.

Three rules decide whether consumers accept the bill:

- **Show only what the consumer can control.** Facilities, power, cooling and
  data-centre operations staff go into the meter price; they are not lines on an
  application team's bill. Target limits people costs in the rate to data-centre
  operations, on the reasoning that platform teams are needed whether a workload runs
  on-premises or in a cloud, which keeps the two comparable.
- **Idle capacity is a separate line, not an overhead.** Folding unused capacity into
  the rates raises every consumer's price for a decision none of them made; the
  Foundation paper asks for idle capacity to be tracked as its own line. Route that line
  to whoever owns capacity planning, as Target does: its unused capacity sits with a
  separate capacity team.
- **Charge reserved capacity at the peak it forces.** Meta charges bursty demand at the
  peak capacity it obliges the company to reserve, unless the workload runs on a
  non-guaranteed elastic tier; allocated quota that goes unused is not reclaimed
  mid-cycle but is visible at the next planning round (James Kneeland and Joshua Louie,
  FinOps X 2026). The rule makes the cost of a spiky workload visible to the team that
  causes the spike, which a flat average rate hides.

For a feature that runs inside shared services and has no resource of its own, see
the "Unit economics" section of `finops-kpis-benchmarking.md` (paragraph "Pricing a
feature that is code, not a resource").

---

## Getting on-premises usage into the same data

The on-premises rows belong in the same FOCUS-shaped table as the cloud rows
(`finops-focus.md` gives the column mapping). Four design choices from Target's
platform make that table maintainable (practitioner-reported):

- **One meter schema for private and public sources**: a source-type field, the
  consumer, the shared identifier, the meter type, and daily average, maximum and
  minimum. The FOCUS mapping in `finops-focus.md` carries the quantity
  (`ConsumedQuantity`, `PricingQuantity`) and the estate owner (`BillingAccountId`);
  name the internal team that exposes the service in `ServiceProviderName`, and keep
  the daily maximum and minimum as extra columns, because FOCUS has none for them and
  utilisation insights (such as Target's, below) are computed from the maximum.
- **Price outside the usage record.** Usage rows hold quantities; the price joins at
  query time from the rate history. A reprice then changes no stored usage.
- **Push over pull.** A feed the service owner publishes is slower to onboard than a
  pull FinOps builds against the owner's system, but it survives that system's changes
  because the owner maintains it.
- **A lookback for late data.** Re-read a short trailing window on each load (Target
  uses three days) so late-arriving usage is not lost.

---

## Changing behaviour without a dollar figure

A monthly bill in currency is a weak signal for a team that cannot change its
hardware. Target replaced the dollar conversation with a score (Ron Tatro and Alex
Kadavil, FinOps X 2026; the scale and thresholds are Target's, quoted as an example):

- **One score per team against one enterprise goal**, on a 300 to 850 scale.
- **Built from insights.** Each insight compares usage with a threshold the service
  owner sets (for non-elastic data-centre VMs, 25% CPU against the hourly maximum over
  14 or 30 days) and prices the gap at the meter rate as an opportunity cost. Trivial
  insights are suppressed.
- **Later versions credit good behaviour** and normalise to a business driver the
  team supplies (transactions per second, or the upper bound of its forecast), so a
  high-traffic team is measured against its own volume.
- **Service owners are scored too**, on billing accuracy and on mapping their
  consumers correctly.
- **Each new version runs for a beta quarter** beside the live score before it counts.
- **Strategic exemptions** stay visible on the bill but are not penalised in the
  score, which keeps allocation clean and puts the subsidy where it is decided.

A score against one fixed goal is not the cross-team league table that the showback
anti-patterns warn against (`finops-allocation-showback.md`): each team is measured
against the goal and its own driver, not ranked against teams with different
workloads.

---

## Hybrid platforms: how they are billed

These platforms put cloud-style billing on hardware in the customer's site. Each one
behaves partly like owned capacity (a term, a fixed footprint) and partly like a cloud
(a monthly meter, an Azure or AWS invoice line). Mechanics read on the providers'
pages on 20 October 2026; prices change and are not given here.

| Platform | What is billed | Commitment and term | What to watch |
|---|---|---|---|
| **AWS Outposts rack** | A configuration of EC2 capacity, EBS and S3 on Outposts; the price includes delivery, installation and servicing ([pricing](https://aws.amazon.com/outposts/rack/pricing/)) | Three-year term; All, Partial or No Upfront; charges start 24 hours after installation, when capacity is available | Without notice before term end, the rack renews monthly at the No Upfront rate. Data transfer from the Outpost to its parent Region, and to the local network or internet through the local gateway, carries no charge; transfer from the parent Availability Zone to the Outpost is charged as regional data transfer out |
| **Azure Local** | A flat fee per physical processor core per month, whatever the number of VMs or vCPUs; tiers L1 (hyperconverged, local storage), L2 (external SAN, multi-rack, disaggregated), L3 (disconnected) ([billing](https://learn.microsoft.com/en-us/azure/azure-local/concepts/billing), [pricing](https://azure.microsoft.com/en-us/pricing/details/azure-local/)) | Monthly; 60-day free trial after registration | Higher VM density lowers the cost per VM, because the fee follows physical cores. Azure Hybrid Benefit (Windows Server Datacenter with Software Assurance, through EA or CSP) waives the L1 host fee and the Windows Server guest subscription, on L1 only. Adding external storage moves the cluster to the L2 meter after a 30-day trial. AKS on Azure Local carries no extra charge from release 2402 |
| **Azure Arc** (servers outside Azure) | The control plane (inventory, tagging, resource organisation) is free; add-on services enabled per server (Update Manager, Policy guest configuration, Monitor, Defender, Sentinel) are charged per server ([pricing](https://azure.microsoft.com/en-us/pricing/details/azure-arc/core-control-plane/)) | None for the control plane | Arc spend grows with each service switched on across the fleet, not with the Arc connection. Some management features are included for servers with Windows Server Software Assurance or a Windows Server subscription; log ingestion they generate is still billed |
| **Oracle Exadata Cloud@Customer** | Infrastructure (rack, database and storage servers) per month, with database compute (ECPUs) sold separately ([pricing](https://www.oracle.com/engineered-systems/exadata/cloud-at-customer/pricing/)) | Four-year infrastructure term; minimum 8 ECPUs per database node | Expansion racks and added servers co-term with the primary rack, priced with a term factor of 48 divided by the lesser of the remaining months and 48, so capacity added late in the term costs more per month |
| **VMware Cloud Foundation and vSphere Foundation** | Subscription per physical CPU core across licensed ESXi hosts, with a minimum of 16 cores counted per CPU; the vSAN add-on per raw TiB ([Broadcom KB 313548](https://knowledge.broadcom.com/external/article/313548)) | Subscription term | A host with two 8-core CPUs is licensed as 32 cores, so older low-core hosts cost more per used core; consolidating onto fewer, denser hosts reduces the count |

Two consequences for practice:

- **Term-based hybrid capacity is a commitment.** An Outposts rack or an Exadata
  Cloud@Customer term is sized, approved and tracked like a Savings Plan or a reserved
  instance, with the same rule: size it on the baseline that remains after
  optimisation (`finops-aws-commitments.md`). Unlike a cloud commitment, its capacity
  cannot burst, so headroom has to be bought up front.
- **Per-core pricing rewards density.** Azure Local and VMware both bill physical cores,
  not what runs on them. Utilisation per core is the metric that moves the bill, the
  same mechanic as the utilisation crossover in `finops-kpis-benchmarking.md`.

---

## Moving a workload out of a cloud

A repatriation or a move between clouds used to carry a large data egress bill. Two
mechanisms now reduce it:

- **Provider exit programmes.** AWS gives eligible customers free data transfer out to
  the internet when they move all their data off AWS, or all their data off one service,
  across their eligible accounts; customers outside the EU have 180 days to complete the
  move, and EU customers switching under the Data Act follow the AWS EU Data Act
  Addendum ([AWS News Blog](https://aws.amazon.com/blogs/aws/free-data-transfer-out-to-internet-when-moving-out-of-aws/),
  updated 8 October 2026). Google Cloud gives free data transfer to customers who
  migrate all workloads and data from the relevant service, through an Exit Notice, a
  30-day initiation period and a migration period of at least 30 days, ending with a
  completion form ([Google Cloud exit request](https://cloud.google.com/exit-cloud),
  read 20 October 2026). Microsoft announced a similar programme for Azure in 2024;
  its terms could not be read on a Microsoft page for this file, so check them directly
  before relying on them.
- **The EU Data Act.** For data processing services offered to customers in the EU
  (it is an EU regulation; customers elsewhere depend on the provider's own exit
  programme above): from 11 January 2024 to 12 January 2027, providers may charge
  only the costs they incur for switching and data egress; from 12 January 2027 they
  may not charge for the operations needed to switch or for data egress at all
  ([European Commission, Data Act explained](https://digital-strategy.ec.europa.eu/en/factpages/data-act-explained),
  read 20 October 2026).

In both cases the waiver covers the move, not the steady state. A hybrid design that
keeps sending data back to a cloud every day still pays regular data transfer. Budget
the exit as a project with an end date, and model the run-state network cost separately
(`finops-onboarding-workloads.md` covers the network model differences).

---

## Maturity markers

| Stage | What is in place |
|---|---|
| Crawl | A rate card for the main services (compute, storage), reviewed on a fixed cycle; on-premises cost shown beside cloud cost in one report, even at a coarse grain |
| Walk | Service owners publish meters and prices; on-premises rows in the FOCUS-shaped table; idle capacity reported as its own line; hybrid platform terms tracked in the commitment portfolio |
| Run | Cost flows through the service graph to applications; a behavioural measure (a score or a unit cost) drives decisions without a dollar conversation; placement decisions between data centre and cloud use one unit cost and the utilisation crossover |

---

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| Treating on-premises workloads as free because there is no invoice | Every comparison with the cloud is then biased toward staying, and nobody optimises owned capacity |
| Pricing at perfect utilisation | Rates come out artificially low, and the idle capacity reappears as an unexplained gap |
| Folding idle capacity into every consumer's rate | Consumers pay for a capacity decision none of them made, and the capacity owner never sees the signal |
| Putting power, facilities and data-centre staff as lines on an application bill | The consumer cannot act on them, so the bill becomes noise |
| Repricing without keeping history | Past months change, trends break, and trust in the bill goes with them |
| One flat rate per VM | A memory-heavy workload and a CPU-heavy one pay the same; split the meter |
| Sizing a hybrid rack on today's peak | The term locks in capacity that optimisation would have removed; size on the post-optimisation baseline |
| Counting on the exit waiver for a permanent hybrid data flow | The waiver covers a move, not daily transfer |

---

## See also

- `finops-focus.md` - the data-centre rate card and FOCUS mapping
- `finops-kpis-benchmarking.md` - comparing environments, unit cost and the utilisation
  crossover; pricing a feature inside shared services
- `finops-allocation-showback.md` - shared-services allocation and showback design
- `finops-chargeback.md` - when the internal bill becomes a ledger entry
- `finops-onboarding-workloads.md` - migration from on-premises
- `finops-itam.md` - licence mobility and BYOL
- `finops-practice-operations.md` - decision rights, including Meta's launch review

---

## Sources

Practitioner material (talks, attributed in the text): Ron Tatro and Alex Kadavil,
Target, "Cloud Was Just the Beginning: Extending FinOps to On-Prem", FinOps X 2026;
James Kneeland and Joshua Louie, Meta, "Managing Capacity at the Feature Level",
FinOps X 2026.

Primary pages, all read 20 October 2026 unless dated otherwise:
[FinOps Foundation, FinOps for Data Center](https://www.finops.org/wg/finops-for-data-center-practical-cost-modeling-focus-alignment/);
[Google Cloud custom machine types](https://cloud.google.com/compute/docs/instances/creating-instance-with-custom-machine-type);
[AWS Outposts rack pricing](https://aws.amazon.com/outposts/rack/pricing/);
[Azure Local billing](https://learn.microsoft.com/en-us/azure/azure-local/concepts/billing) and
[pricing](https://azure.microsoft.com/en-us/pricing/details/azure-local/);
[Azure Arc pricing](https://azure.microsoft.com/en-us/pricing/details/azure-arc/core-control-plane/);
[Oracle Exadata Cloud@Customer pricing](https://www.oracle.com/engineered-systems/exadata/cloud-at-customer/pricing/);
[Broadcom KB 313548, counting cores for VMware Cloud Foundation and vSphere Foundation](https://knowledge.broadcom.com/external/article/313548);
[AWS free data transfer out when moving out of AWS](https://aws.amazon.com/blogs/aws/free-data-transfer-out-to-internet-when-moving-out-of-aws/);
[Google Cloud exit free data transfer request](https://cloud.google.com/exit-cloud);
[European Commission, Data Act explained](https://digital-strategy.ec.europa.eu/en/factpages/data-act-explained).

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
