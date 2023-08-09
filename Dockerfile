FROM python:3.9

# Create a group and user to run our app
ARG APP_USER=appuser
RUN groupadd -r ${APP_USER} && useradd --no-log-init -r -g ${APP_USER} ${APP_USER} \
    && mkdir -p /home/${APP_USER} \
    && chown -R ${APP_USER}:${APP_USER} /home/${APP_USER}

# Install packages needed to run your application
RUN set -ex \
    && RUN_DEPS=" \
    libpcre3 \
    mime-support \
    ffmpeg \
    postgresql-client \
    gstreamer1.0-libav \
    libnss3-tools \
    libatk-bridge2.0-0 \
    libcups2-dev \
    libxkbcommon-x11-0 \
    libxcomposite-dev \
    libxdamage-dev \
    " \
    && seq 1 8 | xargs -I{} mkdir -p /usr/share/man/man{} \
    && apt-get update && apt-get install -y --no-install-recommends $RUN_DEPS \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files and build them
ADD requirements_base.txt /requirements_base.txt
RUN pip install --no-cache-dir -r /requirements_base.txt

ADD requirements_datasources.txt /requirements_datasources.txt
RUN pip install --no-cache-dir -r /requirements_datasources.txt

ADD requirements_processors.txt /requirements_processors.txt.txt
RUN pip install --no-cache-dir -r /requirements_processors.txt.txt

# Copy app code
RUN mkdir /code/
WORKDIR /code/
ADD . /code/

# aWSGI will listen on this port
EXPOSE 9000

# Static environment variables needed by Django
ENV DJANGO_SETTINGS_MODULE=llmstack.settings

# Collect static
RUN python manage.py collectstatic --noinput --clear

# Change to a non-root user
USER ${APP_USER}:${APP_USER}

# Install playwright  browser 
RUN playwright install chromium

# Run entrypoint script
ENTRYPOINT ["/code/docker-entrypoint.sh"]

# Start aWSGI
CMD ["/usr/local/bin/gunicorn", "promptly.asgi:application", "-w", "2", "-t", "120", "-b", ":9000", "-k", "uvicorn.workers.UvicornWorker"]