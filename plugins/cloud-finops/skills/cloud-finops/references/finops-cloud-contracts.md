---
name: finops-cloud-contracts
fcp_domain: "Optimize Usage & Cost"
fcp_capability: "Rate Optimization"
fcp_capabilities_secondary: ["Licensing & SaaS"]
fcp_phases: ["Optimize", "Operate"]
fcp_personas_primary: ["FinOps Practitioner", "Procurement"]
fcp_personas_collaborating: ["Finance", "Leadership"]
fcp_maturity_entry: "Walk"
business_coverage: ["aws:contracts:deep", "azure:contracts:deep", "gcp:contracts:deep", "data-platforms:contracts:partial", "aws:saas:partial", "azure:saas:partial", "gcp:saas:partial"]
---

# Cloud Contract Negotiation - Enterprise Agreements on AWS, Azure and Google Cloud

> Negotiated spend commitments with the three hyperscalers: AWS Private Pricing (EDP,
> PPA), the Azure MACC and its Azure Commitment Discount under an EA or MCA-E, and the
> Google Cloud Minimum Commitment. Covers vocabulary, the clauses of an enterprise
> agreement, Marketplace drawdown, migration credits, the reseller route, an intake
> protocol, a 15-check offer review grid, timing, and where benchmarks come from.

The contract layer sits above the metered instruments (Savings Plans, Reservations, CUDs,
covered in the provider commitment files). This file answers 3 questions: what the
vehicle is, what is negotiable, and what it costs you when the commitment is wrong.

---

## Vocabulary and where the discount shows in billing data

Use the official name in a negotiation; the billing data is how you verify the discount
was applied.

| | AWS | Azure | Google Cloud |
|---|---|---|---|
| Official name | "Private Pricing" | Microsoft Azure Consumption Commitment (MACC), with an Azure Commitment Discount (ACD) | No public product name. Google's documents say "Minimum Commitment" under a "Google Cloud Addendum", and "custom pricing contract" |
| Practitioner names | EDP, PPA (the same instrument today); PPTS for the pre-signature term sheet | MACC with ACD; "Azure Consumption Discount" in a minority of sources | "PPA", "custom contract", committed spend discount (CSD) |
| Signed document | AWS Private Pricing Addendum to the customer's agreement | One amendment per construct on the EA enrollment, or MCA-E amendments | Google Cloud Addendum and Order Form |
| Where the discount shows | CUR 2.0 `Discount` line items (the name varies; parse `line_item_line_item_description`) and `line_item_net_unblended_cost`, present only when the account has a discount | Price sheet: `unitPrice` below `marketPrice`; `basePrice` is the price at signature | A "Negotiated savings" credit, defined as costs at contract price minus costs at list price, shown from 1 May 2021 |

In a FOCUS export the negotiated discount sits between `ListCost` and `ContractedCost`;
commitment discounts sit between `ContractedCost` and `EffectiveCost` (column
definitions in `finops-allocation-showback.md`, export differences in `finops-focus.md`).
The FinOps Foundation leaves this layer out: its Commitment Discounts Overview states
that "private, third-party, or custom pricing will not be discussed", and the Rate
Optimization capability calls negotiated discounts "often private and subject to
non-disclosure terms", managed by Procurement with FinOps supplying usage data
(finops.org, read 13 October 2026).

Sources: AWS pricing page and CUR 2.0 line item dictionary (read 24 October 2026);
Microsoft Learn price sheet pages (updated 25 June 2026); Google Cloud Billing "savings
and credits" (updated 9 October 2026).

---

## Anatomy of an enterprise agreement: 12 clauses

Every enterprise agreement settles the same 12 questions, whatever the provider.
Read the term sheet against this list before reading the discount.

| # | Clause | What to look for |
|---|---|---|
| 1 | Commitment amount and measurement basis | Is spend counted gross or net of the negotiated discount? Which charges count (Marketplace, support, reservation purchases, credits)? |
| 2 | Term | Length, start date, co-terming with other agreements and your fiscal year |
| 3 | Ramp and growth | The amount per year, whether each year must be at or above the previous one, annual or cumulative measurement |
| 4 | Discount mechanism | Percentage on list, private unit rates, credits, or a mix; the scope clause that says which charges receive which discount |
| 5 | Eligible services and exclusions | The exclusion list, and whether the provider can extend it during the term |
| 6 | Marketplace counting rule and cap | The share of Marketplace spend that counts, the cap, the eligibility test |
| 7 | Support obligation and fee basis | Mandatory plan, fee computed before or after discounts, whether the fee counts toward the commitment |
| 8 | Shortfall and cure | When the gap is measured, how it is billed (cash, prepayment, credit), at what rate, and any cure period |
| 9 | Credits | Migration, milestone, training and one-time credits: amount, conditions, expiry, and the fact that they do not count toward the commitment |
| 10 | Price protection and end-of-term reversion | Whether list price rises reach you during the term, and what price applies the day after the term ends |
| 11 | Termination, step-down and M&A events | Termination for convenience on either side, reduction rights for divestiture or acquisition, assignment |
| 12 | Data and reporting obligations | Burn-down statements, drawdown reporting, a FOCUS-conformant export |

