Name:           librespot
Version:        0.4.2
Release:        0
Summary:        librespot is an open source client library for Spotify.
License:        MIT
URL:            https://github.com/librespot-org/librespot
Source0:        https://github.com/librespot-org/librespot/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

Source100:      vendor.tar.xz
Source200:      librespot-patches.tar.gz

BuildRequires:  rust
BuildRequires:  cargo
BuildRequires:  alsa-lib-devel
BuildRequires:  pulseaudio-devel
BuildRequires:  alsa-lib
BuildRequires:  pulseaudio
Requires:       pulseaudio

%description
librespot is an open source client library for Spotify. It enables applications to use Spotify's service, without using the official but closed-source libspotify. Additionally, it will provide extra features which are not available in the official library.

Note: librespot only works with Spotify Premium

%prep
%setup -q -n %{name}-%{version}

# seems to need local stuff
tar -xJf %SOURCE100

# define the offline registry
%global cargo_home $PWD/.cargo
mkdir -p %{cargo_home}
cat >.cargo/config <<EOF
[source.crates-io]
replace-with = "vendored-sources"

[source.vendored-sources]
directory = "vendor"
EOF

# dependencies from plietar (github) also in local form
tar -xzf %SOURCE200

# use our offline registry
export CARGO_HOME="%{cargo_home}"

%build

#cargo build --verbose --release --features "alsa-backend pulseaudio-backend"
cargo build --offline --verbose --release --features "pulseaudio-backend"

%install
mkdir -p %{buildroot}/%{_bindir}
install ./target/release/librespot %{buildroot}/%{_bindir}/librespot

mkdir -p %{buildroot}/%{_sysconfdir}/pulse/xpolicy.conf.d/
cp -r ./sailfish/etc/* %{buildroot}/%{_sysconfdir}/

%preun
if [ "$1" = "0" ]; then
  systemctl-user stop librespot || true
  systemctl-user disable librespot || true
fi

# also restart pulseaudio to set audio permissions for librespot
%post
systemctl-user daemon-reload || true
systemctl-user enable librespot || true
systemctl-user try-restart pulseaudio || true

%pre
if [ "$1" = "2" ]; then
  systemctl-user stop librespot || true
  systemctl-user disable librespot || true
fi

%files
%defattr(-,root,root)
%{_bindir}/librespot
%config(noreplace) %{_sysconfdir}/pulse/xpolicy.conf.d/librespot.conf
%config(noreplace) %{_sysconfdir}/default/librespot
%config(noreplace) %{_sysconfdir}/systemd/user/librespot.service

%changelog
* Fri Feb 22 2019 wdehoog <jdoe@example.com> - 0.0.5
- include uri fix from librespot-org (issue 288 which caused librespot to stop working)
- set device type to smartphone in systemd service file
* Thu Jan 10 2019 wdehoog <jdoe@example.com> - 0.0.4
- use latest master branch but without proto-rust update since rust version
  available on OBS cannot compile that.
* Fri Jan 4 2019 wdehoog <jdoe@example.com> - 0.0.3
- use rpassword crate 2.1.0 to be able to read pasword from stdin
* Fri Jul 21 2018 wdehoog <jdoe@example.com> - 0.0.1
- config and systemd stuff
- patched rust-mdns for 'old' kernel
- initial packaging
