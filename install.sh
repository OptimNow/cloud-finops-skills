#!/usr/bin/env bash
#
# install.sh - Cross-tool installer for the Cloud FinOps Skill.
#
# Usage:
#   ./install.sh                       Auto-detect tools in cwd / $HOME and install for each
#   ./install.sh --tool <name>         Install for one specific tool
#   ./install.sh --tool all            Install for every supported tool
#   ./install.sh --list                List supported tools
#   ./install.sh --dry-run             Print what would happen, no writes
#   ./install.sh --user                Install at user-level paths where supported (Claude Code)
#   ./install.sh --grouped             ChatGPT only: produce a 10-file grouped build
#                                      (same content bundled by domain) instead of
#                                      42 per-reference files. Easier to upload.
#   ./install.sh --dest <dir>          Override the project / target directory
#   ./install.sh --help                Show this help
#
# Tools: claude-code, claude-projects, cursor, windsurf, chatgpt, gemini,
#        gemini-cli, codex, aider, copilot, kiro, mcp
#
# The "mcp" target is special: it does NOT install Python packages. It prints
# the install hint (`pip install cloud-finops-mcp`) plus per-client config
# snippets so you can wire any MCP-aware tool (Claude Code, Cursor, Codex,
# Windsurf, Cline, etc.) at the cloud-finops MCP server.
#
# This script only performs local file copies and writes. No network calls beyond
# git clone (when run via curl), no sudo, no eval. macOS / Linux / WSL.
#
# Source: https://github.com/OptimNow/cloud-finops-skills (CC BY-SA 4.0)

set -euo pipefail

# ---- colours ----
if [[ -t 1 && -z "${NO_COLOR:-}" && "${TERM:-}" != "dumb" ]]; then
  C_GREEN=$'\033[0;32m'; C_YELLOW=$'\033[1;33m'; C_RED=$'\033[0;31m'
  C_BLUE=$'\033[0;34m'; C_BOLD=$'\033[1m'; C_DIM=$'\033[2m'; C_RESET=$'\033[0m'
else
  C_GREEN=''; C_YELLOW=''; C_RED=''; C_BLUE=''; C_BOLD=''; C_DIM=''; C_RESET=''
fi

ok()    { printf "${C_GREEN}[OK]${C_RESET}  %s\n" "$*"; }
warn()  { printf "${C_YELLOW}[!!]${C_RESET}  %s\n" "$*"; }
err()   { printf "${C_RED}[ERR]${C_RESET} %s\n" "$*" >&2; }
info()  { printf "${C_BLUE}[..]${C_RESET}  %s\n" "$*"; }
dim()   { printf "${C_DIM}%s${C_RESET}\n" "$*"; }

# ---- constants ----
REPO_URL="https://github.com/OptimNow/cloud-finops-skills.git"
SKILL_NAME="cloud-finops"
ALL_TOOLS=(claude-code claude-projects cursor windsurf chatgpt gemini gemini-cli codex aider copilot kiro mcp)

# ---- state ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || pwd)"
SRC_DIR=""
TMPDIR=""
TOOL=""
DRY_RUN=""
USER_LEVEL=""
DEST_OVERRIDE=""
GROUPED=""

cleanup() { [[ -n "$TMPDIR" ]] && rm -rf "$TMPDIR" 2>/dev/null || true; }
trap cleanup EXIT

# ---- helpers ----

usage() {
  sed -n '3,24p' "$0" | sed 's/^# \?//'
  exit 0
}

resolve_source() {
  if [[ -f "$SCRIPT_DIR/cloud-finops/SKILL.md" ]]; then
    SRC_DIR="$SCRIPT_DIR"
  elif [[ -f "$PWD/cloud-finops/SKILL.md" ]]; then
    SRC_DIR="$PWD"
  else
    info "Source not found locally. Cloning repo..."
    if ! command -v git >/dev/null 2>&1; then
      err "git not found and no local source. Install git or run from a clone of the repo."
      exit 1
    fi
    TMPDIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'finops-skill')
    git clone --depth 1 --quiet "$REPO_URL" "$TMPDIR/cloud-finops-skills"
    SRC_DIR="$TMPDIR/cloud-finops-skills"
  fi
}

# Strip the YAML frontmatter (between the first two --- lines) from a markdown file.
strip_frontmatter() {
  awk 'BEGIN{f=0} /^---$/{f++; if(f<=2) next} f>=2{print}' "$1"
}