---

## AWS: Private Pricing

**The instrument.** AWS's pricing page describes Private Pricing as access "to commercial
benefits in exchange for a commitment", across "more than 200 eligible services over a
defined term", bought direct or through AWS partners. AWS publishes no threshold, tier or
discount level (read 13 October 2026). The signed instrument is an AWS Private Pricing
Addendum to the customer's agreement; the click-through AWS Customer Agreement (updated
14 August 2026) lets AWS terminate on 30 days' notice, and the addendum overrides that
for its term.

**What the public paper says.** A private pricing addendum filed publicly with the SEC
(a replacement addendum signed 24 October 2024) writes the mechanics: an annual Spend
Commitment per Contract Year; a Shortfall Payment equal to the gap, non-refundable and
usable as a balance against later charges, whose use does not count toward a later year;
commitment-eligible fees measured "net of discounts and refunds"; no termination for
convenience during the addendum term; mandatory Enterprise Support enrolment; repayment
of the discounts received if AWS terminates for cause; an exclusion list AWS can extend;
credits excluded from the commitment.

**How the discount interacts with the metered instruments.** On current contracts Private
Pricing applies after Savings Plans and Reserved Instances, to the already-discounted
amount (practitioner consensus); older paper differed, and the addendum's scope clause
decides. Private pricing customers cannot sell discounted Reserved Instances on the RI
Marketplace (EC2 documentation; AWS notice of January 2024 quoted by several
practitioners), which removes one liquidity route (see `finops-aws-commitments.md`).

**Enterprise Support arithmetic.** The official fee is the greater of $5,000 a month or
10% of monthly charges up to $150,000, 7% from $150,000 to $500,000, 5% from $500,000 to
$1M and 3% above $1M, computed on gross charges "before any discounts or credits are
applied", with Marketplace, Professional Services and Training outside the base. The
$5,000 floor replaced $15,000 on 2 December 2025, and Enterprise On-Ramp, Business and
Developer support end on 1 January 2027 outside GovCloud (AWS Support pricing page and
announcement, read 13 October 2026). At $1M a month of gross charges the fee is $64,500
a month, 6.45% of gross, untouched by the private discount (allocating it:
`finops-allocation-showback.md`, "Provider support fees"). The support fee is a
separate line and is negotiable; it does not follow the cross-service rate
automatically.

**Constructs beside the cross-service rate.** Signed agreements also carry
service-specific discounts; private unit rates on storage and data transfer, each tied
to a service-level usage commitment (a second shortfall risk); step-ups of the
cross-service rate above a spend threshold; and credits written as a share of
incremental spend with an annual cap and an attestation window (MAP mechanics, below),
including generative AI credits conditional on a deployed use case (see
`finops-for-ai.md`), each a separate ask by service.

**Marketplace.** Marketplace spend counts toward the commitment up to 25% of the annual
commitment (practitioner consensus); older paper may still carry a 50% formula, and the
addendum decides. Since 1 May 2025 only SaaS products "100% deployed on AWS
infrastructure", badged "Deployed on AWS", "continue to count towards additional
customer benefits" (AWS Marketplace blog, 25 February 2025).

**Entry and term.** Advisory estimates with undisclosed methodology, from a sample of
2025 to 2026 publications, converge on an entry floor of $500,000 to $1M a year and
terms of 1 to 5 years; AWS publishes neither.

---

## Azure: MACC and the Azure Commitment Discount

**The instrument.** Microsoft defines the MACC as "a contractual agreement where your
organization commits to spending a specific amount on Azure over a defined period"
(Microsoft Learn, updated 25 September 2025). It attaches to an EA enrollment or an MCA
billing account. Portal tracking "is available only to direct Microsoft Customer
Agreement and direct Enterprise Agreement customers", with alerts at 90, 60 and 30 days
(Microsoft Learn, updated 20 March 2026). No document offers a MACC through CSP.

**The amendment family.** On EA paper each construct is a separate amendment built on a
dated Microsoft template: "Microsoft Azure Consumption Commitment", "Azure Commitment
Discount", "Savings Plan Discount", "Azure Reserved Instance Discounting" (by named
families) and "Azure Monetary Commitment Adjustment (Azure Credit Offer)". The name on
the paper is Azure Commitment Discount.

