%global vimdir %{_datadir}/vim/vimfiles
%global commit f7c2274b84394bcf6607284fe4f48ab606c988d5
%global shortcommit %(c=%{commit}; echo ${c:0:7})

Summary: Text based document generation
Name: asciidoc
Version: 8.6.10
Release: 0.5.20180627git%{shortcommit}%{?dist}
# The python code does not specify a version.
# The javascript example code is GPLv2+.
License: GPL+ and GPLv2+

URL: http://asciidoc.org
# Tarball name has to be modified, due github repo 
# is called asciidoc-py3 instead of asciidoc
# This solution is temporary, due upstream 
# haven't released 8.6.10 version yet.
# https://github.com/%%{name}/%%{name}-py3/archive/%%{version}.tar.gz
Source0: %{name}-py3-%{commit}.tar.gz

Patch1: asciidoc-music-noship.patch
Patch2: asciidoc-remove-music.patch

BuildRequires: python3-devel
BuildRequires: dblatex
BuildRequires: docbook-style-xsl
BuildRequires: graphviz
BuildRequires: libxslt
BuildRequires: source-highlight
BuildRequires: texlive-dvipng-bin
BuildRequires: texlive-dvisvgm-bin
BuildRequires: vim-filesystem
BuildRequires: symlinks
BuildRequires: automake
BuildRequires: autoconf

Requires: %{__python3}
Requires: docbook-style-xsl
Requires: graphviz
Requires: libxslt
Requires: source-highlight
Requires: vim-filesystem

BuildArch: noarch

%description
AsciiDoc is a text document format for writing short documents,
articles, books and UNIX man pages. AsciiDoc files can be translated
to HTML and DocBook markups using the asciidoc(1) command.

%package doc
Summary:  Additional documentation and examples for asciidoc
Requires: %{name} = %{version}-%{release}

%description doc
%{summary}.

%package latex
Summary:  Support for asciidoc latex output
Requires: %{name} = %{version}-%{release}
Requires: dblatex
Requires: texlive-dvipng-bin

%description latex
%{summary}.

%prep
%autosetup -p1 -n %{name}-py3-%{commit}
rm -rf filters/music
# Fix line endings on COPYRIGHT file
sed -i "s/\r//g" COPYRIGHT

# Convert README and dict files to utf-8
for file in README.asciidoc doc/*.dict examples/website/*.dict; do
    iconv -f ISO-8859-1 -t UTF-8 -o $file.new $file && \
    touch -r $file $file.new && \
    mv $file.new $file
done

# Fix python shebang
grep -rl '#!/usr/bin/env python' | xargs -r \
    sed -i -e '1s@#!/usr/bin/env python3\?$@#!%{__python3}@'

%build
autoreconf -v
%configure

%install
make install docs DESTDIR=%{buildroot}

install -dm 755 %{buildroot}%{_datadir}/asciidoc/
# real conf data goes to sysconfdir, rest to datadir; symlinks so asciidoc works
for d in dblatex docbook-xsl images javascripts stylesheets; do
    mv -v %{buildroot}%{_sysconfdir}/asciidoc/$d \
          %{buildroot}%{_datadir}/asciidoc/
    # absolute symlink into buildroot is intentional, see below
    ln -s %{buildroot}%{_datadir}/%{name}/$d %{buildroot}%{_sysconfdir}/%{name}/

    # let's symlink stuff for documentation as well so we don't duplicate things
    rm -rf %{buildroot}%{_docdir}/%{name}/$d
    # absolute symlink into buildroot is intentional, see below
    ln -s %{buildroot}%{_datadir}/%{name}/$d %{buildroot}%{_docdir}/%{name}/
done

# Python API
mkdir -p %{buildroot}%{python3_sitelib}/
sed '1d' asciidocapi.py > %{buildroot}%{python3_sitelib}/asciidocapi.py
chmod -x %{buildroot}%{python3_sitelib}/asciidocapi.py
touch -r asciidocapi.py %{buildroot}%{python3_sitelib}/asciidocapi.py

# Make it easier to %%exclude these with both rpm < and >= 4.7
for file in %{buildroot}{%{_bindir},%{_sysconfdir}/asciidoc/filters/*}/*.py ; do
    touch ${file}{c,o}
done

mkdir -p %{buildroot}%{vimdir}/{ftdetect,syntax}
for file in $(cd vim; find * -type f); do
    install -m 0644 vim/$file %{buildroot}%{vimdir}/$file
done

# Absolute symlinks were used above to be able to detect dangling ones. Make
# them relative now (sane for being installed) and remove dangling symlinks.
symlinks -cdr %{buildroot}

# Clean up no needed doc files
for file in BUGS.txt CHANGELOG.txt INSTALL INSTALL.txt README.txt; do
    rm -f %{buildroot}/%{_pkgdocdir}/$file
done

%check
export PATH="../:$PATH"
cd tests
%{__python3} testasciidoc.py update
%{__python3} testasciidoc.py run

%files
%doc COPYING COPYRIGHT README.asciidoc
%doc %{_mandir}/man1/a2x.1*
%doc %{_mandir}/man1/asciidoc.1*
%config(noreplace) %{_sysconfdir}/asciidoc/
%{_bindir}/a2x
%{_bindir}/a2x.py
%{_bindir}/asciidoc
%{_bindir}/asciidoc.py
%{_datadir}/asciidoc/
%{python3_sitelib}/asciidocapi.py*
%{python3_sitelib}/__pycache__/asciidocapi*
%{vimdir}/syntax/asciidoc.vim
%exclude %{_bindir}/*.py[co]
%exclude %{_sysconfdir}/asciidoc/filters/*/*.py[co]
%exclude %{_sysconfdir}/asciidoc/filters/latex
%exclude %{_pkgdocdir}/examples
%exclude %{_pkgdocdir}/doc
%exclude %{_pkgdocdir}/{dblatex,docbook-xsl,images,javascripts,stylesheets}

