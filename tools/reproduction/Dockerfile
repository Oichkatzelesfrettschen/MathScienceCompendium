FROM python:3.11.13-slim-bookworm@sha256:86adf8dbadc3d6e82ee5dd2c74bec2e1c2467cdad47886280501df722372d2e1

ENV PYTHONHASHSEED=0
ENV PYTHONPATH=/workspace/src
ENV JAX_PLATFORMS=cpu
ENV XLA_PYTHON_CLIENT_PREALLOCATE=false

WORKDIR /workspace

COPY requirements-lock.txt pyproject.toml README.md LICENSE ./
RUN python -m pip install --no-cache-dir --disable-pip-version-check \
    -r requirements-lock.txt

COPY . .
RUN python -m pip install --no-cache-dir --disable-pip-version-check \
    --no-deps -e .

CMD ["python", "tools/reproduction/run_independent_reproduction.py"]
