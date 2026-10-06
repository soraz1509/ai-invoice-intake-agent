# Test data generator prompt

Create synthetic test data for an invoice-validation demo. All companies,
people, addresses, VAT IDs and IBANs must be fictitious.

## 1. Vendor master
Create `test-data/vendor_master.csv` with columns vendor_name, vat_id, iban.
Three fictitious German vendors. IBANs must be in German format (DE + 20 digits)
with valid check digits. VAT IDs in format DE + 9 digits.

## 2. Invoice generator
Write `test-data/generate_invoices.py` using only the reportlab library.
It must read vendor_master.csv and create 6 text-based PDF invoices (not images)
in `test-data/invoices/`. No randomness: running it twice produces identical files.

Every invoice is in German and contains: vendor name and address, vendor VAT ID
(USt-IdNr.), vendor IBAN, recipient "Muster Finance GmbH" with address,
invoice number (Rechnungsnummer), invoice date, delivery date (Leistungsdatum),
2–3 line items, net amount (Nettobetrag), VAT rate and amount (USt.),
gross amount (Bruttobetrag). Use German number format, e.g. 1.234,56 €.

Cases:
1. invoice_01_clean.pdf – vendor 1, all fields correct, 19% VAT.
2. invoice_02_duplicate.pdf – identical vendor, invoice number and amounts as #1.
3. invoice_03_math_error.pdf – vendor 2, gross amount is 10,00 € higher than net + VAT.
4. invoice_04_iban_mismatch.pdf – vendor 3, everything correct except the IBAN,
   which differs from vendor_master.csv (still a valid-looking German IBAN).
5. invoice_05_missing_vat_id.pdf – vendor 1, new invoice number, no VAT ID and
   no tax number anywhere on the invoice.
6. invoice_06_unknown_vendor.pdf – a fourth fictitious vendor that is NOT in
   vendor_master.csv, otherwise correct.

## 3. Supporting files
- `test-data/requirements.txt` listing reportlab.
- `test-data/expected_results.md`: a table of the 6 files with the deliberate
  defect and expected status (Ready to post / Exception / Critical – payment block).

## 4. Self-check
After generating, extract the text from each PDF (use pypdf) and confirm that
each deliberate defect is present and that no other defect was introduced.
Report the result per file.

First show me your plan and wait for my OK before creating files.