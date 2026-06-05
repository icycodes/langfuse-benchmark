#!/usr/bin/env bash
# Langfuse prompt promotion workflow: staging -> production
# Usage: bash promote_prompt.sh
# Reads: ZEALT_RUN_ID, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL / LANGFUSE_HOST

set -euo pipefail

# ---------------------------------------------------------------------------
# 1. Resolve configuration
# ---------------------------------------------------------------------------
RUN_ID="${ZEALT_RUN_ID:?ZEALT_RUN_ID env var is required}"
PUBLIC_KEY="${LANGFUSE_PUBLIC_KEY:?LANGFUSE_PUBLIC_KEY env var is required}"
SECRET_KEY="${LANGFUSE_SECRET_KEY:?LANGFUSE_SECRET_KEY env var is required}"
BASE_URL="${LANGFUSE_BASE_URL:-${LANGFUSE_HOST:-https://cloud.langfuse.com}}"
BASE_URL="${BASE_URL%/}"   # remove trailing slash

PROMPT_NAME="movie-critic-${RUN_ID}"
LOG_FILE="/home/user/myproject/output.log"
AUTH="${PUBLIC_KEY}:${SECRET_KEY}"

echo "=== Langfuse Prompt Promotion Workflow ==="
echo "Prompt name : ${PROMPT_NAME}"
echo "Langfuse URL: ${BASE_URL}"

# ---------------------------------------------------------------------------
# Helper: REST helpers (exit non-zero on HTTP errors via -f)
# ---------------------------------------------------------------------------
lf_post() {
  local path="$1"
  local body="$2"
  curl -sS -f \
    -X POST \
    -u "${AUTH}" \
    -H "Content-Type: application/json" \
    --data "${body}" \
    "${BASE_URL}${path}"
}

lf_patch() {
  local path="$1"
  local body="$2"
  curl -sS -f \
    -X PATCH \
    -u "${AUTH}" \
    -H "Content-Type: application/json" \
    --data "${body}" \
    "${BASE_URL}${path}"
}

url_encode() {
  python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$1"
}

# ---------------------------------------------------------------------------
# 2. Create Version 1  — label: staging
#    Content: As a {{criticlevel}} critic, do you like {{movie}}?
# ---------------------------------------------------------------------------
echo ""
echo "--- Creating Version 1 (staging) ---"
V1_RESPONSE=$(lf_post "/api/public/v2/prompts" "$(cat <<EOF
{
  "name": "${PROMPT_NAME}",
  "type": "text",
  "prompt": "As a {{criticlevel}} critic, do you like {{movie}}?",
  "labels": ["staging"]
}
EOF
)")
echo "Response: ${V1_RESPONSE}"
V1_VERSION=$(echo "${V1_RESPONSE}" | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])")
echo "Version 1 number: ${V1_VERSION}"

# ---------------------------------------------------------------------------
# 3. Create Version 2  — label: staging (Langfuse moves "staging" to this version)
#    Content: As an {{criticlevel}} film critic, do you enjoy {{movie}}?
# ---------------------------------------------------------------------------
echo ""
echo "--- Creating Version 2 (staging) ---"
V2_RESPONSE=$(lf_post "/api/public/v2/prompts" "$(cat <<EOF
{
  "name": "${PROMPT_NAME}",
  "type": "text",
  "prompt": "As an {{criticlevel}} film critic, do you enjoy {{movie}}?",
  "labels": ["staging"]
}
EOF
)")
echo "Response: ${V2_RESPONSE}"
V2_VERSION=$(echo "${V2_RESPONSE}" | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])")
echo "Version 2 number: ${V2_VERSION}"

# ---------------------------------------------------------------------------
# 4. Promote Version 2 to production
#    PATCH assigns ["staging","production"] to version 2.
#    - "production" is newly added to version 2.
#    - "staging" label was already on version 2 (created with it).
#    NOTE: Langfuse labels are exclusive per prompt — assigning "production" to
#    version 2 automatically removes it from any prior version.
# ---------------------------------------------------------------------------
echo ""
echo "--- Promoting Version 2 to production ---"
ENCODED_NAME=$(url_encode "${PROMPT_NAME}")
PROMOTE_RESPONSE=$(lf_patch "/api/public/v2/prompts/${ENCODED_NAME}/versions/${V2_VERSION}" \
  '{"newLabels": ["staging", "production"]}')
echo "Response: ${PROMOTE_RESPONSE}"

# Confirm labels
V2_LABELS=$(echo "${PROMOTE_RESPONSE}" | python3 -c "import sys,json; print(json.load(sys.stdin)['labels'])")
echo "Version 2 labels after promotion: ${V2_LABELS}"

# ---------------------------------------------------------------------------
# 5. Write the structured log file
# ---------------------------------------------------------------------------
echo ""
echo "--- Writing log file: ${LOG_FILE} ---"
mkdir -p "$(dirname "${LOG_FILE}")"
cat > "${LOG_FILE}" <<EOF
Prompt name: ${PROMPT_NAME}
Promoted version: ${V2_VERSION}
EOF
echo "Log written:"
cat "${LOG_FILE}"

echo ""
echo "=== Workflow complete ==="
