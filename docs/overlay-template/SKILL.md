---
name: "{org}-commitments-advisory"
description: "Use together with the cloud-finops skill when sizing, renewing or reviewing compute commitments for {Org}. Adds {Org}'s coverage targets, the terms it negotiated and the decisions its committee already took, on top of the public reference finops-aws-commitments. Not for distribution. Triggers on Savings Plan renewal, RI expiry, coverage target, commitment review, {Org} commitment policy."
overlay_of:
  - reference: finops-aws-commitments
    sections:
      - "Compute commitment decision tree"
      - "Commitment portfolio liquidity"
      - "Phased purchasing"
questions:
  - "What coverage target do we hold for compute, and who approved it?"
  - "Which of our Savings Plans expire this quarter, and what did we decide last time?"
  - "Does our policy allow a three-year commitment, and under which conditions?"
  - "Quel taux de couverture visons-nous sur le compute, et qui l'a validé ?"
---

# {Org} commitments advisory (private)

Load the public reference first: `finops-aws-commitments.md` in the cloud-finops skill.
It carries every mechanic: the instruments, the decision tree, the liquidity rules and
the phased purchasing cadence.

**The one rule.** This skill never restates a mechanic. It cites the public file's
section headings and adds what the public file cannot carry: {Org}'s coverage targets
and who set them, the terms {Org} negotiated, how its portfolio sits against the public
liquidity rules, and the decisions already taken with their revisit dates.

## Routing

| Question type | File |
|---|---|
| What our coverage target is, what we negotiated, how our figures sit against the public rules | `calibration.md` |
| What was decided, by whom, and when it is due for review | `decisions.md` |
| Any mechanic, definition, official rate, timeline or decision tree | Not here. The public file: see the headings listed in `overlay_of` |

## How to use it in an engagement

1. Walk the public "Compute commitment decision tree" with the user's usage data.
2. Apply the {Org} coverage target and policy limits from `calibration.md`, naming the
   decision that set them.
3. Check the resulting portfolio against the public "Commitment portfolio liquidity"
   rules; record any exception in `decisions.md`.
4. Schedule purchases with the public "Phased purchasing" cadence, adjusted by the
   budget calendar in `calibration.md`.

## Handling rules

- Every figure in this overlay carries a source, a date and a confidence level.
- Negotiated terms are quoted as rounded percentages and orders of magnitude, never
  with a contract or agreement identifier.
- Confidence levels stay internal; a client or board deliverable carries the source and
  the limit of the claim instead.
- British spelling, straight dashes, the % sign.
