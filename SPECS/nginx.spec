%global  nginx_user          nginx
%global  nginx_group         %{nginx_user}
%global  nginx_home          %{_localstatedir}/lib/nginx
%global  nginx_home_tmp      %{nginx_home}/tmp
%global  nginx_logdir        %{_localstatedir}/log/nginx
%global  nginx_confdir       %{_sysconfdir}/nginx
%global  nginx_datadir       %{_datadir}/nginx
%global  nginx_webroot       %{nginx_datadir}/html

%global real_name            nginx

Name:              nginx-testcookie
Version:           1.5.9
Release:           1.vortex%{?dist}
Conflicts:         nginx

Summary:           A high performance web server and reverse proxy server
Group:             System Environment/Daemons
# BSD License (two clause)
# http://www.freebsd.org/copyright/freebsd-license.html
License:           BSD
URL:               http://nginx.org/

Source0:           http://nginx.org/download/nginx-%{version}.tar.gz
Source1:           nginx.init
Source2:           nginx.logrotate
Source3:           nginx.conf
Source4:           default.conf
Source5:           ssl.conf
Source6:           virtual.conf
Source7:           nginx.sysconfig
Source100:         index.html
Source101:         poweredby.png
Source102:         nginx-logo.png
Source103:         404.html
Source104:         50x.html
Source200:         testcookie-nginx-module-master.tar.gz

# removes -Werror in upstream build scripts.  -Werror conflicts with
# -D_FORTIFY_SOURCE=2 causing warnings to turn into errors.
Patch0:     nginx-auto-cc-gcc.patch

BuildRequires:     GeoIP-devel, libcom_err-devel
BuildRequires:     gd-devel, keyutils-libs-devel
BuildRequires:     libxslt-devel, libsepol-devel
BuildRequires:     openssl-devel, libselinux-devel
BuildRequires:     pcre-devel, krb5-devel
BuildRequires:     perl-devel
BuildRequires:     perl(ExtUtils::Embed)
BuildRequires:     zlib-devel
Requires:          GeoIP
Requires:          gd
Requires:          openssl
Requires:          pcre
Requires:          perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))
Requires(pre):     shadow-utils
Requires(post):    chkconfig
Requires(preun):   chkconfig, initscripts
Requires(postun):  initscripts
Provides:          webserver

%description
Nginx is a web server and a reverse proxy server for HTTP, SMTP, POP3 and
IMAP protocols, with a strong focus on high concurrency, performance and low
memory usage.


%prep
%setup -q -n %{real_name}-%{version}
%patch0 -p0
tar xf %{SOURCE200}


%build
# nginx does not utilize a standard configure script.  It has its own
# and the standard configure options cause the nginx configure script
# to error out.  This is is also the reason for the DESTDIR environment
# variable.
export DESTDIR=%{buildroot}
./configure \
    --prefix=%{nginx_datadir} \
    --sbin-path=%{_sbindir}/nginx \
    --conf-path=%{nginx_confdir}/nginx.conf \
    --error-log-path=%{nginx_logdir}/error.log \
    --http-log-path=%{nginx_logdir}/access.log \
    --http-client-body-temp-path=%{nginx_home_tmp}/client_body \
    --http-proxy-temp-path=%{nginx_home_tmp}/proxy \
    --http-fastcgi-temp-path=%{nginx_home_tmp}/fastcgi \
    --http-uwsgi-temp-path=%{nginx_home_tmp}/uwsgi \
    --http-scgi-temp-path=%{nginx_home_tmp}/scgi \
    --pid-path=%{_localstatedir}/run/nginx.pid \
    --lock-path=%{_localstatedir}/lock/subsys/nginx \
    --user=%{nginx_user} \
    --group=%{nginx_group} \
    --with-file-aio \
    --with-ipv6 \
    --with-http_ssl_module \
    --with-http_realip_module \
    --with-http_addition_module \
    --with-http_xslt_module \
    --with-http_image_filter_module \
    --with-http_geoip_module \
    --with-http_sub_module \
    --with-http_dav_module \
    --with-http_flv_module \
    --with-http_mp4_module \
    --with-http_gzip_static_module \
    --with-http_random_index_module \
    --with-http_secure_link_module \
    --with-http_degradation_module \
    --with-http_stub_status_module \
    --with-http_perl_module \
    --with-mail \
    --with-mail_ssl_module \
    --with-debug \
    --with-cc-opt="%{optflags} $(pcre-config --cflags)" \
    --add-module=testcookie-nginx-module-master \
    --with-ld-opt="-Wl,-E" # so the perl module finds its symbols

make %{?_smp_mflags}


%install
make install DESTDIR=%{buildroot} INSTALLDIRS=vendor

