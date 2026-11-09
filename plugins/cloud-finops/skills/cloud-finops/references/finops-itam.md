---
name: finops-itam
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Licensing & SaaS"
fcp_capabilities_secondary: ["Intersecting Disciplines"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Procurement"]
fcp_personas_collaborating: ["Engineering", "Finance", "Leadership"]
fcp_maturity_entry: "Walk"
business_coverage: ["saas:saas:deep", "saas:contracts:partial", "aws:saas:partial", "azure:saas:partial", "gcp:saas:partial", "on-prem:saas:partial"]
questions:
  - q: "We hold SQL Server licences with Software Assurance. BYOL or licence-included on Azure and AWS, and how do we decide?"
    section: "BYOL strategy"
  - q: "Can we bring our Windows, SQL Server or Oracle licences to the cloud, and when is it cheaper?"
    section: "Common BYOL scenarios"
  - q: "Should we buy software through the AWS or Azure Marketplace to burn down our commitment?"
    section: "Marketplace channel governance"
  - q: "Who owns a licence true-up: FinOps, ITAM or Procurement?"
    section: "Governance alignment"
  - q: "Our SaaS vendor bills on consumption and we keep overshooting. How do we monitor it?"
    section: "Consumption-based SaaS monitoring"
  - q: "Our Software Assurance renewal is due. Does keeping it pay for itself through Azure Hybrid Benefit or licence mobility?"
    persona: "Finance and procurement"
    section: "When the Software Assurance renewal comes up"
  - q: "We are moving Oracle databases to AWS or Azure. How are the licences counted there, and is BYOL still worth it?"
    section: "Deciding between BYOL and licence-included"
  - "Nos licences SQL Server avec Software Assurance : BYOL ou licence incluse dans le cloud ?"
---

# FinOps and ITAM - Collaborating Across the Technology Estate

> Where FinOps and ITAM intersect: shared governance, marketplace channel strategy,
> BYOL cost mechanics, commitment co-ordination, compliance risk, and joint operating
> models. Covers the collaboration patterns that neither discipline can execute alone.
> For SaaS-specific management (discovery, sprawl, SMPs), see `finops-sam.md`.

---

## Why FinOps needs ITAM (and vice versa)

FinOps manages cloud cost through visibility, allocation, and optimisation. ITAM manages
the broader technology estate through governance, compliance, and contractual accountability.
Neither discipline covers the full picture on its own, and the gap between them is growing.

The State of FinOps 2026 survey shows FinOps-ITAM collaboration as a top priority, with
68% of organisations reporting active collaboration between the two functions. The driver
is practical: modern technology estates blend consumption-based cloud, seat-based SaaS,
perpetual licenses, BYOL deployments, and marketplace purchases. A single vendor
relationship (Microsoft, Oracle, SAP) can span all of these billing models simultaneously.
Managing cost without managing entitlements - or managing entitlements without cost
telemetry - creates blind spots that lead to overspend, audit exposure, and missed
negotiation leverage.

**What ITAM brings to FinOps:**
- Entitlement data: what the organisation owns, what it is allowed to deploy, and under what terms
- Compliance tracking: whether deployed assets match contractual use rights
- Vendor audit preparedness: documentation and processes to defend against vendor audits
- Hardware and software lifecycle management: depreciation schedules, refresh cycles, end-of-support dates
- Contract intelligence: renewal terms, price escalation clauses, termination notice periods

**What FinOps brings to ITAM:**
- Real-time usage telemetry: what is being consumed, not just what is deployed
- Cost attribution: linking spend to teams, products, and business outcomes
- Commitment mechanics: how cloud discounts (RIs, Savings Plans, CUDs) interact with license decisions
- Forecasting: consumption projections that inform procurement and renewal decisions
- Anomaly detection: early warning when usage patterns deviate from contracted expectations

---

## ITAM components relevant to FinOps

ITAM traditionally operates as three interdependent components (FinOps Foundation,
[FinOps & ITAM: Collaborating to Optimize Cost, Risk, and Value](https://www.finops.org/wg/finops-itam-optimize-cost-risk-value/), CC BY 4.0, adapted):

**Software Asset Management (SAM)** oversees software licensing, renewals, and audit
readiness. This is where the overlap with FinOps is strongest - see `finops-sam.md` for
detailed SaaS management guidance including discovery methods, sprawl patterns, SMP
landscape, and governance models.

**Hardware Asset Management (HAM)** tracks physical and virtual infrastructure assets.
Relevant to FinOps during cloud migrations (parallel running costs), hybrid deployments
(on-premises + cloud), and hardware refresh decisions that trigger cloud workload shifts.

**Service and Cloud Asset Management** manages SaaS, PaaS, and hybrid assets through
discovery and configuration management databases (CMDBs). This component increasingly
overlaps with FinOps tooling as cloud billing platforms and ITAM platforms converge.

---

## Tier 1 vendors requiring joint FinOps-ITAM management

These vendors have blended pricing models that cross the FinOps-ITAM boundary. Managing
them from one discipline alone creates financial or compliance blind spots.

| Vendor | Key products | Billing model | Why both disciplines are needed |
|---|---|---|---|
| Microsoft | Microsoft 365, Azure | Seats + cloud consumption | E3/E5 tier optimisation requires usage data (FinOps) and entitlement tracking (ITAM). Azure Hybrid Benefit depends on on-premises licence eligibility |
| AWS | EC2, S3, RDS, Marketplace | Cloud consumption + marketplace subscriptions | Marketplace purchases consume cloud commitments (EDP). ITAM needs billing data to validate entitlements |
| Google | GCP, Workspace | Workspace seats + GCP consumption | Workspace licence tiers need usage analysis. GCP CUDs need consumption forecasting |
| Oracle | Oracle DB, Fusion, OCI | Core-based DB licensing + cloud consumption | BYOL to OCI requires precise entitlement mapping. Processor-based licensing creates audit exposure |
| Salesforce | Sales Cloud, Data Cloud | CRM seats + data/AI credits | Consumption credits can spike unpredictably. Seat licences accumulate as shelfware |
| SAP | S/4HANA, BTP | ERP subscriptions + indirect access | Indirect/digital access licensing creates hidden compliance costs |
| Adobe | Creative Cloud, Experience Cloud | Seat subscriptions + e-sign transactions + AI credits | Named-user vs shared-device licensing affects cost significantly |
| ServiceNow | Now Platform, ITSM | Subscription entitlements | Entitlement structures are complex and often misaligned with actual usage |
| Broadcom/VMware | VCF, vSphere, NSX | Core/CPU subscriptions + VCF bundles | Post-acquisition licensing changes require entitlement re-evaluation |

---

## Marketplace channel governance

Cloud marketplace purchasing (AWS Marketplace, Azure Marketplace, GCP Marketplace) is
growing rapidly and creates new problems that require both FinOps and ITAM co-ordination.
This section adapts the FinOps Foundation paper
[FinOps & ITAM Practical Scenarios: Planning & Procurement](https://www.finops.org/wg/finops-itam-practical-scenarios-planning-procurement/) (CC BY 4.0).

### The problem

Engineering teams buy software through marketplaces without centralised oversight. This
creates three categories of risk:

**Entitlement fragmentation.** Licences are split between SAM tools, vendor portals, and
multiple marketplace tenants. ITAM cannot prove compliance or claim BYOL rights when
marketplace SKUs are not mapped to existing contracts.

**Commitment collision.** Marketplace spend draws down cloud commitments (EDP on AWS, MACC
on Azure) that FinOps is actively managing. Meanwhile, Procurement may hold separate
Enterprise Agreements with the same vendor. These competing commitments create risk of
underutilisation, overcommitment, or duplicated commercial obligations. The drawdown
rules per provider (counting rule, cap, eligibility, seller fees) are in the Marketplace
table of `finops-cloud-contracts.md`.

**Governance gaps.** Weak policy on who can buy what, through which channel, and under
which legal entity. Self-service purchasing increases exposure to shadow IT, uncontrolled
spend, and misaligned commitments.

### Practical steps

1. **Discover and baseline.** Aggregate marketplace invoices and usage records from all
   clouds. Tag each line item to a vendor, product, and business owner. Reconcile against
   ITAM entitlement data and existing contracts to identify overlaps and gaps.

2. **Define channel strategy per vendor.** For top vendors, agree on a preferred route to
   market by scenario - for example, dev/test or short-term projects via marketplace,
   strategic workloads via EA. Document rules for EA/BYOL vs marketplace, who can approve
   private offers, and what thresholds trigger Deal Desk involvement.

3. **Integrate processes and tooling.** Implement workflows so marketplace private offers
   and SaaS subscriptions follow the same approval and tagging standards as direct
   purchases. Normalise SKUs between the SAM tool, CMDB, and cloud billing.

4. **Operate a joint marketplace review.** Monthly review where FinOps and ITAM assess
   marketplace pipeline, renewals, and spend trends against commitment targets and
   entitlement positions.

5. **Optimise and renegotiate.** Use the combined view of marketplace and EA spend to
   negotiate better discounts, adjust commitment levels, and consolidate vendors where
   overlapping tools are identified.

### Quick wins
- Enforce a "no credit card marketplace purchases" rule and move to central accounts
- Stand up a joint dashboard of marketplace spend by vendor, tagged with owner and channel
- Reconcile the top 5 marketplace vendors against existing EA entitlements

### Anti-patterns
- Treating marketplaces as a separate channel owned only by engineering or only by procurement
- Assuming marketplace always equals better (or worse) pricing without modelling commit impact and entitlement rights
- Tool-only fixes without governance processes and a joint operating model

---

## BYOL strategy and cost mechanics

Bring Your Own Licence (BYOL) allows organisations to use existing on-premises licences
in cloud environments. When managed correctly, it avoids paying for the same licence
twice. When managed poorly, it creates compliance exposure and hidden costs.

Every rule in this section is the vendor's, read on the vendor's own page on 9 November
2026 and linked where it is used. The rules move with each Product Terms revision (the
Microsoft dates that matter are 1 October 2019, 1 October 2022 and November 2022), so
re-read the page before a decision that depends on one. Oracle's cloud policy says of
itself that it is educational, not part of any contract and subject to change without
notice: an audit defence cannot rest on it alone.

### Where BYOL creates FinOps-ITAM dependency

- **Eligibility verification** requires ITAM entitlement data. Not all licences are portable.
  Microsoft SQL Server, Windows Server, and Oracle DB each have different mobility rules,
  and these rules change with vendor programme updates.
- **Cost modelling** requires FinOps consumption data. The financial benefit of BYOL depends
  on the cloud instance type, region, and commitment discount already in place.
- **Compliance monitoring** requires both. A licence deployed via BYOL that exceeds its
  contractual use rights (wrong edition, wrong core count, wrong deployment model) creates
  audit exposure that neither team can detect alone.

### Deciding between BYOL and licence-included

Six steps, in this order. The first three are gates: in most estates the vendor has
already decided before anyone opens a price list.

**1. Is the licence allowed there at all?** Three Microsoft rules settle Windows Server
and SQL Server:

- *Listed Providers, 1 October 2019.* Microsoft, Amazon (VMware Cloud on AWS included),
  Google and Alibaba. A licence bought without Software Assurance after that date, and
  any product version released after it whatever the purchase date, may not run on
  their dedicated hardware. Licences bought before the date, and true-ups under an
  enrolment effective before it, keep the old right
  ([Microsoft, updated licensing rights for dedicated cloud](https://www.microsoft.com/en-us/licensing/news/updated-licensing-rights-for-dedicated-cloud)).
- *License Mobility through Software Assurance.* Server applications only, SQL Server
  first among them; Windows Server is not eligible. It allows shared-tenancy deployment
  with an Authorized Mobility Partner, with a verification form within 10 days of
  deployment and reassignment to another partner at most once every 90 days. On Azure,
  core-licensed SQL Server uses Azure Hybrid Benefit instead of this process
  ([Microsoft, License Mobility](https://www.microsoft.com/en-us/licensing/licensing-programs/software-assurance-license-mobility)).
- *Flexible Virtualization Benefit, 1 October 2022.* Licences with Software Assurance or
  by subscription may run on any Authorized Outsourcer's servers, shared or dedicated,
  with no form. It excludes the Listed Providers and any outsourcer hosted on one
  ([Microsoft, Flexible Virtualization Benefit](https://www.microsoft.com/licensing/guidance/Flexible-Virtualization-Benefit)).

What follows for the three hyperscalers: Windows Server at AWS or Google Cloud is
licence-included unless you hold pre-October-2019 licences and accept dedicated hosts,
and Windows Server 2019 is the last version eligible there; on Azure the route is Azure
Hybrid Benefit. SQL Server with Software Assurance can go to all three on shared
tenancy. SQL Server without Software Assurance cannot go anywhere new, and since SQL
Server 2022 licensing by individual virtual machine itself requires Software Assurance
or a subscription licence
([Microsoft Product Terms, SQL Server](https://www.microsoft.com/licensing/terms/en-US/productoffering/SQLServer/EAEAS)).
Oracle Database is allowed in all three (AWS EC2 and RDS, Azure and Google Cloud are its
Authorized Cloud Environments); for Oracle the gate is the core count in step 3.

**2. Which deployment model does that force?** The routes open per provider and
product, with the managed-service options that change the answer:

| | Windows Server | SQL Server | Oracle Database |
|---|---|---|---|
| Azure | Azure Hybrid Benefit on any VM with Software Assurance or a subscription licence; Azure Dedicated Host for pre-2019 licences, or for unlimited virtualisation with Datacenter licences covering all physical cores ([Dedicated Host](https://azure.microsoft.com/en-us/products/virtual-machines/dedicated-host/)) | Azure Hybrid Benefit on SQL VMs and on vCore-provisioned SQL Database and Managed Instance; not DTU, not serverless, not new Hyperscale databases, which carry no licence fee since December 2023 ([Azure Hybrid Benefit for SQL](https://learn.microsoft.com/en-us/azure/azure-sql/azure-hybrid-benefit)) | VMs under Oracle's cloud policy; Oracle Database@Azure is a separate commercial construct |
| AWS | EC2 Dedicated Hosts only, with licences bought before 1 October 2019 (or true-ups under an agreement effective before it) and a version released before that date; no Software Assurance route exists; licences bought through CSP are excluded ([AWS Windows licensing FAQ](https://aws.amazon.com/windows/faq/)) | EC2 default tenancy with Software Assurance through License Mobility (Microsoft's form, then AWS's); RDS for SQL Server "Bring Your Own Media" with active Software Assurance, Enterprise and Standard, versions 2019 to 2025, the Windows fee still billed, no in-place major upgrade, no SSAS or SSRS ([RDS Bring Your Own Media](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/sqlserver-byom.html)); without Software Assurance: Dedicated Hosts and SQL Server 2017 or earlier ([AWS License Mobility](https://aws.amazon.com/windows/resources/licensemobility/)) | EC2 BYOL; RDS for Oracle BYOL for Enterprise Edition and Standard Edition 2, licence-included for SE2 only; a BYOL Multi-AZ instance needs licences for primary and standby ([RDS Oracle licensing](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Oracle.Concepts.Licensing.html)) |
| Google Cloud | Sole-tenant nodes only, pre-October-2019 versions and enrolments, your own imported image ([Compute Engine BYOL](https://docs.cloud.google.com/compute/docs/nodes/bringing-your-own-licenses)) | With Software Assurance and License Mobility, on shared-tenancy VMs when the Windows image is Google's; without, sole-tenant and SQL Server 2017 or earlier; Cloud SQL for SQL Server has no BYOL, a four-core licence minimum and bills one licence for a high-availability pair ([Cloud SQL pricing, licensing](https://cloud.google.com/sql/pricing)) | Compute Engine VMs under Oracle's cloud policy |

**3. Count cores the vendor's way, not the console's.** The same VM carries a
different licence count under each vendor's rule:

- *SQL Server per core*: a minimum of four core licences per virtual machine, whatever
  its vCPU count. Under Azure Hybrid Benefit an Enterprise core licence converts to four
  General Purpose vCores or one Business Critical vCore; a Standard core licence to one
  General Purpose vCore, and four Standard cores to one Business Critical vCore (link
  above). Server plus CAL licences are not eligible.
- *Windows Server per core*: a minimum of eight core licences per virtual machine under
  Azure Hybrid Benefit, core for core above that, sixteen core licences per processor
  licence ([AHB for Windows Server](https://learn.microsoft.com/en-us/azure/virtual-machines/windows/hybrid-use-benefit-licensing)).
  Datacenter licences keep the on-premises deployment running alongside Azure;
  Standard licences get a 180-day migration allowance and no ongoing dual use
  ([Windows Server licensing](https://www.microsoft.com/licensing/product-licensing/windows-server)).
- *Oracle Database in an Authorized Cloud Environment*: two vCPUs count as one Processor
  licence when multi-threading is enabled, one vCPU as one licence when it is not, and
  the Processor Core Factor Table does not apply. An x86 core that the factor table
  counts at 0.5 on premises needs a whole licence in the cloud, so a like-for-like move
  doubles the Enterprise Edition licence count for the same physical compute. Standard
  Edition 2 counts four vCPUs as one socket and is capped at 8 vCPUs per instance
  ([Oracle, Licensing Oracle Software in the Cloud Computing Environment](https://www.oracle.com/a/ocom/docs/cloud-licensing-070579.pdf),
  policies as of 4 September 2026). Licences under an Unlimited License Agreement may
  be used there but do not count at certification.
- *Multi-threading off* halves the licensed vCPU count for the SQL Server licence
  component on Cloud SQL, without halving the compute charge. It saves nothing on
  Oracle: two vCPUs per licence with multi-threading on and one with it off both come
  to one licence per physical core.

**4. Price both sides from the bill and the price list, never from the brochure.**
The licence-included premium is the difference between two otherwise identical
products, and each provider exposes it differently:

- *Azure*: the SQL Server licence is its own meter on SQL VMs and on vCore databases,
  so the premium is a filter in Cost Management; the Windows share is folded into the
  VM meter, so compare the VM rate with and without the benefit in the pricing
  calculator. Which VMs claim the benefit is the `licenseType` property on the resource
  (Resource Graph: `where type =~ 'microsoft.compute/virtualmachines' | extend lic = tostring(properties.licenseType)`);
  the FinOps Toolkit's Azure Hybrid Benefit workbook does this fleet-wide (see
  `finops-azure-commitments.md`). Centrally managed Azure Hybrid Benefit assigns SQL
  licences at subscription or billing-account scope on EA and MCA, and bills anything
  above the assignment at pay-as-you-go
  ([centrally managed AHB](https://learn.microsoft.com/en-us/azure/cost-management-billing/scope-level/overview-azure-hybrid-benefit-scope)).
- *AWS*: the Price List API carries `operatingSystem`, `preInstalledSw` and `tenancy`
  per EC2 product; the SQL Server premium is the price gap between two products that
  differ only in `preInstalledSw`, because `licenseModel` reads "No License required"
  even on a licence-included SQL product. In the Cost and Usage Report the
  `product_license_model` column separates `license-included` from
  `bring-your-own-license` usage
  ([CUR product columns](https://docs.aws.amazon.com/cur/latest/userguide/product-columns.html)).
  On a Dedicated Host, an AWS Windows AMI adds a per-vCPU, per-instance-hour software
  charge on top of the host; a BYOL image adds none
  ([Dedicated Hosts pricing](https://aws.amazon.com/ec2/dedicated-hosts/pricing/)).
- *Google Cloud*: premium images (Windows Server, SQL Server, RHEL, SLES) bill per vCPU
  as separate SKUs beside the machine type, committed use discounts never apply to them,
  and a Spot VM pays them in full
  ([disk and image pricing](https://cloud.google.com/compute/disks-image-pricing)).

With the premium per hour in hand, the comparison is annual: the fleet's licence-included
premium (licensed hours in the year, times the premium) against the carrying cost of
owning: the Software Assurance or subscription fee for the cores that must stay covered,
the compliance tooling and the people who run it, and on AWS the Dedicated Host hours
billed whether the host is full or not. Where Software Assurance is paid anyway for the
on-premises estate, its marginal cost for the cloud fleet is close to zero and BYOL wins
on anything steady. Where it is kept only to feed the cloud, the fee against the premium
is the whole decision, and it is the renewal question below.

**5. Weigh what each side gives up.**

| | BYOL | Licence-included |
|---|---|---|
| Elasticity | Cores stay licensed whether they run or not; Windows on AWS or Google needs host-level capacity planning, and AWS holds a Windows licence to the same physical host for 90 days | Scales to zero with the instance; nothing to reassign |
| Replicas | With Software Assurance, one passive high-availability replica, one passive disaster-recovery replica and one passive DR replica in Azure carry no licence; passive means no queries served, backups and checks allowed ([SQL VM pricing guidance](https://learn.microsoft.com/en-us/azure/azure-sql/virtual-machines/windows/pricing-guidance)). Microsoft's licensing guide says the rights differ under License Mobility, so confirm them with the partner before counting them on AWS or Google | Every running instance is a licensed instance, a Multi-AZ standby on RDS included. The exception is Azure, where since November 2022 a pay-as-you-go SQL VM flagged as HA/DR pays no SQL licence when all three replicas run in Azure |
| Commitments | On AWS, Windows and SQL Server Reserved Instances have no size flexibility and a Standard RI cannot change platform, so a move from licence-included to BYOL strands them (a Convertible RI can be exchanged); Compute Savings Plans follow the instance whatever its platform, Dedicated Hosts included ([how RIs apply](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/apply_ri.html), [Savings Plans types](https://docs.aws.amazon.com/savingsplans/latest/userguide/plan-types.html)). On Azure, reservations price compute and the benefit sits underneath either way. On Google Cloud, committed use discounts never cover licence SKUs | The licence rides inside the committed rate: cheaper to commit, impossible to separate later |
| Audit | Assignment records per VM or core, verification forms, the 90-day reassignment rules, and Software Assurance continuity: the day it lapses, Azure Hybrid Benefit and License Mobility end | None beyond paying the bill |
| Upgrades and lock | RDS Bring Your Own Media blocks in-place major upgrades; on AWS an instance launched from an AWS AMI stays licence-included for life, and conversion to BYOL is possible only for instances launched from your own imported image ([licence type conversion](https://docs.aws.amazon.com/license-manager/latest/userguide/conversion-prerequisites.html)); Windows Server 2022 and 2025 are never BYOL-eligible on AWS or Google | Any version the provider offers, in place |

**6. Decide per workload class, and write the rule down.** Working defaults, to be
checked against the counts of step 3 and the prices of step 4:

| Workload | Default | Why |
|---|---|---|
| Steady 24x7 SQL Server Enterprise with Software Assurance, on Azure | Azure Hybrid Benefit, then a reservation on the compute | Four General Purpose vCores per Enterprise core and free passive replicas; the premium would run every hour of the year |
| The same on AWS | License Mobility on EC2, or RDS Bring Your Own Media if the engine constraints fit | Shared tenancy, no host to plan; count the Multi-AZ standby |
| Any Windows Server at AWS or Google with licences bought after 1 October 2019 | Licence-included | No BYOL route exists; stop the debate |
| Elastic, scheduled, autoscaling, dev/test | Licence-included (SQL Server Developer edition for dev/test, free either way) | Licensed hours are low and variable; a licence idle half the year still costs the full fee |
| Oracle Enterprise Edition | BYOL, after recounting at two vCPUs per licence | Licence-included exists only for SE2 on RDS; the recount shapes the instance, not the model |
| Small Oracle Standard Edition 2 | Compare RDS licence-included against owned licences at four vCPUs per socket | The 8-vCPU cap bounds both sides |
| Linux | Nothing to decide, except RHEL and SLES | Premium image and Dedicated Host rules apply to those two; on AWS Dedicated Hosts they need your own AMI |

Record each rule with the licence pool it draws from and the Software Assurance renewal
date that makes it legal. Review at every renewal and every Product Terms change.

### When the Software Assurance renewal comes up

Software Assurance is the ticket to every BYOL route the cloud still allows for
Microsoft software: Azure Hybrid Benefit, License Mobility, the Flexible Virtualization
Benefit, per-virtual-machine licensing of SQL Server 2022 and later, and the passive
replica rights. Letting it lapse is not symmetrical with keeping it: a licence bought
after 1 October 2019 that loses its Software Assurance cannot be deployed with any
Listed Provider at all, so the cloud estate it covered becomes licence-included on the
renewal date, and the right cannot be bought back later except by buying licences again.
The renewal case is therefore the annual fee for the cores the cloud estate consumes,
against that estate's annual licence-included premium plus whatever the on-premises
rights (new versions, dual use for Datacenter, passive replicas) are worth to the
organisation. Where the premium exceeds the fee, Software Assurance has paid for itself
before any on-premises benefit is counted; where it does not, the honest alternative is
licence-included on a planned date, not an unmonitored lapse. Procurement owns the fee,
FinOps owns the premium, ITAM owns the assignment records: the decision needs the three
numbers on one page 90 days before the renewal, which is what the pre-renewal checkpoint
of the operating model below is for.

### Common BYOL scenarios

**Azure Hybrid Benefit:** the licensing overlay under every other Azure commitment
decision, enabled on eligible VMs and vCore databases before any reservation is sized.
`finops-azure-commitments.md` carries the discount order and the sizing patterns; the
table in step 2 carries the eligibility rules.

**AWS License Manager:** self-managed licence rules counted in vCPUs, cores, sockets or
instances, with hard or soft limits, host affinity from 1 to 180 days and a tenancy
requirement (core and socket counting need Dedicated Hosts); host resource groups
allocate and release Dedicated Hosts automatically against those rules
([License Manager configuration](https://docs.aws.amazon.com/license-manager/latest/userguide/config-overview.html),
[host resource groups](https://docs.aws.amazon.com/license-manager/latest/userguide/host-resource-groups.html)).
It is the ITAM record of truth for BYOL on AWS; FinOps reads the Dedicated Host
utilisation it produces, because an under-filled host is the BYOL waste pattern.

**Oracle on a hyperscaler:** the recount of step 3 comes before the architecture. A
lift-and-shift that keeps the on-premises core count doubles the Enterprise Edition
licence requirement; right-sizing the instance to the licences owned and moving
Standard Edition 2 to RDS licence-included are the two levers (turning multi-threading
off is not one: the count stays at one licence per core). Joint FinOps-ITAM review before any Oracle cloud
migration is essential, and because the policy document that defines the count is
explicitly not contractual, the entitlement position must be confirmed against the
licence agreement itself.

---

## Joint operating model

### Governance alignment

In the organisations OptimNow has worked with, FinOps-ITAM collaboration works best
through shared forums rather than through RACI matrices that reinforce boundaries.

| Practice | Purpose | Cadence |
|---|---|---|
| Joint cost and compliance review | Review spend trends, licence utilisation, compliance posture, and upcoming renewals | Monthly |
| Marketplace channel review | Assess marketplace pipeline, spend vs commitment targets, entitlement gaps | Monthly |
| Pre-renewal checkpoint | Validate usage data, entitlement position, and negotiation strategy before vendor renewals; put a FOCUS-conformant billing export on the term sheet (see `finops-focus.md`) | Pre-renewal (60-90 days before) |
| Vendor strategy review | Review channel mix, marketplace volume, EA performance, and consolidation opportunities per strategic vendor | Quarterly |
| Deal Desk engagement | Joint FinOps-ITAM-Procurement review for any commitment above a defined threshold | As needed |
| Licence true-up | ITAM reconciles deployed against licensed and owns the count; FinOps supplies the cloud side (BYOL cores in use, licence-included hours already paid, Azure Hybrid Benefit assignments); Procurement owns the order | Annual, before the enrolment anniversary |

### Shared data requirements

FinOps and ITAM operate from different systems of record. The collaboration only works when
these systems are connected - not necessarily in a single platform, but with consistent,
reconcilable data.

| Data domain | Typical FinOps source | Typical ITAM source | Integration requirement |
|---|---|---|---|
| Usage and consumption | Cloud billing (CUR, Cost Management, BigQuery export) | N/A | ITAM needs consumption signals for licence right-sizing |
| Entitlements and contracts | N/A | SAM tool, contract repository, CMDB | FinOps needs entitlement data for BYOL and commitment modelling |
| Cost allocation | Cloud cost platform, tagging | CMDB, application portfolio | Unified tagging and naming standards across cloud and on-premises |
| Marketplace purchases | Cloud billing line items | SAM tool (if integrated) | SKU normalisation between cloud billing and SAM inventory |
| Forecasts | FinOps forecasting models | ITAM renewal calendar | Shared demand signal for procurement and budget planning |

### Bi-directional skills development

Effective collaboration requires both teams to understand each other's domain. Organisations
that invest in cross-training report better cost avoidance outcomes; this is an
observation from practice, not a measured benchmark.

- FinOps teams need: licensing fundamentals (perpetual vs subscription, use rights, audit triggers), contract structure awareness, compliance risk vocabulary
- ITAM teams need: cloud billing mechanics (consumption models, commitment discounts, reserved pricing), cost allocation principles, FinOps maturity stages

---

## Consumption-based SaaS monitoring

Consumption-based SaaS products (where billing is tied to usage units rather than fixed
seats) require specific monitoring to prevent overage charges. This is distinct from
seat-based SaaS sprawl management covered in `finops-sam.md`.

### The risk

A company purchases a consumption-based SaaS application with an agreed number of
consumption units per SKU. When consumption of one SKU increases significantly beyond
contracted limits, overage charges apply - often at a premium rate.

### Monitoring framework

1. At contract start, identify all SKUs, their consumption limits, whether overages are
   charged or consumption stops, and the overage rates.
2. Ingest consumption data at SKU level into a monitoring platform.
3. Configure anomaly detection or threshold-based alerting at meaningful levels before
   overages occur (e.g., 70%, 85%, 95% of limit).
4. When anomalies are detected, FinOps, ITAM, and Engineering collaborate to determine
   root cause: configuration issue, new use case, or genuine growth.
5. Maintain a baseline forecast and use forward-looking models to project consumption
   against contract limits.

### Key metrics
- % consumed / total contracted units (per SKU)
- Total overage charges (currency)
- Forecast accuracy: projected vs actual consumption at renewal
- Number of SKUs with no monitoring in place

### Anti-patterns
- Paying overages without investigating root cause
- Renewing at the same commitment level without reviewing actual usage data
- Planning to monitor "later" - even manual tracking is better than no tracking

---

## Application onboarding checklist

When new SaaS or cloud-hosted applications are introduced, cost allocation and licence
compliance gaps created at onboarding compound over time. Both FinOps and ITAM should be
involved before the application goes live.

1. **Pre-onboarding assessment**
   - Validate licensing model and subscription tiers
   - Check for duplicate SaaS to avoid sprawl (ideally resolved at procurement stage)
   - Identify any burstable or consumption-based charges within hyperscaler accounts
   - Align enterprise tagging standards for cost allocation

2. **Contract and commitment alignment**
   - Review cloud commitments against vendor licensing models
   - Set up budget notifications and approval gates for consumption spending

3. **Integration and tooling**
   - Connect ITAM/SAM and FinOps tooling
   - Add a complete record to the software asset inventory

4. **Operational governance**
   - Define cadence for usage reviews and renewal checkpoints
   - Implement alerting for non-compliance and cost anomalies

5. **Recurring optimisation**
   - Benchmark performance and cost trends
   - Review licence reclamation and rightsizing opportunities on a defined schedule

---

## Automated governance (advanced)

At Run maturity, organisations deploy automated agents or agentless connectors across
hybrid environments for continuous inventory, compliance, and cost governance.

### What automated governance delivers
- Unified inventory trusted by FinOps, ITAM, Security, and Procurement
- Real-time actions: tag corrections, resource shutdowns, licence re-harvesting
- Reduced manual audit effort
- Waste reduction from orphaned resources and unused licences

### Prerequisites
- Established and consistent tagging strategy
- Strong data quality and attribution across reporting systems
- Agreed governance policies with defined thresholds and remediation actions

### Key metrics
- Compliance status of deployed resources
- % of resources with accurate allocation metadata
- Cost reduction from automated licence re-harvesting or resource shutdowns

### Anti-patterns
- Attempting inventory tracking without a unified data source
- Deploying BYOL without implementing compliance monitoring within 30 days
- Automating governance rules without cross-team agreement on thresholds and actions

---

## Crawl / Walk / Run maturity for FinOps-ITAM collaboration

| Indicator | Crawl | Walk | Run |
|---|---|---|---|
| Organisational alignment | Separate teams, no co-ordination | Regular collaboration meetings, shared KPIs emerging | Integrated practice or unified leadership, shared data and goals |
| Data integration | Siloed systems, no shared data | Key systems linked (billing + SAM), manual reconciliation | Automated data pipelines, unified schemas, single source of truth |
| Marketplace governance | No visibility into marketplace purchases | Channel strategy defined for top vendors, monthly reviews | Automated checks, Deal Desk integration, commitment-aware purchasing |
| BYOL management | No tracking of licence use in cloud | Key licences tracked (SQL Server, Windows), periodic review | Automated eligibility verification, continuous compliance monitoring |
| Vendor negotiation | FinOps and ITAM negotiate separately | Joint preparation for major renewals | Combined volume leverage, channel mix optimisation, unified vendor strategy |
| Consumption monitoring | No SKU-level visibility | Top applications monitored, manual threshold alerts | Automated anomaly detection, forward-looking forecasting, proactive optimisation |

Always assess maturity before recommending changes. An organisation where FinOps and ITAM
have never co-ordinated should start with a shared monthly review of the top 5 vendors -
not with an automated governance platform.

---

> Sources: FinOps Foundation ([FinOps & ITAM: Collaborating to Optimize Cost, Risk, and
> Value](https://www.finops.org/wg/finops-itam-optimize-cost-risk-value/) and [FinOps & ITAM Practical Scenarios: Planning &
> Procurement](https://www.finops.org/wg/finops-itam-practical-scenarios-planning-procurement/), both CC BY 4.0, adapted; FinOps for SaaS scope),
> State of FinOps 2026 (6th edition, February 2026), Gartner MQ for Cloud Financial
> Management Tools (July 2024), vendor entitlement management documentation (Microsoft,
> Oracle, SAP), Flexera 2025 State of Cloud Report. Licensing mechanics in the BYOL
> section: Microsoft Learn and Product Terms, AWS documentation, Oracle's cloud licensing
> policy and Google Cloud documentation, each linked where it is used, read 9 November 2026.

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*