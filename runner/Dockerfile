FROM mcr.microsoft.com/playwright:v1.39.0-jammy

ENV DEBIAN_FRONTEND=noninteractive

# Install python3
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    xdotool \
    x11vnc \
    websockify \
    novnc \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install poetry

RUN mkdir /code
WORKDIR /code

COPY poetry.lock /code/poetry.lock
COPY pyproject.toml /code/pyproject.toml
COPY README.md /code/README.md
COPY llmstack /code/llmstack

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

RUN redis-server --daemonize yes

ENTRYPOINT [ "/code/llmstack/runner/docker-entrypoint.sh" ]

CMD [ "llmstack-runner" ]

