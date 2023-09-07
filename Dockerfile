FROM ubuntu:22.04 AS modicum
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y \
      curl \
      python3-pip \
      python3-virtualenv \
      python3-dev \
      libssl-dev \
      libcurl4-openssl-dev \
      jq \
      tzdata \
      docker.io \
      nginx
RUN curl -sL https://get.bacalhau.org/install.sh | bash
RUN pip3 install supervisor
RUN curl -o kubo.tar.gz https://dist.ipfs.tech/kubo/v0.21.0/kubo_v0.21.0_linux-amd64.tar.gz && \
    tar -xzf kubo.tar.gz && \
    cd kubo && \
    bash install.sh
# this gets the ABI into the python container
ADD ./src/js/artifacts/contracts/Modicum.sol/Modicum.json /Modicum.json
ADD ./src/python/modicum/requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt
ADD ./src/python /app
RUN pip3 install -e .
ENV BACALHAU_API_HOST=localhost
# nvidia-smi wrapper script which actually runs a container from inside a container
ADD nvidia-smi /usr/bin/nvidia-smi
ADD nvidia-container-cli /usr/bin/nvidia-container-cli
RUN mkdir -p /lilypad-results
ENTRYPOINT ["/usr/local/bin/modicum"]

FROM modicum AS resource-provider
ADD ./src/python/supervisord.resourceProvider.conf /etc/supervisord.conf
ADD ./src/python/nginx.conf /etc/nginx/sites-available/default
ENTRYPOINT ["/usr/local/bin/supervisord"]

FROM modicum AS mediator
ADD ./src/python/supervisord.mediator.conf /etc/supervisord.conf
ENTRYPOINT ["/usr/local/bin/supervisord"]
