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
@short_description@


%install
install -Dm755 %{buildroot}/../../dist/sunflower "%{buildroot}/usr/bin/sunflower"
install -d "%{buildroot}/usr/share/sunflower"
cp -r %{buildroot}/../Sunflower/* "%{buildroot}/usr/share/sunflower"
install -Dm644 "%{buildroot}/../Sunflower/images/sunflower.png" "%{buildroot}/usr/share/pixmaps/sunflower.png"
install -Dm644 "%{buildroot}/../Sunflower/images/sunflower.svg" "%{buildroot}/usr/share/pixmaps/sunflower.svg"
install -Dm644 "%{buildroot}/../Sunflower/Sunflower.desktop" "%{buildroot}/usr/share/applications/sunflower.desktop"


%files
%defattr(0644,root,root,0755)
/usr/share/sunflower/*
%attr(0755,root,root) /usr/bin/sunflower
%attr(0755,root,root) /usr/share/sunflower/Sunflower.py
%attr(0644,root,root) /usr/share/pixmaps/sunflower.png
%attr(0644,root,root) /usr/share/pixmaps/sunflower.svg
%attr(0644,root,root) /usr/share/applications/sunflower.desktop

