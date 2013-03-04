
# Directories
working_directory := $(shell hg root)
build_directory ?= $(working_directory)/build
install_directory = $(build_directory)/sunflower

# Version
version_major := $(shell cat $(working_directory)/application/gui/main_window.py | grep \'major\': | cut -f 2 -d : | tr -d [:space:][,])
version_minor := $(shell cat $(working_directory)/application/gui/main_window.py | grep \'minor\': | cut -f 2 -d : | tr -d [:space:][,])
version_build := $(shell cat $(working_directory)/application/gui/main_window.py | grep \'build\': | cut -f 2 -d : | tr -d [:space:][,])
version_stage := $(shell cat $(working_directory)/application/gui/main_window.py | grep \'stage\': | cut -f 2 -d : | tr -d [:space:][\'][,])
version = $(version_major).$(version_minor)$(version_stage)-$(version_build)

# Variables
release ?= 1
packager ?= "Unpecified Packager"
short_description = "Small and highly customizable twin-panel file manager for Linux with support for plugins."

# Paths
file_name = sunflower-$(version)
file_path = $(build_directory)/$(file_name)
deb_file_path = $(build_directory)/sunflower-$(version)-$(release).all.deb
pkg_file_path = $(build_directory)/sunflower-$(version)-$(release)-any.pkg.tar.xz
rpm_file_path = $(build_directory)/sunflower-$(version)-$(release).noarch.rpm
rpm_opensuse_file_path = $(build_directory)/sunflower-$(version)-$(release).noarch.opensuse.rpm
rpm_pclinuxos_file_path = $(build_directory)/sunflower-$(version)-$(release).noarch.pclinuxos.rpm

# define help
define HELP
Usage:
	dist               - create a distribution tgz file
	dist-deb           - create a .deb package for Debian, Mint, Ubuntu
	dist-pkg           - create a .pkg.tar.gz package for ArchLinux
	dist-rpm           - create a .rpm package for Fedora, Mageia, Mandriva
	dist-rpm-opensuse  - create a .rpm package for OpenSUSE
	dist-rpm-pclinuxos - create a .rpm package for PCLinuxOS
	dist-all           - create all package
	language-template  - update language template
	clean              - remove all build files
	version            - print Sunflower version
	help               - print this help
endef
export HELP

# Auxiliary macro for installing sunflower while creating .deb's and .rpm's (Remember to symchronize changes with /dist/PKGBUILD!)
define dist_install
	@mkdir -p $(install_directory)
	# untar archive
	@cd $(build_directory); tar -xf $(file_path).tar
	# install files
	@install -Dm755 $(working_directory)/dist/sunflower "$(install_directory)/usr/bin/sunflower"
	@install -d "$(install_directory)/usr/share/sunflower"
	@cp -r $(build_directory)/Sunflower/* "$(install_directory)/usr/share/sunflower"
	@install -Dm644 "$(build_directory)/Sunflower/images/sunflower.png" "$(install_directory)/usr/share/pixmaps/sunflower.png"
	@install -Dm644 "$(build_directory)/Sunflower/images/sunflower.svg" "$(install_directory)/usr/share/pixmaps/sunflower.svg"
	@install -Dm644 "$(build_directory)/Sunflower/Sunflower.desktop" "$(install_directory)/usr/share/applications/sunflower.desktop"
endef

# Auxiliary macro for building .spec ('Requires' field intentionally not filled!)
define create_spec
	# coping and configuring spec file
	@cp $(working_directory)/dist/sunflower.spec $(build_directory)
	@sed -i s/@version@/$(version)/ $(build_directory)/sunflower.spec
	@sed -i s/@release@/$(release)/ $(build_directory)/sunflower.spec
	@sed -i s/@packager@/$(packager)/ $(build_directory)/sunflower.spec
	@sed -i s/@short_description@/$(short_description)/ $(build_directory)/sunflower.spec
endef

# Auxiliary macro for building .rpm's from spec
define create_rpm
	# building package...
	@rpmbuild -bb $(build_directory)/sunflower.spec --buildroot $(install_directory)
	# coping to $@
	@cp ~/rpmbuild/RPMS/noarch/sunflower-$(version)-$(release).noarch.rpm $@
	# cleaning up
	@rm -rf $(install_directory) $(build_directory)/sunflower.spec $(build_directory)/Sunflower
endef

# configuration options
default: version help

$(file_path).tar:
	$(info Preparing release...)
	@mkdir -p $(build_directory)

	# archive files
	@hg archive --exclude dist/ --exclude Makefile --type tgz --prefix Sunflower $(file_path).tgz

	# remove unneeded files
	@gunzip $(file_path).tgz
	@tar --delete --wildcards --file=$(file_path).tar Sunflower/.hg*
	@tar --delete --wildcards --file=$(file_path).tar Sunflower/images/*.xcf

$(file_path).tgz: $(file_path).tar
	# repacking gzip archive
	@gzip --best -c $(file_path).tar > $(file_path).tgz

$(deb_file_path): $(file_path).tar
	$(info Building package for Debian, Mint, Ubuntu...)
	$(dist_install)

	# coping and configuring control file
	@mkdir -p $(install_directory)/DEBIAN
	@cp $(working_directory)/dist/control $(install_directory)/DEBIAN
	@sed -i s/@version@/$(version)/ $(install_directory)/DEBIAN/control
	@sed -i s/@packager@/$(packager)/ $(install_directory)/DEBIAN/control
	@sed -i s/@short_description@/$(short_description)/ $(install_directory)/DEBIAN/control

	# building package
	@fakeroot dpkg-deb --build $(install_directory)

	# moving to $(deb_file_path)
	@mv $(install_directory).deb $(deb_file_path)

	# cleaning up
	@rm -rf $(install_directory) $(build_directory)/Sunflower

$(pkg_file_path): $(file_path).tgz
	$(info Building package for ArchLinux...)
	@mkdir -p $(install_directory)

	# coping tarball
	@cp $(file_path).tgz $(install_directory)

	# coping and configuring PKGBUILD
	@cp $(working_directory)/dist/PKGBUILD $(working_directory)/dist/sunflower $(install_directory)
	@sed -i s/@version@/$(version)/ $(install_directory)/PKGBUILD
	@sed -i s/@release@/$(release)/ $(install_directory)/PKGBUILD
	@sed -i s/@short_description@/$(short_description)/ $(install_directory)/PKGBUILD

	# generating checksum
	@cd $(install_directory); makepkg -g >> PKGBUILD

	# building
	@cd $(install_directory); makepkg

	# moving to $(pkg_file_path)
	@mv $(install_directory)/sunflower-$(version)-$(release)-any.pkg.tar.xz $(pkg_file_path)

	# cleaning up
	@rm -rf $(install_directory)

$(rpm_file_path): $(file_path).tar
	$(info Building package for Fedora, Mageia, Mandriva...)
	$(dist_install)
	$(create_spec)
	@sed -i s/@requires@/pygtk2/ $(build_directory)/sunflower.spec
	$(create_rpm)

$(rpm_opensuse_file_path): $(file_path).tar
	$(info Building package for OpenSUSE...)
	$(dist_install)
	$(create_spec)
	@sed -i s/@requires@/python-gtk/ $(build_directory)/sunflower.spec
	$(create_rpm)

$(rpm_pclinuxos_file_path): $(file_path).tar
	$(info Building package for PCLinuxOS...)
	$(dist_install)
	$(create_spec)
	@sed -i s/@requires@/pygtk2.0/ $(build_directory)/sunflower.spec
	$(create_rpm)

dist: $(file_path).tgz
dist-deb: $(deb_file_path)
dist-pkg: $(pkg_file_path)
dist-rpm: $(rpm_file_path)
dist-rpm-opensuse: $(rpm_opensuse_file_path)
dist-rpm-pclinuxos: $(rpm_pclinuxos_file_path)

dist-all: dist-deb dist-rpm dist-rpm-opensuse dist-rpm-pclinuxos dist-pkg

language-template:
	$(info Updating language template...)
	find . -iname "*.py" | xargs xgettext --language=Python --package-name=Sunflower --package-version=0.1 --output $(working_directory)/translations/sunflower.pot

clean:
	rm -rf $(build_directory)

version:
	$(info Sunflower $(version))

help:
	@echo "$$HELP"

.PHONY: default dist dist-deb dist-pkg dist-rpm dist-rpm-opensuse dist-rpm-pclinuxos dist-all language-template clean version help

