#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOL_DIR="${PROJECT_DIR}/tools/qemu-9.2.1"
TMP_DEB="${TMPDIR:-/tmp}/qemu-user_9.2.1.deb"
URL="https://mirrors.edge.kernel.org/ubuntu/pool/universe/q/qemu/qemu-user_9.2.1%2Bds-1ubuntu5.2_amd64.deb"

mkdir -p "${TOOL_DIR}"
if [[ -x "${TOOL_DIR}/bin/qemu-riscv64" ]]; then
  "${TOOL_DIR}/bin/qemu-riscv64" --version
  exit 0
fi

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

curl -L --fail "${URL}" -o "${TMP_DEB}"
dpkg-deb -x "${TMP_DEB}" "${workdir}/extract"
mkdir -p "${TOOL_DIR}/bin"
cp "${workdir}/extract/usr/bin/qemu-riscv64" "${TOOL_DIR}/bin/qemu-riscv64"
chmod +x "${TOOL_DIR}/bin/qemu-riscv64"
"${TOOL_DIR}/bin/qemu-riscv64" --version
