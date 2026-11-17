import os
import shutil
from pathlib import Path
from PIL import Image, ImageDraw
import fitz
import docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

TARGET_DIR = Path(r"C:\Users\Lumeed\Desktop\Lumeed\Customer\IC\VS code\Opencode\Docket Local\dist\Docket\Test Docs")

def draw_avatar(draw, x, y, width, height, bg_color=(220, 225, 235)):
    draw.rectangle([x, y, x + width, y + height], fill=bg_color, outline=(160, 170, 185), width=2)
    head_cx = x + width // 2
    head_cy = y + int(height * 0.38)
    head_r = int(width * 0.22)
    draw.ellipse([head_cx - head_r, head_cy - head_r, head_cx + head_r, head_cy + head_r], fill=(130, 140, 160))
    shoulder_y = y + int(height * 0.62)
    draw.pieslice([x + 10, shoulder_y, x + width - 10, y + height + 30], start=180, end=0, fill=(90, 105, 130))

def draw_chip(draw, x, y):
    draw.rectangle([x, y, x + 55, y + 42], fill=(235, 195, 75), outline=(180, 140, 30), width=2)
    draw.rectangle([x + 18, y, x + 37, y + 42], outline=(180, 140, 30), width=1)
    draw.line([x, y + 21, x + 55, y + 21], fill=(180, 140, 30), width=1)

def draw_barcode(draw, x, y, width=280, height=35):
    import random
    cur_x = x
    while cur_x < x + width:
        bar_w = random.choice([1, 2, 3])
        draw.rectangle([cur_x, y, cur_x + bar_w, y + height], fill=(20, 25, 35))
        cur_x += bar_w + random.choice([1, 2, 3])

# --- ID CREATORS ---

def make_driver_license(dest_path: Path, name: str, lic_no: str):
    W, H = 820, 520
    img = Image.new("RGB", (W, H), color=(250, 252, 250))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, 85], fill=(22, 101, 52))
    draw.text((25, 14), "REPUBLIKA NG PILIPINAS - DEPARTMENT OF TRANSPORTATION", fill=(255, 255, 255))
    draw.text((25, 36), "LAND TRANSPORTATION OFFICE", fill=(255, 255, 255))
    draw.text((25, 56), "DRIVER'S LICENSE", fill=(250, 204, 21))
    draw.text((680, 28), "LTO", fill=(255, 255, 255))

    draw_avatar(draw, 35, 115, 175, 230)
    draw.text((240, 110), f"Lic. No.: {lic_no}", fill=(185, 28, 28))
    draw.text((240, 150), f"Name: {name}", fill=(15, 23, 42))
    draw.text((240, 185), "Nationality: PHL       Sex: M      DOB: 1991-04-15", fill=(40, 50, 70))
    draw.text((240, 220), "Address: METRO MANILA, PHILIPPINES", fill=(40, 50, 70))
    draw.text((240, 255), "Expiration Date: 2029-10-14", fill=(15, 25, 45))
    draw.text((240, 285), "Conditions: NONE       REST: 1, 2", fill=(185, 28, 28))
    draw_barcode(draw, 35, 430, 380, 45)
    img.save(str(dest_path), quality=95)

def make_philsys(dest_path: Path, name: str, card_no: str):
    W, H = 820, 520
    img = Image.new("RGB", (W, H), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, 85], fill=(26, 68, 148))
    draw.text((25, 18), "REPUBLIKA NG PILIPINAS", fill=(255, 255, 255))
    draw.text((25, 42), "PHILIPPINE IDENTIFICATION CARD", fill=(245, 215, 90))
    draw.text((620, 30), "PhilSys", fill=(255, 255, 255))

    draw_avatar(draw, 35, 115, 175, 230)
    draw_chip(draw, 240, 115)
    draw.text((320, 115), f"PhilSys Number: {card_no}", fill=(15, 25, 45))
    draw.text((240, 180), f"Name: {name}", fill=(10, 20, 40))
    draw.text((240, 225), "Date of Birth: 1994-08-22       Sex: F", fill=(40, 50, 70))
    draw.text((240, 260), "Tirahan / Address: QUEZON CITY, PHILIPPINES", fill=(40, 50, 70))
    draw_barcode(draw, 35, 430, 340, 45)
    img.save(str(dest_path), quality=95)

