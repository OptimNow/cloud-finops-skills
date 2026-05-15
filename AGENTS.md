# AGENTS.md

This file is the project context entry point for **Codex CLI** (and other agents
that read `AGENTS.md` from the project root). For deeper conventions and
contributor rules, see [CLAUDE.md](./CLAUDE.md) - the two files share the same
project context, this one is just shorter.

---

## What this repo is

A structured, model-agnostic FinOps knowledge skill for AI agents. The
`skills/cloud-finops/` folder contains reference files that give any LLM accurate
Cloud FinOps expertise - Claude, GPT, Gemini, Codex, or any
MCP-compatible agent.

- **SKILL.md** - entry point for Claude Code and generic agents
- **POWER.md** - entry point for Kiro IDE (same references, different format)
- **AGENTS.md** - entry point for Codex CLI (this file)
- **references/** - 28 domain-specific content files (billing mechanics, pricing,
  optimisation patterns)
- **INSTALLATION.md** - cross-tool installer covering 12 tool integrations, plus
  a model-agnostic response contract for non-Claude models

All entry points route to the same reference files. No content is duplicated.

---

## Repository structure

```
cloud-finops-skills/
├── AGENTS.md              <- You are here (Codex CLI entry point)
├── CLAUDE.md              <- Claude Code project context
├── README.md              <- Public-facing documentation
├── INSTALLATION.md        <- Cross-tool installer + response contract
├── LICENSE.md             <- CC BY-SA 4.0
├── install.sh             <- One-liner installer script
├── llms.txt               <- llms.txt index for cross-agent discovery
├── assets/                <- Screenshots for installation guide
├── skills/cloud-finops/          <- The skill (this is what gets installed)
│   ├── SKILL.md           <- Entry point + domain router
│   ├── POWER.md           <- Kiro IDE entry point
│   └── references/        <- 28 reference files, all with YAML FCP frontmatter
└── pipeline/              <- Content update pipeline (gitignored, private)
```

For the full directory listing of the 28 reference files and the pipeline
sub-modules, see CLAUDE.md.

---

## Content update pipeline

The `pipeline/` folder contains a monthly content scanner (around the 1st of each
month) that detects FinOps-relevant changes across 29 sources and proposes
updates to the reference files. It is gitignored and not part of the public
distribution.

The pipeline is human-in-the-loop: nothing is changed automatically. Every
proposed update goes through review (list, preview diffs, approve/reject) before
touching any reference file.

---

## Model compatibility

The skill files are plain markdown - any LLM can read them. What differs across
models is how well they follow the structure and avoid hallucinating billing
rules.

- **Claude Code, claude.ai, Claude Desktop** - read SKILL.md natively
- **Codex CLI** - reads this AGENTS.md as project context
- **Kiro IDE** - reads POWER.md natively
- **GPT, Gemini, other models** - inject the reference files as context and add
  the response contract from INSTALLATION.md ("API integration / Recommended
  response contract" section) to the system prompt

The response contract ensures consistent output structure (Context,
Recommendation, Metrics, Business impact) and prevents models from inventing
pricing figures or discount mechanics.

---

## How to contribute

For the full contributor guide (how to add a new reference file, FCP
frontmatter convention, content rules, PR checklist, Roadmap of deferred work),
see [CLAUDE.md](./CLAUDE.md). The contributor process is shared regardless of
which agent surface you use.

Quick rules:
- Use straight dashes (`-`), never em dashes
- Use British spelling for public-facing content (optimisation, organisation,
  behaviour). Product/framework names keep their official spelling.
- All reference files carry YAML FCP frontmatter mapping the file to the FinOps
  Framework Capability it serves
- Bump the plugin version (`.claude-plugin/plugin.json`, minor digit) for
  user-visible feature changes

---

## License

All content is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Credit OptimNow as the original author.
