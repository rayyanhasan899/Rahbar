#!/usr/bin/env bash
set -euo pipefail
version=v0.6.7
destination=${1:-.venv/tools}
mkdir -p "$destination" .venv/downloads
curl -fsSL --retry 3 "https://github.com/yannh/kubeconform/releases/download/$version/kubeconform-linux-amd64.tar.gz" -o .venv/downloads/kubeconform-linux-amd64.tar.gz
curl -fsSL --retry 3 "https://github.com/yannh/kubeconform/releases/download/$version/CHECKSUMS" -o .venv/downloads/kubeconform-CHECKSUMS
(cd .venv/downloads && grep ' kubeconform-linux-amd64.tar.gz$' kubeconform-CHECKSUMS | sha256sum -c -)
tar -xzf .venv/downloads/kubeconform-linux-amd64.tar.gz -C "$destination" kubeconform
"$destination/kubeconform" -v
