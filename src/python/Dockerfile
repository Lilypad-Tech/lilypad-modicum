FROM ubuntu:22.04
WORKDIR /app
RUN apt-get update && \
    apt-get install -y \
      curl \
      python3-pip \
      python3-virtualenv \
      python3-dev \
      libssl-dev \
      libcurl4-openssl-dev
RUN curl -sL https://get.bacalhau.org/install.sh | bash
RUN pip3 install supervisor
RUN curl -o kubo.tar.gz https://dist.ipfs.tech/kubo/v0.21.0/kubo_v0.21.0_linux-amd64.tar.gz && \
    tar -xzf kubo.tar.gz && \
    cd kubo && \
    bash install.sh
ADD . /app
RUN pip3 install -e .
ENV BACALHAU_HOST=localhost