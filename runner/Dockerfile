FROM mcr.microsoft.com/playwright:next-jammy

ENV DEBIAN_FRONTEND=noninteractive

# Install python3
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    x11vnc \
    novnc \
    redis-server \
    pkg-config \
    libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install poetry
RUN pip3 install RestrictedPython

# Install grpc_health_probe
RUN wget -qO/grpc_health_probe https://github.com/grpc-ecosystem/grpc-health-probe/releases/download/v0.4.22/grpc_health_probe-linux-amd64 && \
    chmod +x /grpc_health_probe

# Empty dir for web
RUN mkdir -p /usr/share/www/html

RUN mkdir /code
WORKDIR /code

COPY poetry.lock /code/poetry.lock
COPY pyproject.toml /code/pyproject.toml
COPY README.md /code/README.md
COPY llmstack /code/llmstack
COPY runner/docker-entrypoint.sh /code/docker-entrypoint.sh

RUN poetry config virtualenvs.create false \
    && poetry install --only server --no-root --no-dev --no-interaction --no-ansi \
    && poetry install --no-interaction --no-ansi

RUN chmod +x /code/docker-entrypoint.sh

ENTRYPOINT [ "/code/docker-entrypoint.sh" ]

CMD [ "llmstack-runner" ]

