# FinOps Tagging and Naming Governance

> Tagging is the foundation of cost allocation, accountability, and automation.
> Without it, FinOps visibility is incomplete and optimization savings are unattributable.
> This file covers tagging strategy design, naming conventions, enforcement, remediation,
> and MCP-based automation.

---

## Why tagging is a prerequisite, not a project

Tagging is often treated as a one-time cleanup project. It is not. It is an ongoing
operational discipline that requires design, enforcement, and continuous monitoring.

**Tagging enables:**
- Cost allocation to teams, products, cost centers, and environments
- Accountability - teams cannot own what they cannot see
- Optimization attribution - savings must be linked to a resource owner
- Governance automation - policies act on tag values, not resource IDs
- Chargeback - financial accountability requires accurate attribution
- Security and compliance - resource classification drives access and audit controls

**The cost of poor tagging:**
- Untagged spend cannot be allocated - it falls into shared cost pools or "unknown"
- Optimization savings cannot be credited to teams - removing the incentive to act
- Anomaly detection produces false positives - spikes in untagged spend are uninvestigable
- Commitment discounts applied to untagged resources create stranded capacity

**OptimNow principle:** Physical tagging must precede virtual tagging. Virtual tagging
(applying metadata in the billing layer without changing actual resource tags) is a
powerful complement but a fragile substitute. Fix the source before adding abstraction.

---

## Tag taxonomy design

### Mandatory tags (minimum viable set)

Every organization needs a minimum set of tags that apply to all resources, without
exception. Start small - enforcement of 5 tags is more valuable than partial compliance
on 20.

| Tag key | Purpose | Example values |
|---|---|---|
| `Environment` | Separate cost by lifecycle stage | `prod`, `staging`, `dev`, `sandbox` |
| `Owner` | Identify the team or individual responsible | `team-platform`, `jean.latiere` |
| `CostCenter` | Map to finance's budget structure | `CC-1042`, `engineering` |
| `Project` | Group resources by initiative or product | `agent-smith`, `customer-portal` |
| `Application` | Identify the workload or service | `api-gateway`, `ml-training` |

### Extended tags (Walk/Run maturity)

| Tag key | Purpose | Example values |
|---|---|---|
| `ManagedBy` | Identify provisioning method | `terraform`, `cloudformation`, `manual` |
| `DataClassification` | Support security and compliance | `public`, `internal`, `confidential` |
| `Schedule` | Enable automated start/stop | `business-hours`, `always-on`, `weekdays` |
| `BackupPolicy` | Drive automated backup configuration | `daily-30d`, `weekly-1y`, `none` |
| `EndDate` | Flag temporary resources for cleanup | `2026-03-31` |

### Naming convention design

Naming conventions complement tags. They encode metadata into resource names for contexts
where tags are not surfaced (logs, alerts, CLI output).

**Recommended pattern:**
```
{environment}-{application}-{resource-type}-{region}-{index}
```

**Examples:**
```
prod-api-gateway-ec2-euw1-01
dev-ml-training-s3-use1-01
staging-agent-smith-rds-euw3-01
```

**Rules:**
- Use lowercase and hyphens only (avoid underscores - incompatible with some services)
- Keep names under 63 characters (DNS compatibility for some resource types)
- Never encode dynamic values (costs, dates) in names - they cannot be updated
- Align naming conventions with your tag taxonomy - the same dimensions, consistently

---

## Tag enforcement strategy

### The three enforcement layers

**Layer 1: Prevention (IaC - highest value)**
Enforce tags at resource creation through infrastructure-as-code validation. Tags defined
in Terraform modules, CloudFormation templates, or Bicep files propagate automatically.
Violations are caught before deployment.

Tools:
- Terraform: `required_tags` variable pattern, `terraform-aws-tag-compliance` modules
- AWS: Service Control Policies (SCPs) that deny resource creation without required tags
- Azure: Azure Policy `deny` effect for missing required tags
- GCP: Organization policies for label requirements

**Layer 2: Detection (continuous compliance monitoring)**
Scan deployed resources for missing or non-compliant tags on a scheduled basis.
Flag violations and route to owners for remediation.

Tools:
- AWS Config rules (`required-tags` managed rule)
- AWS Resource Explorer for cross-account tag inventory
- Azure Policy compliance dashboard
- OptimNow's MCP for Tagging (cross-account, agent-accessible)
- Cloud Custodian policies for custom compliance rules

**Layer 3: Remediation (automated or human-driven)**
Apply missing tags automatically where safe to do so (e.g., resources with identifiable
owners from account or naming convention context). Flag resources that require human
decision for missing mandatory tags.

Remediation approaches:
- **Automated remediation:** Lambda or Azure Functions triggered by Config rules apply
  tags based on account context, resource name parsing, or IaC state files