def make_passport(dest_path: Path, name: str, pass_no: str):
    W, H = 840, 560
    img = Image.new("RGB", (W, H), color=(248, 248, 245))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, 80], fill=(15, 23, 42))
    draw.text((30, 18), "REPUBLIC OF THE PHILIPPINES / REPUBLIKA NG PILIPINAS", fill=(241, 245, 249))
    draw.text((30, 42), "DEPARTMENT OF FOREIGN AFFAIRS", fill=(203, 213, 225))
    draw.text((640, 26), "PASAPORTE / PASSPORT", fill=(250, 204, 21))

    draw_avatar(draw, 35, 105, 185, 250)
    draw.text((250, 105), f"Passport No: {pass_no}", fill=(185, 28, 28))
    draw.text((250, 145), f"Full Name: {name}", fill=(15, 23, 42))
    draw.text((250, 185), "Nationality: FILIPINO    Date of Birth: 12 APR 1988", fill=(51, 65, 85))
    draw.text((250, 225), "Date of Issue: 18 SEP 2024   Date of Expiry: 17 SEP 2034", fill=(51, 65, 85))

    draw.rectangle([0, 430, W, H], fill=(235, 240, 245))
    draw.text((30, 445), f"P<PHL{name.replace(' ', '<')}<<<<<<<<<<<<<<<<<<<<<<<<<<", fill=(15, 23, 42))
    draw.text((30, 480), f"{pass_no}6PHL8804128M3409174<<<<<<<<<<<<<<02", fill=(15, 23, 42))
    img.save(str(dest_path), quality=95)

def make_umid(dest_path: Path, name: str, crn: str):
    W, H = 820, 520
    img = Image.new("RGB", (W, H), color=(245, 250, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, 85], fill=(13, 148, 136))
    draw.text((25, 16), "REPUBLIC OF THE PHILIPPINES", fill=(255, 255, 255))
    draw.text((25, 38), "UNIFIED MULTI-PURPOSE ID (UMID)", fill=(255, 255, 255))
    draw.text((25, 58), "SOCIAL SECURITY SYSTEM", fill=(254, 240, 138))

    draw_avatar(draw, 35, 115, 175, 230)
    draw_chip(draw, 240, 115)
    draw.text((320, 115), f"CRN: {crn}", fill=(15, 23, 42))
    draw.text((240, 180), f"Name: {name}", fill=(15, 23, 42))
    draw.text((240, 215), "Date of Birth: 1986-11-04       Sex: F", fill=(51, 65, 85))
    draw_barcode(draw, 35, 430, 360, 45)
    img.save(str(dest_path), quality=95)

def make_philhealth(dest_path: Path, name: str, pin: str):
    W, H = 800, 500
    img = Image.new("RGB", (W, H), color=(254, 252, 232))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, 80], fill=(21, 128, 61))
    draw.text((25, 16), "PHILIPPINE HEALTH INSURANCE CORPORATION", fill=(255, 255, 255))
    draw.text((25, 42), "PhilHealth Identification Card", fill=(253, 224, 71))

    draw_avatar(draw, 35, 110, 170, 220)
    draw.text((240, 115), f"PhilHealth PIN: {pin}", fill=(185, 28, 28))
    draw.text((240, 160), f"Member Name: {name}", fill=(15, 23, 42))
    draw.text((240, 200), "Member Category: EMPLOYED PRIVATE", fill=(51, 65, 85))
    draw_barcode(draw, 35, 410, 320, 40)
    img.save(str(dest_path), quality=95)

def make_tin(dest_path: Path, name: str, tin_no: str):
    W, H = 800, 500
    img = Image.new("RGB", (W, H), color=(255, 251, 235))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, 80], fill=(180, 83, 9))
    draw.text((25, 16), "REPUBLIKA NG PILIPINAS - BUREAU OF INTERNAL REVENUE", fill=(255, 255, 255))
    draw.text((25, 42), "Taxpayer Identification Number (TIN) Card", fill=(254, 240, 138))
    draw.text((680, 26), "BIR", fill=(255, 255, 255))

    draw_avatar(draw, 35, 110, 170, 220)
    draw.text((240, 115), f"TIN: {tin_no}", fill=(185, 28, 28))
    draw.text((240, 160), f"Taxpayer Name: {name}", fill=(15, 23, 42))
    draw.text((240, 200), "RDO: 044 - TAGUIG-PATEROS", fill=(51, 65, 85))
    draw_barcode(draw, 35, 410, 320, 40)
    img.save(str(dest_path), quality=95)

