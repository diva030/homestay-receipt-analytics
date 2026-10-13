# Homestay Receipt Analytics — Practice Project

This project uses **fictional training receipts only**. It is not actual AQ Wise or Astana Ria D'Raja customer data.

## Files
- `receipts/AR001.pdf` to `receipts/AR006.pdf`: six fictional text-based PDF receipts.
- `extract_receipts.py`: extracts structured fields using `pdfplumber`, regular expressions, and `pandas`.
- The script creates `receipt_extraction.csv` and `receipt_extraction.xlsx`.

## Run on Windows in VS Code
1. Extract this ZIP to a folder.
2. Open the folder in VS Code.
3. In the terminal, create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
4. Install the libraries:
   ```powershell
   python -m pip install pdfplumber pandas openpyxl
   ```
5. Run:
   ```powershell
   python extract_receipts.py
   ```
6. Open `receipt_extraction.xlsx` and compare a few rows with the original PDFs.

## What the script extracts
Receipt number, booking date, check-in/check-out dates, customer label, amount, payment status, and payment method.

## Limitations
- The regular expressions are designed for the sample receipt layout. Real receipts may use different labels and formats, so the patterns will need adjustment.
- This script reads text-based PDFs. Scanned PDFs may require OCR.
- `review_status` flags missing fields, but does not prove that the extracted data is correct.
- Keep real customer documents private and only process them using company-approved tools.
