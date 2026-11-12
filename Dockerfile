# Image for the hosted connector on Fly.io. The release workflow builds it from
# each tagged commit (the `deploy-hosted` job of auto-tag-on-plugin-bump.yml);
# `fly deploy` from the repo root builds the same image by hand.
#
# Builds from this checkout rather than from the PyPI wheel so that a
# connector-URL or content change ships on the next deploy without waiting
# for a release. The bundled data is synced from skills/ at build time by the
# same script the wheel build runs, and the build fails if it comes out short.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# plugin.json is the version holder the content stamp reads.
COPY plugins/cloud-finops/.claude-plugin/plugin.json plugins/cloud-finops/.claude-plugin/plugin.json
COPY plugins/cloud-finops/skills/cloud-finops/references/ plugins/cloud-finops/skills/cloud-finops/references/
COPY plugins/cloud-finops/skills/cloud-finops/playbooks/ plugins/cloud-finops/skills/cloud-finops/playbooks/
COPY mcp_server/ mcp_server/

# serverInfo.version is the installed package's version, which pip reads from
# mcp_server/pyproject.toml. A release bumps plugin.json; pyproject.toml is
# bumped beside it by hand and nothing fails when it is forgotten, because the
# release workflow rewrites the field before it builds the wheel. This image is
# not built from that wheel, so pin the field here too, then check what pip
# installed: the server announces plugin.json's version whoever builds the image.
RUN python mcp_server/scripts/sync_references.py \
 && python mcp_server/scripts/pin_version.py \
 && pip install ./mcp_server \
 && python mcp_server/scripts/pin_version.py --verify-installed \
 && python -c "import cloud_finops_mcp.metadata as m; n = len(list(m.DATA_DIR.glob('*.md'))); assert n >= 30, n; print('bundled references:', n)" \
 && cat mcp_server/src/cloud_finops_mcp/data/content_version.txt

ENV PORT=8080
EXPOSE 8080

# Streamable HTTP on 0.0.0.0:$PORT, route /mcp, stateless (see run_http).
CMD ["cloud-finops-mcp", "--transport", "http"]
