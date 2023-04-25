#!/bin/sh

set -e

log() {
    if [ -z "${DRIBDAT_ENTRYPOINT_NO_LOGS:-}" ]; then
        echo "$@"
    fi
}

if [ -z "${DRIBDAT_ENTRYPOINT_SKIP:-}" ]; then
    if /usr/bin/find "/docker-entrypoint.d/" -mindepth 1 -maxdepth 1 -type f -print -quit 2>/dev/null | read v; then
        log "$0: /docker-entrypoint.d/ not empty, processing it"
        find "/docker-entrypoint.d/" -follow -type f -print | sort -V | while read -r f; do
            case "$f" in
                *.envsh)
                    if [ -x "$f" ]; then
                        log "$0: Sourcing $f";
                        . "$f"
                    else
                        log "$0: Ignoring $f, executable bit not set";
                    fi
                    ;;
                *.sh)
                    if [ -x "$f" ]; then
                        log "$0: Executing $f";
                        "$f"
                    else
                        log "$0: Ignoring $f, executable bit not set";
                    fi
                    ;;
                *) log "$0: Ignoring $f";;
            esac
        done
    else
        log "$0: Nothing found in /docker-entrypoint.d/, skipping"
    fi
fi

echo "$@"
echo "$PATH"
type gunicorn

# execute the command passed to the container
exec "$@"