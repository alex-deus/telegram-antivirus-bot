#!/usr/bin/env bash

args=("$@")

case "${1}" in
    "bash")
        shift
        exec bash -c "${args[@]:1}"
        ;;
    "sleep")
        exec bash -c "while true; do sleep 2; done"
        ;;
    "run")
        ./wait-for-it.sh mongo:27017 --timeout=30 --strict -- echo "Mongo is up"
        exec python -m application.main
        ;;
esac
