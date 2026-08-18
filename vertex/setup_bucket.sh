#!/usr/bin/env bash
# Create and configure the GCS bucket for pvdlowe. Run from Cloud Shell.
#
#   export PROJECT_ID="your-project"
#   ./vertex/setup_bucket.sh
#
# Idempotent: safe to re-run. Existing buckets and bindings are left alone.

set -euo pipefail

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-us-central1}"
# Bucket names are globally unique across all of GCS, so prefix with the
# project ID rather than trying to invent something unclaimed.
BUCKET="${BUCKET:-${PROJECT_ID}-pvdlowe}"

if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "(unset)" ]]; then
  echo "error: no project set. Run: gcloud config set project PROJECT_ID" >&2
  exit 1
fi

echo "project ${PROJECT_ID} | region ${REGION} | bucket gs://${BUCKET}"
echo

# --- enable the APIs the bucket and jobs depend on ----------------------
echo "enabling APIs (no-op if already enabled)"
gcloud services enable \
    storage.googleapis.com \
    aiplatform.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    --project="${PROJECT_ID}"

# --- create the bucket --------------------------------------------------
if gcloud storage buckets describe "gs://${BUCKET}" >/dev/null 2>&1; then
  echo "bucket already exists, skipping creation"
else
  echo "creating gs://${BUCKET}"
  # Same region as the Vertex jobs: a bucket in a different region works but
  # bills cross-region egress on every read, and these jobs read the MP cache
  # on every start.
  gcloud storage buckets create "gs://${BUCKET}" \
      --project="${PROJECT_ID}" \
      --location="${REGION}" \
      --default-storage-class=STANDARD \
      --uniform-bucket-level-access \
      --public-access-prevention
fi

# --- versioning ---------------------------------------------------------
# Results are single-digit MB and the framework's whole point is knowing
# where a number came from. Versioning means an overwritten result file is
# recoverable rather than gone.
echo "enabling object versioning"
gcloud storage buckets update "gs://${BUCKET}" --versioning

# --- lifecycle ----------------------------------------------------------
# Keep current objects forever; expire non-current versions after 90 days so
# versioning does not accumulate cost indefinitely.
LIFECYCLE="$(mktemp)"
cat > "${LIFECYCLE}" <<'JSON'
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {"daysSinceNoncurrentTime": 90, "isLive": false}
    },
    {
      "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
      "condition": {"age": 180, "matchesPrefix": ["pvdlowe/runs/"]}
    }
  ]
}
JSON
gcloud storage buckets update "gs://${BUCKET}" \
    --lifecycle-file="${LIFECYCLE}"
rm -f "${LIFECYCLE}"

# --- folder layout ------------------------------------------------------
# GCS has no real directories, but placeholder objects make the intended
# layout visible in the console and stop people inventing their own.
echo "creating layout"
for prefix in source runs mp-cache dft; do
  printf 'pvdlowe %s\n' "${prefix}" \
    | gcloud storage cp - "gs://${BUCKET}/pvdlowe/${prefix}/.keep" --quiet
done

# --- IAM for the Vertex job service account -----------------------------
PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_ID}" \
    --format='value(projectNumber)')"
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "granting objectAdmin on the bucket to ${COMPUTE_SA}"
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role=roles/storage.objectAdmin \
    --quiet

# --- upload the source, if it is here -----------------------------------
if [[ -f pvdlowe.tar.gz ]]; then
  echo "uploading pvdlowe.tar.gz"
  gcloud storage cp pvdlowe.tar.gz "gs://${BUCKET}/pvdlowe/source/"
elif [[ -f pyproject.toml && -d pvdlowe ]]; then
  echo "packing and uploading the working tree"
  tar -czf /tmp/pvdlowe.tar.gz --exclude='__pycache__' --exclude='.git' .
  gcloud storage cp /tmp/pvdlowe.tar.gz "gs://${BUCKET}/pvdlowe/source/"
  rm -f /tmp/pvdlowe.tar.gz
else
  echo "no source archive found here; upload it later with:"
  echo "  gcloud storage cp pvdlowe.tar.gz gs://${BUCKET}/pvdlowe/source/"
fi

# --- verify -------------------------------------------------------------
echo
echo "layout:"
gcloud storage ls -r "gs://${BUCKET}/pvdlowe/**" | sed 's/^/  /'
echo
echo "config:"
gcloud storage buckets describe "gs://${BUCKET}" \
    --format='value(location, storageClass, versioning.enabled, iamConfiguration.uniformBucketLevelAccess.enabled)' \
  | awk '{print "  location="$1" class="$2" versioning="$3" uniform_access="$4}'

cat <<EOF

done. Add these to your shell so the other scripts pick them up:

  export PROJECT_ID="${PROJECT_ID}"
  export REGION="${REGION}"
  export BUCKET="${BUCKET}"

Next:
  ./vertex/submit.sh                       # build image and run a batch job
  gcloud storage ls gs://${BUCKET}/pvdlowe/runs/
EOF
