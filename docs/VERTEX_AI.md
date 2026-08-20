# Running pvdlowe on Google Cloud Vertex AI

## Does this belong on Vertex at all?

Worth being clear before you spend budget. `pvdlowe` is CPU-bound scientific
Python — scipy quadrature, vectorised numpy, no training, no model artifact,
no inference. Of the Vertex surfaces, only two are useful:

| Surface | Use it? | Why |
|---|---|---|
| **Workbench** | Yes | Managed JupyterLab VM. The natural home for interactive work. |
| **Custom Jobs** | Yes | Batch runner for the expensive sweeps. Parallelises well. |
| Pipelines | No | Nothing here is a multi-step DAG worth orchestrating. |
| Endpoints / Model Registry | No | There is no model to serve. |
| Any GPU | **No** | Zero GPU code paths. It will idle and bill you. |

If you only want to run the analyses once, a plain Compute Engine VM is
cheaper and simpler. Use Vertex if that's where your SGRI compute allocation
and IAM already live, or if you want the job history and log retention.

---

## Part 1 — Interactive: Workbench

### 1.1 Project setup

```bash
export PROJECT_ID="your-project"
export REGION="us-central1"
export BUCKET="your-bucket"          # no gs:// prefix

gcloud config set project "${PROJECT_ID}"
gcloud services enable \
    aiplatform.googleapis.com \
    notebooks.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    storage.googleapis.com

gcloud storage buckets create "gs://${BUCKET}" --location="${REGION}"
```

### 1.2 Create the instance

```bash
gcloud workbench instances create pvdlowe-dev \
    --location="${REGION}-a" \
    --machine-type=n2-standard-8 \
    --metadata=idle-shutdown-seconds=3600
```

`n2-standard-8` (8 vCPU / 32 GB) is deliberate: the parallel silver curve
scales to seven workers and nothing else in the package is parallel, so
larger machines buy nothing. **Set the idle shutdown** — a forgotten
Workbench instance is the most common way to burn a research budget.

Peak memory is under 1 GB, so RAM is never the constraint.

### 1.3 Upload and install

```bash
gcloud storage cp pvdlowe.tar.gz "gs://${BUCKET}/"
```

Open JupyterLab from the Workbench console, then in a terminal:

```bash
gcloud storage cp gs://${BUCKET}/pvdlowe.tar.gz .
tar -xzf pvdlowe.tar.gz && cd lowe
pip install -e .
python tests/run_tests.py          # expect: 68 passed, 0 failed
```

If the tests pass, the physics survived the trip. If they don't, stop — a
failure here means a dependency version has changed the numerics, not that
the tests are flaky.

The Workbench base image already carries numpy, scipy and pandas at
compatible versions; `pyyaml` and `openpyxl` are usually present too. Nothing
needs pinning, unlike the IG-LLM work — the dependency surface here is four
packages with loose lower bounds.

### 1.4 Verify and run

```bash
python -m pvdlowe validate           # model vs literature + consistency
python -m pvdlowe evaluate           # candidate table
python -m pvdlowe check-weights      # the r = 0.996 correlation
python -m pvdlowe report -o gs_out/report.md
gcloud storage cp -r gs_out "gs://${BUCKET}/pvdlowe/"
```

For notebook work, the plotting helpers in `pvdlowe.report` render inline;
install matplotlib if the base image lacks it.

---

## Part 2 — Batch: Custom Jobs

Worth doing for the silver-reduction curve, which is the only genuinely
expensive analysis, and for any composition × thickness map.

### 2.1 Build and push the image

`Dockerfile` and `vertex/submit.sh` are in the repo. The Dockerfile runs the
test suite as a build step, so a broken image fails at build time rather than
producing wrong numbers in production.

```bash
export PROJECT_ID="your-project" BUCKET="your-bucket" REGION="us-central1"
./vertex/submit.sh
```

That script creates the Artifact Registry repo if needed, builds via Cloud
Build, stamps a timestamped run ID into the job config, and submits. To do it
by hand:

