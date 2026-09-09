# Image for the hosted connector on Fly.io (`fly deploy` from the repo root).
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
COPY .claude-plugin/plugin.json .claude-plugin/plugin.json
COPY skills/cloud-finops/references/ skills/cloud-finops/references/
COPY skills/cloud-finops/playbooks/ skills/cloud-finops/playbooks/
COPY mcp_server/ mcp_server/

RUN python mcp_server/scripts/sync_references.py \
 && pip install ./mcp_server \
 && python -c "import cloud_finops_mcp.metadata as m; n = len(list(m.DATA_DIR.glob('*.md'))); assert n >= 30, n; print('bundled references:', n)" \
 && cat mcp_server/src/cloud_finops_mcp/data/content_version.txt

ENV PORT=8080
EXPOSE 8080

# Streamable HTTP on 0.0.0.0:$PORT, route /mcp, stateless (see run_http).
CMD ["cloud-finops-mcp", "--transport", "http"]
