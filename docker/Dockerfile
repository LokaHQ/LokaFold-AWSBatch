# Original Copyright 2021 DeepMind Technologies Limited
# Modifications Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

### ---------------------------------------------
### Modified by Amazon Web Services (AWS) to update cuda version and add Alphafold
### parameter
ARG CUDA=11.4.2
ARG AF_VERSION=v2.1.2
FROM nvcr.io/nvidia/cuda:${CUDA}-cudnn8-runtime-ubuntu18.04
# FROM directive resets ARGS, so we specify again (the value is retained if
# previously set).
ARG CUDA
ARG AF_VERSION
### ---------------------------------------------

# Use bash to support string substitution.
SHELL ["/bin/bash", "-c"]

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
      build-essential \
      cmake \
### ---------------------------------------------
### Modified by AWS to update cuda version    
      cuda-command-line-tools-11.4 \
### ---------------------------------------------
      git \
      hmmer \
      kalign \
      tzdata \
      wget \
### ---------------------------------------------
### Modified by AWS to address openssl issue identified during testing
    && apt-get install -y --only-upgrade openssl \
### ---------------------------------------------
    && rm -rf /var/lib/apt/lists/*

# Compile HHsuite from source.
RUN git clone --branch v3.3.0 https://github.com/soedinglab/hh-suite.git /tmp/hh-suite \
    && mkdir /tmp/hh-suite/build \
    && pushd /tmp/hh-suite/build \
    && cmake -DCMAKE_INSTALL_PREFIX=/opt/hhsuite .. \
    && make -j 4 && make install \
    && ln -s /opt/hhsuite/bin/* /usr/bin \
    && popd \
    && rm -rf /tmp/hh-suite

# Install Miniconda package manager.
RUN wget -q -P /tmp \
  https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && bash /tmp/Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda \
    && rm /tmp/Miniconda3-latest-Linux-x86_64.sh

# Install conda packages.
ENV PATH="/opt/conda/bin:$PATH"
RUN conda update -qy conda \
    && conda install -y -c conda-forge \
      openmm=7.5.1 \
### ---------------------------------------------
### Modified by AWS to update cuda version and add awscli   
      cudatoolkit==${CUDA} \
      pdbfixer \
      pip \
      python=3.7 \
      awscli
### ---------------------------------------------
### Modified by Loka to use our own version of the repository
# RUN git clone --branch ${AF_VERSION} --depth 1 https://github.com/deepmind/alphafold.git /app/alphafold
RUN git clone --branch main --depth 1 https://github.com/LokaHQ/LokaFold.git /app/alphafold
COPY run_aws_alphafold.py /app/alphafold
### ---------------------------------------------     
RUN wget -q -P /app/alphafold/alphafold/common/ \
  https://git.scicore.unibas.ch/schwede/openstructure/-/raw/7102c63615b64735c4941278d92b554ec94415f8/modules/mol/alg/src/stereo_chemical_props.txt

# Install pip packages.
RUN pip3 install --upgrade pip \
    && pip3 install -r /app/alphafold/requirements.txt \
### ---------------------------------------------
### Modified by AWS to update cuda version and add boto3   
    && pip3 install --upgrade jax jaxlib>=0.1.69+cuda${CUDA/./} -f \
      https://storage.googleapis.com/jax-releases/jax_releases.html \
    && pip3 install boto3
### ---------------------------------------------     

# Apply OpenMM patch.
WORKDIR /opt/conda/lib/python3.7/site-packages
RUN patch -p0 < /app/alphafold/docker/openmm.patch

### ---------------------------------------------
### Modified by AWS to clean up container
  
RUN rm -rf /app/alphafold/docker /app/alphafold/imgs /app/alphafold/notebooks /app/alphafold/scripts
### ---------------------------------------------     

# We need to run `ldconfig` first to ensure GPUs are visible, due to some quirk
# with Debian. See https://github.com/NVIDIA/nvidia-docker/issues/1399 for
# details.
# ENTRYPOINT does not support easily running multiple commands, so instead we
# write a shell script to wrap them up.
WORKDIR /app/alphafold
RUN echo $'#!/bin/bash\n\
ldconfig\n\
### ---------------------------------------------
### Modified by AWS to point to new script    
python /app/alphafold/run_aws_alphafold.py "$@"' > /app/run_aws_alphafold.sh \
  && chmod +x /app/run_aws_alphafold.sh
ENTRYPOINT ["/app/run_aws_alphafold.sh"]
### ---------------------------------------------
