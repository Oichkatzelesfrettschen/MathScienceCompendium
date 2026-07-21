#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
    echo "usage: $0 SOURCE_COMMIT" >&2
    exit 2
fi

source_commit=$(git rev-parse --verify "$1^{commit}")
archive_root=$(mktemp -d)
cleanup() {
    rm -rf -- "$archive_root"
}
trap cleanup EXIT HUP INT TERM

git archive "$source_commit" | tar -xf - -C "$archive_root"
(
    cd "$archive_root"
    EVIDENCE_SOURCE_COMMIT="$source_commit" \
        docker compose -p reproduction \
        -f tools/reproduction/compose.yaml build --no-cache
)

image_revision=$(
    docker image inspect reproduction-evidence-reproduction:latest \
        --format '{{index .Config.Labels "org.opencontainers.image.revision"}}'
)
if [ "$image_revision" != "$source_commit" ]; then
    echo "image revision does not match the requested source commit" >&2
    exit 1
fi
printf 'image_revision=%s\n' "$image_revision"
