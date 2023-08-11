# Stage 1: Compile and build code
FROM python:3.11-slim AS builder

ADD requirements_base.txt /requirements_base.txt
RUN pip install --no-cache-dir -r /requirements_base.txt
RUN playwright install chromium

ADD requirements_datasources.txt /requirements_datasources.txt
RUN pip install --no-cache-dir -r /requirements_datasources.txt

ADD requirements_processors.txt /requirements_processors.txt
RUN pip install --no-cache-dir -r /requirements_processors.txt

RUN mkdir /code/
WORKDIR /code/
ADD . /code/

ENV DJANGO_SETTINGS_MODULE=llmstack.settings
RUN python manage.py collectstatic --noinput --clear

# Stage 2: Build final image
FROM python:3.11-slim

ARG APP_USER=appuser
RUN groupadd -r ${APP_USER} && useradd --no-log-init -r -g ${APP_USER} ${APP_USER} \
    && mkdir -p /home/${APP_USER} \
    && chown -R ${APP_USER}:${APP_USER} /home/${APP_USER}

RUN apt-get update && apt-get install -y libpcre3 \
    mime-support \
    ffmpeg \
    postgresql-client \
    gstreamer1.0-libav \
    libnss3-tools \
    libatk-bridge2.0-0 \
    libcups2 \
    libxkbcommon-x11-0 \
    libxcomposite1 \
    libxdamage1 && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY --from=builder /code/apps /code/apps
COPY --from=builder /code/base /code/base
COPY --from=builder /code/client/build/index.html /code/client/build/index.html
COPY --from=builder /code/client/build/static /code/client/build/static
COPY --from=builder /code/common /code/common
COPY --from=builder /code/datasources /code/datasources
COPY --from=builder /code/emails /code/emails
COPY --from=builder /code/fixtures /code/fixtures
COPY --from=builder /code/jobs /code/jobs
COPY --from=builder /code/llmstack /code/llmstack
COPY --from=builder /code/organizations /code/organizations
COPY --from=builder /code/play /code/play
COPY --from=builder /code/processors /code/processors
COPY --from=builder /code/static /code/static
COPY --from=builder /code/manage.py /code/manage.py
COPY --from=builder /code/docker-entrypoint.sh /code/docker-entrypoint.sh

COPY --from=builder /root/.cache/pip /root/.cache/pip
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

COPY --from=builder /root/.cache/ms-playwright /home/${APP_USER}/.cache/ms-playwright
RUN chown -R ${APP_USER}:${APP_USER} /home/${APP_USER}/.cache

WORKDIR /code/

ENV DJANGO_SETTINGS_MODULE=llmstack.settings

EXPOSE 9000

USER ${APP_USER}:${APP_USER}

ENTRYPOINT ["/code/docker-entrypoint.sh"]

CMD ["/usr/local/bin/gunicorn", "promptly.asgi:application", "-w", "2", "-t", "120", "-b", ":9000", "-k", "uvicorn.workers.UvicornWorker"]
