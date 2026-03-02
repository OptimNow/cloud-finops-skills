# CLAUDE.md

Project context for AI assistants and human contributors working on this repository.

---

## What this repo is

A structured, model-agnostic FinOps knowledge skill for AI agents. The `cloud-finops/`
folder contains reference files that give any LLM accurate Cloud FinOps expertise -
Claude, GPT, Gemini, or any MCP-compatible agent.

- **SKILL.md** - entry point for Claude Code and generic agents
- **POWER.md** - entry point for Kiro IDE (same references, different format)
- **references/** - domain-specific content files (billing mechanics, pricing, optimisation patterns)
- **INSTALLATION.md** - 6 setup options including a model-agnostic response contract for non-Claude models

Both entry points route to the same reference files. No content is duplicated.
The response contract in INSTALLATION.md (Option 6) ensures structured, billing-grounded
answers across all models, even when model defaults differ.

---

## Repository structure

```
cloud-finops-skills/
├── CLAUDE.md              <- You are here
├── README.md              <- Public-facing documentation
├── INSTALLATION.md        <- Setup instructions (6 options) + response contract
├── LICENSE.md             <- CC BY-SA 4.0
├── install.sh             <- One-liner installer script
├── assets/                <- Screenshots for installation guide
├── cloud-finops/          <- The skill (this is what gets installed)
│   ├── SKILL.md           <- Entry point + domain router
│   ├── POWER.md           <- Kiro IDE entry point
│   └── references/
│       ├── optimnow-methodology.md
│       ├── finops-for-ai.md
│       ├── finops-ai-value-management.md
│       ├── finops-genai-capacity.md
│       ├── finops-anthropic.md
│       ├── finops-aws.md
│       ├── finops-bedrock.md
│       ├── finops-azure.md
│       ├── finops-azure-openai.md
│       ├── finops-gcp.md
│       ├── finops-vertexai.md
│       ├── finops-tagging.md
│       ├── finops-framework.md
│       ├── finops-databricks.md
│       ├── finops-snowflake.md
│       ├── finops-oci.md
│       └── greenops-cloud-carbon.md
└── pipeline/              <- Content update pipeline (gitignored, private)
    ├── run_scan.py        <- Weekly scan entry point
    ├── run_apply.py       <- Review and apply entry point
    ├── config.yaml        <- Pipeline configuration
    ├── sources.yaml       <- 29 content sources (RSS, pricing pages, blogs)
    ├── scanner/           <- Fetcher + Sonnet-based classifier
    ├── proposer/          <- CHANGES.md report generator
    ├── applier/           <- Opus-based diff generator and file editor
    ├── alerter/           <- Gmail draft builder
    └── state/             <- Runtime state (scan results, history)
```

---

## Content update pipeline

The `pipeline/` folder contains a weekly content scanner that detects FinOps-relevant
changes across 29 sources and proposes updates to the reference files. It is gitignored
and not part of the public distribution.

The pipeline is human-in-the-loop: nothing is changed automatically. Every proposed
update goes through review (list, preview diffs, approve/reject) before touching any
reference file. See `pipeline/README.md` for the full workflow.

---

## Model compatibility

The skill files are plain markdown - any LLM can read them. What differs across models
is how well they follow the structure and avoid hallucinating billing rules.

- **Claude** (Code, .ai, API) - reads SKILL.md natively, no extra configuration needed
- **Kiro IDE** - reads POWER.md natively
- **GPT, Gemini, other models** - inject the reference files as context and add the
  response contract from INSTALLATION.md (Option 6) to the system prompt

The response contract ensures consistent output structure (Context, Recommendation,
Metrics, Business impact) and prevents models from inventing pricing figures or
discount mechanics.

---

## How to add a new reference file

Follow these four steps whenever you add a new domain:

1. **Create the reference file** in `cloud-finops/references/`
   - Name it `finops-{domain}.md` (or `{category}-{domain}.md` for non-FinOps topics like `greenops-cloud-carbon.md`)
   - Follow the structure of an existing reference file as a template
   - Include practical guidance, not abstract theory

2. **Add a routing entry in SKILL.md**
   - Add a row to the "Domain routing" table with the query topic and file path
   - Add a row to the "Reference files" table with the filename, description, and approximate line count

3. **Add a routing entry in POWER.md**
   - Add a row to the "Domain routing" table (same format as SKILL.md)
   - Add relevant keywords to the `keywords` list in the YAML frontmatter

4. **Update README.md**
   - Add a bullet under "What this skill covers"
   - Add the file to the "Directory structure" listing
   - Add usage examples if applicable

---

## Content rules

**Writing style**
- Use straight dashes (`-`), never em dashes
- Use British spelling for public-facing content (optimisation, organisation, behaviour)
- Be direct and practical. Diagnose before prescribing
- Connect cost recommendations to business outcomes

**SKILL.md frontmatter**
- The `description` field must be **under 1024 characters** (Claude.ai upload limit)
- Only `name` and `description` are required in the YAML frontmatter
- Do not add a `license` field to the frontmatter (it renders as visible text in Claude.ai)

**License**
- All content is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
- Credit OptimNow as the original author
- Include the license footer on new reference files if following the existing pattern

**Do not commit**
- `INTERNAL_NOTES.md` is gitignored and must never be committed
- `pipeline/` is gitignored and must not be made public without explicit decision

---

## Testing changes

After editing reference files, verify them by asking questions in the domain you changed.
Good test patterns:

- Ask a question that requires specific billing mechanics (pricing, break-even, discount rules)
- Ask a maturity-sensitive question (the response should adapt to Crawl/Walk/Run context)
- Ask a cross-domain question that requires loading multiple references
- Test with a non-Claude model using the response contract to verify portability

---

## Pull request checklist

- [ ] New reference file follows the `finops-{domain}.md` naming convention
- [ ] Routing table updated in both SKILL.md and POWER.md
- [ ] README directory listing and coverage section updated
- [ ] SKILL.md description stays under 1024 characters
- [ ] No em dashes in any public content
- [ ] No sensitive or internal files included
- [ ] Content is practical and based on how billing actually works, not on documentation summaries
