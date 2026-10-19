"""verify_cleaner.py — Full acceptance test for text_cleaner.py"""
import re
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from src.cleaners.text_cleaner import load_document, clean_text, chunk_text

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
results: list[tuple[str, bool, str]] = []

def record(name: str, ok: bool, detail: str = ""):
    tag = PASS if ok else FAIL
    print(f"  {tag} {name}" + (f": {detail}" if detail else ""))
    results.append((name, ok, detail))

print("=" * 60)
print("  VERIFICATION — text_cleaner.py")
print("=" * 60)

# ─────────────────────────────────────────────────────────────
# TEST 1 — clean_text: basic normalisation
# ─────────────────────────────────────────────────────────────
print("\n[TEST 1] clean_text — normalisation")

raw1 = "   Hello\r\n\r\n\r\nWorld\xa0foo\x00bar  baz   qux.   "
c1 = clean_text(raw1)

record("T1-1  \\r\\n -> \\n normalised",       "\r\n" not in c1)
record("T1-2  No triple blank lines",           "\n\n\n" not in c1)
record("T1-3  Non-breaking space removed",      "\xa0"  not in c1)
record("T1-4  Null byte removed",               "\x00"  not in c1)
record("T1-5  Leading/trailing space stripped",  c1 == c1.strip())
record("T1-6  Intra-line multiple spaces collapsed",
       "  " not in c1.split("\n")[0])

# Full Vietnamese sentence input
raw_vn = "   He mat tro gom Mat Troi va 8 hanh tinh quay quanh.   \n\n\n Trai Dat la hanh tinh thu ba.    Mat Troi cung cap anh sang va nhiet! "
c_vn = clean_text(raw_vn)
record("T1-7  Vietnamese input cleaned successfully", len(c_vn) > 0)
record("T1-8  Triple newline eliminated (VN input)", "\n\n\n" not in c_vn)

record("T1-9  Empty string returns empty string", clean_text("") == "")

# ─────────────────────────────────────────────────────────────
# TEST 2 — chunk_text: sentence-boundary & overlap
# ─────────────────────────────────────────────────────────────
print("\n[TEST 2] chunk_text — sentence boundaries & overlap")

chunks_vn = chunk_text(c_vn, max_words=10, overlap=2)

record("T2-1  Produces > 0 chunks",             len(chunks_vn) > 0)
record("T2-2  All chunks <= max_words",
       all(len(c.split()) <= 10 for c in chunks_vn))
record("T2-3  No chunk is empty",               all(c.strip() for c in chunks_vn))

# Overlap: tail of chunk[i] should share words with head of chunk[i+1]
overlap_ok = True
for i in range(len(chunks_vn) - 1):
    tail = set(chunks_vn[i].split()[-2:])
    head = set(chunks_vn[i + 1].split()[:4])
    if not tail & head:
        overlap_ok = False
record("T2-4  Overlap words carried into next chunk", overlap_ok)

# Empty input
record("T2-5  chunk_text('') returns []",       chunk_text("") == [])

# ─────────────────────────────────────────────────────────────
# TEST 3 — load_document: TXT reading
# ─────────────────────────────────────────────────────────────
print("\n[TEST 3] load_document — file I/O")

os.makedirs("data/raw", exist_ok=True)
with open("data/raw/test.txt", "w", encoding="utf-8") as f:
    f.write("Day la tai lieu on tap mon Lich Su.")

content = load_document("data/raw/test.txt")
record("T3-1  TXT file loaded successfully",    "Lich Su" in content)
record("T3-2  Content is non-empty",            len(content) > 0)

# Missing file → FileNotFoundError
try:
    load_document("data/raw/does_not_exist.txt")
    record("T3-3  FileNotFoundError for missing file", False, "exception NOT raised")
except FileNotFoundError:
    record("T3-3  FileNotFoundError for missing file", True)

# Unsupported extension → ValueError
with open("data/raw/dummy.docx", "w") as f:
    f.write("x")
try:
    load_document("data/raw/dummy.docx")
    record("T3-4  ValueError for unsupported extension", False, "exception NOT raised")
except ValueError:
    record("T3-4  ValueError for unsupported extension", True)

# ─────────────────────────────────────────────────────────────
# TEST 4 — Full pipeline: load → clean → chunk on sample.txt
# ─────────────────────────────────────────────────────────────
print("\n[TEST 4] Full pipeline on data/raw/sample.txt")

raw_doc = load_document("data/raw/sample.txt")
cleaned_doc = clean_text(raw_doc)
chunks_doc = chunk_text(cleaned_doc, max_words=150, overlap=20)

record("T4-1  Document loaded",                 len(raw_doc) > 0)
record("T4-2  Document cleaned",                len(cleaned_doc) > 0)
record("T4-3  Produces multiple chunks",         len(chunks_doc) >= 2)

all_within_budget = all(len(c.split()) <= 150 for c in chunks_doc)
record("T4-4  All chunks within 150-word budget", all_within_budget)

max_wc = max(len(c.split()) for c in chunks_doc)
record("T4-5  Max word count reported",         True,
       f"{max_wc} words in largest chunk")

no_ctrl = all("\x00" not in c and "\xa0" not in c for c in chunks_doc)
record("T4-6  No control chars in any chunk",   no_ctrl)

# ─────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
passed = sum(1 for _, ok, _ in results if ok)
total  = len(results)
print(f"  RESULT: {passed}/{total} tests passed")
print("=" * 60)
if passed < total:
    sys.exit(1)

