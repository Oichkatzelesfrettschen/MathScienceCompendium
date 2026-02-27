FROM python:3.11-slim

# Install system dependencies: TeX Live (pdflatex + bibtex), poppler (pdftotext), ripgrep
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-bibtex-extra \
    bibtex2html \
    poppler-utils \
    ripgrep \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Install Python dependencies first (layer cache)
COPY pyproject.toml README.md LICENSE ./
RUN pip install --upgrade pip && pip install -e ".[dev,lint]"

# Copy source
COPY . .

# Default: run the full test suite
ENV PYTHONHASHSEED=0
ENV PYTHONPATH=src
ENV XLA_PYTHON_CLIENT_PREALLOCATE=false
CMD ["python", "-m", "pytest", "tests", "-q", "--cov=src", "--cov-report=term"]
