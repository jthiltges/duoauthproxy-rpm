Name:           duoauthproxy
Version:        6.1.0
Release:        1%{?dist}
Summary:        Duo Authentication Proxy

Group:          System Environment/Daemons
License:        Commercial
URL:            https://duo.com/docs/authproxy-reference
Source0:        https://dl.duosecurity.com/duoauthproxy-%{version}-src.tgz
Source1:        authproxy.sample-openldap.cfg
Source2:        duoauthproxy.service
Patch0:	        0001-Remove-the-checks-requiring-a-bind_dn.patch
Patch1:	        0002-Add-install-root-to-installer-and-skip-ownership-cha.patch


%define svc_user    nobody
%define install_dir /opt/%{name}
%global debug_package %{nil}

# Bytecode compilation fails in lib2to3/tests/data/py3_test_grammar.py
%global _python_bytecompile_errors_terminate_build 0
%global __brp_mangle_shebangs_exclude_from %{install_dir}

BuildRequires: gcc
BuildRequires: make
BuildRequires: libffi-devel
#BuildRequires: perl
#BuildRequires: python-devel
BuildRequires: zlib-devel
BuildRequires: diffutils
BuildRequires: procps-ng
BuildRequires: systemd-rpm-macros
%{?systemd_requires}

%description
Proxies RADIUS or LDAP authentication attempts and adds Duo authentication

%prep
%setup -q -n %{name}-%{version}-src
%patch -P 0 -p1
%patch -P 1 -p1

# Sample config
cp -p %{SOURCE1} conf

# Set username in authproxyctl and duoauthproxy.tap
#perl -p -i -e "s/^USER_DEFAULT = None$/USER_DEFAULT = '%{svc_user}'/g" \
#    pkgs/duoauthproxy/scripts/authproxyctl \
#    pkgs/duoauthproxy/scripts/duoauthproxy.tap

%build
#make %{_smp_mflags}
make -j1

%install
rm -rf %{buildroot}
duoauthproxy-build/install --install-root=%{buildroot} --install-dir=%{install_dir} --service-user=%{svc_user} --create-init-script=no --log-group=nobody

mkdir -p %{buildroot}%{_unitdir}
install -m 644 %{SOURCE2} %{buildroot}%{_unitdir}/%{name}.service

%clean
rm -rf %{buildroot}

%post
%systemd_post %{name}.service
%preun
%systemd_preun %{name}.service
%postun
%systemd_postun_with_restart %{name}.service

%files
%defattr(-,root,root,-)
%{install_dir}/bin
%config %{install_dir}/conf/ca-bundle.crt
%config(noreplace) %attr(640,%{svc_user},%{svc_user}) %{install_dir}/conf/authproxy.cfg
%{install_dir}/conf/authproxy.sample-openldap.cfg
%{install_dir}/doc
%attr(750,%{svc_user},%{svc_user}) %{install_dir}/log
%attr(750,%{svc_user},%{svc_user}) %{install_dir}/run
%{install_dir}/usr
%{_unitdir}/%{name}.service

%changelog
* Thu Feb 21 2019 John Thiltges <> 2.14.0-1
- Upstream release 2.14.0

* Mon May 16 2016 John Thiltges <> 2.4.17-1
- Upstream release 2.4.17

* Fri Oct 16 2015 John Thiltges <> 2.4.12-1
- Initial package
