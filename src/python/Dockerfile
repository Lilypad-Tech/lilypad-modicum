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
ADD . /app
RUN pip3 install -e .