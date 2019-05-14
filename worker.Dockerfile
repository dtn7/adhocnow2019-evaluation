##### The software used in this evaluation is built in individual 
##### containers in a multi-step build and then copied to the 
##### experiment container in the end.


### Build dtn7
FROM golang:1.11 AS dtn7-builder

COPY dtn7 /dtn7
WORKDIR /dtn7

RUN go build -o /dtncat ./cmd/dtncat \
    && go build -o /dtnd ./cmd/dtnd


### Build serval (batphone-release-0.93)
FROM maciresearch/core_worker:0.3 AS serval-builder

RUN apt-get update \
    && apt-get install -y \
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
RUN make -j 8 servald


##### Compose the actual worker container
FROM maciresearch/core_worker:0.3

# Install further measuring tools
RUN apt-get update \
    && apt-get install --no-install-recommends -yq \
    bwm-ng \
    sysstat \
    tcpdump \
    && apt-get clean

# Install CORE extensions for the network test 
COPY dotcore /root/.core/
RUN echo 'custom_services_dir = /root/.core/myservices' >> /etc/core/core.conf

# Install the software
COPY                        forban                      /forban
RUN ln -s                   /forban/bin/forbanctl       /usr/local/bin
COPY --from=dtn7-builder    /dtnd                       /usr/local/bin/
COPY --from=dtn7-builder    /dtncat                     /usr/local/bin/
COPY --from=serval-builder  /serval-dna                 /usr/local/bin/
