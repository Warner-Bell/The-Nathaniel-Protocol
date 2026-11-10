#!/usr/bin/env python3
"""test_dim_guard.py - regression for the #4 embedding-dimension guard in kb_query.py.

Verifies _check_query_dim raises a clear ValueError on a query/index dim mismatch
(instead of numpy's opaque matmul gufunc error) and stays silent on matching dims.
Run: python3 Nate's-kb/vectorstore/test_dim_guard.py   (exit 0 = all pass)
"""
import importlib.util
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("kb_query", os.path.join(HERE, "kb_query.py"))
kq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kq)

passed = failed = 0
fails = []


def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        fails.append(f"  FAIL [{name}]")


vectors = np.zeros((5, 384), dtype=np.float32)

# matching dim: must NOT raise (positive control)
try:
    kq._check_query_dim(np.zeros(384, dtype=np.float32), vectors)
    check("matching dim passes", True)
except Exception:
    check("matching dim passes", False)

# mismatched dim: must raise ValueError with both dims named (the failure the guard catches)
try:
    kq._check_query_dim(np.zeros(256, dtype=np.float32), vectors)
    check("mismatch raises", False)
except ValueError as e:
    check("mismatch raises", True)
    check("message names both dims", "256" in str(e) and "384" in str(e))

# 1D / non-matrix vectors: guard skips gracefully (negative control, no false raise)
try:
    kq._check_query_dim(np.zeros(384, dtype=np.float32), np.zeros(384, dtype=np.float32))
    check("1D vectors skip guard", True)
except Exception:
    check("1D vectors skip guard", False)

print(f"dim-guard regression: {passed} passed, {failed} failed")
for line in fails:
    print(line)
sys.exit(0 if failed == 0 else 1)
