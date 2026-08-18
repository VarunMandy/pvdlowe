#!/usr/bin/env bash
# End-to-end: build the image, push it, submit the job.
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
BUCKET="${BUCKET:?set BUCKET (no gs:// prefix)}"
REGION="${REGION:-us-central1}"
REPO="${REPO:-pvdlowe}"
TAG="${TAG:-0.1.0}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/pvdlowe:${TAG}"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"

gcloud artifacts repositories describe "${REPO}" \
    --location="${REGION}" --project="${PROJECT_ID}" >/dev/null 2>&1 || \
  gcloud artifacts repositories create "${REPO}" \
    --repository-format=docker --location="${REGION}" \
    --project="${PROJECT_ID}" \
    --description="pvdlowe Low-E coating framework"

echo "building ${IMAGE}"
gcloud builds submit --tag "${IMAGE}" --project="${PROJECT_ID}" --timeout=20m .

CONFIG="$(mktemp)"
sed -e "s|PROJECT_ID|${PROJECT_ID}|g" \
    -e "s|BUCKET/pvdlowe/runs/latest|${BUCKET}/pvdlowe/runs/${RUN_ID}|g" \
    -e "s|pvdlowe:0.1.0|pvdlowe:${TAG}|g" \
    vertex/custom_job.yaml > "${CONFIG}"

gcloud ai custom-jobs create \
  --region="${REGION}" --project="${PROJECT_ID}" \
  --display-name="pvdlowe-${RUN_ID}" \
  --config="${CONFIG}"

echo
echo "results will appear under gs://${BUCKET}/pvdlowe/runs/${RUN_ID}/"
echo "stream logs with:  gcloud ai custom-jobs stream-logs <JOB_ID> --region=${REGION}"
