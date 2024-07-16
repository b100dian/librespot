Name:           librespot
Version:        0.4.2
Release:        0
Summary:        librespot is an open source client library for Spotify.
License:        MIT
URL:            https://github.com/librespot-org/librespot
Source0:        https://github.com/librespot-org/librespot/archive/refs/tags/v0.4.2.tar.gz#/%{name}-0.4.2.tar.gz

Source100:      vendor.tar.xz

BuildRequires:  rust
BuildRequires:  cargo
BuildRequires:  alsa-lib-devel
BuildRequires:  pulseaudio-devel
Requires:       alsa-lib
Requires:       pulseaudio

%description
librespot is an open source client library for Spotify. It enables applications to use Spotify's service, without using the official but closed-source libspotify. Additionally, it will provide extra features which are not available in the official library.

Note: librespot only works with Spotify Premium

%define BUILD_DIR "$PWD"/upstream/target
%prep
%setup -q -n %{name}-%{version}/upstream

%ifarch %arm32
%define SB2_TARGET armv7-unknown-linux-gnueabihf
%endif
%ifarch %arm64
%define SB2_TARGET aarch64-unknown-linux-gnu
%endif
%ifarch %ix86
%define SB2_TARGET i686-unknown-linux-gnu
%endif


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

# Adopted from https://github.com/sailfishos/gecko-dev/blob/master/rpm/xulrunner-qt5.spec

export CARGO_HOME="%{BUILD_DIR}/cargo"
export CARGO_BUILD_TARGET=%SB2_TARGET

# When cross-compiling under SB2 rust needs to know what arch to emit
# when nothing is specified on the command line. That usually defaults
# to "whatever rust was built as" but in SB2 rust is accelerated and
# would produce x86 so this is how it knows differently. Not needed
# for native x86 builds
export SB2_RUST_TARGET_TRIPLE=%SB2_TARGET
export RUST_HOST_TARGET=%SB2_TARGET

export RUST_TARGET=%SB2_TARGET
export TARGET=%SB2_TARGET
export HOST=%SB2_TARGET
export SB2_TARGET=%SB2_TARGET

%ifarch %arm32 %arm64
export CROSS_COMPILE=%SB2_TARGET

# This avoids a malloc hang in sb2 gated calls to execvp/dup2/chdir
# during fork/exec. It has no effect outside sb2 so doesn't hurt
# native builds.
export SB2_RUST_EXECVP_SHIM="/usr/bin/env LD_PRELOAD=/usr/lib/libsb2/libsb2.so.1 /usr/bin/env"
export SB2_RUST_USE_REAL_EXECVP=Yes
export SB2_RUST_USE_REAL_FN=Yes
%endif

export CC=gcc
export CXX=g++
export AR="ar"
export NM="gcc-nm"
export RANLIB="gcc-ranlib"
export PKG_CONFIG="pkg-config"

export RUSTFLAGS="-Clink-arg=-Wl,-z,relro,-z,now -Ccodegen-units=1 %{?rustflags}"
export CARGO_INCREMENTAL=0

export CRATE_CC_NO_DEFAULTS=1

cargo build --offline --verbose --release --features "pulseaudio-backend" --target-dir=%{BUILD_DIR}

%install
mkdir -p %{buildroot}/%{_bindir}
install %{BUILD_DIR}/%{SB2_TARGET}/release/librespot %{buildroot}/%{_bindir}/librespot

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
