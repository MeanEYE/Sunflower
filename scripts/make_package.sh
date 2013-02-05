#!/bin/sh
#
#   Sunflower Package Build Script (Version 0.0.5)
#   Written by Wojciech Kluczka <wojtekkluczka@gmail.com>
#

type="none"
distro="none"
source="none"
packager="none"
release="1"
short_description="Small and highly customizable twin-panel file manager for Linux with support for plugins."

function install_sunflower() {
	rm -fR "$1"
	mkdir -p "$1/usr/bin" "$1/usr/share/pixmaps" "$1/usr/share/applications"
	tar xzpf "$source" --directory "$1/usr/share"
	sunflower_path="/usr/share/sunflower"
	mv "$1/usr/share/Sunflower" "$1$sunflower_path"
	
	version=`cat "$1$sunflower_path/CHANGES" | grep Version -m 1 | cut -d " " -f 2`
	version=${version/-/.}
	echo -e "\t-- Version $version --\n"
	
	echo -e "#!/bin/sh\npython $sunflower_path/Sunflower.py" > "$1/usr/bin/sunflower"
	chmod 755 "$1/usr/bin/sunflower"
	
	cp -f "$1$sunflower_path/images/sunflower.png" "$1/usr/share/pixmaps/sunflower.png"
	cp -f "$1$sunflower_path/images/sunflower.svg" "$1/usr/share/pixmaps/sunflower.svg"

	case $distro in mageia|mandriva|pclinuxos)
		desktop-file-edit --add-category="X-MandrivaLinux-System-FileTools" $1$sunflower_path/Sunflower.desktop ;;
	esac
	cp -f "$1$sunflower_path/Sunflower.desktop" "$1/usr/share/applications/sunflower.desktop"
}

function make_deb() {
	build_dir=sunflower
	install_sunflower $build_dir

	mkdir -p $build_dir/DEBIAN
	echo "Package: sunflower"                                       >  $build_dir/DEBIAN/control
	echo "Version: $version"                                        >> $build_dir/DEBIAN/control
	echo "Section: misc"                                            >> $build_dir/DEBIAN/control
	echo "Priority: optional"                                       >> $build_dir/DEBIAN/control
	echo "Architecture: all"                                        >> $build_dir/DEBIAN/control
	echo "Depends: python, python-gtk2"                             >> $build_dir/DEBIAN/control
	echo "Recommends: python-notify, python-vte"                    >> $build_dir/DEBIAN/control
	echo "Suggests: python-gnome2, python-argparse, python-mutagen" >> $build_dir/DEBIAN/control
	if test "$packager" != "none"; then
		echo "Maintainer: $packager"                                >> $build_dir/DEBIAN/control
	fi
	echo "Installed-Size: 5000"                                     >> $build_dir/DEBIAN/control
	echo "Description: $short_description"                          >> $build_dir/DEBIAN/control

	fakeroot dpkg-deb --build $build_dir
	mv $build_dir.deb sunflower-$version-$release.all.deb

	rm -R $build_dir
}

function make_pkg() {
	install_sunflower src

	echo "pkgname=sunflower"                                   >  PKGBUILD
	echo "pkgver=$version"                                     >> PKGBUILD
	echo "pkgrel=$release"                                     >> PKGBUILD
	echo "arch=(any)"                                          >> PKGBUILD
	echo "url=https://code.google.com/p/sunflower-fm/"         >> PKGBUILD
	echo "license=(GPLv3)"                                     >> PKGBUILD
	echo "depends=(pygtk)"                                     >> PKGBUILD
	echo "optdepends=('python2-notify: notifications',"        >> PKGBUILD
	echo " 'python2-gnomekeyring: access to saved passwords'," >> PKGBUILD
	echo " 'vte: support for built-in terminal')"              >> PKGBUILD
	echo "pkgdesc='$short_description'"                        >> PKGBUILD
	echo ""                                                    >> PKGBUILD
	echo "function build() {"                                  >> PKGBUILD
	echo "    cp -a * \$pkgdir"                                >> PKGBUILD
	echo "}"                                                   >> PKGBUILD

	makepkg --noextract --force
	
	rm -R pkg src PKGBUILD
}