def make_postal(dest_path: Path, name: str, prn: str):
    W, H = 800, 500
    img = Image.new("RGB", (W, H), color=(255, 245, 245))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, 80], fill=(159, 18, 57))
    draw.text((25, 16), "PHILIPPINE POSTAL CORPORATION - PHLPost", fill=(255, 255, 255))
    draw.text((25, 42), "POSTAL IDENTITY CARD / POSTAL ID", fill=(253, 224, 71))

    draw_avatar(draw, 35, 110, 170, 220)
    draw.text((240, 115), f"Postal ID PRN: {prn}", fill=(185, 28, 28))
    draw.text((240, 160), f"Cardholder Name: {name}", fill=(15, 23, 42))
    draw.text((240, 200), "Valid Until: 2028-10-28", fill=(51, 65, 85))
    draw_barcode(draw, 35, 410, 320, 40)
    img.save(str(dest_path), quality=95)

def make_prc(dest_path: Path, name: str, reg_no: str):
    W, H = 800, 500
    img = Image.new("RGB", (W, H), color=(240, 249, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, 80], fill=(30, 64, 175))
    draw.text((25, 16), "PROFESSIONAL REGULATION COMMISSION", fill=(255, 255, 255))
    draw.text((25, 42), "Registration Certificate / Professional Identification Card", fill=(254, 240, 138))

    draw_avatar(draw, 35, 110, 170, 220)
    draw.text((240, 115), f"Registration No. {reg_no}", fill=(185, 28, 28))
    draw.text((240, 155), f"Name: {name}", fill=(15, 23, 42))
    draw.text((240, 195), "Profession: REGISTERED ELECTRICAL ENGINEER", fill=(30, 64, 175))
    draw_barcode(draw, 35, 410, 320, 40)
    img.save(str(dest_path), quality=95)

def make_clearance(dest_path: Path, name: str):
    W, H = 850, 1000
    img = Image.new("RGB", (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, 100], fill=(241, 245, 249))
    draw.text((220, 20), "REPUBLIKA NG PILIPINAS", fill=(15, 23, 42))
    draw.text((180, 45), "OFFICE OF THE PUNONG BARANGAY", fill=(15, 23, 42))
    draw.text((240, 70), "BARANGAY CLEARANCE", fill=(185, 28, 28))

    draw.text((80, 200), f"This is to certify that {name}, of legal age,", fill=(51, 65, 85))
    draw.text((80, 230), "is a bonafide resident with good moral character and has", fill=(51, 65, 85))
    draw.text((80, 260), "NO DEROGATORY RECORD in this Barangay.", fill=(22, 101, 52))
    draw.text((80, 310), "BARANGAY CERTIFICATION / RESIDENCY", fill=(30, 64, 175))
    draw_avatar(draw, 580, 280, 160, 200)
    img.save(str(dest_path), quality=95)

def make_nbi(dest_path: Path, name: str):
    W, H = 850, 560
    img = Image.new("RGB", (W, H), color=(240, 253, 244))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, 85], fill=(22, 101, 52))
    draw.text((30, 20), "NATIONAL BUREAU OF INVESTIGATION - NBI CLEARANCE", fill=(255, 255, 255))
    draw.text((30, 50), "Republic of the Philippines - Department of Justice", fill=(254, 240, 138))

    draw_avatar(draw, 40, 115, 175, 230)
    draw.text((250, 115), "NBI ID NO: NBI-2026-99214812", fill=(185, 28, 28))
    draw.text((250, 155), f"Name: {name}", fill=(15, 23, 42))
    draw.text((250, 195), "REMARKS: NO DEROGATORY RECORD (PASSED)", fill=(22, 101, 52))
    draw_barcode(draw, 40, 450, 420, 50)
    img.save(str(dest_path), quality=95)

# --- PDF & DOCX CREATORS ---

def make_bill_pdf(dest_path: Path, customer_name: str, utility_type: str = "MERALCO"):
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    text = (
        f"{utility_type} - ELECTRIC BILL\n"
        "Statement of Account\n\n"
        f"Customer Name: {customer_name}\n"
        "Account No: 0192-3841-9214\n"
        "Total Amount Due: P 5,420.50\n"
        "Due Date: November 28, 2026\n"
    )
    page.insert_text((50, 80), text, fontsize=12)
    doc.save(str(dest_path))
    doc.close()

def make_bir2316_pdf(dest_path: Path, employee_name: str):
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    text = (
        "BUREAU OF INTERNAL REVENUE - REPUBLIKA NG PILIPINAS\n"
        "BIR Form No. 2316\n"
        "Certificate of Compensation Payment / Tax Withheld\n\n"
        f"Employee Name: {employee_name}\n"
        "Taxpayer Identification Number (TIN): 284-912-840-000\n"
        "Gross Compensation Income: P 740,000.00\n"
        "Tax Withheld: P 62,400.00\n"
    )
    page.insert_text((50, 80), text, fontsize=11)
    doc.save(str(dest_path))
    doc.close()

