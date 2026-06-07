#!/bin/bash
set -e

RESPONSE=$(langfuse api prompts create \
  --name "welcome-email-${ZEALT_RUN_ID}" \
  --prompt "Hello {{name}}, welcome to {{service}}! Your plan is {{plan}}." \
  --config '{"model":"gpt-4o-mini","temperature":0.5}' \
  --labels '["production","staging"]' \
  --tags '["onboarding"]' \
  --commitMessage "Initial onboarding template" \
  --type text \
  --json)

NAME=$(echo "$RESPONSE" | jq -r '.body.name')
VERSION=$(echo "$RESPONSE" | jq -r '.body.version')

echo "Prompt created: name=$NAME version=$VERSION" > /home/user/langfuse-task/output.log
cat /home/user/langfuse-task/output.log