```bash
gcloud artifacts repositories create pvdlowe \
    --repository-format=docker --location="${REGION}"

IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/pvdlowe/pvdlowe:0.1.0"
gcloud builds submit --tag "${IMAGE}" --timeout=20m .

# edit vertex/custom_job.yaml to substitute PROJECT_ID and BUCKET
gcloud ai custom-jobs create \
    --region="${REGION}" \
    --display-name=pvdlowe-full \
    --config=vertex/custom_job.yaml
```

### 2.2 Monitor

```bash
gcloud ai custom-jobs list --region="${REGION}" --limit=5
gcloud ai custom-jobs stream-logs JOB_ID --region="${REGION}"
gcloud storage ls "gs://${BUCKET}/pvdlowe/runs/"
```

### 2.3 Individual tasks

```yaml
      args:
        - --output=gs://BUCKET/pvdlowe/runs/ema-variant
        - --task=silver
        - --mixing-model=ema
        - --workers=7
```

Tasks are `silver`, `microstructure`, `sweeps`, `candidates`, `validate`,
`all`. `--spec '{"T_vis": 0.75}'` relaxes the specification, which is worth
running: at T_vis ≥ 0.75 the Cu-rich compositions that currently fail come
into range, and the trade-off curve looks very different.

### 2.4 IAM

The job's service account (default: the Compute Engine default SA) needs
`roles/storage.objectAdmin` on the bucket:

```bash
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" \
    --format='value(projectNumber)')
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role=roles/storage.objectAdmin
```

---

## Part 3 — The Materials Project API

Stage-2 screening needs `MP_API_KEY` and network egress. Two wrinkles specific
to how the client is built.

**Store the key in Secret Manager, not the image.**

```bash
printf '%s' "$MP_API_KEY" | gcloud secrets create mp-api-key --data-file=-
gcloud secrets add-iam-policy-binding mp-api-key \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role=roles/secretmanager.secretAccessor
```

Custom Jobs don't inject secrets the way Cloud Run does, so fetch it in code:

```python
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
name = f"projects/{PROJECT_ID}/secrets/mp-api-key/versions/latest"
key = client.access_secret_version(name=name).payload.data.decode()
mp = MPClient(api_key=key)
```

**Warm the cache before going to batch.** `MPClient` caches every query to
`~/.cache/pvdlowe/mp`, which is ephemeral in a container. The client
deliberately raises rather than returning fabricated data when offline with a
cold cache — so populate it once interactively, then carry it:

```bash
# on Workbench, with the key exported
python -c "
from pvdlowe.mp import MPClient, screen_all
c = MPClient()
print(screen_all(c)['coverage'])
"
tar -czf mp-cache.tar.gz -C ~/.cache pvdlowe
gcloud storage cp mp-cache.tar.gz "gs://${BUCKET}/pvdlowe/"
```

Then unpack it in the container and run with `offline=True`. This also makes
your screening reproducible, which matters more than the saved API calls —
the Materials Project database changes between releases.

---

## Part 4 — Cost

Approximate `us-central1` on-demand rates; check current pricing.

| Item | Rate | Typical use |
|---|---|---|
| Workbench `n2-standard-8` | ~$0.39/hr | with 1 hr idle shutdown |
| Custom Job `n2-standard-8` | ~$0.39/hr | full run is minutes, so cents |
| Cloud Build | 120 free min/day | image build ~4 min |
| GCS standard | ~$0.02/GB/mo | outputs are single-digit MB |

A complete `--task=all` run costs a few cents of compute. The financial risk
is entirely the idle Workbench instance, which is why the idle-shutdown flag
is in the create command rather than a footnote.

---

## Part 5 — What Vertex actually buys you

Measured on the silver-reduction curve, the only expensive analysis:

| Configuration | Wall time |
|---|---|
| Serial (single core) | 238 s |
| `vertex/job.py --workers 7` on 8 vCPU | ~35 s expected |