**What the ACD reaches.** The ACD does not apply to reservations or savings plans;
separate discount amendments on savings plan rates and on named reservation families
exist and must be asked for and written in. The ACD's reach is set by the amendment's
scope clause (for example, Azure Services "billed at Consumption Rates"), and contracts
differ: read the scope clause, then verify on the price sheet by comparing `unitPrice`
with `marketPrice` on a reservation or savings plan purchase line. The list of
discounted reservation families is negotiated line by line; what is not on it is not
discounted; check database, analytics and cache reservations. The net discount of a
reservation under an ACD is computed in `finops-azure-commitments.md` ("Net discount
under a MACC with an Azure Commitment Discount").

**Price protection.** Under an EA, Microsoft guarantees prices "at or below" the
Customer Price Sheet and the prices in effect on the coverage start date, for the
prepayment term (Microsoft Learn, updated 21 April 2026). ACD amendments express this
as an Effective Price equal to the lowest of the baseline price (list at provisioning,
or at general availability for later services), the current month's list less the ACD,
and any service-specific price-sheet price. On the price sheet it shows as a `unitPrice`
that stays anchored to `basePrice` while `marketPrice` rises. Under MCA-E there is no
price protection by default (practitioner consensus); no Microsoft document states it
either way, so write Azure meter protection in explicitly.

**What counts toward the MACC.**
- Eligible Azure consumption, reservation and savings plan purchases, and "Azure benefit
  eligible" Marketplace offers bought through the Azure portal on a subscription tied
  to the agreement: "100% of the pretax purchase amount" counts when Microsoft invoices
  it, during the active term only (MACC FAQ, updated 24 July 2026).
- Not counted: Azure credits, consumption covered by prepayment or by a shortfall
  credit, Marketplace purchases paid by credit card or funded from Azure Prepayment,
  licences deployed on-premises or hybrid, support plans. The prepayment purchase itself
  does decrement the MACC.
- Timing: no retroactive credit for purchases made before eligibility; future instalment
  payments are not eligible; in the last month only the amount invoiced the following
  month counts; refunds replenish the MACC.

**Shortfall.** "If you don't meet the total MACC amount by the MACC end date, a shortfall
charge is applied to your account for the remaining balance. The charge takes the form
of an Azure prepayment credit"; a missed milestone triggers the same charge (Microsoft
Learn, updated 20 March 2026). EA amendments write 3 cases: the enrollment is still
active, and the prepayment is usable for the remaining term or 12 months, whichever
is shorter; the enrollment has expired and been renewed, and the prepayment is usable
under the new enrollment for 12 months; the enrollment has expired with no renewal,
and the shortfall invoice is paid in cash. The 12-month window is practitioner
consensus and matches the amendment wording. A customer who leaves Azure pays the
shortfall in money, not in credit.

**Credits.** The Azure Credit Offer is a one-time credit applied at the commitment start
and forfeited at the next anniversary. It does not count toward the commitment, and the
amendment states that Microsoft "is under no obligation to repeat" it.

**EA, MCA-E and CSP.** No Microsoft document sets a retirement date for the EA (October
2026); practitioner sources report smaller EA renewals declined and MACC customers moved
to MCA-E from 1 March 2026. On transition, reservations and savings
plans move "with no change to benefits or term", support benefits do not transfer, all
credits must be used first, and the move "can't be reverted" (Microsoft Learn, updated
31 March 2026). Treat a vehicle change as a new negotiation: every discount and
protection is restated, not carried over. Under CSP the partner sets the price and
bills; Partner Earned Credit excludes reservations, savings plans, Spot and Marketplace
products (Microsoft Learn, updated 27 March 2025).

**Support and bundling.** Unified Support is priced as a share of spend (practitioner
consensus), so Azure growth raises it; it does not count toward the MACC and is a
separate negotiation. Practitioner sources concur that field teams bundle Microsoft 365
and Copilot targets into MACC talks; keep the consumption commitment a separate,
separately timed negotiation.

---

## Google Cloud: Minimum Commitment under a Google Cloud Addendum

**The instrument.** Google publishes no product name. Its documents speak of a "Minimum
Commitment" under a "Google Cloud Addendum" (RaMP terms, modified 5 October 2026) and of
a "custom pricing contract" whose effect is the "Negotiated savings" credit (Cloud
Billing, updated 9 October 2026). Google told the UK CMA that "all Google Cloud
agreements are open to individual contract negotiation at the customer's request" and
that committed spend discounts are offered to customers "of all sizes" (Google response
to the CMA working paper, 14 June 2024). No current primary Google contract is public.

**Defaults to strike in the Terms.** The Google Cloud Platform Terms say "Google may
change the Fees at any time unless otherwise expressly agreed in an addendum or Order
Form", that Google may terminate an Order Form "for its convenience at any time with 30
days' prior written notice", and that Google "may revise or revoke any previously-extended
credit at any time". Price protection, credit protection and termination limits exist
only if written into the Order Form or Addendum.

**Credits.** Contracts can carry spend-based milestone credits, applied within about 45
days of the milestone and tracked on the Incentives page (see `finops-gcp.md`). They pay
eligible costs after the fact and leave the unit rate unchanged. RaMP credits do not
count toward the Minimum Commitment (below); confirm in the contract whether milestone
credits do.

**Premium Support is computed on list.** The fee is the greater of $15,000 a month or
10% of monthly charges up to $150,000, 7% to $500,000, 5% to $1M and 3% above, "based on
the list prices of all eligible services before the application of any discounts,
credits, or other adjustments"; for BigQuery reservations and resource-based CUDs it is
based on the list price of the commitment fee (Google Cloud support page, read 24
October 2026). A negotiated discount does not reduce the support fee unless the contract
says so.

