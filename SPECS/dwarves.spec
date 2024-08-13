%global package_speccommit ac484050d9d35d6e139e66727bf450e63467cd0c
%global usver 1.26
%global xsver 3
%global xsrel %{xsver}%{?xscount}%{?xshash}
%define libname libdwarves
%define libver 1

# Workaround until libdw of devtoolset-11 is fixed
%if 0%{?xenserver} >= 9
%bcond_with    static_libdw
%else
%bcond_without static_libdw
%endif

Name: dwarves
Version: 1.26
Release: %{?xsrel}%{?dist}
License: GPL-2.0-only
Summary: Debugging Information Manipulation Tools (pahole & friends)
URL: http://acmel.wordpress.com
Source0: dwarves-1.26.tar.xz
Requires: %{libname}%{libver} = %{version}-%{release}
%if 0%{?xenserver} >= 9
BuildRequires: gcc
BuildRequires: cmake >= 2.8.12
BuildRequires: zlib-devel
BuildRequires: elfutils-devel >= 0.130
%else
BuildRequires: devtoolset-11-gcc-c++
BuildRequires: cmake3
BuildRequires: zlib-devel
%endif
%if %{with static_libdw}
Source1: elfutils-0.189.tar.bz2
BuildRequires: m4 bzip2-devel libcurl-devel xz-devel
%else
BuildRequires: devtoolset-11-elfutils-devel >= 0.185
%endif

%description
dwarves is a set of tools that use the debugging information inserted in
ELF binaries by compilers such as GCC, used by well known debuggers such as
GDB, and more recent ones such as systemtap.

Utilities in the dwarves suite include pahole, that can be used to find
alignment holes in structs and classes in languages such as C, C++, but not
limited to these.

It also extracts other information such as CPU cacheline alignment, helping
pack those structures to achieve more cache hits.

These tools can also be used to encode and read the BTF type information format
used with the Linux kernel bpf syscall, using 'pahole -J' and 'pahole -F btf'.

A diff like tool, codiff can be used to compare the effects changes in source
code generate on the resulting binaries.

Another tool is pfunct, that can be used to find all sorts of information about
functions, inlines, decisions made by the compiler about inlining, etc.

One example of pfunct usage is in the fullcircle tool, a shell that drivers
pfunct to generate compileable code out of a .o file and then build it using
gcc, with the same compiler flags, and then use codiff to make sure the
original .o file and the new one generated from debug info produces the same
debug info.

Pahole also can be used to use all this type information to pretty print raw data
according to command line directions.

Headers can have its data format described from debugging info and offsets from
it can be used to further format a number of records.

The btfdiff utility compares the output of pahole from BTF and DWARF to make
sure they produce the same results.

%package -n %{libname}%{libver}
Summary: Debugging information  processing library

%description -n %{libname}%{libver}
Debugging information processing library.

%package -n %{libname}%{libver}-devel
Summary: Debugging information library development files
Requires: %{libname}%{libver} = %{version}-%{release}

%description -n %{libname}%{libver}-devel
Debugging information processing library development files.

%prep
%if %{with static_libdw}
%setup -T -q -b 1 -n elfutils-0.189
cd ..
%endif
%setup -q
%if 0%{?xenserver} < 9
sed -i 's@/usr/inclu@/opt/rh/devtoolset-11/root/usr/inclu@g' cmake/modules/FindDWARF.cmake
sed -i 's@/usr/lib64@/opt/rh/devtoolset-11/root/usr/lib64@g' cmake/modules/FindDWARF.cmake
%endif

%build
%if 0%{?xenserver} < 9
source /opt/rh/devtoolset-11/enable
%endif
%if %{with static_libdw}
cd ../elfutils-0.189
./configure --disable-debuginfod --prefix=$HOME/usr/local --libdir=$HOME/usr/local/lib64 \
    CFLAGS="${CFLAGS:-%optflags} -fPIC"
