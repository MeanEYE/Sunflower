%{!?__python3: %global __python3 /usr/bin/python3}
%{!?python3_sitelib: %global python3_sitelib %(%{__python3} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

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
mkdir -p "$RPM_BUILD_ROOT/usr/share/sunflower"
mkdir -p "$RPM_BUILD_ROOT/usr/share/icons/hicolor/scalable/apps"
install -d "$RPM_BUILD_ROOT/usr/share/pixmaps/sunflower"
install -d "$RPM_BUILD_ROOT%{python3_sitelib}/sunflower"

tar -xf build/sunflower-*.tar -C build/
install -Dm755 "dist/sunflower" "$RPM_BUILD_ROOT/usr/local/bin/sunflower"
cp -r build/Sunflower/sunflower/* "$RPM_BUILD_ROOT%{python3_sitelib}/sunflower"
cp -r build/Sunflower/styles "$RPM_BUILD_ROOT/usr/share/sunflower"
cp -r build/Sunflower/images "$RPM_BUILD_ROOT/usr/share/sunflower"
rsync -r build/Sunflower/translations/* "$RPM_BUILD_ROOT/usr/share/locale" --exclude "*.po*"
install -Dm644 "build/Sunflower/images/sunflower.svg" "$RPM_BUILD_ROOT/usr/share/pixmaps/sunflower.svg"
install -Dm644 "build/Sunflower/Sunflower.desktop" "$RPM_BUILD_ROOT/usr/share/applications/sunflower.desktop"
desktop-file-edit --add-category="X-MandrivaLinux-System-FileTools" "$RPM_BUILD_ROOT/usr/share/applications/sunflower.desktop"

%files
%defattr(0644,root,root,0755)
%attr(0755,root,root) /usr/local/bin/sunflower
/%{python3_sitelib}/sunflower/*
/usr/share/locale/*
/usr/share/pixmaps/sunflower.svg
/usr/share/applications/sunflower.desktop
/usr/share/sunflower/images/*.png
/usr/share/sunflower/images/*.svg
/usr/share/sunflower/styles/*.css
%doc README.md CHANGES COPYING LICENSE AUTHORS