**First contracts.** Flex Agreements (announced 16 February 2023) onboard workloads "with
no up-front commitments" while keeping monthly spend discounts, CUDs, credits and
services; the monthly spend discounts are not available through Partner Advantage
resellers. Google told the CMA in 2024 that Flex discounts "do not require customers to
agree to a certain level of committed spend".

**CUDs under a commitment.** Resource-based CUDs are tied to region and machine series
and cannot be cancelled; spend-based CUDs moved to direct discounted pricing for all
customers on 21 January 2026; Flexible Savings Plans (10% for 1 year, 20% for 3 years on
eligible generative AI SKUs) cannot be cancelled and usage beyond them "is billed at
on-demand or negotiated rates" (Google CUD documentation, updated 9 October 2026).
Google does not document the stacking order of negotiated pricing and CUDs; confirm it
in the contract. Spend-based CUDs cover Cloud SQL, AlloyDB, Spanner and Bigtable;
negotiated discounts on them are not public. No official document says whether Google
Workspace spend counts toward a Cloud commitment; do not assume either way. Google Ads
is "neither eligible to be discounted nor to be drawn down against" commitments (Google
to the CMA, 2024).

---

## Migration funding: MAP, Azure Accelerate, RaMP

The rule common to all three: migration credits never retire the commitment, which is
met by spend alone.

| | AWS Migration Acceleration Program | Azure Accelerate | Google RaMP |
|---|---|---|---|
| What is public | Mechanics: credits = credit percentage x spend growth; nothing paid until tagged MAP-workload spend reaches $50,000; disbursed within 30 days after each calendar quarter; tagging before migration required, no retroactive credits; applied "before the application of any other discounts"; data transfer excluded. Credit percentages are not published by AWS | Structure only: replaced Azure Migrate and Modernize and Azure Innovate on 7 July 2025; partner funding, Azure credits and Cloud Accelerate Factory deployment help; "no cap on investments"; no amounts or criteria published. Funding is nominated by a partner, not applied for by the customer (practitioner consensus) | Exact rates and caps (table below) |
| Counts toward the commitment | No: fees paid from credits are excluded on public AWS paper | No: Azure credits do not count | No: "Service Credits will not count towards Customer's Minimum Commitment obligation" |
| Expiry | 1 year from the first day of the month of disbursement | Not published | 12 months from issuance |

Sources: MAP Migration Tracking and Incentive Guide (changelog to 5 October 2026) and MAP
terms (19 November 2025); Azure blog, 7 July 2025; Google RaMP terms (modified 5 October
2026, read 24 October 2026).

**RaMP incentive rates (2026 terms).** Service credits are a share of trailing twelve
months (TTM) Google Cloud spend each calendar quarter, capped across the 3-year RaMP
Period; Projected Annual Run Rate (PARR) is the estimated annual run rate of the fully
ramped workload.

| Workload type | Service credits per quarter | Cumulative cap | Consulting or partner services funds |
|---|---|---|---|
| General | 25% of TTM | Lesser of 30% of PARR and $3M | Lesser of 20% of PARR and $2M |
| Oracle | 65% of TTM | Lesser of 70% of PARR and $3M | Lesser of 30% of PARR and $2M |
| Windows | 35% of TTM | Lesser of 40% of PARR and $3M | As General |
| Modern Infra (GKE, Cloud Run, Arm/Axion) | 30% of TTM | Lesser of 35% of PARR and $3M | Lesser of 30% of PARR and $2M |
| VMware | As General | As General | Lesser of 45% of PARR and $2M |
| Database, Data Analytics | As General | As General | Lesser of 30% of PARR and $2M |
| SAP | None | None | SAP partner services funds: lesser of 100% of PARR and $1M |

Credits are deposited within 45 days of each quarter-end from 30 June 2026; projects must
carry the workload ID tag; the customer must show overall account growth; pre-existing
spend is ineligible; consulting funds require "an active Minimum Commitment under a
Google Cloud Addendum". The RaMP user guide sets a PARR floor of $60,000 per workload.
The highest rates apply to Oracle and Windows estates, the workloads Google pays most to
displace.

---

## Marketplace private offers as a commitment lever

A private offer is a Marketplace transaction priced and negotiated with the seller (an
ISV or a channel partner) and billed on the cloud provider's invoice. One purchase can
retire part of the commitment and buy the software; the rules below decide how much.

