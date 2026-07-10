# Minimal BART socat server.
# Speaks MRD binary protocol — compatible with client.py and Open Recon.
FROM debian:bullseye-slim
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        socat make gcc git \
        python3 python3-pip \
        libfftw3-dev libblas-dev liblapacke-dev libpng-dev && \
    pip install --no-cache-dir h5py numpy ismrmrd && \
    rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/mrirecon/bart.git /bart && \
    cd /bart && git checkout v0.9.00 && make -j$(nproc) all --silent

ENV PATH="/bart:${PATH}" BART_TOOLBOX_PATH=/bart

WORKDIR /opt/server
COPY server.sh reconstruct.sh mrd_adapter.py ./
RUN chmod +x server.sh reconstruct.sh

EXPOSE 9002
CMD ["./server.sh"]
