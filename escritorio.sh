#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
export LABCLIN_MODO=escritorio
exec "$@"
