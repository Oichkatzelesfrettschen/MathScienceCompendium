FROM vllm/vllm-openai:v0.21.0@sha256:4ac9b7c6dabc3ec762c0edef4e9245abe98373844da91cc53ee42e5c58280c5b

ARG MINERU_VERSION=3.4.4

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        fontconfig \
        fonts-noto-core \
        fonts-noto-cjk \
        libgl1 \
    && fc-cache -f \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir \
        "mineru[core]==${MINERU_VERSION}" \
        --break-system-packages

RUN mineru-models-download -s huggingface -m all

ENV MINERU_MODEL_SOURCE=local

ENTRYPOINT ["/bin/bash", "-lc"]
CMD ["mineru --version"]
