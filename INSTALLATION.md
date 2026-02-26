# Installation Guide

## Prerequisites

- Claude Code, or another agent that supports the Agent Skills specification
- Git

---

## Option 1: One-liner install (recommended)

```bash
curl -sL https://raw.githubusercontent.com/OptimNow/cloud-finops-skills/main/install.sh | bash
```

This downloads the skill into the current directory. To install into a specific project:

```bash
curl -sL https://raw.githubusercontent.com/OptimNow/cloud-finops-skills/main/install.sh | bash -s -- --dir ~/my-project
```

The script clones the repo, copies the `cloud-finops/` folder, verifies the installation,
and cleans up. Works on Mac, Linux, and WSL.

---

## Option 2: Manual install (Claude Code)

```bash
# Clone the repository
git clone https://github.com/OptimNow/cloud-finops-skills.git

# Copy the skill folder to your project or skills directory
cp -r cloud-finops-skills/cloud-finops ~/.claude/skills/

# Verify structure
ls ~/.claude/skills/cloud-finops/
# Should show: SKILL.md, references/
```

After copying, Claude Code will automatically detect the skill. Test it:

```
"What are the first steps to manage AI inference costs?"
"How do I choose between Reserved Instances and Savings Plans on AWS?"
"We have zero tagging compliance - where do we start?"
```

---

## Option 3: Claude.ai Project (manual context injection)

If you are using Claude.ai without Claude Code, add the skill content as project knowledge:

1. Open your Claude.ai Project
2. Go to Project Knowledge → Add content
3. Add `cloud-finops/SKILL.md`
4. Add each file from `cloud-finops/references/` as separate knowledge documents
5. The agent will reference them when relevant queries are made

---

## Option 4: Agent Smith integration

The skill is designed to integrate directly with OptimNow's Agent Smith.

```python
# In your Agent Smith configuration, add to the skills loader:
skill_loader.load_skill("cloud-finops")
```

Refer to the Agent Smith documentation for skill configuration details.

---

## Option 5: API integration (system prompt injection)

For direct API use, concatenate the skill files into your system prompt:

```python
import os

def load_cloud_finops_skill(skill_dir: str) -> str:
    skill_md = open(f"{skill_dir}/SKILL.md").read()
    references = []
    ref_dir = f"{skill_dir}/references"
    for filename in sorted(os.listdir(ref_dir)):
        if filename.endswith(".md"):
            content = open(f"{ref_dir}/{filename}").read()
            references.append(f"## {filename}\n\n{content}")
    return skill_md + "\n\n---\n\n" + "\n\n---\n\n".join(references)

system_prompt = load_cloud_finops_skill("./cloud-finops")
```

For token efficiency, load only the domain reference files relevant to your use case
rather than all references at once.

---

## Updating the skill

```bash
# Pull latest changes
cd cloud-finops-skills
git pull origin main

# Re-copy to your skills directory
cp -r cloud-finops ~/.claude/skills/
```

Or re-run the one-liner installer - it will replace the existing installation automatically.

---

## Adding Azure content from your local repo

The `finops-azure.md` file is a skeleton. To populate it from your local Azure course:

```bash
# Review the placeholder and identify which sections to fill
cat cloud-finops/references/finops-azure.md

# Copy or adapt content from your Azure FinOps course repo
# ~/github/azure-finops-master → cloud-finops/references/finops-azure.md

# Commit the updated file
git add cloud-finops/references/finops-azure.md
git commit -m "Populate Azure reference from azure-finops-master content"
git push
```

---

## Troubleshooting

**Skill not activating:** Check that the YAML frontmatter in `SKILL.md` is valid.
The `name` and `description` fields are required.

**References not loading:** Ensure all files in `references/` are readable and correctly
named. The SKILL.md router references files by exact filename.

**Token budget exceeded:** Load only the relevant domain reference file rather than all
references. For most queries, one reference file + `optimnow-methodology.md` is sufficient.
