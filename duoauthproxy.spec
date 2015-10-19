Name:           duoauthproxy
Version:        2.4.12
Release:        1%{?dist}
Summary:        Duo Authentication Proxy

Group:          System Environment/Daemons
License:        Commercial
URL:            https://www.duosecurity.com/docs/ldap
Source0:        https://dl.duosecurity.com/duoauthproxy-%{version}-src.tgz
Source1:        authproxy.sample-openldap.cfg
Patch0:         non-interactive-install.patch
Patch1:         allow-anon-bind.patch

%define svc_user    nobody
%define install_dir /opt/%{name}
%global debug_package %{nil}

BuildRequires: python-devel
BuildRequires: openssl-devel
BuildRequires: perl

# Needed by the init script
Requires: initscripts
Requires: chkconfig

%description
Proxies RADIUS or LDAP authentication attempts and adds Duo authentication

%prep
%setup -q -n %{name}-%{version}-src
%patch0 -p1
%patch1 -p1

# Sample config
cp -p %{SOURCE1} conf

# Set username in authproxyctl
perl -p -i -e "s/^USER_DEFAULT = None$/USER_DEFAULT = '%{svc_user}'/g" pkgs/duoauthproxy/scripts/authproxyctl

%build
make

%install
rm -rf %{buildroot}

# The included installer doesn't work with buildroots, so we install manually
#duoauthproxy-build/install

########################################################
# Extract the RHEL init script from the python installer
mv duoauthproxy-build/install install.py

cat > get_init.py << EOF
import install
params = {'service_user': '%{svc_user}',
          'install_dir':  '%{install_dir}' }

print install.INITSCRIPT_REDHAT_TMPL % params
EOF
python get_init.py > init
install -D init %{buildroot}/%{_initddir}/%{name}

########################################################
# Install the application
mkdir -p %{buildroot}/%{install_dir}
cp -a duoauthproxy-build/* %{buildroot}/%{install_dir}

%clean
rm -rf %{buildroot}

%post
/sbin/chkconfig --add %{name}

%preun
if [ $1 = 0 ]; then # Final removal
    /sbin/service %{name} stop >/dev/null 2>&1 || :
    /sbin/chkconfig --del %{name}
fi

%files
%defattr(-,root,root,-)
%{install_dir}/bin
%config %{install_dir}/conf/ca-bundle.crt
%config(noreplace) %attr(640,%{svc_user},%{svc_user}) %{install_dir}/conf/authproxy.cfg
%{install_dir}/conf/authproxy.sample-openldap.cfg
%{install_dir}/doc
%{install_dir}/include
%{install_dir}/lib
%{install_dir}/lib64
%attr(750,%{svc_user},%{svc_user}) %{install_dir}/log
%attr(750,%{svc_user},%{svc_user}) %{install_dir}/run
%{_initddir}/%{name}

%changelog
* Fri Oct 16 2015 John Thiltges <> 2.4.12-1
- Initial package
