#!/bin/bash
cd "$(dirname "$0")"
exec uvx --from . mymcp --config "$(pwd)/config.yaml" "$@"

