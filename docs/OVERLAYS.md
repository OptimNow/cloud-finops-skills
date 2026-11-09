# Private overlays: extend the skill without forking it

The public skill carries billing mechanics, methods and decision rules that anyone can
verify on a provider page. It deliberately carries nothing that is yours: your
negotiated rates, your tag taxonomy, your coverage targets, the figures you observed in
your own contracts, the decisions your committee already took. An **overlay** is where
that goes. It is a second, private skill that sits on top of the public one, cites it,
and never copies it.

This page is the convention for writing one. It is the convention OptimNow follows for
its own advisory layers, which stay outside this repository: what is published here is
the structure, not their content.

## Why an overlay rather than a fork

A fork gives you a copy of the public files to edit. It also gives you a merge every
time the public files change, and they change on a fortnightly rhythm. Forks drift, and
a fork that has drifted stops receiving corrections to the mechanics it depends on.

An overlay copies nothing. It names the public sections it builds on, by heading, and
adds what the public cannot carry. When a public file is updated, the overlay keeps
working; when a public heading is renamed, a check tells you. Delete the overlay and
the public skill is intact; upgrade the public skill and the overlay is intact. That is
the test of a well-formed overlay.

A fork is still the right tool when you want to change the public text itself: a
different methodology, a different house style, a provider this repository does not
cover. The README section "Adapting this skill for your organisation" covers both
paths.

## The one rule

**An overlay never restates a mechanic.** Definitions, official rates and their dates,
timelines, intake questions, grid checks, decision trees: those live in the public file,
and the overlay points at them by heading. The overlay adds what the public file cannot
carry: who published which figure and when, how your own contracts or estate sit
against it, which tactics rest on which evidence, what your organisation treats as
acceptable on each check, and the decisions already taken.

The rule has two consequences worth stating. When you find a mechanic missing from the
public file, fix it in public with a pull request rather than in your overlay: the
overlay stays thin and the base improves for everyone. And copied or closely paraphrased
text carries the public licence with it (CC BY-SA 4.0, ShareAlike), so an overlay that
cites and calibrates rather than restates keeps the licence question simple.

## Anatomy

An overlay is a skill folder beside the public one, never inside the plugin folder and
never pushed to this repository:

```
~/.claude/skills/{org}-{domain}-advisory/      (or .claude/skills/ inside a project)
├── SKILL.md            <- entry point: frontmatter, routing, the one rule
├── calibration.md      <- your figures, each with source, date and confidence
└── decisions.md        <- what was decided, by whom, and when to revisit it
```

Name the folder after the organisation and the domain it calibrates. One overlay per
domain keeps each one small enough to read in full: commitments, contracts, tagging,
chargeback, one client account.

For Claude Code and claude.ai the folder is a skill like any other and loads beside the
public plugin. For ChatGPT and Gemini, upload the overlay files as additional knowledge
files next to the public ones. The hosted MCP connector serves public content only; an
overlay is a skill-side object and never reaches it.

## The SKILL.md contract

### Frontmatter

```yaml
---
name: "{org}-commitments-advisory"
description: "Use together with the cloud-finops skill when {situation}. Adds {what the public cannot carry} on top of the public reference {public-file}. Not for distribution. Triggers on {the words your users say}."
overlay_of:
  - reference: finops-aws-commitments
    sections:
      - "Compute commitment decision tree"
      - "Commitment portfolio liquidity"
questions:
  - "What coverage target do we hold for compute, and who approved it?"
  - "Quel taux de couverture visons-nous sur le compute, et qui l'a validé ?"
---
```

- `description` says the overlay is used together with the cloud-finops skill, names
  what it adds and which public file it builds on, and lists the trigger words. Add
  "Not for distribution" when that is the case.
- `overlay_of` lists each public file and the exact H2 or H3 headings the overlay
  cites. This is what the check verifies, and what `get_reference(name=, section=)`
  fetches on the connector.
