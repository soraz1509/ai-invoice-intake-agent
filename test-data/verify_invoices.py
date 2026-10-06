"""Regenerate the test invoices twice, confirm determinism, and verify that each
file contains exactly its deliberate defect (and no other)."""
import csv
import hashlib
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

from pypdf import PdfReader

BASE = Path(__file__).parent
GEN = BASE / "generate_invoices.py"
INV = BASE / "invoices"

# Defects expected per invoice number. Duplicates are order-dependent:
# #1 is the original, only #2 is the duplicate.
EXPECTED = {1: set(), 2: {"duplicate"}, 3: {"math"}, 4: {"iban"}, 5: {"vatid"}, 6: {"unknown"}}


def hashes():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(INV.glob("*.pdf"))}


def num(s):
    return Decimal(s.replace(".", "").replace(",", ".").replace(" €", ""))


def iban_ok(i):
    return bool(re.fullmatch(r"DE\d{20}", i)) and int(i[4:] + "1314" + i[2:4]) % 97 == 1


def main():
    subprocess.run([sys.executable, str(GEN)], check=True)
    h1 = hashes()
    subprocess.run([sys.executable, str(GEN)], check=True)
    deterministic = h1 == hashes()
    print(f"Deterministic: {deterministic} | files: {len(h1)}")

    with open(BASE / "vendor_master.csv", newline="", encoding="utf-8") as f:
        master = {r["vendor_name"]: r for r in csv.DictReader(f)}
    master_ibans = {r["iban"] for r in master.values()}

    all_ok = deterministic and len(h1) == 6
    seen = set()
    ibans = {}
    for p in sorted(INV.glob("*.pdf")):
        n = int(p.name[8:10])
        t = "\n".join(pg.extract_text() for pg in PdfReader(p).pages)
        defects = set()
        vendor = t.split("\n")[0].strip()
        number = re.search(r"Rechnungsnummer: (\S+)", t).group(1)
        iban = re.search(r"IBAN: (\S+)", t).group(1)
        ibans[n] = iban
        vat = re.search(r"USt-IdNr\.: (DE\d{9})", t)
        required = ["Muster Finance GmbH", "Rechnungsdatum:", "Leistungsdatum:",
                    "Nettobetrag", "Bruttobetrag", "USt. 19 %"]
        if vendor not in master:
            defects.add("unknown")
        else:
            if iban != master[vendor]["iban"]:
                defects.add("iban")
            if vat and vat.group(1) != master[vendor]["vat_id"]:
                defects.add("vat-mismatch")
        if not vat:
            defects.add("vatid")
        if re.search(r"Steuernummer|St\.-?Nr", t):
            defects.add("taxno-present")
        net = num(re.search(r"Nettobetrag:\s+(\S+ €)", t).group(1))
        v = num(re.search(r"USt\. 19 %:\s+(\S+ €)", t).group(1))
        gross = num(re.search(r"Bruttobetrag:\s+(\S+ €)", t).group(1))
        if v != (net * Decimal("0.19")).quantize(Decimal("0.01")):
            defects.add("vat-wrong")
        if gross != net + v:
            defects.add("math")
        if not iban_ok(iban):
            defects.add("iban-invalid")
        if (vendor, number) in seen:
            defects.add("duplicate")
        seen.add((vendor, number))
        if not all(k in t for k in required):
            defects.add("missing-field")
        ok = defects == EXPECTED[n]
        all_ok &= ok
        extra = ""
        if n == 3:
            extra = f" gross-(net+vat)={gross - net - v}"
        if n == 5:
            extra = f" 'USt-IdNr' in text: {'USt-IdNr' in t}"
        print(f"{p.name}: {'PASS' if ok else 'FAIL'} defects={sorted(defects)} "
              f"expected={sorted(EXPECTED[n])}{extra}")

    # Wrong IBAN (#4) and unknown vendor's IBAN (#6) must be distinct and not in the master.
    distinct = ibans[4] != ibans[6] and ibans[4] not in master_ibans and ibans[6] not in master_ibans
    print(f"IBANs #4/#6 distinct and not in master: {distinct}")
    all_ok &= distinct
    print("ALL CHECKS PASSED" if all_ok else "CHECKS FAILED")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
