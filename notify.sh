#!/bin/bash

TOKEN="$1"
URLHASH="$2"
FILEPATH="$3"
EXPIRY="$4"

# Extract filename only if needed
# FILENAME="$(basename "$FILEPATH")"

# Job ID could be embedded in filename or directory
# Example: storage/downloads/{job_id}/file.opus
# JOB_ID="$(basename "$(dirname "$FILEPATH")")"
# echo "$FILEPATH"

/usr/bin/redis-cli -h redis -p 6379 HSET "job:$TOKEN" \
    status completed \
    audio_path "$FILEPATH" 

/usr/bin/redis-cli -h redis -p 6379 HSET "$URLHASH"\
    token "$TOKEN"\
    # audio_path "$FILEPATH"

## It is configured at /api/vi/jobs
# redis-cli EXPIRE "$URLHASH" 86400

/usr/bin/redis-cli -h redis -p 6379 HSET FILE-CLEAN-UP\
    "$FILEPATH" "$EXPIRY"