| | AWS | Azure | Google Cloud |
|---|---|---|---|
| Counting rule | 100% of eligible spend up to the cap; since 1 May 2025 only SaaS "Deployed on AWS" | "100% of the pretax purchase amount" for "Azure benefit eligible" offers bought through the Azure portal during the term | "100% of spend on Google Cloud Marketplace Services", minus exclusions (Maps, Ads, services not running on Google Cloud, resold services whose vendor has not opted in, the purchaser's own services, professional services) |
| Cap | 25% of the annual commitment (practitioner consensus); older paper may carry a 50% formula | None stated by Microsoft | 25% of the Minimum Commitment, cumulative; any excess neither counts nor rolls over |
| Instalments | Not stated publicly | Future instalments not eligible; refunds replenish | Instalments over 12 months count pro rata per year |
| Channel offers | Channel partner private offers (CPPO) | Multiparty private offers count the same way; professional services excluded | Channel private offers draw down "100%" of the final offer price from 9 June 2025 if associated with the customer and not inside a reseller-held commitment |
| Seller fee (not visible to the buyer) | Private offers 3% under $1M contract value, 2% from $1M to under $10M, 1.5% at $10M and above and on renewals; CPPO adds 0.5 point | 3% store service fee; 1.5% on qualifying private offer renewals | 3% under $1M, 2% from $1M to under $10M, 1.5% at $10M and above and for channel shifts, migrations and native renewals |

Google's Marketplace Customer Credit Program adds up to 3% of annualised value in credits
on a first-time ISV purchase by private offer (from $100,000, capped at $250,000;
programme brief and partner blog, 15 May 2025).

**Rules that follow.**
- Confirm eligibility in writing, offer by offer, before the purchase is planned, not
  after it is invoiced. On AWS the commitment link is not stated publicly; the badge is
  the proxy.
- Put planned software renewals on the same calendar as the commitment, and pace them
  against the cap.
- Buy-to-burn is an anti-pattern: a purchase made because it counts creates a vendor,
  licence and integration cost no business case asked for. The FinOps Foundation notes
  that Marketplace purchases "can consume cloud commitments while Procurement pushes EA
  minimums with the same vendor" (FinOps and ITAM working group paper, updated 7 April
  2026). Channel governance is in `finops-itam.md` ("Marketplace channel governance");
  the AWS detection pattern is "Double Counting On Edp Commitments" in
  `finops-aws-patterns-other.md`.

---

## Reseller channel: a qualitative checklist

No reseller publishes its discount on list, credits or exit terms, so the decision rests
on the checklist below and on a rate card obtained under NDA.

- [ ] **Billing ownership.** On Google Cloud the customer's subaccount sits under the
      reseller's billing account, which the reseller can suspend or cancel ("Billing
      subaccounts can't be restored or reopened"). Under Azure CSP the partner sets the
      price, bills and is the first support line; reservations need a partner-granted
      permission.
- [ ] **Commitment visibility.** The Azure portal tracks a MACC only on direct
      agreements. Ask how burn-down is reported to you.
- [ ] **Marketplace drawdown.** On Google Cloud a reseller Marketplace purchase counts
      only when associated in Google's systems, not inside a reseller-held commitment,
      and from a vendor that opted in.
- [ ] **Fee basis and pass-through.** Partner incentives such as Partner Earned Credit
      exclude reservations and savings plans by construction. AWS opened a Private
      Pricing Resell path for resellers and their end customers on 1 January 2026 (APN
      blog, 11 November 2025).
- [ ] **Exit and transfer.** A written right for the remaining commitment and its
      discounts to move to the provider direct, or to another partner, without
      repricing.
- [ ] **Existing commitments.** Whether CUDs and reservations transfer into the
      reseller's billing account or must be bought again.

---

## Situations and what changes

Advisory estimates with undisclosed methodology, from a sample of 2025 to 2026
publications, supply the thresholds in this section; they are envelopes, not quotes.

**First contract.** Expect a flat or front-loaded proposal, a growth assumption above
your trailing trend, and, on AWS, mandatory Enterprise Support. Below about $1M a year
of Azure spend Microsoft steers customers to CSP or a commitment-free MCA. Google told
the CMA that commitments help attract first-time and secondary-provider customers, and
Flex Agreements onboard without one. Negotiate exit terms before signing, when the next dollar of spend
is still the customer's to place.

**Renewal with growing spend.** Treat the renewal as a new negotiation. When consumption
runs ahead of the commitment, signed renewals show the early-renewal
pattern: the remaining term is replaced by a larger, longer commitment at a higher
rate, before the old one ends, sometimes with two providers renegotiated in the same
procurement window. On Azure the renewal is when EA customers are re-papered onto
MCA-E; restate every discount and protection. Practitioner sources concur that Microsoft
offers a lower discount for the same commitment at renewal.

**Vehicle change (EA to MCA-E).** Add 3 months to the timeline (see "Timing"),
inventory every protection the EA carried, and write each one back in.

**Competitive migration.** An alternative counts only when it is documented: scoped
workloads, costed, with a timeline. A named rival without that work is a claim the
account team will test. Migration programmes pay most where the source estate is
elsewhere (RaMP Oracle and Windows tiers above); negotiate credits as one-time funding,
separately from the commitment size.

**Customer considering leaving.** Know the exit price before you signal it: on AWS paper
there is no termination for convenience during the term; on Azure an unrenewed shortfall
is paid in cash; Google's default terms let Google terminate an Order Form on 30 days'
notice while the customer's own right is "subject to any financial commitments", and
RaMP incentives are cancelled if the Addendum ends. For data platforms, see
the rollover and true-up clauses in `finops-snowflake.md` and `finops-databricks.md`.

---

## Intake protocol: 9 questions before advising

Ask these in order before giving any advice on a contract. The protocol assumes a
Walk-stage practice, with billing data at effective rates and a commitment portfolio in
place; at Crawl, the metered instruments come first (see the provider commitment files).
Each answer changes the advice; when one is missing, say which output it blocks rather
than filling it with an assumption. Do not quote a discount target: say what the public record allows (see
"Where benchmarks come from").

