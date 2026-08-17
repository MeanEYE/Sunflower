#!/bin/sh
# makepkg refuses to run as root; when the container runs as root, hand the
# working directory to the builder user, run the real makepkg, and hand the
# results back so they map to the invoking host user.
if [ "$(id -u)" != "0" ]; then
	exec /usr/bin/makepkg "$@"
fi

chown -R builder:builder .
runuser -u builder -- /usr/bin/makepkg "$@"
status=$?
chown -R root:root .
exit $status
