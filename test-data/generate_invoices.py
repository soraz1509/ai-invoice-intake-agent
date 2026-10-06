"""Generate 6 deterministic, text-based German test invoices (all data fictitious)."""
import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

HERE = Path(__file__).parent
OUT = HERE / "invoices"

RECIPIENT = ("Muster Finance GmbH", "Beispielstraße 12", "10115 Berlin")

ADDRESSES = {
    "Nordlicht Bürotechnik GmbH": ("Hafenstraße 4", "20457 Hamburg"),
    "Rheinauen Logistik AG": ("Uferweg 27", "50667 Köln"),
    "Alpenblick Catering GmbH": ("Bergstraße 9", "80331 München"),
    "Sonnenfeld Software GmbH": ("Lindenallee 15", "70173 Stuttgart"),
}

# Fourth vendor, deliberately NOT in vendor_master.csv (valid-checksum fictitious IBAN).
UNKNOWN_VENDOR = ("Sonnenfeld Software GmbH", "DE844567890", "DE12500105170648489890")
# Valid-looking IBAN that differs from the master (used for invoice 4).
WRONG_IBAN = "DE90760400610123456789"

Q = Decimal("0.01")


def eur(x):
    s = f"{x:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".") + " €"


def build_items(items):
    """items: list of (description, qty, unit_price) -> rows and net sum."""
    rows, net = [], Decimal("0")
    for desc, qty, price in items:
        total = (Decimal(qty) * Decimal(price)).quantize(Q, ROUND_HALF_UP)
        rows.append((desc, qty, Decimal(price), total))
        net += total
    return rows, net


def make_invoice(filename, vendor, number, inv_date, delivery_date, items,
                 iban=None, show_vat_id=True, gross_extra=Decimal("0")):
    name, vat_id, v_iban = vendor
    street, city = ADDRESSES[name]
    rows, net = build_items(items)
    vat = (net * Decimal("0.19")).quantize(Q, ROUND_HALF_UP)
    gross = net + vat + gross_extra

    c = canvas.Canvas(str(OUT / filename), pagesize=A4, invariant=1)
    c.setTitle(f"Rechnung {number}")
    c.setAuthor(name)
    w, h = A4
    y = h - 25 * mm

    def line(text, x=20 * mm, font="Helvetica", size=10, dy=5 * mm):
        nonlocal y
        c.setFont(font, size)
        c.drawString(x, y, text)
        y -= dy

    line(name, font="Helvetica-Bold", size=14, dy=7 * mm)
    line(street)
    line(city)
    if show_vat_id:
        line(f"USt-IdNr.: {vat_id}")
    line(f"IBAN: {iban or v_iban}", dy=12 * mm)

    line("Rechnungsempfänger", font="Helvetica-Bold")
    for part in RECIPIENT:
        line(part)
    y -= 7 * mm

    line("RECHNUNG", font="Helvetica-Bold", size=16, dy=9 * mm)
    line(f"Rechnungsnummer: {number}")
    line(f"Rechnungsdatum: {inv_date}")
    line(f"Leistungsdatum: {delivery_date}", dy=10 * mm)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Pos. Beschreibung")
    c.drawRightString(120 * mm, y, "Menge")
    c.drawRightString(150 * mm, y, "Einzelpreis")
    c.drawRightString(190 * mm, y, "Gesamt")
    y -= 6 * mm
    c.setFont("Helvetica", 10)
    for i, (desc, qty, price, total) in enumerate(rows, 1):
        c.drawString(20 * mm, y, f"{i}.   {desc}")
        c.drawRightString(120 * mm, y, str(qty))
        c.drawRightString(150 * mm, y, eur(price))
        c.drawRightString(190 * mm, y, eur(total))
        y -= 6 * mm
    y -= 6 * mm

    for label, val, bold in (
        ("Nettobetrag", net, False),
        ("USt. 19 %", vat, False),
        ("Bruttobetrag", gross, True),
    ):
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 10)
        c.drawString(120 * mm, y, label + ":")
        c.drawRightString(190 * mm, y, eur(val))
        y -= 6 * mm

    y -= 8 * mm
    line("Zahlbar innerhalb von 14 Tagen ohne Abzug.", size=9)
    c.showPage()
    c.save()


def main():
    OUT.mkdir(exist_ok=True)
    with open(HERE / "vendor_master.csv", newline="", encoding="utf-8") as f:
        v1, v2, v3 = [(r["vendor_name"], r["vat_id"], r["iban"]) for r in csv.DictReader(f)]

    items1 = [("Bürostuhl ErgoPlus", 4, "189.90"), ("Schreibtischlampe LED", 6, "34.50")]
    items2 = [("Palettentransport Hamburg–Köln", 3, "420.00"), ("Lagergebühr (Woche)", 2, "95.00")]
    items3 = [("Catering Firmenfeier (Personen)", 40, "28.50"), ("Getränkepauschale", 1, "310.00"),
              ("Service und Aufbau", 1, "150.00")]
    items5 = [("Toner-Set Schwarz", 10, "62.40"), ("Aktenordner (Karton)", 5, "24.90")]
    items6 = [("Softwarelizenz Jahresabo", 5, "249.00"), ("Support-Paket", 1, "480.00")]

    make_invoice("invoice_01_clean.pdf", v1, "RE-2026-0101", "05.09.2026", "03.09.2026", items1)
    make_invoice("invoice_02_duplicate.pdf", v1, "RE-2026-0101", "05.09.2026", "03.09.2026", items1)
    make_invoice("invoice_03_math_error.pdf", v2, "RH-48213", "08.09.2026", "07.09.2026", items2,
                 gross_extra=Decimal("10.00"))
    make_invoice("invoice_04_iban_mismatch.pdf", v3, "AB-2026-377", "10.09.2026", "09.09.2026", items3,
                 iban=WRONG_IBAN)
    make_invoice("invoice_05_missing_vat_id.pdf", v1, "RE-2026-0102", "12.09.2026", "11.09.2026", items5,
                 show_vat_id=False)
    make_invoice("invoice_06_unknown_vendor.pdf", UNKNOWN_VENDOR, "SF-100234", "15.09.2026", "14.09.2026",
                 items6)
    print(f"Wrote 6 invoices to {OUT}")


if __name__ == "__main__":
    main()
