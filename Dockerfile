##### The software used in this evaluation is built in individual
##### containers in a multi-step build and then copied to the
##### experiment container in the end.

### Build dtn7d dtn7cat
FROM golang:1.11 AS dtn7-builder

COPY dtn7 /dtn7
WORKDIR /dtn7
RUN go build -o /dtn7cat ./cmd/dtncat \
    && go build -o /dtn7d ./cmd/dtnd


### Build ibrdtn
FROM maciresearch/core_worker:0.4.2 AS ibrdtn-builder

# Install depencencies according to https://github.com/ibrdtn/ibrdtn/wiki/Build-IBR-DTN
# install common dependencies
RUN apt-get update \
    && apt-get install --no-install-recommends -yq \
    build-essential \
    devscripts \
    automake \
    autoconf \
    pkg-config \
    libtool \
    debhelper \
    cdbs \
    git \
    subversion \
    wget \
    curl \
    gawk \
    libncurses5-dev

# install library packages
RUN apt-get install --no-install-recommends -yq \
    libssl-dev \
    libz-dev \
    libsqlite3-dev \
    libcurl4-openssl-dev \
    libdaemon-dev \
    libcppunit-dev \
    libnl-3-dev \
    libnl-cli-3-dev \
    libnl-genl-3-dev \
    libnl-nf-3-dev \
    libnl-route-3-dev \
    libarchive-dev

ENV CXXFLAGS -Wno-deprecated

ADD ibrdtn /ibrdtn
WORKDIR /ibrdtn/ibrdtn
RUN bash autogen.sh
RUN ./configure
RUN make -j $(nproc)
RUN make install


### Build serval
FROM maciresearch/core_worker:0.4.2 AS serval-builder

RUN apt-get update \
    && apt-get install --no-install-recommends -yq \
    build-essential \
    autoconf \
    automake \
    libtool \
    grep \
    sed \
    gawk \
    jq \
    curl \
    git \
    libsodium-dev \
    gcc-5 \
    && apt-get clean

ADD serval-dna /serval-dna
WORKDIR /serval-dna
RUN autoreconf -f -i -I m4
ENV CFLAGS -Wno-error=deprecated-declarations -O1
ENV CC gcc-5
RUN ./configure
RUN make -j $(nproc) servald


##### Compose the actual worker container
FROM maciresearch/core_worker:0.4.2

# Install further measuring tools
RUN apt-get update \
    && apt-get install --no-install-recommends -yq \
    bwm-ng \
    sysstat \
    tcpdump \
    patch \
    python-nacl \
    python-ipcalc \
    libdaemon-dev \
    libnl-3-dev \
    libnl-cli-3-dev \
    libnl-genl-3-dev \
    libnl-nf-3-dev \
    libnl-route-3-dev \
    libarchive-dev \
    psmisc \
    && apt-get clean

# Install CORE extensions for the network test
COPY dotcore /root/.core/
RUN echo 'custom_services_dir = /root/.core/myservices' >> /etc/core/core.conf

# Force Serval to use its instance_path
ENV BASH_ENV /root/.serval
RUN echo 'export SERVALINSTANCE_PATH=$SESSION_DIR/`hostname`.conf' >> /root/.serval \
    && echo 'export SERVALINSTANCE_PATH=$SESSION_DIR/`hostname`.conf' >> /root/.bashrc

# Install the software
# DTN7
COPY --from=dtn7-builder    /dtn7d                              /usr/local/sbin/
COPY --from=dtn7-builder    /dtn7cat                            /usr/local/sbin/
# IBR-DTN
COPY --from=ibrdtn-builder  /usr/local/bin/dtnsend              /usr/local/sbin/
COPY --from=ibrdtn-builder  /usr/local/sbin/dtnd                /usr/local/sbin/
COPY --from=ibrdtn-builder  /usr/local/lib/libibrdtn.so.1       /usr/lib/
COPY --from=ibrdtn-builder  /usr/local/lib/libibrcommon.so.1    /usr/lib/
# SERVAL
COPY --from=serval-builder  /serval-dna/servald                 /usr/local/sbin/
# FORBAN
COPY                        forban                              /forban
COPY                        forban.diff                         /tmp/forban.diff

# Patch Forban's announce interval and logging
RUN cd /forban && patch -p1 < /tmp/forban.diff