| # | Question | What the answer changes |
|---|---|---|
| 1 | Which provider, and which situation: first contract, renewal on the same vehicle, vehicle change, competitive migration, considering leaving? | The provider section and situation that apply, the timeline (plus 3 months for a vehicle change or a documented migration), the levers available |
| 2 | Trailing 12 to 24 months of spend at effective rates, by service, and its trend? | The baseline. A list-price or gross baseline overstates what the commitment can absorb; on AWS the commitment is measured net by default |
| 3 | Optimisation status: is waste removed, what is the commitment coverage today? | Whether to size on today's spend or on the post-optimisation floor, and whether optimisation must land before signature |
| 4 | Forecast and confidence in growth, with its source? | The ramp shape and how much of the growth to commit. A forecast built by the account team carries the provider's growth targets; treat it as one input among several |
| 5 | Term appetite and step-down needs (divestiture, acquisition, exit of a business line)? | Term length, step-down and M&A clauses, the share of the estate to leave uncommitted |
| 6 | Marketplace share of spend and planned software renewals? | The Marketplace cap to ask for, the eligibility checks, the pacing of purchases |
| 7 | Support plan and its fee basis? | The total cost model; whether to negotiate support as its own line |
| 8 | Credible alternatives: documented, not named? | Whether a competitive case exists, which migration programme applies, 3 more months |
| 9 | Your decision calendar against the provider's fiscal calendar? | Sequencing: when approvals must be ready, which quarter-end the signature can meet |

**Outputs, five of them.**
1. **Negotiation brief**: situation, baseline, forecast, the commitment you can defend,
   and what you will not sign.
2. **Lever list**: the clauses from the 12-clause anatomy you will negotiate, in
   priority order, with the evidence for each.
3. **Offer review grid**: the 15 checks below, filled in for the offer on the table.
4. **Scenario table**: commitment, growth, discount, shortfall exposure, for at least a
   low, expected and high case.
5. **Red flags**: the checks that failed and the clauses that are missing.

**The shortfall arithmetic for the scenario table.** With commitment `C`, discount `d`
and eligible net spend `S` over a measurement period, the shortfall is `max(0, C - S)`,
the list value of the usage is `S / (1 - d)`, and the effective discount against list
is `1 - max(C, S) x (1 - d) / S`. The commitment beats pay-as-you-go only while net
spend stays above `(1 - d) x C`. An illustrative case at `d = 10%`: a commitment of 10
with net spend of 8 pays 10 for usage listed at 8.89, an effective discount of minus
12.5%. Where the shortfall becomes a balance or prepayment usable later (AWS during the
term, Azure on renewal), the same money is spent later rather than saved.

---

## Offer review grid: 15 checks on a term sheet

Apply each check to the agreement text rather than to the sales summary; a check passes
only when the answer is written there.

- [ ] **Measurement basis.** Gross or net of the negotiated discount, and which charge
      types count.
- [ ] **Ramp shape.** Year one at or below your sized baseline; annual or cumulative
      measurement; no year forced above the forecast you own.
- [ ] **Exclusions.** The full list, and whether the provider can add services to it
      during the term.
- [ ] **Marketplace cap.** The percentage, the eligibility test, and the treatment of
      older contracts and instalments.
- [ ] **Support.** Plan, fee basis (gross or net), discount on the support line, and
      whether the fee counts toward the commitment.
- [ ] **Shortfall timing and rate.** When measured (milestone, annual, end of term),
      billed in cash or as prepayment, at face value or discounted.
- [ ] **Cure period.** Time to close a gap before the shortfall is billed, and whether
      a shortfall can convert into future credit.
- [ ] **Credits expiry.** Each credit with its amount, condition, attestation window and
      expiry date, on the same calendar as the milestones.
- [ ] **Price protection.** Which prices are fixed for the term, including service-specific
      and new services, and how a list price rise is treated.
- [ ] **Reversion clause.** The price that applies the day after the term ends, and for
      how long.
- [ ] **Termination.** Either side's right to terminate for convenience, and what
      termination for cause costs you (repayment of discounts received, remaining
      commitment).
- [ ] **M&A.** Step-down or transfer on divestiture, acquisition of an estate with its
      own contract, assignment to a successor entity.
- [ ] **Reporting.** Burn-down statements, Marketplace drawdown reporting, a FOCUS export,
      and who provides them.
- [ ] **Renewal mechanics.** Notice dates, auto-renewal, what happens to unconsumed
      commitment or rollover, the renewal price basis.
- [ ] **What is missing.** Any of the 12 clauses the paper does not address; silence
      defaults to the provider's standard terms.

---

## Pitfalls

- **Committing on unoptimised spend.** Optimisation after signature lowers the bill but
  not the commitment. Size on the post-optimisation floor (see
  `finops-aws-commitments.md`, "Commitment portfolio liquidity").
- **The growth tax.** First proposals assume growth above the trailing trend (practitioner
  consensus). Bring your own forecast and its source.