# Concatenated body: SKILL.md (no frontmatter) + every reference file +
# every playbook. SKILL.md routes named waste patterns to playbooks/<slug>.md,
# so the playbooks must be inlined too - otherwise the routing contract points
# the model at files that are not present in the installed artefact.
write_concat_body() {
  strip_frontmatter "$SRC_DIR/cloud-finops/SKILL.md"
  echo
  echo "---"
  echo
  echo "## Reference files"
  echo
  for ref in "$SRC_DIR/cloud-finops/references"/*.md; do
    echo "### $(basename "$ref" .md)"
    echo
    cat "$ref"
    echo
    echo "---"
    echo
  done
  if [[ -d "$SRC_DIR/cloud-finops/playbooks" ]]; then
    echo
    echo "## Playbooks"
    echo
    for pb in "$SRC_DIR/cloud-finops/playbooks"/*.md; do
      local pb_name
      pb_name=$(basename "$pb")
      # Skip the directory's own README - it documents the format /
      # convention for human contributors, not a runbook the model
      # should retrieve as a pattern.
      [[ "$pb_name" == "README.md" ]] && continue
      echo "### playbooks/$pb_name"
      echo
      cat "$pb"
      echo
      echo "---"
      echo
    done
  fi
}

# Idempotent file write with dry-run support
do_write() {
  local target="$1"
  local content_fn="$2"
  if [[ -n "$DRY_RUN" ]]; then
    info "DRY-RUN would write: $target"
    return
  fi
  mkdir -p "$(dirname "$target")"
  $content_fn > "$target"
}

# Idempotent directory copy with dry-run support.
# Excludes local-only artefacts that may exist in the maintainer's worktree:
#   .claude/         - local Claude Code settings
#   .backups/        - pipeline backups (cloud-finops/references/.backups/)
#   .git/            - if SRC happens to be a git repo
do_copy_dir() {
  local src="$1" dest="$2"
  if [[ -n "$DRY_RUN" ]]; then
    info "DRY-RUN would copy: $src -> $dest (excluding .claude, .backups, .git)"
    return
  fi
  mkdir -p "$(dirname "$dest")"
  rm -rf "$dest"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude='.claude' --exclude='.backups' --exclude='.git' "$src/" "$dest/"
  else
    cp -r "$src" "$dest"
    rm -rf "$dest/.claude" "$dest/.git" 2>/dev/null || true
    find "$dest" -type d -name '.backups' -exec rm -rf {} + 2>/dev/null || true
  fi
}

# ---- detection ----

detect_claude_code()     { [[ -d ".claude" || -d "$HOME/.claude" ]]; }
detect_claude_projects() { return 1; }   # web-only, never auto-detected
detect_cursor()          { command -v cursor >/dev/null 2>&1 || [[ -d ".cursor" || -d "$HOME/.cursor" ]]; }
detect_windsurf()        { command -v windsurf >/dev/null 2>&1 || [[ -d ".windsurf" || -d "$HOME/.codeium" ]]; }
detect_chatgpt()         { return 1; }   # web-only
detect_gemini()          { return 1; }   # web-only
detect_gemini_cli()      { command -v gemini >/dev/null 2>&1 || [[ -d "$HOME/.gemini" ]]; }
detect_codex()           { command -v codex >/dev/null 2>&1 || [[ -d ".codex" || -d "$HOME/.codex" ]]; }
detect_aider()           { command -v aider >/dev/null 2>&1 || [[ -f "CONVENTIONS.md" ]]; }
detect_copilot()         {
  # Heuristic: VS Code CLI present OR an existing copilot-instructions.md
  # already in this repo. The previous version also detected on the
  # presence of any .github/ directory, which over-detected on every
  # repo with issue templates or workflows. Removed.
  command -v code >/dev/null 2>&1 || [[ -f ".github/copilot-instructions.md" ]]
}
detect_kiro()            { command -v kiro >/dev/null 2>&1 || [[ -d ".kiro" ]]; }
# MCP target is always opt-in via --tool mcp; auto-detection is intentionally off.
detect_mcp()             { return 1; }

is_detected() {
  case "$1" in
    claude-code)     detect_claude_code ;;
    claude-projects) detect_claude_projects ;;
    cursor)          detect_cursor ;;
    windsurf)        detect_windsurf ;;
    chatgpt)         detect_chatgpt ;;
    gemini)          detect_gemini ;;
    gemini-cli)      detect_gemini_cli ;;
    codex)           detect_codex ;;
    aider)           detect_aider ;;
    copilot)         detect_copilot ;;
    kiro)            detect_kiro ;;
    mcp)             detect_mcp ;;
    *)               return 1 ;;
  esac
}

# ---- per-tool installers ----

install_claude_code() {
  local target
  if [[ -n "$DEST_OVERRIDE" ]]; then
    target="$DEST_OVERRIDE/$SKILL_NAME"
  elif [[ -n "$USER_LEVEL" ]]; then
    target="$HOME/.claude/skills/$SKILL_NAME"
  else
    target="$PWD/.claude/skills/$SKILL_NAME"
  fi
  do_copy_dir "$SRC_DIR/cloud-finops" "$target"
  ok "Claude Code: skill copied -> $target"
  dim "  Restart Claude Code or run /reload-plugins to pick up changes."
}

install_claude_projects() {
  local outdir="${DEST_OVERRIDE:-$PWD}/dist/claude-projects"
  if [[ -n "$DRY_RUN" ]]; then
    info "DRY-RUN would build: $outdir/cloud-finops.zip"
    return
  fi
  mkdir -p "$outdir"
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$SRC_DIR/cloud-finops" "$outdir/cloud-finops.zip" <<'PYEOF'
import os, sys, zipfile
src_dir, out_zip = sys.argv[1], sys.argv[2]
src_root = os.path.dirname(os.path.abspath(src_dir))
EXCLUDE = {".claude", ".backups", ".git"}
with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE]
        for f in files:
            full = os.path.join(root, f)
            arcname = os.path.relpath(full, src_root).replace(os.sep, '/')
            z.write(full, arcname)
PYEOF
  elif command -v zip >/dev/null 2>&1; then
    (cd "$SRC_DIR" && zip -r -q "$outdir/cloud-finops.zip" cloud-finops \
      -x 'cloud-finops/.claude/*' \
      -x 'cloud-finops/**/.backups/*' \
      -x 'cloud-finops/.git/*')
  else
    err "Neither python3 nor zip found. Cannot build claude-projects zip."
    return 1
  fi
  ok "Claude Projects: zip built -> $outdir/cloud-finops.zip"
  dim "  Manual upload: claude.ai or Claude Desktop -> Settings -> Skills -> Upload zip."
}

install_cursor() {
  local target="${DEST_OVERRIDE:-$PWD}/.cursor/rules/cloud-finops.mdc"
  do_write "$target" build_cursor_rule
  ok "Cursor: rule written -> $target"
  dim "  Cursor auto-loads .cursor/rules/. Trigger by asking a FinOps question in chat."
}

build_cursor_rule() {
  cat <<'EOF'
---
description: Expert FinOps guidance for cloud, AI, SaaS, and data-platform spend (multi-provider, model-agnostic). Use for cost questions on AWS, Azure, GCP, Anthropic, Bedrock, Vertex AI, Azure OpenAI, Databricks, Microsoft Fabric, Snowflake, OCI, AI coding tools, self-hosted vs managed AI inference, GenAI capacity planning, AI value management, GreenOps, FinOps Framework, SaaS asset management, ITAM, anomaly management, allocation and showback, chargeback, onboarding workloads, Kubernetes FinOps, waste detection.
globs:
  - "**/*"
alwaysApply: false
---

EOF
  write_concat_body
}

