#!/bin/sh

set -e

# Start redis server if RUNNER_REDIS_HOST is not set or is set to localhost
if [ -z "$RUNNER_REDIS_HOST" ] || [ "$RUNNER_REDIS_HOST" = "localhost" ] || [ "$RUNNER_REDIS_HOST" = "127.0.0.1" ]; then
    echo "Starting redis server"
    redis-server --daemonize yes --protected-mode no
fi

# Start llmstack-runner
exec "$@"