- `questions` follows the public rules (`docs/DESIGN.md`, "Reference-file
  frontmatter"): four to eight, in the user's words, at least one in the language your
  users write, no repository vocabulary. These are the questions the public files
  cannot answer and the overlay can: "what discount is realistic for our size", "does
  our policy allow a three-year term". A question already declared by a public file is
  a routing ambiguity, and the check refuses it.

### Body

Five sections, in this order, keep every overlay readable by someone who has seen
another one:

1. **Load the public first.** Name the public files and the one line of why: those
   files carry every mechanic.
2. **The one rule.** Restate it in one paragraph, with what this overlay adds.
3. **Routing.** A table from question type to overlay file, whose last row is always
   "Any mechanic, definition, official rate, timeline or grid check: not here, see the
   public headings".
4. **How to use it in an engagement.** The order of operations, which starts with the
   public intake and ends with your calibration applied to the public grid or tree.
5. **Handling rules.** How figures are rounded and anonymised, what stays internal,
   what the house style is.

## Citing public sections

Cite a public section by its heading, verbatim, in quotation marks. The heading is the
stable handle: the connector's `get_reference(name=, section=)` returns that section and
nothing else, and the check confirms the heading still exists. The check matches the way
the connector's first tier does, case-insensitive with punctuation set aside, so a
citation written without the heading's dash still passes; the connector is more tolerant
still, so a citation that passes the check always resolves there. Do not cite by line
number or by paraphrase.

When the heading you need does not exist, the content you want to anchor to is
probably missing from the public file. Propose it there first.

## What goes in, what stays out

| Public (this repository) | Private (your overlay) |
|---|---|
| Any mechanic verifiable on a provider page | Any figure observed in your own contracts, bills or estate |
| Methods, decision trees, intake protocols, review grids | Benchmarks, tactics, acceptance thresholds |
| Diagnostic questions in the user's words | Names of clients, accounts, legal entities, contract identifiers |
| Skeletons of deliverables | Filled, calibrated deliverables |
| Illustrative, dated figures that make a mechanic concrete | Negotiated rates, coverage targets, decisions taken |

The quick test: if a competitor could monetise the paragraph as it stands, it is
private.

## Handling rules for figures

- Every figure carries its source, its date and a confidence level. A figure without a
  date is a figure that will be quoted after it has expired.
- Round observed figures and strip identifiers: a calibration point is a year, a term,
  an order of magnitude and a rounded percentage, never a company or a contract number.
- Confidence levels are for the overlay's readers. In a client-facing deliverable,
  replace each with its prose equivalent: the source, the sample, the limit of the
  claim.
- The public dated-price rule applies unchanged: a figure is quoted with its date, and
  a live figure comes from the tool that owns it.

## How the model uses it

Public first, overlay second. The model reads the mechanic in the public section the
overlay cites, then applies the overlay's calibration or decision. A good answer makes
the two layers visible: "the public decision tree says X; your policy caps it at Y,
decided on {date}". If the overlay disagrees with the public file on a mechanic, either
the public file is wrong or the overlay has broken the one rule; in both cases the fix
is a pull request, not a private correction.

## Keeping it in sync

```bash
python scripts/check-overlay.py ~/.claude/skills/{org}-{domain}-advisory
```

The check reads the overlay's `SKILL.md` and every `.md` beside it, and reports:

- a `description` that does not name the cloud-finops skill, or a `name` that shadows
  a public file or the public skill itself (`cloud-finops`);
- a cited public file that does not exist, or a cited heading that no longer matches an
  H2 or H3 of that file (it prints the headings available);
- a missing or malformed `questions` list, a question in repository vocabulary, or a
  question already declared by a public file;
- any sentence of ten words or more that appears verbatim in a public reference or
  playbook, in any file of the overlay: the mechanical form of the one rule;
- an em dash, since the house style is straight dashes.

Run it after every public release. The template in `docs/overlay-template/` is checked
in CI on every pull request, so a public heading cannot be renamed without the template
and this page being updated.

The script needs PyYAML (`pip install pyyaml`); installing the MCP server with its dev
extras provides it. Pass `--public <path>` when the public skill is installed somewhere
other than this repository.

## Client profiles are overlays too

A consultancy or a platform team that serves several accounts can keep one overlay per
account: the estate, the tag taxonomy, the negotiated rates, the maturity stage, the
decisions in flight. The same rules apply, and the folder name carries the account. The
model then pre-diagnoses against the profile instead of asking the intake questions
from zero.

## Start from the template

`docs/overlay-template/` holds a minimal overlay that passes the check: a `SKILL.md`
built on three sections of `finops-aws-commitments`, a `calibration.md` and a
`decisions.md` with the table shapes. Copy the folder beside your public skill, rename
it, replace every `{placeholder}`, and run the check. The placeholders in the
frontmatter sit inside quotes because braces mean something to YAML; the quotes can go
once the values are real.
