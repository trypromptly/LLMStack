#!/bin/sh
set -e
DATABASE_HOST=${DATABASE_HOST:-postgres}

apiserver() {
    echo "Starting API server"
    if [ "x$DJANGO_MANAGEPY_MIGRATE" != 'xoff' ]; then
        python manage.py migrate --noinput
    fi

    if [ "x$DJANGO_MANAGEPY_COLLECTSTATIC" != 'xoff' ]; then
        python manage.py collectstatic --noinput
    fi

    if [ "x$DJANGO_MANAGEPY_CREATECACHETABLE" != 'xoff' ]; then
        python manage.py createcachetable
    fi

    if [ "x$DJANGO_MANAGEPY_CLEARCACHE" != 'xoff' ]; then
        python manage.py clearcache
    fi
    
    if [ "x$AUTORELOAD" = 'xTrue' ] && [ "x$SINGLE_THREAD" = 'xFalse' ]; then
        uvicorn llmstack.asgi:application --reload --port 9000 --host 0.0.0.0 --reload-dir /code
    elif [ "x$AUTORELOAD" = 'xFalse' ] && [ "x$SINGLE_THREAD" = 'xTrue' ]; then
        python manage.py runserver --nothreading --noreload 0.0.0.0:9000
    else
        /usr/local/bin/gunicorn llmstack.asgi:application -w 6 -b :9000 --timeout 0 -k uvicorn.workers.UvicornWorker
    fi
}

rqworker() {
    echo "Starting RQ worker"
    python manage.py rqworker default --verbosity=0 --with-scheduler
}

until pg_isready -h $DATABASE_HOST; do
    >&2 echo "Postgres is unavailable - sleeping"
    sleep 1
done

>&2 echo "Postgres is up - continuing"

case "$1" in
    apiserver)
        apiserver
        ;;
    rqworker)
        rqworker
        ;;
    *)
        exec "$@"
        ;;
esac
