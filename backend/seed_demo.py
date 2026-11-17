from pathlib import Path
import fitz
import docx
from PIL import Image, ImageDraw

def create_sample_documents(target_dir: Path):
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    # 1. Raymond Gudito - Driver's License (PDF)
    raymond_dir = target_dir / "Raymond Gudito"
    raymond_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 60),
        "REPUBLIKA NG PILIPINAS\n"
        "DEPARTMENT OF TRANSPORTATION\n"
        "LAND TRANSPORTATION OFFICE\n"
        "DRIVER'S LICENSE\n"
        "Lic. No.: D02-18-004521\n"
        "Name: RAYMOND GUDITO\n"
        "REST: 1, 2\n"
        "Expiration: 2028-10-14"
    )
    doc.save(str(raymond_dir / "driver_license.pdf"))
    doc.close()

    # 2. Raymond Gudito - Payslip (Word docx)
    doc_p = docx.Document()
    doc_p.add_heading("COMPANY PAY SLIP", level=1)
    doc_p.add_paragraph("Employee Name: Raymond Gudito\nPeriod: Oct 1 - Oct 15, 2026")
    doc_p.add_paragraph("Basic Salary: P 45,000.00\nEarnings: P 48,000.00\nDeductions: P 5,200.00\nNet Pay: P 42,800.00")
    doc_p.save(str(raymond_dir / "payslip_oct2026.docx"))

    # 3. Maria Santos - Certificate of Employment (Word docx)
    maria_dir = target_dir / "Maria Santos"
    maria_dir.mkdir(parents=True, exist_ok=True)

    doc_coe = docx.Document()
    doc_coe.add_heading("CERTIFICATE OF EMPLOYMENT", level=1)
    doc_coe.add_paragraph(
        "This is to certify that Maria Santos is currently employed as Senior Software Engineer "
        "with our organization from January 15, 2021 up to the present. Employment Period: 2021-Present."
    )
    doc_coe.save(str(maria_dir / "coe_employment.docx"))

    # 4. Maria Santos - Utility Bill (Digital PDF)
    doc_bill = fitz.open()
    page_bill = doc_bill.new_page()
    page_bill.insert_text(
        (50, 60),
        "MERALCO - ELECTRIC BILL\n"
        "Statement of Account\n"
        "Customer Name: Maria Santos\n"
        "Account No: 1234-5678-9012\n"
        "Total Amount Due: P 3,450.75"
    )
    doc_bill.save(str(maria_dir / "meralco_bill.pdf"))
    doc_bill.close()

    # 5. Pedro Penduko - Philippine Passport (Scanned Image PNG)
    pedro_dir = target_dir / "Pedro Penduko"
    pedro_dir.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (700, 260), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((20, 30), "REPUBLIC OF THE PHILIPPINES", fill="black")
    draw.text((20, 70), "DEPARTMENT OF FOREIGN AFFAIRS", fill="black")
    draw.text((20, 110), "PASAPORTE / PASSPORT", fill="black")
    draw.text((20, 150), "Passport No: P1234567A", fill="black")
    draw.text((20, 190), "Surname: PENDUKO  Given Names: PEDRO", fill="black")
    img.save(str(pedro_dir / "passport_scan.png"))

    # 6. Unlabeled Batch - Ambiguous document (should fall back to Unsorted)
    batch_dir = target_dir / "Unlabeled Batch"
    batch_dir.mkdir(parents=True, exist_ok=True)

    doc_rnd = docx.Document()
    doc_rnd.add_heading("Meeting Notes", level=1)
    doc_rnd.add_paragraph("Discussion about office pantry supplies and coffee beans.")
    doc_rnd.save(str(batch_dir / "random_notes.docx"))

    print(f"Sample test documents created at: {target_dir.resolve()}")

if __name__ == "__main__":
    create_sample_documents(Path("./sample_documents"))