The seven compositions are fully independent — the oxide re-optimisation and
thickness bisection for Ag₇₀Cu₃₀ knows nothing about Ag₉₀Cu₁₀ — so speedup is
linear up to seven workers and flat after. Requesting 32 vCPUs gets you the
same 35 seconds at four times the price.

Where more machine genuinely helps is a **composition × thickness map**:
`composition_thickness_map()` with an 11 × 11 grid is 121 independent stack
evaluations, and that scales to as many cores as you care to pay for. If you
want to explore the design space rather than just answer the brief's
question, that's the analysis to parallelise next — it needs the same
`multiprocessing.Pool` treatment `silver_curve()` already has in
`vertex/job.py`.

Beyond speed, the real argument for Custom Jobs here is provenance: each run
is stamped, logged, and its outputs land in an immutable timestamped GCS
prefix. Given that the framework's whole design principle is tracking where
numbers came from, having the compute leave an audit trail is consistent with
the rest of it.

---

# Part 6 — ML interatomic potentials on Workbench

The CPU-only guidance above does not apply to `pvdlowe.ml`. MACE and CHGNet are
PyTorch models: they want a GPU, and PyTorch alone is about 3 GB on disk, which
is why Cloud Shell's 5 GB home cannot hold them.

## 6.1 An instance sized for it

```bash
export PROJECT_ID="sg-llamole" REGION="us-central1"

gcloud workbench instances create pvdlowe-mlip \
    --location="${REGION}-a" \
    --machine-type=n1-standard-8 \
    --accelerator-type=NVIDIA_TESLA_T4 --accelerator-core-count=1 \
    --install-gpu-driver \
    --boot-disk-size=100 \
    --metadata=idle-shutdown-seconds=1800
```

A T4 is enough — these are small graph networks, not language models. If GPU
quota is unavailable, `n2-standard-16` on CPU works and is roughly 10x slower,
which for a handful of interfaces is tolerable.

**Set the idle shutdown.** A T4 instance is about $0.55/hr against
`n2-standard-8`'s $0.39, and unlike the CPU work in Part 1 this is not a
few-minutes job.

## 6.2 Setup

```bash
gcloud storage cp gs://sg-llamole-pvdlowe/pvdlowe/source/pvdlowe.tar.gz .
tar -xzf pvdlowe.tar.gz && cd lowe
pip install -e . --quiet
pip install mace-torch ase pymatgen mp-api --quiet
python -c "import torch; print('cuda:', torch.cuda.is_available())"
```

Store the Materials Project key in the environment, never in the repo:

```bash
read -s -p "MP API key: " MP_API_KEY && export MP_API_KEY && echo
```

## 6.3 Run

```bash
python examples/08_mlip_validate.py     # gate, then Ag-Cu mixing energies
python examples/09_mlip_adhesion.py     # the adhesion comparison
```

`08` stops if the surrogate cannot reproduce two known Materials Project hull
distances. That gate is not a formality: MLIP accuracy is 30-50 meV/atom and
the hull distances are 86-90, so the margin is about a factor of two.

## 6.4 Which question is worth the compute

**The adhesion comparison, not the mixing energies.**

The mixing energies restate something already known — the Materials Project
convex hull says Ag-Cu has no stable ordered compound, at DFT level, for free.
A surrogate would refine a number whose sign and rough magnitude are settled,
at a precision barely better than the quantity being measured.

The adhesion comparison asks something genuinely open. `metal_growth_factor`
is currently an empirical fit to one measured series with no mechanism behind
it. Work of adhesion is that mechanism, and the comparison is between
dielectrics computed identically — so the *ordering* is far more robust to
model error than any absolute value would be.

## 6.5 Shut it down

```bash
gcloud workbench instances stop pvdlowe-mlip --location="${REGION}-a"
# and when finished with it entirely:
gcloud workbench instances delete pvdlowe-mlip --location="${REGION}-a"
```
