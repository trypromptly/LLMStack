# Stage 1: Compile and build code
FROM python:3.11 AS builder

# Add poetry to the image
RUN pip install --no-cache-dir poetry

# Copy pyproject.toml and poetry.lock
ADD pyproject.toml /pyproject.toml
ADD poetry.lock /poetry.lock

# Install dependencies
RUN poetry config virtualenvs.create false
RUN poetry install --no-root --no-dev --no-interaction --no-ansi
RUN poetry install --only server --no-root --no-dev --no-interaction --no-ansi

# Download nltk and spacy data
RUN mkdir -p /usr/local/share/nltk_data/tokenizers
RUN mkdir -p /usr/local/share/nltk_data/taggers

ENV NLTK_DATA=/usr/local/share/nltk_data
ARG UNIQUE_IDENTIFIER=promptly

# Install processors
RUN poetry install --no-root --with processors

RUN python -m nltk.downloader -d /usr/local/share/nltk_data 'punkt'
RUN python -m nltk.downloader -d /usr/local/share/nltk_data 'averaged_perceptron_tagger'
RUN python -m spacy download en_core_web_sm

# Hack for installing chromadb embedding models
RUN python -c "from chromadb.utils import embedding_functions as f; f.DefaultEmbeddingFunction()(['a'])"

RUN mkdir /code/
WORKDIR /code/
ADD ./manage.py /code/manage.py
ADD ./llmstack /code/llmstack
ADD ./docker /code/docker

# Environment variables
ENV DJANGO_SETTINGS_MODULE=llmstack.server.settings

# Call collectstatic
RUN python manage.py collectstatic --noinput --clear

# Stage 2: Build final image
FROM python:3.11-slim

ARG APP_USER=appuser
RUN groupadd -r ${APP_USER} && useradd --no-log-init -r -g ${APP_USER} ${APP_USER} \
  && mkdir -p /home/${APP_USER} \
  && mkdir -p /home/${APP_USER}/.cache/chroma \
  && chown -R ${APP_USER}:${APP_USER} /home/${APP_USER} \
  && chown -R ${APP_USER}:${APP_USER} /home/${APP_USER}/.cache/chroma

# Install runtime dependencies
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
  tesseract-ocr \
  libtesseract-dev \
  tesseract-ocr-eng \
  tesseract-ocr-chi-sim \
  tesseract-ocr-script-latn \
  tesseract-ocr-script-deva \
  poppler-utils \
  " \
  && seq 1 8 | xargs -I{} mkdir -p /usr/share/man/man{} \
  && apt-get update && apt-get install -y --no-install-recommends $RUN_DEPS \
  && rm -rf /var/lib/apt/lists/*  

# Copy application code
COPY --from=builder /code/llmstack/client/build/index.html /code/client/build/index.html
COPY --from=builder /code/llmstack/client/build/static /code/client/build/static
COPY --from=builder /code/llmstack/contrib/apps /code/llmstack/contrib/apps
COPY --from=builder /code/llmstack /code/llmstack
COPY --from=builder /code/llmstack/static /code/llmstack/static
COPY --from=builder /code/manage.py /code/manage.py
COPY --from=builder /code/docker/api/docker-entrypoint.sh /code/docker-entrypoint.sh

COPY --from=builder /root/.cache/pip /root/.cache/pip
COPY --from=builder /root/.cache/chroma /home/${APP_USER}/.cache/chroma
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/share/nltk_data /usr/local/share/nltk_data

RUN chown -R ${APP_USER}:${APP_USER} /home/${APP_USER}/.cache/chroma
RUN chown -R ${APP_USER}:${APP_USER} /code

WORKDIR /code/

ENV DJANGO_SETTINGS_MODULE=llmstack.server.settings

EXPOSE 9000

USER ${APP_USER}:${APP_USER}

ENV PATH="/home/${APP_USER}/.local/bin:${PATH}" 

ENTRYPOINT ["/code/docker-entrypoint.sh"]

CMD ["/usr/local/bin/gunicorn", "llmstack.server.asgi:application", "-w", "2", "-t", "120", "-b", ":9000", "-k", "uvicorn.workers.UvicornWorker"]