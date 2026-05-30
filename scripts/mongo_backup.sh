#!/usr/bin/env bash
# Simple MongoDB backup script using mongodump
# Requires: mongodump in PATH. Upload to S3 if AWS CLI and AWS env vars are configured.
set -euo pipefail

TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
OUT_DIR="/tmp/mongo-backup-$TIMESTAMP"
MONGO_URI=${MONGO_URI:-"mongodb://localhost:27017"}

mkdir -p "$OUT_DIR"

echo "Starting mongodump to $OUT_DIR..."
mongodump --uri="$MONGO_URI" --out "$OUT_DIR"

if [ -n "${AWS_S3_BUCKET:-}" ]; then
  if ! command -v aws >/dev/null 2>&1; then
    echo "AWS CLI not found; skipping upload to S3"
    exit 0
  fi
  ARCHIVE="mongo-backup-$TIMESTAMP.tar.gz"
  tar -czf "/tmp/$ARCHIVE" -C "$OUT_DIR" .
  echo "Uploading /tmp/$ARCHIVE to s3://$AWS_S3_BUCKET/"
  aws s3 cp "/tmp/$ARCHIVE" "s3://$AWS_S3_BUCKET/" --acl private
  echo "Upload complete"
fi

echo "Backup finished: $OUT_DIR"