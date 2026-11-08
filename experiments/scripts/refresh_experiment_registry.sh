#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE_ROOT="$(cd "${PROJECT_DIR}/../../.." && pwd)"
PERSONAL_OS_ROOT="${PERSONAL_OS_ROOT:-/root/personal-os/PersonalOS}"
REGISTRY_SCRIPT="${PERSONAL_OS_ROOT}/scripts/experiment_registry.py"
CATALOG_SCRIPT="${PROJECT_DIR}/scripts/build_paper_evidence_catalog.py"
AUDIT_SCRIPT="${PROJECT_DIR}/scripts/build_final_experiment_audit.py"

python3 "${CATALOG_SCRIPT}"
python3 "${AUDIT_SCRIPT}"

if [[ ! -f "${REGISTRY_SCRIPT}" ]]; then
  echo "[registry] skipped; script not found: ${REGISTRY_SCRIPT}"
  exit 0
fi

args=()
for experiment_id in "$@"; do
  args+=(--completed-id "${experiment_id}")
done

python3 "${REGISTRY_SCRIPT}" refresh \
  --workspace-root "${WORKSPACE_ROOT}" \
  "${args[@]}"
