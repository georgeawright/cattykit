FROM debian:bookworm-slim@sha256:311f7a192fd9a92b165a86b32fa3aae9005b11849bfb1db2d4fd784559ee464f AS base

FROM base AS build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates curl libncurses-dev libx11-dev tk8.6-dev uuid-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY archives.sha256 swl-repl-load.patch ./
RUN curl -fSL --retry 3 -O 'https://science.slc.edu/~jmarshall/metacat/ChezScheme-9.5.4.tgz' \
    -O 'https://science.slc.edu/~jmarshall/metacat/swl1.3-src-patched-linux.tgz' \
    -O 'https://science.slc.edu/~jmarshall/metacat/Metacat-1.2.tgz' \
    && sha256sum -c archives.sha256 \
    && tar xzf ChezScheme-9.5.4.tgz \
    && tar xzf swl1.3-src-patched-linux.tgz \
    && tar xzf Metacat-1.2.tgz
RUN cd ChezScheme && ./configure --machine=a6le --installprefix=/usr/local && make install
RUN cd swl1.3 && patch -p1 < ../swl-repl-load.patch \
    && make install Tclsh=tclsh8.6 CFLAGS='-m64 -O2 -I/usr/include/tcl8.6 -fPIC -fcommon'
RUN dpkg-query -W > /build/build-packages.txt

FROM base
RUN apt-get update && apt-get install -y --no-install-recommends \
    libncurses6 libx11-6 libuuid1 python3 tk8.6 xauth xfonts-base xvfb \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /usr/local/ /usr/local/
COPY --from=build /build/Metacat/ /opt/Metacat/
COPY --from=build /build/build-packages.txt /opt/metacat-batch/build-packages.txt
COPY --from=build /build/ChezScheme/LICENSE /opt/metacat-batch/licenses/ChezScheme.txt
COPY --from=build /build/swl1.3/Notice /opt/metacat-batch/licenses/SWL.txt
WORKDIR /opt/metacat-batch
COPY *.py adapter.ss ./original_metacat/
RUN dpkg-query -W > runtime-packages.txt \
    && mkdir /results \
    && mkdir -m 1777 /tmp/.X11-unix \
    && python3 original_metacat/make_loader.py /opt/Metacat/metacat.ss original_metacat/metacat-linux.ss
ENTRYPOINT ["python3", "-m", "original_metacat"]