function make_rpm() {	
	case $distro in
		fedora) requires="python pygtk2";;
		mageia) requires="python pygtk2";;
		mandriva) requires="python pygtk2";;
		opensuse) requires="python python-gtk";;
		pclinuxos) requires="python pygtk2.0";;
		*) echo "Unsupported distro"; exit 6;;
	esac

	mkdir -p "$HOME/rpmbuild/RPMS/noarch" "$HOME/rpmbuild/BUILD"

	rpmroot=rpmroot
	buildroot=buildroot
	
	install_sunflower "$rpmroot/$buildroot"
	
	echo "Summary: Sunflower file manager"                                 >  sunflower.spec
	echo "Name: sunflower"                                                 >> sunflower.spec
	echo "Version: $version"                                               >> sunflower.spec
	echo "Release: $release"                                               >> sunflower.spec
	echo "License: GPL"                                                    >> sunflower.spec
	echo "Group: Applications/File"                                        >> sunflower.spec
	echo "BuildArch: noarch"                                               >> sunflower.spec
	echo "Vendor: Sunflower Team"                                          >> sunflower.spec
	if test "$packager" != "none"; then
		echo "Packager: $packager"                                         >> sunflower.spec
	fi
	echo "Requires: $requires"                                             >> sunflower.spec
	echo ""                                                                >> sunflower.spec
	echo "%description"                                                    >> sunflower.spec
	echo "$short_description"                                              >> sunflower.spec
	echo ""                                                                >> sunflower.spec
	echo ""                                                                >> sunflower.spec
	echo "%install"                                                        >> sunflower.spec
	echo ""                                                                >> sunflower.spec
	echo "%files"                                                          >> sunflower.spec
	echo "%defattr(0644,root,root,0755)"                                   >> sunflower.spec
	echo "$sunflower_path/*"                                               >> sunflower.spec
	echo "%attr(0755,root,root) /usr/bin/sunflower"                        >> sunflower.spec
	echo "%attr(0644,root,root) /usr/share/pixmaps/sunflower.png"          >> sunflower.spec
	echo "%attr(0644,root,root) /usr/share/pixmaps/sunflower.svg"          >> sunflower.spec
	echo "%attr(0644,root,root) /usr/share/applications/sunflower.desktop" >> sunflower.spec

	rpmbuild -bb sunflower.spec --root `pwd`/$rpmroot --buildroot $buildroot
	
	rm -R $rpmroot sunflower.spec
	cp ~/rpmbuild/RPMS/noarch/sunflower-$version-$release.noarch.rpm \
	                          sunflower-$version-$release.noarch.$distro.rpm
}

function print_usage() {
	echo -e "Usage:"
	echo -e "\t-t --type     - deb|pkg|rpm [required]\n"
	echo -e "\t-d --distro   - deb: [not used (yet)]"
	echo -e "\t                pkg: [not used]"
	echo -e "\t                rpm: fedora|mageia|mandriva|opensuse|pclinuxos [required]\n"
	echo -e "\t-s --source   - tarball with source [required]\n"
	echo -e "\t-r --release  - actual release [default = 1]\n"
	echo -e "\t-p --packager - info about you\n"
	echo -e "\t-h --help     - print this help"
}

function print_help() {
	print_usage
	echo
	echo -e "You need to have following programs installed in order to build packages:"
	echo -e "\tdeb: dpkg-deb fakeroot"
	echo -e "\tpkg: makepkg"
	echo -e "\trpm: rpmbuild"
	echo
	echo -e "Supported distros:"
	echo -e "\tArch, Debian, Fedora, Mageia, Mandriva, Mint, OpenSUSE, PCLinuxOS, Ubuntu"
	echo
}



if test "`id -u`" = "0"; then
	echo "Don't ever run this script as root!"
	exit 1
fi

while test $# -ne 0; do
	case $1 in
		-t|--type)
			shift
			type=$1
		;;
		-d|--distro)
			shift
			distro=$1
		;;
		-s|--source)
			shift
			source=$1
		;;
		-r|--release)
			shift
			release=$1
		;;
		-p|--packager)
			shift
			packager=$1
		;;
		-h|--help)
			print_help
			exit 0
		;;
		*)
			echo -e "Unknown option $1\n"
			print_usage
			exit 2
	esac

	shift
done

if test "$type" = "none"; then
	echo -e "No type specified\n"
	print_usage
	exit 3
fi

if test "$source" = "none"; then
	echo -e "No source specified\n"
	print_usage
	exit 4
fi

if test ! -e "$source"; then
	echo -e "Source file '$source' does not exists!"
	exit 5
fi

make_$type