def make_voter_pdf(dest_path: Path, voter_name: str):
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    text = (
        "COMMISSION ON ELECTIONS - REPUBLIC OF THE PHILIPPINES\n"
        "VOTER'S CERTIFICATION / VOTER'S IDENTIFICATION\n\n"
        f"Name: {voter_name}\n"
        "VIN: 7401-0129A-D1589AVL10000\n"
        "Voting Center: Manila District Precinct 0142A\n"
    )
    page.insert_text((50, 80), text, fontsize=11)
    doc.save(str(dest_path))
    doc.close()

def make_payslip_docx(dest_path: Path, employee_name: str, salary: int):
    doc = docx.Document()
    title = doc.add_heading("GLOBAL HORIZONS PHILIPPINES INC.", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("PAY SLIP / CONFIDENTIAL")
    doc.add_paragraph(f"Employee Name: {employee_name}")
    doc.add_paragraph("Pay Period: October 16 - October 31, 2026")

    table = doc.add_table(rows=4, cols=4)
    table.style = 'Table Grid'
    hdr = table.rows[0].cells
    hdr[0].text = "Earnings"
    hdr[1].text = "Amount (PHP)"
    hdr[2].text = "Deductions"
    hdr[3].text = "Amount (PHP)"

    r1 = table.rows[1].cells
    r1[0].text = "Basic Salary"
    r1[1].text = f"{salary // 2:,.2f}"
    r1[2].text = "Tax Withheld"
    r1[3].text = "4,200.00"

    r2 = table.rows[2].cells
    r2[0].text = "Gross Pay"
    r2[1].text = f"{(salary // 2 + 2000):,.2f}"
    r2[2].text = "SSS Contribution"
    r2[3].text = "1,125.00"

    r3 = table.rows[3].cells
    r3[0].text = "Net Pay:"
    r3[1].text = f"PHP {(salary // 2 - 3500):,.2f}"
    r3[2].text = "PhilHealth Contribution"
    r3[3].text = "900.00"

    doc.save(str(dest_path))

def make_coe_docx(dest_path: Path, employee_name: str, position: str):
    doc = docx.Document()
    h1 = doc.add_heading("PACIFIC TECH INNOVATIONS INC.", level=0)
    h1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_heading("CERTIFICATE OF EMPLOYMENT", level=1)
    body = doc.add_paragraph(
        f"\nThis is to certify that {employee_name} is currently employed with "
        f"Pacific Tech Innovations Inc. holding the position of {position}.\n\n"
        f"Her/His Employment Period started on February 10, 2020 up to the present date.\n\n"
        f"Issued upon the request of the employee for verification purposes."
    )
    body.style.font.size = Pt(11)
    doc.add_paragraph("\n\n_____________________________\nDirector of People Operations")
    doc.save(str(dest_path))

def make_random_note_docx(dest_path: Path):
    doc = docx.Document()
    doc.add_heading("Weekly Team Sync Agenda", level=1)
    doc.add_paragraph("Agenda items:\n1. Review sprint tasks\n2. Discuss office supplies\n3. Coffee machine maintenance.")
    doc.save(str(dest_path))

def make_random_receipt_jpg(dest_path: Path):
    img = Image.new("RGB", (500, 700), color=(250, 250, 250))
    draw = ImageDraw.Draw(img)
    draw.text((50, 40), "SUPERMARKET EXPRESS", fill=(20, 20, 20))
    draw.text((50, 80), "Date: 11/12/2026", fill=(40, 40, 40))
    draw.text((50, 120), "1x Whole Milk ............. 95.00", fill=(50, 50, 50))
    draw.text((50, 150), "2x Sourdough Bread ....... 140.00", fill=(50, 50, 50))
    draw.text((50, 180), "Total: PHP 235.00", fill=(10, 10, 10))
    img.save(str(dest_path), quality=90)

def main():
    print(f"Scrambling and generating 30 diverse test files directly in: {TARGET_DIR}")

    # Remove all subfolders & files in TARGET_DIR
    if TARGET_DIR.exists():
        for item in TARGET_DIR.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    else:
        TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # List of 30 scrambled documents with random camera/scanner filenames
    docs = [
        # Raymond Gudito
        lambda p: make_driver_license(p, "Raymond Gudito", "N02-19-084215"),
        lambda p: make_payslip_docx(p, "Raymond Gudito", 95000),
        lambda p: make_coe_docx(p, "Raymond Gudito", "Lead Software Architect"),
        lambda p: make_bir2316_pdf(p, "Raymond Gudito"),

        # Clarissa Ramos
        lambda p: make_philsys(p, "Clarissa Ramos", "7120-8491-3042-9512"),
        lambda p: make_bill_pdf(p, "Clarissa Ramos", "MERALCO"),
        lambda p: make_payslip_docx(p, "Clarissa Ramos", 72000),
        lambda p: make_clearance(p, "Clarissa Ramos"),

        # Juan Carlos Dela Cruz
        lambda p: make_passport(p, "Juan Carlos Dela Cruz", "P8942103A"),
        lambda p: make_bir2316_pdf(p, "Juan Carlos Dela Cruz"),
        lambda p: make_driver_license(p, "Juan Carlos Dela Cruz", "D01-22-901412"),
        lambda p: make_coe_docx(p, "Juan Carlos Dela Cruz", "Operations Manager"),

        # Maria Teresa Santos
        lambda p: make_umid(p, "Maria Teresa Santos", "CRN-0111-4829104-7"),
        lambda p: make_coe_docx(p, "Maria Teresa Santos", "VP of Product"),
        lambda p: make_bill_pdf(p, "Maria Teresa Santos", "MAYNILAD"),
        lambda p: make_payslip_docx(p, "Maria Teresa Santos", 88000),

        # Eduardo Castro Dizon
        lambda p: make_tin(p, "Eduardo Castro Dizon", "412-890-123-000"),
        lambda p: make_clearance(p, "Eduardo Castro Dizon"),
        lambda p: make_driver_license(p, "Eduardo Castro Dizon", "N11-18-449102"),
        lambda p: make_payslip_docx(p, "Eduardo Castro Dizon", 64000),

        # Beatriz Navarro Morales
        lambda p: make_philhealth(p, "Beatriz Navarro Morales", "12-054928194-3"),
        lambda p: make_nbi(p, "Beatriz Navarro Morales"),
        lambda p: make_coe_docx(p, "Beatriz Navarro Morales", "Chief Financial Officer"),
        lambda p: make_payslip_docx(p, "Beatriz Navarro Morales", 110000),

        # Antonio Villanueva Luna
        lambda p: make_postal(p, "Antonio Villanueva Luna", "P109 4821 942 B"),
        lambda p: make_voter_pdf(p, "Antonio Villanueva Luna"),
        lambda p: make_bill_pdf(p, "Antonio Villanueva Luna", "MANILA WATER"),

        # Angelika Mercado Reyes
        lambda p: make_prc(p, "Angelika Mercado Reyes", "0084921"),
        lambda p: make_payslip_docx(p, "Angelika Mercado Reyes", 78000),

        # Ambiguous / Unsorted items (to test fallback)
        lambda p: make_random_note_docx(p),
        lambda p: make_random_receipt_jpg(p)
    ]

    filenames = [
        "IMG_20261113_084122.png",
        "SCAN_DOC_984.docx",
        "FILE_8492.docx",
        "UPLOAD_771.pdf",
        "DSC_00491.png",
        "MERALCO_BILL_OCT.pdf",
        "PAYROLL_SLIP_551.docx",
        "BRGY_CLEAR_099.png",
        "PASSPORT_SCAN_402.jpg",
        "TAX_RETURN_2316.pdf",
        "DL_FRONT_PHOTO_712.png",
        "CERT_EMPLOYMENT_21.docx",
        "UMID_CARD_SCAN.png",
        "COE_SIGNED_2026.docx",
        "WATER_STATEMENT_88.pdf",
        "PAYSLIP_STUB_331.docx",
        "TIN_CARD_PHOTO.png",
        "CLEARANCE_DOC_11.png",
        "DRIVERS_LIC_CARD.png",
        "PAYSLIP_BIWEEKLY.docx",
        "PHILHEALTH_MEMBER.png",
        "NBI_CLEARANCE_VERIF.png",
        "HR_EMPLOYMENT_CERT.docx",
        "SALARY_VOUCHER_90.docx",
        "POSTAL_ID_CARD.png",
        "VOTER_CERT_COMELEC.pdf",
        "UTILITY_BILL_NOV.pdf",
        "PRC_ENGINEER_LIC.png",
        "PAY_RECORD_OCTOBER.docx",
        "OFFICE_MEETING_NOTES.docx",
        "STORE_RECEIPT_04.jpg"
    ]

    for gen_fn, fname in zip(docs, filenames):
        dest = TARGET_DIR / fname
        gen_fn(dest)

    print(f"\nSUCCESS: Generated {len(filenames)} flat, scrambled test files in {TARGET_DIR} with ZERO subfolders!")

if __name__ == "__main__":
    main()
