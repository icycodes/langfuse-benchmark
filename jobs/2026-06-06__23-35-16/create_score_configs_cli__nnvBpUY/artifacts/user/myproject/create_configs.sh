#!/bin/bash
set -e

RUN_ID=$ZEALT_RUN_ID
LOG_FILE="/home/user/myproject/output.log"
> "$LOG_FILE"

# 1. NUMERIC
NAME1="quality-score-${RUN_ID}"
RES1=$(langfuse api score-configs create --name "$NAME1" --dataType NUMERIC --minValue 0 --maxValue 10 --json)
ID1=$(echo "$RES1" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "ScoreConfig: ${NAME1}=${ID1}" >> "$LOG_FILE"

# 2. CATEGORICAL
NAME2="feedback-sentiment-${RUN_ID}"
RES2=$(langfuse api score-configs create --name "$NAME2" --dataType CATEGORICAL --categories '[{"label":"positive","value":1},{"label":"neutral","value":0},{"label":"negative","value":-1}]' --json)
ID2=$(echo "$RES2" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "ScoreConfig: ${NAME2}=${ID2}" >> "$LOG_FILE"

# 3. BOOLEAN
NAME3="is-relevant-${RUN_ID}"
RES3=$(langfuse api score-configs create --name "$NAME3" --dataType BOOLEAN --json)
ID3=$(echo "$RES3" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "ScoreConfig: ${NAME3}=${ID3}" >> "$LOG_FILE"

echo "Done"
