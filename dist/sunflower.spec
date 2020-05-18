Summary: Sunflower file manager
Name: sunflower
Version: @version@
Release: @release@
License: GPL
Group: Applications/File
BuildArch: noarch
Vendor: Sunflower Team
Packager: @packager@
Requires: @requires@

%description
Small and highly customizable twin-panel file manager for Linux with support for plugins.

%install
mkdir -p "$RPM_BUILD_ROOT"
mkdir -p "$RPM_BUILD_ROOT/usr/local/bin"
mkdir -p "$RPM_BUILD_ROOT/usr/share/locale"
mkdir -p "$RPM_BUILD_ROOT/usr/share/applications"
mkdir -p "$RPM_BUILD_ROOT/usr/share/icons/hicolor/scalable/apps"
install -d "$RPM_BUILD_ROOT/usr/share/pixmaps/sunflower"
install -d "$RPM_BUILD_ROOT/usr/lib/python3/dist-packages/sunflower"

tar -xf build/sunflower-*.tar -C build/
install -Dm755 "dist/sunflower" "$RPM_BUILD_ROOT/usr/local/bin/sunflower"
cp -r build/Sunflower/sunflower/* "$RPM_BUILD_ROOT/usr/lib/python3/dist-packages/sunflower"
rsync -r build/Sunflower/translations/* "$RPM_BUILD_ROOT/usr/share/locale" --exclude "*.po*"
install -Dm644 "build/Sunflower/images/sunflower.png" "$RPM_BUILD_ROOT/usr/share/pixmaps/sunflower.png"
install -Dm644 "build/Sunflower/images/sunflower.svg" "$RPM_BUILD_ROOT/usr/share/pixmaps/sunflower.svg"
install -Dm644 "build/Sunflower/Sunflower.desktop" "$RPM_BUILD_ROOT/usr/share/applications/sunflower.desktop"
desktop-file-edit --add-category="X-MandrivaLinux-System-FileTools" "$RPM_BUILD_ROOT/usr/share/applications/sunflower.desktop"

%files
%defattr(0644,root,root,0755)
/usr/share/sunflower/*
%attr(0755,root,root) /usr/local/bin/sunflower
%attr(0644,root,root) /usr/share/pixmaps/sunflower.png
%attr(0644,root,root) /usr/share/pixmaps/sunflower.svg
%attr(0644,root,root) /usr/share/applications/sunflower.desktop
%doc README.md CHANGES COPYING LICENSE AUTHORS
