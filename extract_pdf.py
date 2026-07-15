import os
import glob
import json
try:
    from PyPDF2 import PdfReader
except ImportError:
    print("PyPDF2 not installed yet.")
    exit(1)

download_dir = r"C:\Users\hp\Downloads"
pdf_files = glob.glob(os.path.join(download_dir, "*.pdf"))

# We only care about the ones the user listed
target_files = [
    "Travel-Tourism-and-Hospitality.pdf", "Transportation-Logistics-Warehousing-and-Packaging.pdf",
    "Healthcare.pdf", "IT-and-ITeS.pdf", "Leather-and-Leather-Goods.pdf", "Textile-and-Clothing.pdf",
    "Handlooms-Handicrafts.pdf", "Food-Processing.pdf", "Electronics-IT-hardware.pdf",
    "Domestic-Help.pdf", "Construction-Material-Building-Hardware.pdf", "Building-Construction-Real-Estate.pdf",
    "Beauty-Wellness.pdf", "Banking-Financial-Services-Insurance.pdf", "Auto-and-Auto-Components.pdf",
    "Telecommunications.pdf", "Private-Security-Services.pdf", "Pharmaceuticals.pdf", "Retail.pdf",
    "Media-Entertainment.pdf", "Agriculture.pdf", "Furniture-Furnishing.pdf"
]

extracted_data = {}

for f in target_files:
    path = os.path.join(download_dir, f)
    if os.path.exists(path):
        try:
            reader = PdfReader(path)
            text = ""
            for i in range(min(5, len(reader.pages))): # Extract first 5 pages for summary
                text += reader.pages[i].extract_text() + "\n"
            
            # Simple heuristic: find "Job Role", "Qualification Pack", etc.
            extracted_data[f.replace(".pdf", "")] = text[:2000] # Save first 2000 chars for analysis
            print(f"Extracted {f}")
        except Exception as e:
            print(f"Failed to read {f}: {e}")

with open("pdf_extracted_preview.json", "w", encoding="utf-8") as out:
    json.dump(extracted_data, out, indent=4)

print("Done extracting preview data.")