find %{buildroot} -type f -name .packlist -exec rm -f '{}' \;
find %{buildroot} -type f -name perllocal.pod -exec rm -f '{}' \;
find %{buildroot} -type f -empty -exec rm -f '{}' \;
find %{buildroot} -type f -iname '*.so' -exec chmod 0755 '{}' \;

install -p -D -m 0755 %{SOURCE1} \
    %{buildroot}%{_initrddir}/nginx
install -p -D -m 0644 %{SOURCE2} \
    %{buildroot}%{_sysconfdir}/logrotate.d/nginx
install -p -D -m 0644 %{SOURCE7} \
    %{buildroot}%{_sysconfdir}/sysconfig/nginx

install -p -d -m 0755 %{buildroot}%{nginx_confdir}/conf.d
install -p -d -m 0700 %{buildroot}%{nginx_home}
install -p -d -m 0700 %{buildroot}%{nginx_home_tmp}
install -p -d -m 0700 %{buildroot}%{nginx_logdir}
install -p -d -m 0755 %{buildroot}%{nginx_webroot}

install -p -m 0644 %{SOURCE3} \
    %{buildroot}%{nginx_confdir}
install -p -m 0644 %{SOURCE4} %{SOURCE5} %{SOURCE6} \
    %{buildroot}%{nginx_confdir}/conf.d
install -p -m 0644 %{SOURCE100} \
    %{buildroot}%{nginx_webroot}
install -p -m 0644 %{SOURCE101} %{SOURCE102} \
    %{buildroot}%{nginx_webroot}
install -p -m 0644 %{SOURCE103} %{SOURCE104} \
    %{buildroot}%{nginx_webroot}

install -p -D -m 0644 %{_builddir}/nginx-%{version}/man/nginx.8 \
    %{buildroot}%{_mandir}/man8/nginx.8

%pre
getent group %{nginx_group} > /dev/null || groupadd -r %{nginx_group}
getent passwd %{nginx_user} > /dev/null || \
    useradd -r -d %{nginx_home} -g %{nginx_group} \
    -s /sbin/nologin -c "Nginx web server" %{nginx_user}
exit 0

%post
if [ $1 -eq 1 ]; then
    /sbin/chkconfig --add %{name}
fi
if [ $1 -eq 2 ]; then
    # Make sure these directories are not world readable.
    chmod 700 %{nginx_home}
    chmod 700 %{nginx_home_tmp}
    chmod 700 %{nginx_logdir}
fi

%preun
if [ $1 -eq 0 ]; then
    /sbin/service %{name} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{name}
fi

%postun
if [ $1 -eq 2 ]; then
    /sbin/service %{name} upgrade || :
fi

%files
%doc LICENSE CHANGES README
%{nginx_datadir}/
%{_sbindir}/nginx
%{_mandir}/man3/nginx.3pm*
%{_mandir}/man8/nginx.8*
%{_initrddir}/nginx
%dir %{nginx_confdir}
%dir %{nginx_confdir}/conf.d
%config(noreplace) %{nginx_confdir}/fastcgi.conf
%config(noreplace) %{nginx_confdir}/fastcgi.conf.default
%config(noreplace) %{nginx_confdir}/fastcgi_params
%config(noreplace) %{nginx_confdir}/fastcgi_params.default
%config(noreplace) %{nginx_confdir}/koi-utf
%config(noreplace) %{nginx_confdir}/koi-win
%config(noreplace) %{nginx_confdir}/mime.types
%config(noreplace) %{nginx_confdir}/mime.types.default
%config(noreplace) %{nginx_confdir}/nginx.conf
%config(noreplace) %{nginx_confdir}/nginx.conf.default
%config(noreplace) %{nginx_confdir}/scgi_params
%config(noreplace) %{nginx_confdir}/scgi_params.default
%config(noreplace) %{nginx_confdir}/uwsgi_params
%config(noreplace) %{nginx_confdir}/uwsgi_params.default
%config(noreplace) %{nginx_confdir}/win-utf
%config(noreplace) %{nginx_confdir}/conf.d/*.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/nginx
%config(noreplace) %{_sysconfdir}/sysconfig/nginx
%dir %{perl_vendorarch}/auto/nginx
%{perl_vendorarch}/nginx.pm
%{perl_vendorarch}/auto/nginx/nginx.so
%attr(700,%{nginx_user},%{nginx_group}) %dir %{nginx_home}
%attr(700,%{nginx_user},%{nginx_group}) %dir %{nginx_home_tmp}
%attr(700,%{nginx_user},%{nginx_group}) %dir %{nginx_logdir}


%changelog
* Thu Jul 24 2014 Ilya Otyutskiy <ilya.otyutskiy@icloud.com> - 1.5.9-1.vortex
- Add testcookie module.
