## dtn7 builder
FROM golang:1.11 AS dtn7-builder

RUN git clone https://github.com/dtn7/dtn7.git \
 && cd dtn7 \
 && git checkout 50251a4aecc821e707489e715fce9c5db0ff717b \
 && go build -o /dtncat ./cmd/dtncat \
 && go build -o /dtnd ./cmd/dtnd


## Serval builder
FROM ubuntu:18.04 AS serval-builder

RUN apt-get update \
 && apt-get install --no-install-recommends -y \
      autoconf \
      automake \
      build-essential \
      ca-certificates \
      curl \
      gawk \
      gcc \
      git \
      grep \
      jq \
      libsodium-dev \
      libtool \
      sed

RUN git clone https://github.com/servalproject/serval-dna.git /serval-dna \
 && cd /serval-dna \
 && git checkout c2526446edc7244377a56bdb7468d90a327d9588 \
 && autoreconf -f -i -I m4 \
 && ./configure \
 && make servald


## Final CORE image
FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install --no-install-recommends -yq \
      bridge-utils \
      ca-certificates \
      curl \
      ebtables \
      git \
      iproute2 \
      iputils-ping \
      jq \
      kmod \
      libev4 \
      libtk-img \
      lxterminal \
      net-tools \
      netcat \
      openssh-server \
      python \
      python-enum34 \
      python-lxml \
      python3 \
      quagga \
      socat \
      tcl \
      tcpdump \
      tk \
      tmux \
      vim \
      wget \
      xauth

# SSH-Config
ADD ssh_jail.sh /ssh_jail.sh
RUN chmod +x /ssh_jail.sh

RUN mkdir /var/run/sshd \
 && mkdir /root/.ssh \
 && echo 'ForceCommand /ssh_jail.sh' >> /etc/ssh/sshd_config

ADD keyfile.pub /root/.ssh/authorized_keys

# CORE
RUN wget -q https://github.com/coreemu/core/releases/download/release-5.2.1/python-core_sysv_5.2.1_all.deb \
 && dpkg -i python-core_sysv_5.2.1_all.deb

RUN wget -q https://github.com/coreemu/core/releases/download/release-5.2.1/core-gui_5.2.1_amd64.deb \
 && dpkg -i core-gui_5.2.1_amd64.deb

RUN rm python-core_sysv_5.2.1_all.deb \
 && rm core-gui_5.2.1_amd64.deb \
 && apt-get clean

# dtn7
COPY --from=dtn7-builder /dtncat /usr/bin/dtn7cat
COPY --from=dtn7-builder /dtnd /usr/bin/dtn7d

# Forban
RUN wget -q http://www.foo.be/forban/release/forban-0.0.34.tar.gz \
 && mkdir /forban \
 && tar xfz forban-0.0.34.tar.gz -C /forban/ --strip-components=1 \
 && rm forban-0.0.34.tar.gz

# Serval
COPY --from=serval-builder /serval-dna/servald /usr/bin/
RUN echo 'export SERVALINSTANCE_PATH=$SESSION_DIR/`hostname`.conf' >> /root/.serval \
 && echo 'export SERVALINSTANCE_PATH=$SESSION_DIR/`hostname`.conf' >> /root/.bashrc

# Serval Shell Scripts
RUN git clone https://github.com/gh0st42/servalshellscripts.git /servalshellscripts \
 && cd /servalshellscripts \
 && git checkout 01a28547e6e709beec949bf94eb04e04f68ce311 \
 && cp /servalshellscripts/cmds/* /usr/bin \
 && cd .. \
 && rm -r servalshellscripts

# Custom CORE stuff
COPY dotcore /root/.core/
RUN echo 'custom_services_dir = /root/.core/myservices' >> /etc/core/core.conf

# Benchmark script, `make bench` or via CORE-GUI's import
ADD bench_script.py /

# Start and expose sshd for X-forwarding
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
