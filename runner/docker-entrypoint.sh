#!/bin/sh

set -e

# Start redis server
redis-server --daemonize yes

# Start llmstack-runner
exec "$@"