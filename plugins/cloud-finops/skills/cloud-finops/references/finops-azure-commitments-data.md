---
name: finops-azure-commitments-data
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Rate Optimization"
fcp_capabilities_secondary: ["Architecting & Workload Placement", "Forecasting"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Finance"]
fcp_personas_collaborating: ["Engineering", "Procurement", "Leadership"]
fcp_maturity_entry: "Walk"
business_coverage: ["azure:commitments:deep"]
questions:
  - q: "Can we reserve Azure SQL, Cosmos DB or storage, and when is it worth it?"
    section: "Database commitment decision tree"
  - q: "Savings Plan for Databases or database reservations: which one fits our Azure SQL and PostgreSQL estate?"
    section: "Savings Plan for Databases"
  - q: "Is reserved capacity worth buying for our blob storage and Azure Files, for one year or for three?"
    section: "Storage reserved capacity"
  - q: "Should we buy reservations for our Premium SSD managed disks?"
    section: "Storage reserved capacity"
  - q: "Can Azure SQL serverless, DTU tiers or Burstable servers be reserved, and what does a database reservation never cover?"
    section: "Database commitment decision tree"
  - q: "Is Cosmos DB reserved capacity worth it when our throughput runs on autoscale?"
    section: "Database commitment decision tree"
  - "Faut-il réserver nos bases Azure SQL et Cosmos DB et notre stockage Blob, et pour quelle durée ?"
---

# Azure Commitment Discounts: databases and storage

> Azure commitments beyond compute: the database commitment decision tree (reservations
> for SQL Database, SQL Managed Instance, PostgreSQL, MySQL and Cosmos DB, and the
> Savings Plan for Databases), what cannot be reserved, and storage reserved capacity
> for Blob, ADLS Gen2, Azure Files and Premium SSD managed disks. Compute instruments,
> the liquidity rules after 1 February 2027, the net discount under a MACC and phased
> purchasing are in `finops-azure-commitments.md`; compute sizing and Advisor
> calibration in `finops-azure-commitments-sizing.md`; database and storage usage
> optimisation in `finops-azure-data.md`.

---

## Database commitment decision tree and fundamentals

### Database commitment decision tree

Azure offers two commitment instruments for database services, plus operational
optimisations that should be applied before any commitment purchase.

**Pre-commitment optimisation (do these first):**
1. Enable Azure Hybrid Benefit on all eligible SQL Database and SQL MI instances
2. Switch dev/test databases to SQL Serverless (auto-pause)
3. Stop PostgreSQL/MySQL Flexible Servers outside business hours
4. Consolidate small databases into Elastic Pools
5. Review DTU vs vCore: migrate to vCore if AHB-eligible for licence savings
6. Right-size overprovisioned compute and storage tiers

**Decision tree:**

```
Is the database workload stable and predictable (90+ days)?
+-- NO -> Stay on PAYG or use Serverless (auto-pause for intermittent use).
|         Re-evaluate quarterly.
|
\-- YES -> Has the database been right-sized and optimised? (steps 1-6 above)
    +-- NO -> Optimise first, commit second. Do not lock in waste.
    |         (A keel sized to the post-optimisation floor can be bought now:
    |         see finops-aws-commitments.md, keel commitment.)
    |
    \-- YES -> What is the database estate profile?
        |
        +-- Single service, single region, stable configuration
        |   -> Azure Reservation (deeper discount than Savings Plan)
        |     - Available for: SQL Database, Cosmos DB, PostgreSQL,
        |       MySQL, SQL MI
        |     - Exchange retires 1 Feb 2027 for these services (one final
        |       exchange for reservations bought before that date)
        |     - Pro-rated refund (up to $50K/12 months) and trade-in to a
        |       savings plan remain
        |
        +-- Multiple database services or regions
        |   -> Savings Plan for Databases (up to 35%, March 2026)
        |     - Covers: SQL Database, PostgreSQL, MySQL, Cosmos DB,
        |       SQL MI
        |     - Applies savings across services and regions automatically
        |     - Cannot be exchanged or refunded once purchased
        |     - CAUTION: SQL Server on Azure VMs and Azure Arc consume
        |       the commitment at PAYG rates (no discount) - factor
        |       this into sizing the hourly commitment
        |
        +-- Mix of stable and evolving workloads
        |   -> Layer both: Savings Plan for Databases as broad baseline,
        |     then add Reservations for the most stable, high-spend
        |     database instances to capture deeper discounts
        |
        \-- Cosmos DB (special case)
            -> Reserved capacity on a predictable RU/s baseline (units and
              ratios below); serverless first for low or intermittent usage
```

**Diagnostic questions beyond the pre-commitment list:** how much of a Database Savings
Plan's hourly commitment would SQL Server on Azure VMs absorb at PAYG rates? Are
overprovisioned tiers (Business Critical on non-prod, RA-GRS backup storage on
non-critical DBs) inflating the baseline you would commit to?

**What cannot be reserved.** DTU-based SQL tiers (Basic, Standard, Premium); Azure
SQL Database serverless compute (Learn: "Reservation discounts don't apply to Azure
SQL Database serverless", read 15 October 2026); the PostgreSQL and MySQL Flexible
Server Burstable tier (only General Purpose and Memory Optimized have reservation SKUs
in the price list); Cosmos DB serverless; and the storage, backup, IOPS and licence
meters of every database service, since reservations cover compute vCores only. The
reservable base of a mid-size estate is therefore often a fraction of the "database"
line in Cost Management: size it from the vCore meters, not from the service total.

**Reservation units per service:**
- **SQL Database and SQL MI:** one vCore per region + service tier + hardware
  generation, with size flexibility within the tier and region, elastic pools
  included. Zone redundancy is a separate add-on reservation type ("vCore ZR"; read
  its rate from the Retail Prices API). Reservations cover the primary and the billable
  secondary replicas.
- **PostgreSQL Flexible:** one vCore per region + tier + compute series (Ddsv4,
  Ddsv5, Dsv6, Edsv5 and so on). Advisor includes zone-redundant HA standby vCores in
  its recommended quantity, which implies the standby compute is reservable
  (moderate confidence; Learn does not state it).
- **Cosmos DB:** fixed reservations in 100 RU/s units, 20% for 1 year and 30% for
  3 years below 1 M RU/s (larger quantities tier deeper; read the page), bought
  without a region but applied per region with ratios (most regions 1.0, France
  Central 1.25, France South 1.625); autoscale throughput consumes the reservation
  with a 1.5 multiplier; serverless and storage are excluded. Source:
  https://learn.microsoft.com/en-us/azure/cosmos-db/reserved-capacity (page dated
  27 April 2026).

**Sizing with daily data.** Unlike savings plans, database reservations are
count-based: Cost Management daily vCore-hours divided by 24 gives the vCores billed
per day, and the 90-day minimum (or P10) per key is the quantity to reserve. No hourly
join is needed (contrast "Why daily data hurts Savings Plan sizing more than RI
sizing" in `finops-azure-commitments-sizing.md`). Under a MACC, apply the net-discount
rule (`finops-azure-commitments.md`) before ranking candidates.

### Savings Plan for Databases (announced March 2026)

A fixed hourly spend (e.g. $5/hr) committed for one year, applied each hour across
services and regions to the usage with the greatest discount first. Scope:
subscription, resource group, management group or billing account; monthly or upfront
payment, optional auto-renewal. Azure Database for MariaDB retired in September 2025
and is not covered: MariaDB workloads still running sit on VMs, containers or a third
party, outside any database commitment.

**Terms and coverage as published (Azure savings plans page and Redmondmag, 10 April
2026; both read 15 October 2026).** 1-year term only. Covered: Azure SQL Database
(provisioned, serverless and Hyperscale), SQL Managed Instance, Azure Database for
PostgreSQL, Azure Database for MySQL, Azure Cosmos DB, Azure DocumentDB and Database
Migration Service; SQL Server hourly licences on Azure VMs and Arc draw down the
commitment at 0% discount, as above. Indicative 1-year discounts: SQL Database
serverless 35%; SQL Database provisioned, PostgreSQL and MySQL about 20%; Cosmos DB
12% (Redmondmag table; the Azure page says "0% to 35%"). The plan cannot be modified
or cancelled. It combines with reservations, and the billing engine applies the
highest-percentage usage first; portal recommendations use the last 30 days of
pay-as-you-go usage. Position: this is the only commitment instrument that reaches
SQL serverless. On provisioned workloads a 3-year reservation beats it by a wide
margin, and under a MACC its 12-20% tiers lose most of their value (see "Net discount
under a MACC with an Azure Commitment Discount" in `finops-azure-commitments.md`).

Database usage optimisation (serverless auto-pause, Flexible Server start/stop, elastic
pools, Cosmos DB autoscale) is in `finops-azure-data.md`, "Database optimisation patterns".

---

## Storage reserved capacity - Blob, ADLS Gen2, Files, managed disks

Storage is the commitment surface most Azure estates leave uncovered, and the one
where the discount shape differs most from compute: shallow 1-year terms, a strict
matching key, and an hourly use-it-or-lose-it model with no size flexibility. The
figures below are West Europe USD list prices from the Azure Retail Prices API
(queried 15 October 2026, `serviceName eq 'Storage' and armRegionName eq
'westeurope' and type eq 'Reservation'`), illustrative and dated; other regions and
redundancies follow similar ratios but must be read from the portal or the API.

| Instrument | Unit and term | Matching key | What is discounted | 1-year / 3-year discount (West Europe list, 15 October 2026) |
|---|---|---|---|---|
| Blob and ADLS Gen2 reserved capacity | 100 TiB or 1 PiB per month; 1 or 3 years; upfront or monthly | Region + access tier (Hot, Cool, Archive) + redundancy | "Data Stored" capacity meters only | Hot LRS 100 TiB 18% / 34%; Hot LRS 1 PiB 22% / 38%; Cool LRS 100 TiB 18% / 34%; Archive LRS 100 TiB 11% / 18% |
| Azure Files reserved capacity | 10 TiB or 100 TiB; 1 or 3 years | Region + tier (Premium, Hot, Cool) + redundancy | Provisioned (Premium) or stored capacity | Premium LRS 10 TiB 18% / 34%; Premium ZRS 10 TiB 18% / 34% |
| Premium SSD managed disk reservation | Per disk, P30 to P80 only; 1 year only | Region + disk SKU, no size flexibility | The disk's monthly rate | P30 to P80 LRS: 5% |

**Blob and ADLS Gen2.** Eligible: standard GPv2 and Blob storage accounts, block
blobs and ADLS Gen2. Not eligible: GPv1, premium block blob accounts, page blobs,
queues, tables (Azure Files has its own reservation, below). Cold does not appear in
the reservation documentation or the pricing grid; treat it as not reservable and
verify if a customer asks. The key is strict: a Hot LRS West Europe reservation covers
no Cool data, no ZRS data and no France Central data, so each key needs its own
reservation. Only the capacity meters are discounted; operations, bandwidth,
early-deletion and index charges stay pay-as-you-go. The reservation applies hourly:
hours above the reserved quantity bill at pay-as-you-go, unused reserved hours are
lost, and coverage resets every hour. Exchange is unlimited but storage-for-storage
only and goes through a support request; refunds sit inside the $50,000 rolling
12-month cap. No savings plan covers storage, so the 1 February 2027 exchange
retirement should not reach storage reservations (moderate confidence: the exchange
page does not name storage).

Sizing: take 90 days of daily stored capacity per key (Azure Monitor `BlobCapacity`
split by `BlobTier`, or the Cost Management "Data Stored" meter quantity), use the P10
as the floor, subtract any planned lifecycle tiering (Hot to Cool or Archive moves
shrink the Hot key), then count whole 100 TiB blocks. Tier first, reserve second: a
Hot reservation bought before a lifecycle policy lands locks a shrinking base for 1 or
3 years. Calibration: the 1-year blob discount is shallow (11 to 18%), and under a
MACC with an ACD on pay-as-you-go it collapses to single digits (see "Net discount
under a MACC with an Azure Commitment Discount" in `finops-azure-commitments.md`).
The 3-year term is where blob
reservations carry value; the trade-off is a 3-year lock on the key that tiering
projects tend to shrink.

**Azure Files.** Units of 10 TiB and 100 TiB, 1 or 3 years, per region + tier
(Premium, Hot, Cool) + redundancy. Premium Files bill on provisioned GiB whether used
or not, so the base is very stable, which makes Premium Files a better reservation
candidate per TiB than blob. Sequence: shrink over-provisioned premium shares first
(provisioned v1 sizes shares for IOPS, so many are oversized), then reserve.
Whether the reservation applies to the provisioned v2 billing model
is not documented: verify before recommending it on v2 accounts.

**Premium SSD managed disks.** Premium SSD P30 to P80 only (P1 to P20 are listed as
"currently unavailable"), 1-year term only, LRS SKUs only in the price list (no ZRS
reservation SKU observed). Not eligible: Standard SSD and HDD, Premium SSD v2, Ultra,
unmanaged disks. The reservation is per disk SKU and region with no size flexibility
(a P40 reservation does not cover two P30 disks); quantity is the number of disks. It
applies hourly, and a disk in the "Reserved" state (attached to a deallocated VM)
still bills and still consumes the reservation. Calibration: any ACD above 5% erases the
5% list discount; under an illustrative 10% ACD the reservation costs about 6% more than
discounted pay-as-you-go. The disk
levers that pay are Premium to Standard SSD rightsizing where premium IOPS are not
needed, deleting unattached disks (`azure-orphan-disks` playbook) and reviewing disks
attached to long-deallocated VMs. A disk reservation only makes sense on a large,
stable P30+ fleet with no ACD or an ACD below 5%.

Sources: https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blob-reserved-capacity,
https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/understand-storage-charges
and https://learn.microsoft.com/en-us/azure/virtual-machines/disks-reserved-capacity
(all read 15 October 2026); https://azure.microsoft.com/en-us/pricing/details/storage/blobs/
and https://prices.azure.com/api/retail/prices (queried 15 October 2026).

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
