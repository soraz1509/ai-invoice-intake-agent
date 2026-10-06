# Expected results

| # | File | Deliberate defect | Expected status |
|---|------|-------------------|-----------------|
| 1 | invoice_01_clean.pdf | None (vendor 1, 19 % VAT, all fields correct) | Ready to post |
| 2 | invoice_02_duplicate.pdf | Same vendor, invoice number and amounts as #1 (duplicate; #1 is the original) | Exception |
| 3 | invoice_03_math_error.pdf | Vendor 2; VAT is correct (19 % of net) but gross is 10,00 € higher than net + VAT | Exception |
| 4 | invoice_04_iban_mismatch.pdf | Vendor 3; IBAN differs from vendor_master.csv | Critical – payment block |
| 5 | invoice_05_missing_vat_id.pdf | Vendor 1, new invoice number; no VAT ID or tax number anywhere | Exception |
| 6 | invoice_06_unknown_vendor.pdf | Vendor not in vendor_master.csv, otherwise correct | Exception |
