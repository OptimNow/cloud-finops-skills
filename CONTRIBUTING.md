# Contributing to the Cloud FinOps Skill

Practitioner experience is the highest-value contribution. Frameworks and
vendor docs are already public; what is rare is "we tried X in production,
this is what actually billed". Issues and PRs that bring that lens are welcome
in any of the layers below.

**Before you start**, if your change touches anything that names another OptimNow
tool - an MCP tool name, an endpoint URL, a provenance field - check
[`DEPENDENCIES.md`](./DEPENDENCIES.md). It maps the five repositories in this family
and tells you which ones a change ripples into. Most cross-repo breakage here is
documentation drift that no CI check catches.

## Process and credit

Open an issue first for anything larger than a typo or single fact correction, so we
can scope before you write. Pull requests should keep the existing structure of the
file you are touching, follow the conventions in [`CLAUDE.md`](./CLAUDE.md) (FCP
frontmatter, no em dashes, British spelling in prose, license footer), and pass the
FCP coverage check (`./scripts/fcp-coverage.sh --check`).

You keep authorship: every contribution lives in the commit history under your name
and shows up in `git blame`. Substantive contributors are visible in the repo's
contributors list on GitHub.

## License and what that means for you

All contributions are licensed under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). This is an
OptimNow-maintained repo, but CC BY-SA was chosen specifically so anyone - including
you - can fork, customise, and redistribute under their own brand, as long as they
credit and share-alike. If you want a project under your own name rather than
contributing here, fork freely; see "Adapting this skill for your organisation" in
the [README](./README.md#adapting-this-skill-for-your-organisation) for the fork
playbook. Both paths are first-class.

## Concrete contribution types we actively want

- **Pricing or billing-mechanic correction.** A CUR column name we got wrong, a
  CUD / Reservation discount depth that has shifted, a refund cap that does not
  match the latest contract terms. Cite the primary source (provider doc, your
  invoice, an enrollment agreement) so the change is verifiable.
- **New named playbook.** A waste pattern you see in the field that is not yet in
  `skills/cloud-finops/playbooks/`. Follow the format documented in
  [`playbooks/README.md`](./skills/cloud-finops/playbooks/README.md): symptoms /
  detection query / fix / anti-pattern / sources, ~3-8 KB. Examples we'd love:
  Lambda cold-start sprawl, Bedrock model proliferation, Snowflake warehouse
  fragmentation, Databricks all-purpose-cluster default-on, Cloud Run min-instance
  creep.
- **Fix or enrich an existing playbook.** A detection query that returns false
  positives in your data, an anti-pattern you saw burn a team, a fix step that
  does not work without a precondition we missed.
- **Pick up a deferred reference file.** The `Deferred reference files` section of
  [`docs/ROADMAP.md`](./docs/ROADMAP.md) lists the P2/P3 items (forecasting, unit
  economics, practice operations, education & enablement, benchmarking, cost
  warehouse) with the rationale and trigger to revisit. If your engagement has
  surfaced one of those, that is the trigger - open an issue with the engagement
  context and we will scope the file together.
- **Tool installer addition.** Adding `--tool <new-tool>` for a coding assistant or
  agent we do not yet support. Match the existing installer pattern in `install.sh`
  (idempotent, dry-run-safe, exclude local-only files like `.claude/` and
  `.backups/`).
- **Real-world case study or counter-example.** Something you tried that did not
  work, or worked under conditions we do not flag. These end up as anti-pattern
  blocks in the relevant reference or playbook.
- **Adversarial review.** Disagreement on a recommendation, with reasoning and
  ideally a source. The repo is opinionated; it should also be falsifiable.
- **Bug report.** Installer fails on your setup, a file does not render in your
  tool, a guard rail false-positives. Open an issue with the exact command and
  output.
- **Translation.** Selected references in another language, maintained as a
  parallel directory rather than a fork, when you can commit to keeping them in
  sync with the next refresh.

## What we push back on

- Vendor marketing material restated as fact, without a primary source or
  practitioner-grade evidence behind the claim.
- Wholesale AI-generated reference content with no human practitioner pass. The
  pipeline that powers the fortnightly refresh has hard guard rails (see the
  `Lessons learned` section of `CLAUDE.md` for why). Hand-written contributions go
  through human review for the same reasons.
- "Best practices" lists with no business-value framing. Every recommendation in
  this repo connects cost to a business outcome; contributions should follow that
  pattern.

---

> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
