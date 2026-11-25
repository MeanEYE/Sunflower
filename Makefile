# directories
WORKING_DIRECTORY := $(dir $(lastword $(MAKEFILE_LIST)))
BUILD_DIRECTORY ?= $(WORKING_DIRECTORY)build
DEBIAN_BUILD_DIRECTORY = $(BUILD_DIRECTORY)/Debian
ARCH_BUILD_DIRECTORY = $(BUILD_DIRECTORY)/Arch
FEDORA_BUILD_DIRECTORY = $(BUILD_DIRECTORY)/Fedora

# version
VERSION_MAJOR := $(shell cat $(WORKING_DIRECTORY)/sunflower/gui/main_window.py | grep \'major\': | cut -f 2 -d : | tr -d [:space:][,])
VERSION_MINOR := $(shell cat $(WORKING_DIRECTORY)/sunflower/gui/main_window.py | grep \'minor\': | cut -f 2 -d : | tr -d [:space:][,])
VERSION_BUILD := $(shell cat $(WORKING_DIRECTORY)/sunflower/gui/main_window.py | grep \'build\': | cut -f 2 -d : | tr -d [:space:][,])
VERSION_STAGE := $(shell cat $(WORKING_DIRECTORY)/sunflower/gui/main_window.py | grep \'stage\': | cut -f 2 -d : | tr -d [:space:][\'][,])

# generate file name based on version
ifeq ($(VERSION_STAGE),f)
VERSION = $(VERSION_MAJOR).$(VERSION_MINOR).$(VERSION_BUILD)
FILE_NAME = sunflower-$(VERSION_MAJOR).$(VERSION_MINOR)-$(VERSION_BUILD)
else
VERSION = $(VERSION_MAJOR).$(VERSION_MINOR)$(VERSION_STAGE).$(VERSION_BUILD)
FILE_NAME = sunflower-$(VERSION_MAJOR).$(VERSION_MINOR)$(VERSION_STAGE)-$(VERSION_BUILD)
endif

# variables used in packages, packager defaults to the identity configured in git
RELEASE ?= 1
DEBIAN_VERSION := $(shell sed -n '1s/.*(\(.*\)).*/\1/p' $(WORKING_DIRECTORY)/debian/changelog)
GIT_USER_NAME := $(shell git config user.name 2>/dev/null)
GIT_USER_EMAIL := $(shell git config user.email 2>/dev/null)
ifneq ($(GIT_USER_NAME),)
PACKAGER ?= $(GIT_USER_NAME) <$(GIT_USER_EMAIL)>
else
PACKAGER ?=
endif

# container tool used by the docker-* targets (docker or podman)
CONTAINER ?= $(shell command -v docker >/dev/null 2>&1 && echo docker || echo podman)
# rootless podman maps container root to the invoking user, so no remap is
# needed; rootful docker needs an explicit uid to keep build/ owned by the user.
# Packager and release are handed over, as git identity is not known inside.
ifeq ($(CONTAINER),podman)
CONTAINER_RUN = $(CONTAINER) run --rm -e HOME=/tmp -e PACKAGER="$(PACKAGER)" -e RELEASE="$(RELEASE)" -v $(abspath $(WORKING_DIRECTORY)):/src -w /src
else
CONTAINER_RUN = $(CONTAINER) run --rm --user $(shell id -u):$(shell id -g) -e HOME=/tmp -e PACKAGER="$(PACKAGER)" -e RELEASE="$(RELEASE)" -v $(abspath $(WORKING_DIRECTORY)):/src -w /src
endif

# additional directories
FILE_PATH = $(BUILD_DIRECTORY)/$(FILE_NAME)
DEB_FILE_PATH = $(BUILD_DIRECTORY)/sunflower-$(VERSION)-$(RELEASE).all.deb
PKG_FILE_PATH = $(BUILD_DIRECTORY)/sunflower-$(VERSION)-$(RELEASE)-any.pkg.tar.xz
RPM_FILE_PATH = $(BUILD_DIRECTORY)/sunflower-$(VERSION)-$(RELEASE).noarch.rpm
RPM_OPENSUSE_FILE_PATH = $(BUILD_DIRECTORY)/sunflower-$(VERSION)-$(RELEASE).noarch.opensuse.rpm
RPM_PCLINUXOS_FILE_PATH = $(BUILD_DIRECTORY)/sunflower-$(VERSION)-$(RELEASE).noarch.pclinuxos.rpm
FLATPAK_FILE_PATH = $(BUILD_DIRECTORY)/sunflower-$(VERSION)-$(RELEASE).flatpak
APP_FILE_PATH = $(FILE_PATH).app

# publishing of built packages to the download server
PUBLISH_HOST ?= eu2
PUBLISH_PATH ?= /var/www/vhosts/sunflower-fm.org/httpdocs/pub
PUBLISH_OWNER ?= meaneye:psacln
PUBLISH_GLOBS = *.tgz *.tar.gz *.deb *.rpm *.pkg.tar.xz *.flatpak *.app *.sha256

# prepare help
define HELP
Usage:
	dist               - create a distribution tgz file
	dist-py            - create a python egg distribution file
	dist-deb           - create a .deb package for Debian, Mint, Ubuntu
	dist-arch          - create a .pkg.tar.gz package for ArchLinux
	dist-rpm           - create a .rpm package for Fedora, Mageia, Mandriva
	dist-rpm-opensuse  - create a .rpm package for OpenSUSE
	dist-rpm-pclinuxos - create a .rpm package for PCLinuxOS
	dist-flatpak       - create a single-file .flatpak bundle (needs flatpak-builder;
	                     runtimes are installed automatically from Flathub)
	dist-all           - create all packages
	standalone         - create a single-file executable (zip archive with a shebang)
	publish            - upload built packages and checksums to the download server
	                     (PUBLISH_HOST=, PUBLISH_PATH=, PUBLISH_OWNER= to override)
	docker-dist-*      - run any dist target in a container with the matching
	                     native toolchain (docker-dist-deb, docker-dist-py,
	                     docker-dist-rpm[-opensuse|-pclinuxos], docker-dist-arch,
	                     docker-dist-standalone); uses docker or podman (CONTAINER=)
	docker-dist-all    - create all packages, in containers where possible;
	                     flatpak bundle is built with flatpak-builder directly
	language-template  - update language template
	language-compile   - compile language files to .mo format
	clean              - remove all build files, flatpak build cache and runtimes
	version            - print Sunflower version
	help               - print this help

Options for dist-* passed through environment variables:
	RELEASE=1   - release number
	PACKAGER="" - packagers name (e.i. "John Smith <mail@example.com>"),
	              defaults to user name and email configured in git
endef
export HELP

# replace variables in spec file
define CREATE_RPM_SPEC_FILE
	cp $(WORKING_DIRECTORY)/dist/sunflower.spec $(BUILD_DIRECTORY)
	sed -i s/@version@/$(VERSION)/ $(BUILD_DIRECTORY)/sunflower.spec
	sed -i s/@release@/$(RELEASE)/ $(BUILD_DIRECTORY)/sunflower.spec
	sed -i s/@file_name@/$(FILE_NAME)/ $(BUILD_DIRECTORY)/sunflower.spec
	sed -i s/@packager@/"$(PACKAGER)"/ $(BUILD_DIRECTORY)/sunflower.spec
	sed -i "/^Packager: *$$/d" $(BUILD_DIRECTORY)/sunflower.spec
endef

# configuration options
all: version help

archive:
	$(info Creating release archive...)
	mkdir -p $(BUILD_DIRECTORY)
	git archive --format=tar --output=$(FILE_PATH).tar --prefix=Sunflower/ HEAD

dist: archive
	$(info Compressing release archive...)
	gzip -9 $(FILE_PATH).tar
	mv $(FILE_PATH).tar.gz $(FILE_PATH).tgz
	cd $(BUILD_DIRECTORY); sha256sum $(notdir $(FILE_PATH).tgz) > $(notdir $(FILE_PATH).tgz).sha256

dist-py:
	$(info Building package for Python...)
	python3 setup.py sdist --dist-dir $(BUILD_DIRECTORY)
	rm -rf Sunflower.egg-info

dist-deb: archive
	$(info Building package for Debian, Mint, Ubuntu...)
	@if [ "$(DEBIAN_VERSION)" != "$(VERSION)-$(RELEASE)" ]; then \
		echo "Version in debian/changelog ($(DEBIAN_VERSION)) does not match $(VERSION)-$(RELEASE), add a new entry first."; \
		exit 1; \
	fi
	rm -rf "$(DEBIAN_BUILD_DIRECTORY)"
	mkdir -p "$(DEBIAN_BUILD_DIRECTORY)"
	tar -xf $(FILE_PATH).tar -C $(DEBIAN_BUILD_DIRECTORY)
	cp -r $(WORKING_DIRECTORY)/debian $(DEBIAN_BUILD_DIRECTORY)/Sunflower
	cd $(DEBIAN_BUILD_DIRECTORY)/Sunflower; dpkg-buildpackage --build=binary --no-sign
	mv $(DEBIAN_BUILD_DIRECTORY)/sunflower_$(DEBIAN_VERSION)_all.deb $(DEB_FILE_PATH)
	cd $(BUILD_DIRECTORY); sha256sum $(notdir $(DEB_FILE_PATH)) > $(notdir $(DEB_FILE_PATH)).sha256

dist-arch: dist
	$(info Building package for ArchLinux...)
	mkdir -p $(ARCH_BUILD_DIRECTORY)
	cp $(FILE_PATH).tgz $(ARCH_BUILD_DIRECTORY)
	cp $(WORKING_DIRECTORY)/dist/PKGBUILD $(WORKING_DIRECTORY)/dist/sunflower $(ARCH_BUILD_DIRECTORY)
	sed -i s/@version@/$(VERSION)/ $(ARCH_BUILD_DIRECTORY)/PKGBUILD
	sed -i s/@release@/$(RELEASE)/ $(ARCH_BUILD_DIRECTORY)/PKGBUILD
	sed -i s/@file_name@/$(FILE_NAME)/ $(ARCH_BUILD_DIRECTORY)/PKGBUILD
	cd $(ARCH_BUILD_DIRECTORY); makepkg -g >> PKGBUILD
	cd $(ARCH_BUILD_DIRECTORY); PACKAGER="$(PACKAGER)" PKGEXT='.pkg.tar.xz' makepkg
	mv $(ARCH_BUILD_DIRECTORY)/sunflower-$(VERSION)-$(RELEASE)-any.pkg.tar.xz $(PKG_FILE_PATH)
	cd $(BUILD_DIRECTORY); sha256sum $(notdir $(PKG_FILE_PATH)) > $(notdir $(PKG_FILE_PATH)).sha256

dist-rpm: archive
	$(info Building package for Fedora, Mageia, Mandriva...)
	$(CREATE_RPM_SPEC_FILE)
	sed -i "s/@requires@/python3, python3-gobject, python3-chardet, gobject-introspection, gtk3, vte291, gnome-desktop3/" $(BUILD_DIRECTORY)/sunflower.spec
	rpmbuild -bb $(BUILD_DIRECTORY)/sunflower.spec --build-in-place --buildroot "$(abspath $(FEDORA_BUILD_DIRECTORY))"
	cp ~/rpmbuild/RPMS/noarch/sunflower-$(VERSION)-$(RELEASE).noarch.rpm $(RPM_FILE_PATH)
	cd $(BUILD_DIRECTORY); sha256sum $(notdir $(RPM_FILE_PATH)) > $(notdir $(RPM_FILE_PATH)).sha256

dist-rpm-opensuse: archive
	$(info Building package for OpenSUSE...)
	$(CREATE_RPM_SPEC_FILE)
	sed -i "s/@requires@/python3, python3-gobject, python3-gobject-cairo, python3-chardet, typelib-1_0-Gtk-3_0, typelib-1_0-Vte-2_91, typelib-1_0-GnomeDesktop-3_0/" $(BUILD_DIRECTORY)/sunflower.spec
	rpmbuild -bb $(BUILD_DIRECTORY)/sunflower.spec --build-in-place --buildroot "$(abspath $(FEDORA_BUILD_DIRECTORY))"
	cp ~/rpmbuild/RPMS/noarch/sunflower-$(VERSION)-$(RELEASE).noarch.rpm $(RPM_OPENSUSE_FILE_PATH)
	cd $(BUILD_DIRECTORY); sha256sum $(notdir $(RPM_OPENSUSE_FILE_PATH)) > $(notdir $(RPM_OPENSUSE_FILE_PATH)).sha256

dist-rpm-pclinuxos: archive
	$(info Building package for PCLinuxOS...)
	$(CREATE_RPM_SPEC_FILE)
	sed -i "s/@requires@/python3, python3-gobject, python3-chardet, gtk+3.0/" $(BUILD_DIRECTORY)/sunflower.spec
	rpmbuild -bb $(BUILD_DIRECTORY)/sunflower.spec --build-in-place --buildroot "$(abspath $(FEDORA_BUILD_DIRECTORY))"
	cp ~/rpmbuild/RPMS/noarch/sunflower-$(VERSION)-$(RELEASE).noarch.rpm $(RPM_PCLINUXOS_FILE_PATH)
	cd $(BUILD_DIRECTORY); sha256sum $(notdir $(RPM_PCLINUXOS_FILE_PATH)) > $(notdir $(RPM_PCLINUXOS_FILE_PATH)).sha256

dist-flatpak:
	$(info Building Flatpak bundle...)
	flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
	flatpak-builder --force-clean --user --install-deps-from=flathub --repo=$(BUILD_DIRECTORY)/flatpak-repo $(BUILD_DIRECTORY)/flatpak-build $(WORKING_DIRECTORY)/dist/flatpak/org.sunflower_fm.Sunflower.yml
	flatpak build-bundle --runtime-repo=https://flathub.org/repo/flathub.flatpakrepo $(BUILD_DIRECTORY)/flatpak-repo $(FLATPAK_FILE_PATH) org.sunflower_fm.Sunflower
	cd $(BUILD_DIRECTORY); sha256sum $(notdir $(FLATPAK_FILE_PATH)) > $(notdir $(FLATPAK_FILE_PATH)).sha256

dist-all: dist-deb dist-rpm dist-rpm-opensuse dist-rpm-pclinuxos dist-arch dist-py dist-flatpak standalone

# containerized builds: each package is built with its native distro toolchain
docker-image-%:
	$(CONTAINER) build -t sunflower-build-$* -f $(WORKING_DIRECTORY)dist/docker/Dockerfile.$* $(WORKING_DIRECTORY)dist/docker

docker-dist-deb: docker-image-debian
	$(CONTAINER_RUN) sunflower-build-debian make dist-deb

docker-dist-py: docker-image-debian
	$(CONTAINER_RUN) sunflower-build-debian make dist-py

docker-dist-rpm: docker-image-fedora
	$(CONTAINER_RUN) sunflower-build-fedora make dist-rpm

docker-dist-rpm-opensuse: docker-image-fedora
	$(CONTAINER_RUN) sunflower-build-fedora make dist-rpm-opensuse

docker-dist-rpm-pclinuxos: docker-image-fedora
	$(CONTAINER_RUN) sunflower-build-fedora make dist-rpm-pclinuxos

docker-dist-arch: docker-image-arch
	$(CONTAINER_RUN) sunflower-build-arch make dist-arch

docker-dist-standalone: docker-image-debian
	$(CONTAINER_RUN) sunflower-build-debian make standalone

# flatpak-builder brings its own sandbox and runtimes, so that bundle is built
# directly instead of nesting one container tool inside of another
docker-dist-all: docker-dist-deb docker-dist-py docker-dist-rpm docker-dist-rpm-opensuse docker-dist-rpm-pclinuxos docker-dist-arch docker-dist-standalone dist-flatpak

language-template:
	$(info Updating language template...)
	find sunflower/ -iname "*.py" | xargs xgettext --language=Python --package-name=Sunflower --package-version=0.1 --output $(WORKING_DIRECTORY)/translations/sunflower.pot

language-compile:
	$(info Compiling language templates...)
	find translations -iname "*.po" -execdir msgfmt sunflower.po -o sunflower.mo \;

clean:
	$(RM) -rf $(BUILD_DIRECTORY)
	$(RM) -rf sunflower.*
	$(RM) -rf Sunflower.egg-info
	$(RM) -rf $(WORKING_DIRECTORY).flatpak-builder
	for ref in $$(flatpak list --user --columns=ref 2>/dev/null | grep -E '^(org\.sunflower_fm\.Sunflower|org\.gnome\.(Sdk|Platform))'); do \
		flatpak uninstall --user --noninteractive $$ref 2>/dev/null || true; \
	done
	flatpak uninstall --user --noninteractive --unused 2>/dev/null || true

version:
	$(info Sunflower $(VERSION))

standalone:
	$(info Building standalone executable...)
	mkdir -p $(BUILD_DIRECTORY)
	$(RM) -f $(FILE_PATH).zip
	cd $(WORKING_DIRECTORY) && zip --quiet $(abspath $(FILE_PATH)).zip -r sunflower images styles -x '*.pyc' -x '*/__pycache__/*' -x '*.xcf' -x 'images/screenshot.png'
	cd $(WORKING_DIRECTORY) && zip --quiet --junk-paths $(abspath $(FILE_PATH)).zip sunflower/__main__.py
	echo '#!/usr/bin/env python3' > $(APP_FILE_PATH)
	cat $(FILE_PATH).zip >> $(APP_FILE_PATH)
	$(RM) -f $(FILE_PATH).zip
	chmod a+x $(APP_FILE_PATH)
	cd $(BUILD_DIRECTORY); sha256sum $(notdir $(APP_FILE_PATH)) > $(notdir $(APP_FILE_PATH)).sha256

publish:
	$(info Publishing packages to $(PUBLISH_HOST):$(PUBLISH_PATH)...)
	@cd $(BUILD_DIRECTORY) && files=$$(ls $(PUBLISH_GLOBS) 2>/dev/null); \
	if [ -z "$$files" ]; then echo "No packages found in $(BUILD_DIRECTORY), build them first."; exit 1; fi; \
	echo "$$files" | sed 's/^/  /'; \
	scp $$files $(PUBLISH_HOST):$(PUBLISH_PATH)/ && \
	ssh $(PUBLISH_HOST) "cd $(PUBLISH_PATH) && chown $(PUBLISH_OWNER) $$(echo $$files)"

help:
	@echo "$$HELP"

.PHONY: default dist dist-py dist-deb dist-arch dist-rpm dist-rpm-opensuse dist-rpm-pclinuxos dist-flatpak dist-all standalone publish docker-dist-deb docker-dist-py docker-dist-rpm docker-dist-rpm-opensuse docker-dist-rpm-pclinuxos docker-dist-arch docker-dist-standalone docker-dist-all language-template clean version help

