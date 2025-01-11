release: rm -rf /tmp/build_* /tmp/tmp.* /tmp/.apt && playwright install
web: gunicorn "app:create_app()" --bind 0.0.0.0:8000
