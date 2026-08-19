#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parent / "build_batch_07.py"
text = path.read_text(encoding="utf-8")
marker = "if __name__=='__main__': main()"
injected = "import sys\nfrom batch07_verified_supplement import apply as _apply_batch07_verified_supplement\n_apply_batch07_verified_supplement(sys.modules[__name__])\n\nif __name__=='__main__': main()"
if injected in text:
    print("Batch07 supplement already injected")
elif marker in text:
    path.write_text(text.replace(marker, injected), encoding="utf-8")
    print("Injected Batch07 verified supplement")
else:
    raise SystemExit("Batch07 main marker not found")
