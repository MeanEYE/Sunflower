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

%files
%defattr(0644,root,root,0755)
/usr/share/sunflower/*
%attr(0755,root,root) /usr/bin/sunflower
%attr(0755,root,root) /usr/share/sunflower/Sunflower.py
%attr(0644,root,root) /usr/share/pixmaps/sunflower.png
%attr(0644,root,root) /usr/share/pixmaps/sunflower.svg
%attr(0644,root,root) /usr/share/applications/sunflower.desktop