install_windsurf() {
  local target="${DEST_OVERRIDE:-$PWD}/.windsurf/rules/cloud-finops.md"
  do_write "$target" build_windsurf_rule
  ok "Windsurf: rule written -> $target"
}

build_windsurf_rule() {
  cat <<'EOF'
---
trigger: model_decision
description: Expert FinOps guidance for cloud, AI, SaaS, and data-platform spend (multi-provider, model-agnostic).
---

EOF
  write_concat_body
}

install_chatgpt() {
  local outdir="${DEST_OVERRIDE:-$PWD}/dist/chatgpt"
  local instructions_path="$outdir/instructions.md"
  local knowledge_dir="$outdir/knowledge"

  if [[ -n "$DRY_RUN" ]]; then
    info "DRY-RUN would write: $instructions_path"
    info "DRY-RUN would write: $knowledge_dir/*.md"
    return
  fi

  # Wipe any previous build so renamed/removed references don't linger
  rm -rf "$knowledge_dir"
  mkdir -p "$knowledge_dir"
  if [[ -n "$GROUPED" ]]; then
    # Grouped build emits a routing contract that points at the 9 grouped
    # filenames (aws.md, azure.md, ai.md, ...) rather than per-reference names.
    build_grouped_instructions > "$instructions_path"
  else
    build_chatgpt_instructions > "$instructions_path"
  fi
  local size
  size=$(wc -c < "$instructions_path")

  if [[ -n "$GROUPED" ]]; then
    # Grouped build: same domain bundling as Gemini. Produces 9 knowledge
    # files instead of 27 - well under any historical ChatGPT Custom GPT
    # cap and easier to upload reliably. Routing contract above already
    # points at the grouped filenames.
    build_gemini_grouped_knowledge "$knowledge_dir"
  else
    # Per-reference build: one knowledge file per reference, methodology merged
    # into finops-for-ai.md. 27 files - may exceed ChatGPT's historical cap.
    local methodology="$SRC_DIR/cloud-finops/references/optimnow-methodology.md"
    for ref in "$SRC_DIR/cloud-finops/references"/*.md; do
      local name
      name=$(basename "$ref")
      if [[ "$name" == "optimnow-methodology.md" ]]; then
        continue
      fi
      if [[ "$name" == "finops-for-ai.md" ]]; then
        {
          cat "$ref"
          echo
          echo "---"
          echo
          echo "## Reasoning Methodology Appendix"
          echo
          [[ -f "$methodology" ]] && cat "$methodology"
        } > "$knowledge_dir/$name"
      else
        cp "$ref" "$knowledge_dir/$name"
      fi
    done
    # Playbooks: SKILL.md routes named-pattern queries to playbooks/<slug>.md,
    # so each playbook must be uploadable as a knowledge file too. Prefix
    # the filename so they group together in the GPT Knowledge UI and don't
    # collide with reference filenames.
    if [[ -d "$SRC_DIR/cloud-finops/playbooks" ]]; then
      for pb in "$SRC_DIR/cloud-finops/playbooks"/*.md; do
        local pb_name
        pb_name=$(basename "$pb")
        [[ "$pb_name" == "README.md" ]] && continue
        cp "$pb" "$knowledge_dir/playbook-$pb_name"
      done
    fi
  fi

  local file_count
  file_count=$(find "$knowledge_dir" -maxdepth 1 -name "*.md" | wc -l | tr -d ' ')

  ok "ChatGPT: instructions ($size chars) -> $instructions_path"
  ok "ChatGPT: $file_count knowledge files -> $knowledge_dir/"
  if [[ $size -gt 8000 ]]; then
    warn "Instructions exceed ChatGPT's ~8000 char limit ($size chars). Manual trim needed."
  fi
  if [[ $file_count -gt 20 ]]; then
    warn "ChatGPT historically capped Custom GPT Knowledge at 20 files. Current build is $file_count files."
    dim "  If your upload is rejected, re-run with --grouped to produce a smaller"
    dim "  bundled build (same content, fewer files): ./install.sh --tool chatgpt --grouped"
  fi
  dim "  Manual upload steps:"
  dim "    1. Open https://chatgpt.com/gpts/editor"
  dim "    2. Paste $instructions_path into the Instructions field"
  dim "    3. Upload all files from $knowledge_dir/ to Knowledge"
  if [[ -z "$GROUPED" ]]; then
    dim "    4. Note: methodology is merged into finops-for-ai.md to keep file count down."
    dim "       Playbook files are prefixed playbook-* so they sort together in the GPT UI."
  else
    dim "    4. Grouped mode: 10 thematic files (aws, azure, gcp, ai, data-platforms,"
    dim "       oci, cross-cutting, finops-discipline, playbooks, methodology)"
  fi
}

build_chatgpt_instructions() {
  cat <<'EOF'
# Cloud FinOps Expert Assistant

You are an expert FinOps practitioner. Help users understand and optimise spend on cloud (AWS / Azure / GCP / OCI), AI platforms (Anthropic, Bedrock, Azure OpenAI / Foundry, Vertex AI), data platforms (Databricks, Microsoft Fabric, Snowflake), AI coding tools (Cursor, Claude Code, Copilot, Codex, Windsurf, Gemini Code Assist), SaaS, and cross-cutting concerns (tagging, FinOps Framework, GreenOps, ITAM).

Your knowledge files contain accurate, current billing mechanics and optimisation patterns refreshed monthly (around the 1st of each month). Always retrieve relevant knowledge files before answering - do not rely on general training data for billing specifics.

## Domain routing

Use these knowledge files for the following query types:

| Query topic | Knowledge file |
|---|---|
| AWS cost management, EC2, RIs, Savings Plans, EDP, RDS | finops-aws.md |
| AWS Bedrock model pricing, Application Inference Profiles, prompt caching | finops-bedrock.md |
| Azure cost management, Reservations, Savings Plans, AHB, MACC, AKS, MCA | finops-azure.md |
| Azure OpenAI / Foundry PTU reservations, locality | finops-azure-openai.md |
| Anthropic Claude billing, Fast mode, prompt caching, long-context | finops-anthropic.md |
| GCP cost management, BigQuery export, CUDs, SUDs, Spot, Carbon Footprint | finops-gcp.md |
| Vertex AI pricing, Provisioned Throughput, Context Caching | finops-vertexai.md |
| AI cost management, LLM economics, agentic patterns, ROI, methodology lens | finops-for-ai.md |
| AI investment governance, Investment Council, stage gates | finops-ai-value-management.md |
| GenAI capacity planning, provisioned vs shared, spillover | finops-genai-capacity.md |
| Self-hosted vs managed AI inference, build-vs-buy LLM, vLLM, GPU rental, hidden cost surface | finops-ai-self-hosted-vs-managed.md |
| AI coding tools (Cursor, Copilot, Claude Code, Codex, Windsurf, Gemini Code Assist) | finops-ai-dev-tools.md |
| Databricks (system.billing.usage, DBCU, allocation, Photon) | finops-databricks.md |
| Microsoft Fabric (F-SKUs, CU smoothing, pause/resume, governance trap) | finops-fabric.md |
| Snowflake (QUERY_ATTRIBUTION_HISTORY, Budgets, Cortex, resource monitors) | finops-snowflake.md |
| OCI (Cost Reports, FOCUS, cost-tracking tags, Universal Credits) | finops-oci.md |
| FinOps Framework (4 domains 2024 + Executive Strategy Alignment 2026) | finops-framework.md |
| Tagging strategy, naming conventions, IaC enforcement | finops-tagging.md |
| SaaS management, licence optimisation, shadow IT | finops-sam.md |
| ITAM, BYOL, marketplace governance | finops-itam.md |
| GreenOps, cloud carbon, sustainability | greenops-cloud-carbon.md |
| Cost anomaly management, masked anomalies, layered detection, threshold tuning | finops-anomaly-management.md |
| Cost allocation methodology and showback, FOCUS EffectiveCost vs BilledCost, defensible allocation keys, shared-services hard cases | finops-allocation-showback.md |
| Chargeback, soft-to-hard maturity, Finance and accounting prerequisites (ERP, transfer pricing, cross-border tax, SOX), chargeback-revolt anti-pattern | finops-chargeback.md |
| Onboarding workloads, migration-time cost hygiene, intake gate, 60-90 day forecast-then-commit rule, double-bubble cost, M&A integration | finops-onboarding-workloads.md |
| Kubernetes FinOps (EKS / GKE / AKS), OpenCost / Kubecost, FOCUS-emitting K8s allocation, container rightsizing, Karpenter, Spot diversification | finops-kubernetes.md |
| Waste detection playbooks, seven-category waste taxonomy, two-signal classification, WasteLine appliance | finops-waste-detection-playbooks.md |
| Named waste pattern (zombie NAT, snapshot sprawl, idle ELB, cross-AZ egress, oversized RDS, orphan EBS, orphan Azure disks, App Service overprovisioning, Log Analytics ingestion sprawl, idle Azure SQL, idle GKE Autopilot, orphan Persistent Disks, Cloud Functions cold starts, schedule blindness, untagged spend drift, idle SageMaker endpoint, always-on SageMaker notebook, SageMaker endpoint sprawl / MME consolidation, oversized GPU instance, multi-GPU underutilized, MIG candidate, GPU for CPU-bound workload, outdated GPU generation) | playbook-<slug>.md (e.g. playbook-aws-zombie-nat-gateway.md) |

For multi-domain queries, retrieve all relevant files and synthesise. For named
waste patterns, retrieve the matching `playbook-<slug>.md` knowledge file.

## Reasoning sequence

1. Apply the methodology lens (see Reasoning Methodology Appendix in finops-for-ai.md): diagnose before prescribing, connect cost to value, recommend progressively.
2. Retrieve the domain knowledge file(s) matching the query.
3. Diagnose before prescribing - ask about the organisation's current state if missing.
4. Connect cost recommendations to business outcomes.
5. Recommend progressively - quick wins first, structural changes second.
6. Reference open-source FinOps tools (FinOps Toolkit, OpenCost, Kubecost, Infracost, etc.) where they fit.

## Response format

Structure substantive answers with these headers:
- **Context** - what the user told you, what assumptions you're making
- **Recommendation** - the actionable advice
- **Metrics and signals** - what to measure or watch
- **Business impact** - how this connects to outcomes (cost saved, risk reduced, capability unlocked)

For brief factual questions, skip the structure. Use it for advisory or strategy questions.

## Maturity awareness

Always assess maturity before recommending solutions. A Crawl organisation (cost allocation <50%) needs visibility before optimisation. Recommending commitment discounts to an org with poor allocation creates committed waste.

## Source

Cloud FinOps Skill by OptimNow (https://optimnow.io). Licensed CC BY-SA 4.0.
Source: https://github.com/OptimNow/cloud-finops-skills
EOF
}

build_grouped_instructions() {
  cat <<'EOF'
# Cloud FinOps Expert Assistant

You are an expert FinOps practitioner. Help users understand and optimise spend on cloud (AWS / Azure / GCP / OCI), AI platforms (Anthropic, Bedrock, Azure OpenAI / Foundry, Vertex AI), data platforms (Databricks, Microsoft Fabric, Snowflake), AI coding tools (Cursor, Claude Code, Copilot, Codex, Windsurf, Gemini Code Assist), SaaS, and cross-cutting concerns (tagging, FinOps Framework, GreenOps, ITAM, anomaly management, allocation/showback, chargeback, onboarding, Kubernetes, waste detection).

Your knowledge files are grouped thematically and refreshed monthly (around the 1st of each month). Always retrieve the relevant grouped file before answering - do not rely on general training data for billing specifics.

## Domain routing (grouped layout)

Use these knowledge files for the following query types:

| Query topic | Knowledge file |
|---|---|
| AWS cost management, EC2, RIs, Savings Plans, EDP, RDS, Bedrock pricing, Application Inference Profiles | aws.md |
| Azure cost management, Reservations, Savings Plans, AHB, MACC, AKS, MCA, Azure OpenAI / Foundry PTUs | azure.md |
| GCP cost management, BigQuery export, CUDs, SUDs, Spot, Carbon Footprint, Vertex AI, Gemini pricing | gcp.md |
| AI cost management, LLM economics, agentic patterns, ROI, Anthropic billing, AI coding tools (Cursor / Copilot / Claude Code / Codex / Windsurf), GenAI capacity, AI Investment Council, self-hosted vs managed inference | ai.md |
| Databricks (DBCU, allocation, Photon), Microsoft Fabric (F-SKUs, CU smoothing), Snowflake (QUERY_ATTRIBUTION_HISTORY, Cortex) | data-platforms.md |
| OCI (Cost Reports, FOCUS, cost-tracking tags, Universal Credits) | oci.md |
| FinOps Framework (4 domains 2024 + Executive Strategy Alignment 2026), tagging, SaaS management, ITAM, GreenOps, Kubernetes FinOps, waste detection playbooks | cross-cutting.md |
| Anomaly management, allocation and showback, chargeback (incl. Finance / accounting prerequisites), onboarding workloads (migration-time cost hygiene + M&A) | finops-discipline.md |
| Named waste pattern (zombie NAT, snapshot sprawl, idle ELB, cross-AZ egress, oversized RDS, orphan EBS, orphan Azure disks, App Service overprovisioning, Log Analytics ingestion sprawl, idle Azure SQL, idle GKE Autopilot, orphan Persistent Disks, Cloud Functions cold starts, schedule blindness, untagged spend drift, idle SageMaker endpoint, always-on SageMaker notebook, SageMaker endpoint sprawl / MME consolidation, oversized GPU instance, multi-GPU underutilized, MIG candidate, GPU for CPU-bound workload, outdated GPU generation) | playbooks.md |
| Reasoning methodology lens (diagnose before prescribing, connect cost to value, recommend progressively) | methodology.md |

For multi-domain queries, retrieve all relevant grouped files and synthesise. For
named waste patterns, look up the matching `## playbook: <slug>` section inside
`playbooks.md`.

## Reasoning sequence

1. Apply the methodology lens (methodology.md): diagnose before prescribing, connect cost to value, recommend progressively.
2. Retrieve the grouped knowledge file(s) matching the query.
3. Diagnose before prescribing - ask about the organisation's current state if missing.
4. Connect cost recommendations to business outcomes.
5. Recommend progressively - quick wins first, structural changes second.
6. Reference open-source FinOps tools (FinOps Toolkit, OpenCost, Kubecost, Infracost, etc.) where they fit.

## Response format

Structure substantive answers with these headers:
- **Context** - what the user told you, what assumptions you're making
- **Recommendation** - the actionable advice
- **Metrics and signals** - what to measure or watch
- **Business impact** - how this connects to outcomes (cost saved, risk reduced, capability unlocked)

For brief factual questions, skip the structure. Use it for advisory or strategy questions.

## Maturity awareness

Always assess maturity before recommending solutions. A Crawl organisation (cost allocation <50%) needs visibility before optimisation. Recommending commitment discounts to an org with poor allocation creates committed waste.

## Source

Cloud FinOps Skill by OptimNow (https://optimnow.io). Licensed CC BY-SA 4.0.
Source: https://github.com/OptimNow/cloud-finops-skills
EOF
}


install_gemini() {
  local outdir="${DEST_OVERRIDE:-$PWD}/dist/gemini"
  local instructions_path="$outdir/instructions.md"
  local knowledge_dir="$outdir/knowledge"

  if [[ -n "$DRY_RUN" ]]; then
    info "DRY-RUN would write: $instructions_path"
    info "DRY-RUN would write: $knowledge_dir/*.md"
    return
  fi

  # Wipe any previous build so renamed/removed references don't linger
  rm -rf "$knowledge_dir"
  mkdir -p "$knowledge_dir"
  # Gemini always uses the grouped knowledge layout, so the routing contract
  # must point at the grouped filenames - not the per-reference names that
  # the ChatGPT default uses.
  build_grouped_instructions > "$instructions_path"
  build_gemini_grouped_knowledge "$knowledge_dir"

  local file_count
  file_count=$(find "$knowledge_dir" -maxdepth 1 -name "*.md" | wc -l | tr -d ' ')
  ok "Gemini Gems: instructions -> $instructions_path"
  ok "Gemini Gems: $file_count grouped knowledge files -> $knowledge_dir/"
  dim "  Manual upload: https://gemini.google.com/gems/ - paste instructions, upload knowledge files."
  dim "  Note: references are grouped by domain to fit Gemini's tighter file cap."
}

build_gemini_grouped_knowledge() {
  local outdir="$1"
  local refs="$SRC_DIR/cloud-finops/references"

  # cat_required <output> <input1> [<input2> ...]
  # Concatenates the inputs into the output. Fails loudly if any input is
  # missing - silent omission would let a renamed reference disappear from a
  # grouped artefact without the maintainer noticing, defeating the purpose
  # of the grouped build as a fallback path for capped uploads.
  cat_required() {
    local out="$1"; shift
    local f
    for f in "$@"; do
      if [[ ! -f "$f" ]]; then
        err "build_gemini_grouped_knowledge: missing input '$f' for $(basename "$out")"
        return 1
      fi
    done
    cat "$@" > "$out"
  }

  cat_required "$outdir/aws.md" \
    "$refs/finops-aws.md" "$refs/finops-bedrock.md"
  cat_required "$outdir/azure.md" \
    "$refs/finops-azure.md" "$refs/finops-azure-openai.md"
  cat_required "$outdir/gcp.md" \
    "$refs/finops-gcp.md" "$refs/finops-vertexai.md"
  cat_required "$outdir/ai.md" \
    "$refs/finops-for-ai.md" "$refs/finops-anthropic.md" "$refs/finops-ai-dev-tools.md" \
    "$refs/finops-genai-capacity.md" "$refs/finops-ai-value-management.md" \
    "$refs/finops-ai-self-hosted-vs-managed.md"
  cat_required "$outdir/data-platforms.md" \
    "$refs/finops-databricks.md" "$refs/finops-fabric.md" "$refs/finops-snowflake.md"
  cat_required "$outdir/oci.md" \
    "$refs/finops-oci.md"
  cat_required "$outdir/cross-cutting.md" \
    "$refs/finops-framework.md" "$refs/finops-tagging.md" "$refs/finops-sam.md" \
    "$refs/finops-itam.md" "$refs/greenops-cloud-carbon.md" \
    "$refs/finops-kubernetes.md" "$refs/finops-waste-detection-playbooks.md"
  cat_required "$outdir/finops-discipline.md" \
    "$refs/finops-anomaly-management.md" "$refs/finops-allocation-showback.md" \
    "$refs/finops-chargeback.md" "$refs/finops-onboarding-workloads.md"
  cat_required "$outdir/methodology.md" \
    "$refs/optimnow-methodology.md"

  # Playbooks bundle: SKILL.md routes named-pattern queries to
  # playbooks/<slug>.md, so the grouped artefact must include the
  # playbook content too. Bundled into a single playbooks.md to keep
  # the grouped layout's 1-bundle-per-domain shape.
  local playbooks="$SRC_DIR/cloud-finops/playbooks"
  if [[ -d "$playbooks" ]]; then
    {
      echo "# Cloud FinOps Playbooks Bundle"
      echo
      echo "Each section below is a self-contained named-pattern runbook."
      echo "When SKILL.md routes a 'named waste pattern X' query to"
      echo "\`playbooks/<slug>.md\`, look up the section here whose title"
      echo "matches the slug."
      echo
      for pb in "$playbooks"/*.md; do
        local pb_name
        pb_name=$(basename "$pb")
        # README.md is the format / contributor guide, not a runbook
        [[ "$pb_name" == "README.md" ]] && continue
        echo "---"
        echo
        echo "## playbook: ${pb_name%.md}"
        echo
        cat "$pb"
        echo
      done
    } > "$outdir/playbooks.md"
  fi
}

install_gemini_cli() {
  local target
  if [[ -n "$DEST_OVERRIDE" ]]; then
    target="$DEST_OVERRIDE/$SKILL_NAME"
  else
    target="$HOME/.gemini/skills/$SKILL_NAME"
  fi
  do_copy_dir "$SRC_DIR/cloud-finops" "$target"
  ok "Gemini CLI: skill copied -> $target"
}

install_codex() {
  local default_target="${DEST_OVERRIDE:-$PWD}/AGENTS.md"
  local target="$default_target"
  if [[ -f "$target" && -z "$DRY_RUN" ]]; then
    warn "Codex: $target already exists. Writing to AGENTS-cloud-finops.md instead."
    target="${DEST_OVERRIDE:-$PWD}/AGENTS-cloud-finops.md"
  fi
  do_write "$target" build_codex_agents_md
  ok "Codex CLI: agent context written -> $target"
  dim "  Codex reads AGENTS.md from project root. If AGENTS-cloud-finops.md was used,"
  dim "  manually merge into your existing AGENTS.md (or rename when ready)."
  dim "  An MCP server (planned) will be the cleaner cross-agent path - this is the"
  dim "  interim option until then."
}

build_codex_agents_md() {
  cat <<'EOF'
# Cloud FinOps Skill - Codex CLI context

This file injects Cloud FinOps expertise into your Codex CLI session. Source:
https://github.com/OptimNow/cloud-finops-skills

EOF
  write_concat_body
}

install_aider() {
  local default_target="${DEST_OVERRIDE:-$PWD}/CONVENTIONS.md"
  local target="$default_target"
  if [[ -f "$target" && -z "$DRY_RUN" ]]; then
    warn "Aider: $target already exists. Writing to CONVENTIONS-cloud-finops.md instead."
    target="${DEST_OVERRIDE:-$PWD}/CONVENTIONS-cloud-finops.md"
  fi
  do_write "$target" build_aider_conventions
  ok "Aider: conventions written -> $target"
  dim "  Aider auto-reads CONVENTIONS.md. For more references, add via --read flags:"
  dim "    aider --read cloud-finops/references/finops-bedrock.md ..."
}

build_aider_conventions() {
  cat <<'EOF'
# Cloud FinOps Conventions

When asked about cloud cost, AI cost, SaaS cost, commitment strategy, rightsizing,
tagging, or FinOps practice questions, apply the guidance below. Default coverage
is the four most general areas (AWS, Azure, GCP, AI). For richer coverage on
Bedrock, Vertex AI, Databricks, Microsoft Fabric, Snowflake, OCI, etc., add the
specific references via `aider --read cloud-finops/references/<file>.md`.

EOF
  strip_frontmatter "$SRC_DIR/cloud-finops/SKILL.md"
  for ref in finops-aws.md finops-azure.md finops-gcp.md finops-for-ai.md; do
    if [[ -f "$SRC_DIR/cloud-finops/references/$ref" ]]; then
      echo
      echo "---"
      echo
      echo "## Reference: $ref"
      echo
      cat "$SRC_DIR/cloud-finops/references/$ref"
    fi
  done
}

install_copilot() {
  local target="${DEST_OVERRIDE:-$PWD}/.github/copilot-instructions.md"
  do_write "$target" build_copilot_instructions
  ok "Copilot: instructions written -> $target"
  warn "Copilot fit is limited - the instruction surface is shallow. The skill informs"
  warn "  code-suggestion context but won't power deep FinOps Q&A like Claude / Cursor do."
}

build_copilot_instructions() {
  cat <<'EOF'
# Cloud FinOps - Copilot Custom Instructions

When suggesting code or answering questions involving cloud cost, AI inference cost,
commitment strategy (Reserved Instances, Savings Plans, CUDs), rightsizing, tagging,
or FinOps practices, apply the guidance below.

EOF
  strip_frontmatter "$SRC_DIR/cloud-finops/SKILL.md"
  echo
  echo "## Available reference files (for deeper context, see source repo)"
  echo
  for ref in "$SRC_DIR/cloud-finops/references"/*.md; do
    local fname
    fname=$(basename "$ref")
    local desc
    desc=$(awk '/^>/{sub(/^> ?/,""); print; exit}' "$ref" | head -c 180)
    echo "- \`$fname\` - $desc"
  done
  echo
  echo "Source: https://github.com/OptimNow/cloud-finops-skills"
}

install_kiro() {
  local target="${DEST_OVERRIDE:-$PWD}/.kiro/powers/$SKILL_NAME"
  do_copy_dir "$SRC_DIR/cloud-finops" "$target"
  ok "Kiro IDE: power copied -> $target"
  dim "  Kiro reads POWER.md as the entry point."
}

install_mcp() {
  # Print install hint + per-client config snippets. We intentionally do NOT
  # run pip from a shell installer.
  printf "${C_BOLD}Cloud FinOps MCP server${C_RESET}\n"
  dim "  Adds six queryable tools across two surfaces:"
  dim "    references: list_references / get_reference / find_references"
  dim "                (faceted by FinOps Capability/Phase frontmatter)"
  dim "    playbooks:  list_playbooks / get_playbook / find_playbooks"
  dim "                (faceted by scope / service / waste_category / confidence)"
  printf "\n"
  ok "Step 1 - install the server (Python 3.10+):"
  printf "    pip install cloud-finops-mcp\n"
  printf "    ${C_DIM}# or, no install: ${C_RESET}uvx cloud-finops-mcp\n"
  printf "\n"
  ok "Step 2 - add to your MCP client config:"
  printf "\n"
  printf "  ${C_BOLD}Claude Code${C_RESET}  (.mcp.json at project root, or ~/.claude/mcp.json):\n"
  cat <<'EOF'
    {
      "mcpServers": {
        "cloud-finops": { "command": "cloud-finops-mcp" }
      }
    }
EOF
  printf "\n  ${C_BOLD}Cursor${C_RESET}  (~/.cursor/mcp.json):\n"
  cat <<'EOF'
    {
      "mcpServers": {
        "cloud-finops": { "command": "cloud-finops-mcp" }
      }
    }
EOF
  printf "\n  ${C_BOLD}Codex CLI${C_RESET}  (~/.codex/config.toml):\n"
  cat <<'EOF'
    [mcp_servers.cloud-finops]
    command = "cloud-finops-mcp"
EOF
  printf "\n  ${C_BOLD}Windsurf${C_RESET}  (~/.windsurf/mcp.json):\n"
  cat <<'EOF'
    {
      "mcpServers": {
        "cloud-finops": { "command": "cloud-finops-mcp" }
      }
    }
EOF
  printf "\n"
  ok "Step 3 - restart your client. Verify:"
  dim "    Claude Code: /mcp"
  dim "    Cursor: chat panel will list cloud-finops as an available MCP"
  dim "    Codex CLI: codex mcp list"
  printf "\n"
  dim "  PyPI:    https://pypi.org/project/cloud-finops-mcp/"
  dim "  Source:  https://github.com/OptimNow/cloud-finops-skills/tree/main/mcp_server"
}

install_tool() {
  case "$1" in
    claude-code)     install_claude_code ;;
    claude-projects) install_claude_projects ;;
    cursor)          install_cursor ;;
    windsurf)        install_windsurf ;;
    chatgpt)         install_chatgpt ;;
    gemini)          install_gemini ;;
    gemini-cli)      install_gemini_cli ;;
    codex)           install_codex ;;
    aider)           install_aider ;;
    copilot)         install_copilot ;;
    kiro)            install_kiro ;;
    mcp)             install_mcp ;;
    *)               err "Unknown tool: $1"; return 1 ;;
  esac
}

list_tools() {
  echo "Supported tools:"
  for t in "${ALL_TOOLS[@]}"; do
    echo "  - $t"
  done
}

main() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --tool)     TOOL="${2:?--tool requires a value}"; shift 2 ;;
      --dry-run)  DRY_RUN=1; shift ;;
      --user)     USER_LEVEL=1; shift ;;
      --grouped)  GROUPED=1; shift ;;
      --dest)     DEST_OVERRIDE="${2:?--dest requires a value}"; shift 2 ;;
      --dir)      DEST_OVERRIDE="${2:?--dir requires a value}"; shift 2 ;;  # legacy alias
      --list)     list_tools; exit 0 ;;
      --help|-h)  usage ;;
      *)          err "Unknown option: $1"; echo; usage ;;
    esac
  done

  resolve_source

  printf "\n${C_BOLD}Cloud FinOps Skill - cross-tool installer${C_RESET}\n"
  dim "  Source: $SRC_DIR/cloud-finops/"
  printf "\n"

  local selected=()
  if [[ -n "$TOOL" && "$TOOL" != "all" ]]; then
    local valid=false t
    for t in "${ALL_TOOLS[@]}"; do
      [[ "$t" == "$TOOL" ]] && valid=true && break
    done
    if ! $valid; then
      err "Unknown tool: $TOOL"
      list_tools
      exit 1
    fi
    selected=("$TOOL")
  elif [[ "$TOOL" == "all" ]]; then
    selected=("${ALL_TOOLS[@]}")
  else
    local t
    for t in "${ALL_TOOLS[@]}"; do
      if is_detected "$t" 2>/dev/null; then
        selected+=("$t")
        printf "  ${C_GREEN}[*]${C_RESET} %s detected\n" "$t"
      else
        printf "  ${C_DIM}[ ] %s not detected${C_RESET}\n" "$t"
      fi
    done
    if [[ ${#selected[@]} -eq 0 ]]; then
      printf "\n"
      warn "No tools auto-detected. Use --tool <name> or --tool all."
      dim "  Run --list to see supported tools."
      exit 0
    fi
    printf "\n"
  fi

  local t
  for t in "${selected[@]}"; do
    install_tool "$t"
  done

  printf "\n"
  ok "Done. Installed for: ${selected[*]}"
  dim "  Source: https://github.com/OptimNow/cloud-finops-skills (CC BY-SA 4.0)"
}

main "$@"