%make_build V=1
make install V=1
# Force linking with libdw.a to not link a private libdw.so:
echo "GROUP(libdw.a -lpthread -ldl)
INPUT(-llzma -lbz2 -lz)" >~/usr/local/lib64/libdw.so
echo 'INPUT(libelf.a)'   >~/usr/local/lib64/libelf.so
cd -
%endif
%cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_LIBRARY_PATH_FLAG=$HOME/usr/local/lib64 .
%cmake_build

%install
rm -Rf %{buildroot}
%if 0%{?xenserver} < 9
source /opt/rh/devtoolset-11/enable
%endif
%cmake_install
cp %{buildroot}%{_bindir}/pahole %{_builddir}

%ldconfig_scriptlets -n %{libname}%{libver}

%check
# Test pahole to work because we need it to generate BTF from DWARF debug info:
export LD_LIBRARY_PATH=%{buildroot}%{_libdir}
ldd %{buildroot}%{_bindir}/pahole
%{buildroot}%{_bindir}/pahole -J --btf_encode_detached=btf.o %{_builddir}/pahole
hexdump -n 4 btf.o|grep "eb9f 0001"

%files
%doc README.ctracer
%doc README.btf
%doc changes-v1.26
%doc NEWS
%{_bindir}/btfdiff
%{_bindir}/codiff
%{_bindir}/ctracer
%{_bindir}/dtagnames
%{_bindir}/fullcircle
%{_bindir}/pahole
%{_bindir}/pdwtags
%{_bindir}/pfunct
%{_bindir}/pglobal
%{_bindir}/prefcnt
%{_bindir}/scncopy
%{_bindir}/syscse
%{_bindir}/ostra-cg
%dir %{_datadir}/dwarves/
%dir %{_datadir}/dwarves/runtime/
%dir %{_datadir}/dwarves/runtime/python/
%defattr(0644,root,root,0755)
%{_mandir}/man1/pahole.1*
%{_datadir}/dwarves/runtime/Makefile
%{_datadir}/dwarves/runtime/linux.blacklist.cu
%{_datadir}/dwarves/runtime/ctracer_relay.c
%{_datadir}/dwarves/runtime/ctracer_relay.h
%attr(0755,root,root) %{_datadir}/dwarves/runtime/python/ostra.py*

%files -n %{libname}%{libver}
%{_libdir}/%{libname}.so.*
%{_libdir}/%{libname}_emit.so.*
%{_libdir}/%{libname}_reorganize.so.*

%files -n %{libname}%{libver}-devel
%doc MANIFEST README
%{_includedir}/dwarves/btf_encoder.h
%{_includedir}/dwarves/config.h
%{_includedir}/dwarves/ctf.h
%{_includedir}/dwarves/dutil.h
%{_includedir}/dwarves/dwarves.h
%{_includedir}/dwarves/dwarves_emit.h
%{_includedir}/dwarves/dwarves_reorganize.h
%{_includedir}/dwarves/elfcreator.h
%{_includedir}/dwarves/elf_symtab.h
%{_includedir}/dwarves/gobuffer.h
%{_includedir}/dwarves/hash.h
%{_includedir}/dwarves/libctf.h
%{_includedir}/dwarves/list.h
%{_includedir}/dwarves/rbtree.h
%{_libdir}/%{libname}.so
%{_libdir}/%{libname}_emit.so
%{_libdir}/%{libname}_reorganize.so

%changelog
* Thu Apr 18 2024 Bernhard Kaindl <bernhard.kaindl@cloud.com> - 1.26-3
- Fix build in Koji to link the latest elfutils DWARF library.
* Tue Apr 16 2024 Bernhard Kaindl <bernhard.kaindl@cloud.com> - 1.26-2
- Fix missing checksum
* Tue Apr 16 2024 Bernhard Kaindl <bernhard.kaindl@cloud.com> - 1.26-1
- First imported release

