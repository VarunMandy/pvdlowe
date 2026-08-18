# CPU-only image for pvdlowe batch runs on Vertex AI Custom Jobs.
# No GPU, no ML framework -- the workload is scipy and vectorised numpy.
FROM python:3.12-slim

# Build tools are needed only for wheels that lack manylinux builds; slim
# them out afterwards to keep the image small enough for fast cold starts.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies first so the layer caches across code changes.
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
        "numpy>=1.24" "scipy>=1.10" "pandas>=2.0" "pyyaml>=6.0" \
        openpyxl tabulate \
        gcsfs google-cloud-storage google-cloud-secret-manager

COPY . /app
RUN pip install --no-cache-dir -e . \
    && apt-get purge -y build-essential && apt-get autoremove -y

# Fail the build if the physics is broken. 68 tests, about two seconds --
# cheap insurance against shipping a container that computes nonsense.
RUN python tests/run_tests.py

ENTRYPOINT ["python", "/app/vertex/job.py"]
