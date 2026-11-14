---
name: azure-database-extended-support
scope: azure
service: Azure Database for PostgreSQL / MySQL flexible server
waste_category: modernization
confidence: obvious
questions:
  - q: "Which of our Azure PostgreSQL and MySQL servers are being charged for extended support?"
    persona: "Engineering and platform"
    also: ["finops-azure-data"]
  - "Our Azure database bill went up in September with no change on our side. What happened?"
  - "When does Azure start charging extended support for PostgreSQL 14 and MySQL 8.0?"
  - "How do we stop paying extended support on an Azure Database for PostgreSQL or MySQL server?"
  - "Quels serveurs PostgreSQL et MySQL paient un support étendu sur Azure, et comment en sortir ?"
---

# Azure Database Extended Support Surcharge

## Problem

An Azure Database for PostgreSQL or MySQL flexible server left on a major
version past its end of standard support is enrolled automatically in paid
extended support. Nobody chose the surcharge, it appears with no deployment
change, and it runs until the server is upgraded. PostgreSQL 11, 12 and 13
have been billed since 1 September 2026 and MySQL 5.7 since 1 October 2026.
PostgreSQL 14 and MySQL 8.0 follow on 1 February 2027. On MySQL the charge is
per vCore-hour, so read replicas and high-availability standbys add to it.

## Symptoms

- PostgreSQL or MySQL flexible server cost steps up in September or October
  2026 while usage is flat
- Servers created years ago for an application nobody upgrades
- Infrastructure-as-code modules that pin `version` to "12", "13" or "5.7"
- A MySQL 5.7 primary with read replicas: each replica pays the surcharge
  on its own vCores
- A PostgreSQL 14 or MySQL 8.0 fleet with no upgrade planned before
  1 February 2027

## Detection

Two read-only Azure Resource Graph queries. The version is a property of the
server, so one signal is enough. Property names come from Microsoft's
resource reference and the queries were not run against a live estate: check
one server whose version you know.

```kusto
// PostgreSQL flexible servers on a version in, or about to enter, extended support
resources
| where type =~ "microsoft.dbforpostgresql/flexibleservers"
| extend version = tostring(properties.version),
         state = tostring(properties.state),
         skuName = tostring(sku.name),
         ha = tostring(properties.highAvailability.mode),
         role = tostring(properties.replicationRole)
| where version in ("11", "12", "13", "14")
| project subscriptionId, resourceGroup, name, location, version, state, skuName, ha, role
| order by version asc
```

```kusto
// MySQL flexible servers on a version in, or about to enter, extended support
resources
| where type =~ "microsoft.dbformysql/flexibleservers"
| extend version = tostring(properties.version),
         state = tostring(properties.state),
         skuName = tostring(sku.name),
         role = tostring(properties.replicationRole)
| where version startswith "5.7" or version startswith "8.0"
| project subscriptionId, resourceGroup, name, location, version, state, skuName, role
| order by version asc
```

PostgreSQL 11 to 13 and MySQL 5.7 are billed today; PostgreSQL 14 and MySQL
8.0 are the backlog for the next date. To size the charge, compare each
server's daily cost before and after its billing start date in Cost
Management, or read the surcharge on the pricing page for its compute tier.

## Fix

Ordered safest-first.

1. **Retire what nobody claims.** A server with no owner and no connections
   is cheaper to export and delete than to upgrade. A stopped PostgreSQL
   server is not charged the surcharge, but it restarts by itself after seven
   days, so a stop is a pause, not an exit.
2. **Trim what multiplies the charge.** On MySQL, drop the read replicas and
   high-availability standbys that non-production servers do not need: the
   surcharge is per vCore-hour.
3. **Upgrade in place.** Both engines offer an in-place major version upgrade
   that keeps the data and the connection string. PostgreSQL only upgrades to
   a version still in standard support and has pre-upgrade validation checks.
   MySQL goes from 5.7 to 8.0 and from 8.0 to 8.4, with a downtime that grows
   with the size of the instance and its number of tables. Rehearse on a
   restored copy and keep a tested restore point.
4. **Pick a target with runway.** PostgreSQL 14 enters extended support on
   1 February 2027 and MySQL 8.0 on the same day: an upgrade that lands on
   either buys weeks. Go to the newest version the application accepts.
5. **Stop it coming back.** Remove the pinned version from the modules, and
   put each version's end of standard support in the review calendar.

Sources: [PostgreSQL extended support](https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/extended-support),
[MySQL version policy](https://learn.microsoft.com/en-us/azure/mysql/concepts-version-policy),
[PostgreSQL major version upgrade](https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/concepts-major-version-upgrade)
and [MySQL major version upgrade](https://learn.microsoft.com/en-us/azure/mysql/flexible-server/how-to-upgrade),
read 14 November 2026.

## Anti-pattern

- Filing the increase as an anomaly to dismiss. It is a permanent rate change
  that ends only with an upgrade.
- Waiting for the application team's roadmap without pricing the wait: the
  surcharge runs every hour the server does.
- Upgrading one version up, onto a version that enters extended support a few
  weeks later.
- Upgrading production in place with no rehearsal and no restore point.

## See also

- `references/finops-azure-data.md`, "Paid extended support on Flexible
  Server versions" - the dates per version, and the stop and start rules of
  Flexible Server
- `references/finops-whats-new.md` - the dated list of scheduled provider
  changes, where the 1 February 2027 date sits
- `references/finops-aws-billing.md` - RDS Extended Support, the same
  mechanism on AWS
- `references/finops-waste-detection-playbooks.md` - the taxonomy this
  pattern fits ("modernization")

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
