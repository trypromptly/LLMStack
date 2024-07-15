ARG REGISTRY
ARG TAG

FROM ${REGISTRY:-}llmstack-api:${TAG:-latest} AS builder
FROM nginx:stable-alpine3.19-slim

RUN rm /etc/nginx/conf.d/default.conf
ADD docker/app/nginx.conf /etc/nginx/conf.d

# Copy static files from Django to nginx
COPY --from=builder /code/llmstack/static /usr/share/nginx/html/static