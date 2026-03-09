#!/usr/bin/env bash
set -euo pipefail

conda run -n conda_py_env_312 python -m pytest