%files doc
%{_pkgdocdir}/examples
%{_pkgdocdir}/doc
%{_pkgdocdir}/{dblatex,docbook-xsl,images,javascripts,stylesheets}
%exclude %{_docdir}/%{name}/{COPYING,COPYRIGHT,README.asciidoc}

%files latex
%dir %{_sysconfdir}/asciidoc/filters/latex
%{_sysconfdir}/asciidoc/filters/latex/*.py
%config(noreplace) %{_sysconfdir}/asciidoc/filters/latex/*.conf

%changelog
* Wed Sep 19 2018 Tomas Orsava <torsava@redhat.com> - 8.6.10-0.5.20180627gitf7c2274
- Require the Python interpreter directly instead of using the package name
- Related: rhbz#1619153

* Tue Aug 14 2018 Josef Ridky <jridky@redhat.com> - 8.6.10-0.4.20180627gitf7c2274
- Remove ImageMagic requirement

* Wed Jun 27 2018 Josef Ridky <jridky@redhat.com> - 8.6.10-0.3.20180627gitf7c2274
- Update to master branch version from 27/06/2018

* Thu Jun 14 2018 Josef Ridky <jridky@redhat.com> - 8.6.10-0.2.20180605git986f99d
- Various rpmlint fixes
- Remove musicfilter from package (#1571138)

* Wed Jun 06 2018 Josef Ridky <jridky@redhat.com> - 8.6.10-0.1.20180605git986f99d
- New upstream version with Python3 support - asciidoc-py3 (commit 986f99d)
- Update versioning, Source and Url label information

* Wed Feb 14 2018 Josef Ridky <jridky@redhat.com> - 8.6.8-15
- spec file cleanup (remove Group tag, use autosetup)
- add python2 build support for RHEL

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 8.6.8-14
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Wed Dec 06 2017 Todd Zullinger <tmz@pobox.com> - 8.6.8-13
- Explicitly use python2, in preparation for python3 becoming the default
  python

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 8.6.8-12
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 8.6.8-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 8.6.8-10
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 8.6.8-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Fri Oct 30 2015 Stanislav Ochotnicky <sochotnicky@redhat.com> - 8.6.8-8
- Fix build due to doc files (rhbz#1266596)

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 8.6.8-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 8.6.8-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Mon Feb 10 2014 Nils Philippsen <nils@redhat.com> - 8.6.8-5
- explicitly use system copy of Python 2.x
- fix broken and remove dangling symlinks

* Tue Dec 03 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 8.6.8-3
- Fix duplicate documentation files (#1001234)
- Fix encoding of manifests being written (#968308)

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 8.6.8-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Thu Mar  7 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 8.6.8-1
- Update to latest upstream version
- Move things around make docs dir actually working
- Add proper requires on vim-filesystem
- Run testsuite
- Split music and latex support to subpackages

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 8.4.5-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 8.4.5-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Thu Jan 12 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 8.4.5-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 8.4.5-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Wed Jul 21 2010 David Malcolm <dmalcolm@redhat.com> - 8.4.5-5
- Rebuilt for https://fedoraproject.org/wiki/Features/Python_2.7/MassRebuild

* Tue Sep  8 2009 Ville Skyttä <ville.skytta@iki.fi> - 8.4.5-4
- Remaining improvements from #480288:
- Add dependencies on libxslt and docbook-style-xsl.
- Install dblatex style sheets.
- Exclude unneeded *.py[co].
- Install python API.
- Specfile cleanups.

* Thu Aug 13 2009 Todd Zullinger <tmz@pobox.com> - 8.4.5-3
- Use 'unsafe' mode by default (bug 506953)
- Install filter scripts in %%{_datadir}/asciidoc
- Convert spec file, CHANGELOG, and README to utf-8
- Preserve timestamps on installed files, where feasible
- s/$RPM_BUILD_ROOT/%%{buildroot} and drop duplicated /'s
- Fix rpmlint mixed-use-of-spaces-and-tabs and end-of-line-encoding warnings

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 8.4.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Fri Jun 19 2009 Dave Airlie <airlied@redhat.com> 8.4.5-1
- new upstream version 8.4.5 - required by X.org libXi to build

* Mon Feb 23 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 8.2.5-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Thu May 22 2008 Tom "spot" Callaway <tcallawa@redhat.com> - 8.2.5-3
- fix license tag

* Wed Dec 05 2007 Florian La Roche <laroche@redhat.com> - 8.2.5-2
- remove doc/examples from filelist due to dangling symlinks

* Tue Nov 20 2007 Florian La Roche <laroche@redhat.com> - 8.2.5-1
- new upstream version 8.2.5

* Mon Oct 22 2007 Florian La Roche <laroche@redhat.com> - 8.2.3-1
- new upstream version 8.2.3

* Sat Sep 01 2007 Florian La Roche <laroche@redhat.com> - 8.2.2-1
- new upstream version 8.2.2

* Mon Mar 19 2007 Chris Wright <chrisw@redhat.com> - 8.1.0-1
- update to asciidoc 8.1.0

* Thu Sep 14 2006 Chris Wright <chrisw@redhat.com> - 7.0.2-3
- rebuild for Fedora Extras 6

* Tue Feb 28 2006 Chris Wright <chrisw@redhat.com> - 7.0.2-2
- rebuild for Fedora Extras 5

* Mon Aug 29 2005 Chris Wright <chrisw@osdl.org> - 7.0.2-1
- convert spec file to UTF-8
- Source should be URL
- update to 7.0.2

* Fri Aug 19 2005 Chris Wright <chrisw@osdl.org> - 7.0.1-3
- consistent use of RPM_BUILD_ROOT

* Thu Aug 18 2005 Chris Wright <chrisw@osdl.org> - 7.0.1-2
- Update BuildRoot
- use _datadir
- use config and _sysconfdir

* Wed Jun 29 2005 Terje Røsten <terje.rosten@ntnu.no> - 7.0.1-1
- 7.0.1
- Drop patch now upstream
- Build as noarch (Petr Klíma)

* Sat Jun 11 2005 Terje Røsten <terje.rosten@ntnu.no> - 7.0.0-0.3
- Add include patch

* Fri Jun 10 2005 Terje Røsten <terje.rosten@ntnu.no> - 7.0.0-0.2
- Fix stylesheets according to Stuart

* Fri Jun 10 2005 Terje Røsten <terje.rosten@ntnu.no> - 7.0.0-0.1
- Initial package
- Based on Debian package, thx!
