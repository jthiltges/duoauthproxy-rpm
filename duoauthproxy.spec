Name:           duoauthproxy
Version:        2.14.0
%define srctag  bd60798
Release:        1%{?dist}
Summary:        Duo Authentication Proxy

Group:          System Environment/Daemons
License:        Commercial
URL:            https://duo.com/docs/authproxy-reference
Source0:        https://dl.duosecurity.com/duoauthproxy-%{version}-src.tgz
Source1:        authproxy.sample-openldap.cfg
Patch0:         allow-anon-bind.patch

%define svc_user    nobody
%define install_dir /opt/%{name}
%global debug_package %{nil}

# Bytecode compilation fails in lib2to3/tests/data/py3_test_grammar.py
%global _python_bytecompile_errors_terminate_build 0

BuildRequires: gcc
BuildRequires: libffi-devel
BuildRequires: make
BuildRequires: perl
BuildRequires: python-devel
BuildRequires: zlib-devel
%{?systemd_requires}

%description
Proxies RADIUS or LDAP authentication attempts and adds Duo authentication

%prep
%setup -q -n %{name}-%{version}-%{srctag}-src
%patch0 -p1

# Sample config
cp -p %{SOURCE1} conf

# Set username in authproxyctl and duoauthproxy.tap
perl -p -i -e "s/^USER_DEFAULT = None$/USER_DEFAULT = '%{svc_user}'/g" \
    pkgs/duoauthproxy/scripts/authproxyctl \
    pkgs/duoauthproxy/scripts/duoauthproxy.tap

%build
#make %{_smp_mflags}
make -j1

%install
rm -rf %{buildroot}

# The included installer doesn't work with buildroots, so we install manually
#duoauthproxy-build/install --install-dir=%{buildroot}%{install_dir} --service-user=%{svc_user} --create-init-script=yes

########################################################
# Extract the systemd service file from the python installer
mv duoauthproxy-build/install install.py

cat > get_init.py << EOF
import install
params = {'service_user': '%{svc_user}',
          'install_dir':  '%{install_dir}' }

print install.INITSCRIPT_SYSTEMD_TMPL % params
EOF
python get_init.py > init
install -D init %{buildroot}/%{_unitdir}/%{name}.service

########################################################
# Install the application
mkdir -p %{buildroot}/%{install_dir}
cp -a duoauthproxy-build/* %{buildroot}/%{install_dir}

# Remove static libraries from install
# - They are not needed at runtime
# - libpython2.7.a is installed with 555 perms and RPM symbol stripping fails
find %{buildroot} -name '*.a' -delete

# Remove headers and manpages
rm -rf %{buildroot}/%{install_dir}/usr/local/include \
       %{buildroot}/%{install_dir}/usr/local/openssl/include \
       %{buildroot}/%{install_dir}/usr/local/*/man

# Fix the python interpreter path
pkgs/Python-2.7.14/Tools/scripts/pathfix.py -i %{install_dir}/usr/local/bin/python \
  %{buildroot}/%{install_dir}/usr/local/bin \
  %{buildroot}/%{install_dir}/usr/local/lib/python2.7/cgi.py \
  %{buildroot}/%{install_dir}/usr/local/bin/{2to3,authproxy,authproxy_connectivity_tool,authproxyctl,authproxy_primary_only,authproxy_support,automat-visualize,cftp,ckeygen,conch,easy_install,easy_install-2.7,idle,install,m2r,mailmail,netaddr,pbr,pydoc,pyhtmlizer,python2.7-config,tkconch,trial,twist,twistd}
# And remove backup files
rm %{buildroot}/%{install_dir}/usr/local/bin/*~ \
   %{buildroot}/%{install_dir}/usr/local/lib/python2.7/cgi.py~

# Remove unnecessary OpenSSL pieces which drag in perl
rm %{buildroot}/%{install_dir}/usr/local/openssl/{misc/tsget,misc/CA.pl,bin/c_rehash}

# Add symlinks for Duo components
ln -s -t %{buildroot}/%{install_dir}/bin ../usr/local/bin/{authproxy,authproxy_connectivity_tool,authproxy_primary_only,authproxy_support,authproxyctl}

# Switch over to the bundled python for byte-compilation
%define __python %{buildroot}/%{install_dir}/usr/local/bin/python

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
