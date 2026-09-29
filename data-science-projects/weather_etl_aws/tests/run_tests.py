"""Zero-dependency test runner. Runs every test_* function in test_lambdas.py."""
import os
import sys
import tempfile
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "lambdas"))
os.environ["USE_MOCK_WEATHER"] = "1"

# Import the test module without pytest
import test_lambdas as mod  # noqa: E402


class TmpPath:
    def __init__(self, p): self._p = Path(p)
    def __fspath__(self): return str(self._p)
    def __truediv__(self, other): return TmpPath(self._p / other)
    def __str__(self): return str(self._p)


class Monkey:
    def __init__(self): self._chdir = None
    def chdir(self, p):
        self._chdir = os.getcwd()
        os.chdir(p)
    def undo(self):
        if self._chdir:
            os.chdir(self._chdir)


tests = [(name, getattr(mod, name)) for name in dir(mod)
         if name.startswith("test_") and callable(getattr(mod, name))]

passed = failed = 0
for name, fn in tests:
    m = Monkey()
    try:
        params = fn.__code__.co_varnames[:fn.__code__.co_argcount]
        if "tmp_path" in params and "monkeypatch" in params:
            with tempfile.TemporaryDirectory() as td:
                fn(TmpPath(td), m)
        else:
            fn()
        print(f"  PASS  {name}")
        passed += 1
    except Exception as e:  # noqa: BLE001
        print(f"  FAIL  {name}: {type(e).__name__}: {e}")
        traceback.print_exc()
        failed += 1
    finally:
        m.undo()

print(f"\n{passed} passed, {failed} failed  ({len(tests)} total)")
sys.exit(0 if failed == 0 else 1)