- **Tier chasing.** Stretching the commitment to reach the next discount band trades a
  few points of rate for exposure on the whole gap; run the shortfall arithmetic above
  at the low case before accepting.
- **Marketplace forecast omission.** Software renewals planned by other teams count
  toward the commitment and are left out of its sizing.
- **Support erosion.** On AWS and Google Cloud the support fee is computed on gross or
  list charges, so it does not fall with the discount; at small commitments it can
  absorb a large share of the saving.
- **Amortised versus actual burn-down.** Azure decrements the MACC on invoiced charges,
  so an upfront reservation counts in full in the invoice month while amortised views
  spread it. Fix one view for the burn-down and use it with the provider.
- **Capacity risk, 2026.** The commitment is owed whether or not the capacity is
  available in your regions; advisory publications in 2026 report providers asking for
  larger, earlier commitments in exchange for supply. Ask what the contract says when
  quota is unavailable.
- **The optimisation paradox.** Every dollar saved is a dollar that does not burn the
  commitment; track burn rate beside savings (see `finops-azure-commitments.md`, "MACC -
  commercial commitment alignment").
- **Credits expiring.** MAP and RaMP credits expire after 12 months, the Azure Credit
  Offer at the first anniversary, and milestone credits land weeks after the milestone.

---

## Timing

Start 6 to 9 months before the end date for a renewal on the same vehicle. Add 3 months
when the vehicle changes (EA to MCA-E) or when a competitive migration has to be
documented, because documenting the alternative is what takes time. Advisory
publications of 2025 to 2026, with undisclosed methodology, converge on 3 months as the
floor from first proposal to signature.

Fiscal calendars decide sequencing; nothing in the public record ties them to discount
depth. Have approvals ready so the signature can meet the provider's quarter or year end
if the deal is ready.
Amazon and Alphabet close their fiscal years on 31 December (10-K filings), Microsoft on
30 June (investor relations FAQ), Snowflake and Databricks on 31 January (see their
files). Paperwork deadlines sit days before the quarter end: Microsoft's Volume
Licensing calendar set the guaranteed cut-off for the quarter ending 30 September 2026
at 25 September (VL Central, updated 28 August 2026).

---

## Where benchmarks come from

No provider publishes negotiated discount levels, and only regulated disclosures
(prospectuses, public procurement notices) reveal contract sizes, never rates. The
envelopes below are advisory estimates with undisclosed methodology, from a sample of
2025 to 2026 publications; a single cell in any published table is weaker than the
envelope.

| Provider | Convergent envelope (annual commitment) |
|---|---|
| AWS | About 5% at $1M a year, rising to 25 to 30% at $50M a year and above |
| Azure (ACD) | Single digits to about 10% at $1M to $5M a year; 10 to 20% at tens of millions; above 20% only for very large deals; lower at renewal for the same commitment |
| Google Cloud | No credible public figure. The closest concrete proxy is channel-specific: two UK G-Cloud 15 reseller pricing documents (January 2026) publish identical indicative tiers for buyers committing to annual spend targets, 7% up to $500,000, 10% to $1M, 13% to $3M, 16% to $5M, 19% above |

Ranges depend on tier, term, growth and competitive context, and the publishers disagree
with each other and, on some pages, with themselves. Contract structure ages more slowly
than figures; check the date on any source before using a number.

Negotiated outcomes are confidential. The envelopes above come from advisory publications with undisclosed methodology; the public record does not allow a tighter figure. A practitioner who has reviewed signed agreements can calibrate them; this file cannot.

---

## Data platform contracts inside cloud contracts

Data platform contracts interlock with the cloud commitment; their own levers (credit
price, rollover, true-up, support) are in the vendor files.

- **Snowflake through a Marketplace.** Snowflake states that purchases through the AWS,
  Azure and Google Cloud Marketplaces are eligible for commitment drawdown (Snowflake
  cloud partners page). The caps in the Marketplace table apply. A contract signed
  through a Snowflake reseller loses the `ORGANIZATION_USAGE` billing views, and
  Snowflake's own Marketplace Capacity Drawdown is unavailable to reseller customers and
  to contracts made through Google Cloud Marketplace (Snowflake documentation, read 24
  October 2026). See `finops-snowflake.md`, "Commitment model vs. IaaS reserved
  capacity".
- **Databricks.** On AWS the Databricks listing carries the "Deployed on AWS" badge, so
  its private offers fall under the Marketplace rules above; on Google Cloud a
  Marketplace private offer counts toward the Minimum Commitment. Azure Databricks is
  Microsoft first-party consumption and decrements the MACC as Azure usage; Microsoft
  does not state how a DBCU pre-purchase is treated. A direct Databricks commitment does
  not cover Azure Databricks by default (Databricks Cloud Provider Directory). See
  `finops-databricks.md`, "Databricks commitment instruments".
- **Serverless moves spend between the two commitments.** A move to serverless shifts
  infrastructure spend out of the cloud commitment and into the data platform
  commitment. Size the two together, in the same model and the same negotiation window.

---

> Sources (official documents only; advisory and procurement publications, 2025 to 2026,
> informed the envelopes and practitioner-consensus statements and are not listed):
> AWS: <https://aws.amazon.com/pricing/>; <https://aws.amazon.com/agreement/>;
> <https://www.sec.gov/Archives/edgar/data/1793663/000095017025026601/ck0001793663-ex4_03.htm>;
> <https://aws.amazon.com/premiumsupport/pricing/>;
> <https://docs.aws.amazon.com/awssupport/latest/user/support-plans-eos.html>;
> <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ri-market-general.html>;
> <https://docs.aws.amazon.com/cur/latest/userguide/table-dictionary-cur2-line-item.html>;
> <https://aws.amazon.com/blogs/awsmarketplace/aws-marketplace-announces-upcoming-expansion-to-saas-product-catalog/>;
> <https://docs.aws.amazon.com/marketplace/latest/userguide/listing-fees.html>;
> <https://s3.us-west-2.amazonaws.com/map-2.0-customer-documentation/forms/MAP-Guide-CCS.pdf>;
> <https://aws.amazon.com/migration-acceleration-program/terms/>;
> <https://aws.amazon.com/blogs/apn/updates-to-aws-channel-programs-to-drive-growth-in-2026/>.
> Microsoft: <https://learn.microsoft.com/en-us/marketplace/azure-consumption-commitment-benefit>;
> <https://learn.microsoft.com/en-us/marketplace/macc-frequently-asked-questions>;
> <https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/track-consumption-commitment>;
> <https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/mca-understand-pricesheet>;
> <https://learn.microsoft.com/en-gb/azure/cost-management-billing/manage/ea-pricing-overview>;
> <https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/mca-setup-account>;
> <https://learn.microsoft.com/marketplace/private-offers-overview>;
> <https://learn.microsoft.com/partner-center/marketplace/multiparty-private-offers-for-selling-partners>;
> <https://learn.microsoft.com/en-us/partner-center/marketplace-offers/marketplace-commercial-transaction-capabilities-and-considerations>;
> <https://learn.microsoft.com/en-us/partner-center/billing/partner-earned-credit-explanation>;
> <https://azure.microsoft.com/en-us/blog/introducing-azure-accelerate-fueling-transformation-with-experts-and-investments-across-your-cloud-and-ai-journey/>;
> <https://learn.microsoft.com/en-us/volume-licensing-central/latest-news>;
> <https://www.microsoft.com/en-us/investor/faq>.
> Google: <https://docs.cloud.google.com/billing/docs/how-to/reports/savings-and-credits>;
> <https://docs.cloud.google.com/billing/docs/how-to/spend-milestone-credits>;
> <https://cloud.google.com/terms>; <https://cloud.google.com/support>;
> <https://cloud.google.com/terms/ramp>;
> <https://services.google.com/fh/files/misc/ramp_user_guide.pdf>;
> <https://docs.cloud.google.com/marketplace/docs/commit-drawdown>;
> <https://cloud.google.com/terms/marketplace/commit-policy>;
> <https://cloud.google.com/terms/marketplace-revenue-share-schedule>;
> <https://cloud.google.com/blog/topics/partners/upgrades-to-google-cloud-marketplace-for-partners>;
> <https://services.google.com/fh/files/misc/google_cloud_marketplace_customer_credit_program_brief.pdf>;
> <https://cloud.google.com/blog/topics/cost-management/introducing-flexible-new-cloud-services-and-pricing/>;
> <https://docs.cloud.google.com/docs/cuds>;
> <https://knowledge.workspace.google.com/reseller/cloud/console/cancel-or-suspend-a-google-cloud-billing-subaccount-for-resellers>;
> <https://assets.publishing.service.gov.uk/media/6682719faec8650b100901a8/Non-confidential_-_Google_Cloud_s_response_to_the_CMA_s_committed_spend_agreements_working_paper_dated_23_May_2024.pdf>;
> UK G-Cloud 15 reseller pricing documents
> <https://assets.applytosupply.digitalmarketplace.service.gov.uk/g-cloud-15/documents/92726/929719456568962-pricing-document-2026-01-23-1509.pdf>
> and <https://assets.applytosupply.digitalmarketplace.service.gov.uk/g-cloud-15/documents/92315/568291536123933-pricing-document-2026-01-27-1952.pdf>.
> Filings: Amazon 10-K FY2025 <https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm>;
> Alphabet 10-K <https://www.sec.gov/Archives/edgar/data/1652044/000165204424000022/goog-20231231.htm>.
> FinOps Foundation: <https://www.finops.org/wg/commitment-based-discounts-overview/>;
> <https://www.finops.org/framework/capabilities/rate-optimization/>;
> <https://www.finops.org/wg/finops-itam-practical-scenarios-planning-procurement/>.
> Data platforms: <https://www.snowflake.com/en/why-snowflake/partners/cloud-partners/>;
> <https://docs.snowflake.com/en/collaboration/marketplace-capacity-drawdown>;
> <https://databricks.com/legal/cloud-provider-directory>;
> <https://aws.amazon.com/marketplace/pp/prodview-wtyi5lgtce6n6>.

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
