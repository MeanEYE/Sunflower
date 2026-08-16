#!/bin/sh
# Flatpak launcher; the application tree lives in /app/share/sunflower and
# bundled Python dependencies are installed with --prefix=/app.
site_dir=$(python3 -c 'import sysconfig; print(sysconfig.get_path("purelib", vars={"base": "/app"}))')
export PYTHONPATH="/app/share/sunflower:${site_dir}${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m sunflower "$@"