- **Human-driven remediation:** Compliance reports routed to team leads with deadlines
- **Guardrail-based:** Resources without required tags are quarantined (stopped, flagged,
  or denied network access) until compliant

---

## Virtual tagging

Virtual tagging applies cost allocation metadata in the billing layer without modifying
actual resource tags. It is useful when:
- Resources cannot be tagged (shared infrastructure, third-party services)
- Tags need to be applied retroactively to historical data
- Business dimensions don't map cleanly to resource-level tags

**How it works:**
Cost management platforms (AWS Cost Categories, Azure Cost Management views, Apptio,
CloudHealth, Anodot) allow you to define rules that apply labels to spending based on
account, service, region, resource ID, or existing tag values.

**When to use virtual tagging:**
- Shared services (NAT gateways, Transit Gateway, shared load balancers) that serve
  multiple teams but cannot be tagged to a single owner
- Marketplace costs and support charges that have no taggable resource
- Retroactive allocation for historical analysis

**When not to rely on virtual tagging:**
- As a substitute for physical tagging on resources you control
- When governance automation requires reading actual resource tags (MCP tools, Config rules,
  and security tools read physical tags, not billing-layer virtual tags)

---

## MCP-based tagging automation

OptimNow's `finops-tagging` MCP server enables AI agents to interact with AWS tagging
infrastructure through natural language. This changes the operational model from
periodic audits to continuous, conversational governance.

**What the MCP server enables:**

```
Practitioner: "Which resources in production lack a CostCenter tag?"
Agent: [calls finops-tagging MCP] Returns list of non-compliant resources with account,
region, resource type, and current tags.

Practitioner: "Apply CostCenter=CC-1042 to the EC2 instances in that list."
Agent: [calls finops-tagging MCP] Applies tags, confirms changes, logs to audit trail.

Practitioner: "Generate a compliance report for the platform team."
Agent: [calls finops-tagging MCP + generates report] Delivers structured compliance
summary with violation count, resource list, and recommended remediation steps.
```

**Architecture:**
The MCP server connects to AWS via read/write IAM roles with least-privilege permissions.
Tag read operations are always permitted. Tag write operations require explicit user
confirmation in the conversation before execution. All changes are logged.

**Integration with Agent Smith:**
The finops-tagging MCP is a core tool in Agent Smith's toolkit, enabling conversational
tag governance alongside cost analysis. The agent can detect untagged resources driving
cost anomalies and immediately propose and apply remediation - closing the loop between
cost visibility and corrective action.

**Current capability status:**
Tag compliance auditing (read, validate, report) is production-ready. Tag write automation
with human-in-the-loop confirmation is in active testing. Fully autonomous tag remediation
(without per-operation confirmation) is intentionally not implemented - governance requires
human approval for write operations.

---

## Tagging maturity progression

### Crawl
- Mandatory tags defined (5 or fewer)
- Tags applied manually at resource creation
- Compliance checked manually on a monthly basis
- No enforcement - violations are flagged but not blocked

**Quick win:** Run a one-time tag audit, identify the top 10 untagged resources by spend,
tag them manually. This typically achieves 15–20% allocation improvement in one session.

### Walk
- Tags enforced at IaC layer for new resources
- AWS Config / Azure Policy scans for violations continuously
- Compliance reports delivered to team leads weekly
- Remediation SLA defined (e.g., 5 business days to resolve violations)
- Virtual tagging applied for shared services and untaggable resources

### Run
- Tags required before deployment (CI/CD gate)
- Automated remediation for safe cases (account-context tagging)
- Human review required only for ambiguous resources
- Compliance >90% sustained with automated monitoring
- Tagging policy version-controlled and reviewed quarterly
- MCP-based governance enabling conversational compliance workflows

---

## Common tagging mistakes

**Too many tags at launch**
Organizations that define 25 mandatory tags at launch achieve lower compliance than those
that enforce 5. Start with the minimum viable set. Add tags only when there is a clear use
case for them.

**Inconsistent tag values**
`prod`, `Prod`, `PROD`, `production` all mean the same thing but break automation, reporting,
and filtering. Enforce lowercase and an approved value list from day one.

**Tags without owners**
Every tag key should have an owner responsible for its definition, value list, and
compliance. Ownerless tags drift and become inconsistent.

**Manual-only enforcement**
Compliance achieved through manual audits degrades immediately when team attention moves
elsewhere. Automated enforcement (Config rules, SCPs, Azure Policy) maintains compliance
without ongoing human effort.

**Skipping IaC alignment**
Tagging new resources manually while existing IaC modules don't include tags means every
new deployment starts non-compliant. Tag requirements belong in the IaC templates, not
in a post-deployment process.
