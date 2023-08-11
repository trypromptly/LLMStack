#!/bin/bash

set -e

# Trap specific signals and forward them to the docker-compose command
trap stop SIGINT SIGTERM
stop() {
    echo "Received stop signal, stopping containers..."
    docker compose stop
    exit 0
}

# Parse the .env file to get LLMSTACK_PORT and other environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo ".env file not found"
fi

docker compose up -d

# If the output of the curl command contains "200", it means the server is ready
while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' localhost:${LLMSTACK_PORT:-3000})" != "200" ]]; do
    echo "Waiting for LLMStack to be ready..."
    sleep 3
done

echo "LLMStack is ready!"

# Open the web browser
case "$(uname)" in
    "Darwin")  # macOS
        open http://localhost:${LLMSTACK_PORT:-3000}
        ;;
    "Linux")   # Linux
        xdg-open http://localhost:${LLMSTACK_PORT:-3000}
        ;;
    "CYGWIN"*) # Windows/Cygwin
        cygstart http://localhost:${LLMSTACK_PORT:-3000}
        ;;
    "MINGW"*)  # Windows/Git Bash
        start http://localhost:${LLMSTACK_PORT:-3000}
        ;;
    *)         # Unknown OS
        echo "Please open your browser and go to http://localhost:${LLMSTACK_PORT:-3000}"
        ;;
esac

# stop script from finishing while waiting for a SIGINT or SIGTERM
while :; do :; done & kill -STOP $! && wait $!