# Privacy policy - Cloud FinOps Skill & MCP

Last updated: 13 October 2026. Publisher: OptimNow (<https://optimnow.io>).

This policy covers the three ways the Cloud FinOps library reaches you:

1. **The skill files** - this repository, the Claude plugin built from it, the release
   zip, and the copies `install.sh` writes for other tools.
2. **The hosted MCP connector** at `https://mcp.optimnow.io/mcp` (served by the
   Fly.io app `cloud-finops-mcp`; its former `cloud-finops-mcp.fly.dev` address still
   answers and is covered by the same terms).
3. **The `cloud-finops-mcp` package** from PyPI, which runs the same server on your
   own machine.

## What is collected

**Skill files: nothing.** They are static markdown. They run no code, make no network
request, set no cookie and carry no credential. The playbooks contain detection queries
you run yourself in your own cloud account; nothing in the library reads a cloud
account.

**Local package: nothing.** The server runs on your machine with the library bundled
inside the package. It makes no outbound request and reports nothing back to OptimNow.

**Hosted connector: the tool calls your AI client sends.** Each call carries the tool
name and its arguments: a reference or playbook name, an optional section phrase, and
facet filters such as FinOps domain, phase, persona, maturity, cloud scope, service or
waste category. The server answers from the bundled library and keeps no copy of the
request. Specifically, the hosted connector has:

- no user accounts and no authentication;
- no cookies and no per-user identifier;
- no database and no per-user state;
- no conversation text by design: the tools take names, filter values and short
  phrases the model writes, such as a section heading or a service name. A model can
  copy a word from your question into one of those phrases, so keep confidential
  names out of questions you route through the connector if that matters to you.

Two logs exist:

- **Application log.** The server writes one line per request: method, the `/mcp`
  path, status code and request type, never the arguments. When a lookup matches
  nothing, it also writes the tool name and the arguments that missed: the facet
  filters, or the reference name and section phrase. OptimNow reads these lines to
  find coverage gaps in the library.
- **Web server access log.** The hosting platform keeps the standard HTTP access log
  (client IP address, timestamp, method, path, status code). The path is always
  `/mcp`, so the access log records that a call happened, not what it asked.

OptimNow does not export, archive, sell or share these logs, does not use them for
advertising or profiling, and does not combine them with any other data.

## Where it runs

The hosted connector runs on Fly.io (<https://fly.io>), primary region Paris (`cdg`),
which processes the traffic on OptimNow's behalf. Log retention follows the platform's
default; OptimNow keeps no separate copy.

On AI hosts that render MCP Apps, the interactive widgets are served from the same
origin as the connector, and their content security policy allows no third-party
domain.

## Other sites the library points to

The skill instructs the model to look up current prices on the OptimNow AI Pricing
Hub (<https://optimtoken.optimnow.io>) rather than quote a stale figure. That is a
separate site; whether the model opens it is decided in your conversation, and any
visit is governed by that site's own notice. The hosted server names no site: it
tells the model to use a live pricing tool if one is connected in the session.

## Your rights

Because the hosted connector stores no personal data and identifies no user, there is
nothing to access, correct or delete on request. For any question about this policy,
contact OptimNow at <jean@optimnow.io>.

## Changes

Changes to this policy are made in this file, in the public repository, with the date
above updated.
