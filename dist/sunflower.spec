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
mkdir -p $FEDORA_BUILD_DIRECTORY
tar -xf $FILE_PATH.tar -C $BUILD_DIRECTORY
install -Dm755 $WORKING_DIRECTORY/dist/sunflower "$FEDORA_BUILD_DIRECTORY/usr/bin/sunflower"
install -d "$FEDORA_BUILD_DIRECTORY/usr/share/sunflower"
cp -r $BUILD_DIRECTORY/Sunflower/* "$FEDORA_BUILD_DIRECTORY/usr/share/sunflower"
install -Dm644 "$BUILD_DIRECTORY/Sunflower/images/sunflower.png" "$FEDORA_BUILD_DIRECTORY/usr/share/pixmaps/sunflower.png"
install -Dm644 "$BUILD_DIRECTORY/Sunflower/images/sunflower.svg" "$FEDORA_BUILD_DIRECTORY/usr/share/pixmaps/sunflower.svg"
install -Dm644 "$BUILD_DIRECTORY/Sunflower/Sunflower.desktop" "$FEDORA_BUILD_DIRECTORY/usr/share/applications/sunflower.desktop"

%files
%defattr(0644,root,root,0755)
/usr/share/sunflower/*
%attr(0755,root,root) /usr/bin/sunflower
%attr(0755,root,root) /usr/share/sunflower/Sunflower.py
%attr(0644,root,root) /usr/share/pixmaps/sunflower.png
%attr(0644,root,root) /usr/share/pixmaps/sunflower.svg
%attr(0644,root,root) /usr/share/applications/sunflower.desktop
