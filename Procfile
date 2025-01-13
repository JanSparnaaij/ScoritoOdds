release: rm -rf /tmp/build_* /tmp/tmp.* /tmp/.apt && playwright install
web: rm -rf /tmp/build_* /tmp/tmp.* /tmp/.apt && gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --timeout 120
