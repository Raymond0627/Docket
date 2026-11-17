import os
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import fitz
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

TARGET_DIR = Path(r"C:\Users\Lumeed\Desktop\Lumeed\Customer\IC\VS code\Opencode\Docket Local\dist\Docket\Test Docs")

def draw_avatar(draw, x, y, width, height, bg_color=(220, 225, 235)):
    """Draws a clean, stylized ID portrait avatar."""
    # Background photo box
    draw.rectangle([x, y, x + width, y + height], fill=bg_color, outline=(160, 170, 185), width=2)

    # Head circle
    head_cx = x + width // 2
    head_cy = y + int(height * 0.38)
    head_r = int(width * 0.22)
    draw.ellipse([head_cx - head_r, head_cy - head_r, head_cx + head_r, head_cy + head_r], fill=(130, 140, 160))

    # Shoulders ellipse
    shoulder_y = y + int(height * 0.62)
    draw.pieslice([x + 10, shoulder_y, x + width - 10, y + height + 30], start=180, end=0, fill=(90, 105, 130))

def draw_chip(draw, x, y):
    """Draws a realistic golden smart card chip."""
    draw.rectangle([x, y, x + 55, y + 42], fill=(235, 195, 75), outline=(180, 140, 30), width=2)
    draw.rectangle([x + 18, y, x + 37, y + 42], outline=(180, 140, 30), width=1)
    draw.line([x, y + 21, x + 55, y + 21], fill=(180, 140, 30), width=1)

def draw_barcode(draw, x, y, width=180, height=35):
    """Draws a clean barcode graphic."""
    cur_x = x
    while cur_x < x + width:
        bar_w = random.choice([1, 2, 3])
        draw.rectangle([cur_x, y, cur_x + bar_w, y + height], fill=(20, 25, 35))
        cur_x += bar_w + random.choice([1, 2, 3])

# ----------------- ID CARD GENERATORS ----------------- #

def create_philsys_id(dest_path: Path):
    """Generates PhilSys National ID card image."""
    W, H = 820, 520
    img = Image.new("RGB", (W, H), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)

    # Blue top banner
    draw.rectangle([0, 0, W, 85], fill=(26, 68, 148))
    draw.text((25, 18), "REPUBLIKA NG PILIPINAS", fill=(255, 255, 255))
    draw.text((25, 42), "PHILIPPINE IDENTIFICATION CARD", fill=(245, 215, 90))
    draw.text((620, 30), "PhilSys", fill=(255, 255, 255))

    # Cardholder Portrait
    draw_avatar(draw, 35, 115, 175, 230)

    # Smart chip
    draw_chip(draw, 240, 115)

    # Card Details
    draw.text((320, 115), "PhilSys Card Number (PCN):", fill=(90, 100, 120))
    draw.text((320, 135), "7120-8491-3042-9512", fill=(15, 25, 45))

    draw.text((240, 185), "Apelyido / Last Name:", fill=(90, 100, 120))
    draw.text((240, 205), "RAMOS", fill=(10, 20, 40))

    draw.text((240, 240), "Mga Pangalan / Given Names:", fill=(90, 100, 120))
    draw.text((240, 260), "CLARISSA BAUTISTA", fill=(10, 20, 40))

    draw.text((240, 295), "Kapanganakan / Date of Birth: 1994-08-22", fill=(40, 50, 70))
    draw.text((240, 320), "Kasarian / Sex: F      Tirahan: QUEZON CITY, METRO MANILA", fill=(40, 50, 70))

    # QR / Barcode
    draw_barcode(draw, 35, 430, 340, 45)
    draw.text((450, 445), "PHILIPPINE STATISTICAL AUTHORITY", fill=(120, 130, 145))

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(dest_path), quality=95)

def create_driver_license(dest_path: Path):
    """Generates Philippine Driver's License image."""
    W, H = 820, 520
    img = Image.new("RGB", (W, H), color=(250, 252, 250))
    draw = ImageDraw.Draw(img)

    # Green top banner
    draw.rectangle([0, 0, W, 85], fill=(22, 101, 52))
    draw.text((25, 14), "REPUBLIKA NG PILIPINAS - DEPARTMENT OF TRANSPORTATION", fill=(255, 255, 255))
    draw.text((25, 36), "LAND TRANSPORTATION OFFICE", fill=(255, 255, 255))
    draw.text((25, 56), "DRIVER'S LICENSE", fill=(250, 204, 21))
    draw.text((680, 28), "LTO", fill=(255, 255, 255))

    # Portrait Avatar
    draw_avatar(draw, 35, 115, 175, 230)

    # License Details
    draw.text((240, 110), "License No. / Lic. No.:", fill=(90, 100, 120))
    draw.text((240, 130), "N02-19-084215", fill=(185, 28, 28))

    draw.text((240, 165), "Name: GUDITO, RAYMOND ALCANTARA", fill=(15, 25, 45))
    draw.text((240, 195), "Nationality: PHL       Sex: M      DOB: 1991-04-15", fill=(40, 50, 70))
    draw.text((240, 225), "Address: PASIG CITY, METRO MANILA", fill=(40, 50, 70))
    draw.text((240, 255), "Expiration Date: 2029-10-14", fill=(15, 25, 45))
    draw.text((240, 285), "Conditions: NONE       REST: 1, 2", fill=(185, 28, 28))

    # Signature line & Barcode
    draw.line([240, 360, 480, 360], fill=(120, 130, 145), width=2)
    draw.text((260, 368), "Signature of Licensee", fill=(120, 130, 145))
    draw_barcode(draw, 35, 430, 380, 45)

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(dest_path), quality=95)

def create_passport(dest_path: Path):
    """Generates Philippine Passport data page image."""
    W, H = 840, 560
    img = Image.new("RGB", (W, H), color=(248, 248, 245))
    draw = ImageDraw.Draw(img)

    # Navy top header
    draw.rectangle([0, 0, W, 80], fill=(15, 23, 42))
    draw.text((30, 18), "REPUBLIC OF THE PHILIPPINES / REPUBLIKA NG PILIPINAS", fill=(241, 245, 249))
    draw.text((30, 42), "DEPARTMENT OF FOREIGN AFFAIRS / KAGAWARAN NG UGNAYANG PANLABAS", fill=(203, 213, 225))
    draw.text((640, 26), "PASAPORTE / PASSPORT", fill=(250, 204, 21))

    # Portrait
    draw_avatar(draw, 35, 105, 185, 250)

    # Passport details
    draw.text((250, 105), "Type / Uri: P    Country Code: PHL    Passport No:", fill=(71, 85, 105))
    draw.text((540, 105), "P8942103A", fill=(185, 28, 28))

    draw.text((250, 145), "Surname / Apelyido:", fill=(71, 85, 105))
    draw.text((250, 165), "DELA CRUZ", fill=(15, 23, 42))

    draw.text((250, 200), "Given Names / Pangalan:", fill=(71, 85, 105))
    draw.text((250, 220), "JUAN CARLOS", fill=(15, 23, 42))

    draw.text((250, 255), "Nationality: FILIPINO    Date of Birth: 12 APR 1988", fill=(51, 65, 85))
    draw.text((250, 285), "Date of Issue: 18 SEP 2024   Date of Expiry: 17 SEP 2034", fill=(51, 65, 85))
    draw.text((250, 315), "Issuing Authority: DFA NCR EAST", fill=(51, 65, 85))

    # Machine Readable Zone (MRZ)
    draw.rectangle([0, 430, W, H], fill=(235, 240, 245))
    draw.text((30, 445), "P<PHLDELA<CRUZ<<JUAN<CARLOS<<<<<<<<<<<<<<<<<<", fill=(15, 23, 42))
    draw.text((30, 480), "P8942103A6PHL8804128M3409174<<<<<<<<<<<<<<02", fill=(15, 23, 42))

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(dest_path), quality=95)

def create_umid_id(dest_path: Path):
    """Generates UMID / SSS ID card image."""
    W, H = 820, 520
    img = Image.new("RGB", (W, H), color=(245, 250, 255))
    draw = ImageDraw.Draw(img)

    # Teal header
    draw.rectangle([0, 0, W, 85], fill=(13, 148, 136))
    draw.text((25, 16), "REPUBLIC OF THE PHILIPPINES", fill=(255, 255, 255))
    draw.text((25, 38), "UNIFIED MULTI-PURPOSE ID (UMID)", fill=(255, 255, 255))
    draw.text((25, 58), "SOCIAL SECURITY SYSTEM", fill=(254, 240, 138))

    draw_avatar(draw, 35, 115, 175, 230)
    draw_chip(draw, 240, 115)

    draw.text((320, 115), "Common Reference Number (CRN):", fill=(71, 85, 105))
    draw.text((320, 135), "CRN-0111-4829104-7", fill=(15, 23, 42))

    draw.text((240, 185), "Name: SANTOS, MARIA TERESA DIAZ", fill=(15, 23, 42))
    draw.text((240, 220), "Date of Birth: 1986-11-04       Sex: F", fill=(51, 65, 85))
    draw.text((240, 250), "Address: MAKATI CITY, METRO MANILA", fill=(51, 65, 85))

    draw_barcode(draw, 35, 430, 360, 45)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(dest_path), quality=95)

def create_philhealth_id(dest_path: Path):
    """Generates PhilHealth ID card image."""
    W, H = 800, 500
    img = Image.new("RGB", (W, H), color=(254, 252, 232))
    draw = ImageDraw.Draw(img)

    # Green & Gold banner
    draw.rectangle([0, 0, W, 80], fill=(21, 128, 61))
    draw.text((25, 16), "PHILIPPINE HEALTH INSURANCE CORPORATION", fill=(255, 255, 255))
    draw.text((25, 42), "PhilHealth Identification Card", fill=(253, 224, 71))

    draw_avatar(draw, 35, 110, 170, 220)

    draw.text((240, 115), "PhilHealth Identification Number (PIN):", fill=(71, 85, 105))
    draw.text((240, 135), "12-054928194-3", fill=(185, 28, 28))

    draw.text((240, 175), "Member Name: MORALES, BEATRIZ NAVARRO", fill=(15, 23, 42))
    draw.text((240, 210), "Member Category: EMPLOYED PRIVATE", fill=(51, 65, 85))
    draw.text((240, 240), "Date of Birth: 1993-02-19       Gender: FEMALE", fill=(51, 65, 85))

    draw_barcode(draw, 35, 410, 320, 40)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(dest_path), quality=95)

def create_tin_id(dest_path: Path):
    """Generates TIN ID card image."""
    W, H = 800, 500
    img = Image.new("RGB", (W, H), color=(255, 251, 235))
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, W, 80], fill=(180, 83, 9))
    draw.text((25, 16), "REPUBLIKA NG PILIPINAS - BUREAU OF INTERNAL REVENUE", fill=(255, 255, 255))
    draw.text((25, 42), "Taxpayer Identification Number (TIN) Card", fill=(254, 240, 138))
    draw.text((680, 26), "BIR", fill=(255, 255, 255))

    draw_avatar(draw, 35, 110, 170, 220)

    draw.text((240, 115), "TIN: 412-890-123-000", fill=(185, 28, 28))
    draw.text((240, 155), "Name: DIZON, EDUARDO CASTRO", fill=(15, 23, 42))
    draw.text((240, 190), "Date of Issue: 2022-03-10       DOB: 1989-07-28", fill=(51, 65, 85))
    draw.text((240, 225), "RDO: 044 - TAGUIG-PATEROS", fill=(51, 65, 85))

    draw_barcode(draw, 35, 410, 320, 40)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(dest_path), quality=95)

def create_postal_id(dest_path: Path):
    """Generates Postal ID card image."""
    W, H = 800, 500
    img = Image.new("RGB", (W, H), color=(255, 245, 245))
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, W, 80], fill=(159, 18, 57))
    draw.text((25, 16), "PHILIPPINE POSTAL CORPORATION - PHLPost", fill=(255, 255, 255))
    draw.text((25, 42), "POSTAL IDENTITY CARD / POSTAL ID", fill=(253, 224, 71))

    draw_avatar(draw, 35, 110, 170, 220)

    draw.text((240, 115), "Postal ID PRN: P109 4821 942 B", fill=(185, 28, 28))
    draw.text((240, 155), "Name: LUNA, ANTONIO VILLANUEVA", fill=(15, 23, 42))
    draw.text((240, 190), "Date of Birth: 1990-10-29       Sex: MALE", fill=(51, 65, 85))
    draw.text((240, 225), "Address: ERMITA, MANILA", fill=(51, 65, 85))
    draw.text((240, 260), "Valid Until: 2028-10-28", fill=(15, 23, 42))

    draw_barcode(draw, 35, 410, 320, 40)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(dest_path), quality=95)

def create_prc_id(dest_path: Path):
    """Generates PRC ID card image."""
    W, H = 800, 500
    img = Image.new("RGB", (W, H), color=(240, 249, 255))
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, W, 80], fill=(30, 64, 175))
    draw.text((25, 16), "PROFESSIONAL REGULATION COMMISSION", fill=(255, 255, 255))
    draw.text((25, 42), "Registration Certificate / Professional Identification Card", fill=(254, 240, 138))

    draw_avatar(draw, 35, 110, 170, 220)

    draw.text((240, 115), "Profession: REGISTERED ELECTRICAL ENGINEER", fill=(30, 64, 175))
    draw.text((240, 145), "Registration No. 0084921", fill=(185, 28, 28))
    draw.text((240, 180), "Name: REYES, ANGELIKA MERCADO", fill=(15, 23, 42))
    draw.text((240, 215), "Registration Date: 2018-05-24   Valid Until: 2027-08-11", fill=(51, 65, 85))

    draw_barcode(draw, 35, 410, 320, 40)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(dest_path), quality=95)

def create_barangay_clearance(dest_path: Path):
    """Generates Barangay Clearance document image."""
    W, H = 850, 1100
    img = Image.new("RGB", (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, W, 120], fill=(241, 245, 249))
    draw.text((220, 25), "REPUBLIKA NG PILIPINAS", fill=(15, 23, 42))
    draw.text((180, 50), "OFFICE OF THE PUNONG BARANGAY", fill=(15, 23, 42))
    draw.text((250, 75), "BARANGAY CERTIFICATION / RESIDENCY", fill=(30, 64, 175))

    draw.text((240, 180), "BARANGAY CLEARANCE", fill=(185, 28, 28))
    draw.text((80, 260), "TO WHOM IT MAY CONCERN:", fill=(15, 23, 42))

    body = (
        "This is to certify that MR. EDUARDO CASTRO DIZON, of legal age, Filipino,\n"
        "is a bonafide resident of this Barangay with good moral character.\n\n"
        "Records of this office show that he/she has NO DEROGATORY RECORD filed\n"
        "against him/her as of this date.\n\n"
        "This BARANGAY CLEARANCE is issued upon the request of the interested party\n"
        "for Local Employment and Verification purposes.\n\n"
        "Issued this 12th day of November 2026."
    )
    draw.text((80, 310), body, fill=(51, 65, 85))

    draw_avatar(draw, 600, 320, 160, 200)

    draw.line([480, 780, 720, 780], fill=(15, 23, 42), width=2)
    draw.text((500, 790), "HON. PUNONG BARANGAY", fill=(15, 23, 42))

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(dest_path), quality=95)

def create_nbi_clearance(dest_path: Path):
    """Generates NBI Clearance document image."""
    W, H = 850, 600
    img = Image.new("RGB", (W, H), color=(240, 253, 244))
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, W, 90], fill=(22, 101, 52))
    draw.text((30, 20), "NATIONAL BUREAU OF INVESTIGATION - NBI CLEARANCE", fill=(255, 255, 255))
    draw.text((30, 50), "Republic of the Philippines - Department of Justice", fill=(254, 240, 138))

    draw_avatar(draw, 40, 120, 175, 230)

    draw.text((250, 120), "NBI ID NO: NBI-2026-08492019", fill=(185, 28, 28))
    draw.text((250, 160), "Name: MORALES, BEATRIZ NAVARRO", fill=(15, 23, 42))
    draw.text((250, 195), "Address: MANDALUYONG CITY, METRO MANILA", fill=(51, 65, 85))
    draw.text((250, 230), "Date of Birth: 1993-02-19    Sex: FEMALE    Civil Status: SINGLE", fill=(51, 65, 85))
    draw.text((250, 270), "REMARKS: NO DEROGATORY RECORD (PASSED)", fill=(22, 101, 52))

    draw_barcode(draw, 40, 480, 420, 50)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(dest_path), quality=95)

# ----------------- PDF & DOCX GENERATORS ----------------- #

def create_meralco_bill_pdf(dest_path: Path):
    """Generates Meralco Electric Bill PDF."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # Letter size
    text = (
        "MERALCO - ELECTRIC BILL\n"
        "Statement of Account\n\n"
        "Customer Name: Clarissa Ramos\n"
        "Service Address: Block 4 Lot 12, Commonwealth, Quezon City\n"
        "Account No: 0192-3841-9214\n"
        "Billing Period: Oct 10, 2026 to Nov 09, 2026\n"
        "Total Amount Due: P 4,815.20\n"
        "Due Date: November 24, 2026\n\n"
        "Please pay on or before due date to avoid service disconnection."
    )
    page.insert_text((50, 80), text, fontsize=12)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(dest_path))
    doc.close()

def create_bir_2316_pdf(dest_path: Path):
    """Generates BIR Form 2316 ITR PDF."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    text = (
        "BUREAU OF INTERNAL REVENUE - REPUBLIKA NG PILIPINAS\n"
        "BIR Form No. 2316\n"
        "Certificate of Compensation Payment / Tax Withheld\n"
        "For Compensation Payment With or Without Tax Withheld\n\n"
        "Part I - Employee Information:\n"
        "Taxpayer Identification Number (TIN): 284-912-840-000\n"
        "Employee's Name: Juan Carlos Dela Cruz\n"
        "Registered Address: Taguig City, Metro Manila\n\n"
        "Part II - Employer's Information:\n"
        "Employer's Name: ACME Global Technologies Philippines Inc.\n"
        "TIN: 009-841-209-000\n\n"
        "Gross Compensation Income: P 680,000.00\n"
        "Tax Withheld: P 54,200.00\n"
        "Total Deductions & Exemptions: P 90,000.00"
    )
    page.insert_text((50, 70), text, fontsize=11)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(dest_path))
    doc.close()

def create_voter_cert_pdf(dest_path: Path):
    """Generates Voter Certification PDF."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    text = (
        "COMMISSION ON ELECTIONS - REPUBLIC OF THE PHILIPPINES\n"
        "OFFICE OF THE ELECTION OFFICER - DISTRICT II\n\n"
        "VOTER'S CERTIFICATION / VOTER'S IDENTIFICATION\n\n"
        "THIS IS TO CERTIFY that the person named below is a duly registered voter:\n\n"
        "Name: Antonio Villanueva Luna\n"
        "Voter's Identification Number / VIN: 7401-0129A-D1589AVL10000\n"
        "Date of Registration: July 14, 2016\n"
        "Precinct No.: 0142A\n"
        "Voting Center: Ermita Elementary School\n\n"
        "Issued this 5th day of November 2026."
    )
    page.insert_text((50, 80), text, fontsize=11)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(dest_path))
    doc.close()

def create_payslip_docx(dest_path: Path, employee_name: str, salary: int):
    """Generates professional corporate Payslip Word Document."""
    doc = docx.Document()
    title = doc.add_heading("APEX SOLUTIONS PHILIPPINES INC.", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sub = doc.add_paragraph("PAY SLIP / CONFIDENTIAL")
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph(f"Employee Name: {employee_name}")
    doc.add_paragraph("Pay Period: October 01 - October 15, 2026")

    # Table with Earnings & Deductions
    table = doc.add_table(rows=6, cols=4)
    table.style = 'Table Grid'
    hdr = table.rows[0].cells
    hdr[0].text = "Earnings"
    hdr[1].text = "Amount (PHP)"
    hdr[2].text = "Deductions"
    hdr[3].text = "Amount (PHP)"

    half_salary = salary // 2
    tax = int(half_salary * 0.12)
    sss = 1125
    philhealth = 900
    net_pay = half_salary - tax - sss - philhealth

    row1 = table.rows[1].cells
    row1[0].text = "Basic Salary"
    row1[1].text = f"{half_salary:,.2f}"
    row1[2].text = "Withholding Tax"
    row1[3].text = f"{tax:,.2f}"

    row2 = table.rows[2].cells
    row2[0].text = "Allowance"
    row2[1].text = "2,500.00"
    row2[2].text = "SSS Contribution"
    row2[3].text = f"{sss:,.2f}"

    row3 = table.rows[3].cells
    row3[0].text = "Overtime Pay"
    row3[1].text = "1,800.00"
    row3[2].text = "PhilHealth Contribution"
    row3[3].text = f"{philhealth:,.2f}"

    row4 = table.rows[4].cells
    row4[0].text = "Gross Pay"
    row4[1].text = f"{(half_salary + 4300):,.2f}"
    row4[2].text = "Pag-IBIG Fund"
    row4[3].text = "200.00"

    row5 = table.rows[5].cells
    row5[0].text = "Net Pay:"
    row5[1].text = f"PHP {(net_pay + 4100):,.2f}"
    row5[2].text = "Total Deductions:"
    row5[3].text = f"{(tax + sss + philhealth + 200):,.2f}"

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(dest_path))

def create_coe_docx(dest_path: Path, employee_name: str, position: str):
    """Generates Certificate of Employment Word Document."""
    doc = docx.Document()
    title = doc.add_heading("INNOVATION SYSTEMS LABS INC.", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph("Bonifacio Global City, Taguig, Philippines\n")

    h2 = doc.add_heading("CERTIFICATE OF EMPLOYMENT", level=1)
    h2.alignment = WD_ALIGN_PARAGRAPH.CENTER

    body = doc.add_paragraph(
        f"\nThis is to certify that {employee_name} is currently employed with "
        f"Innovation Systems Labs Inc. holding the position of {position}.\n\n"
        f"Her/His Employment Period started on January 18, 2021 up to the present date.\n\n"
        f"This Certificate of Employment is being issued upon the request of the employee "
        f"for whatever legal purpose it may serve.\n\n"
        f"Given this 10th day of November 2026."
    )
    body.style.font.size = Pt(11)

    doc.add_paragraph("\n\n_____________________________\nHead of Human Resources")

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(dest_path))

def main():
    print(f"Creating unique AI test documents and IDs in: {TARGET_DIR}")
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Raymond Gudito Bundle
    raymond_folder = TARGET_DIR / "Raymond Gudito"
    create_driver_license(raymond_folder / "Raymond_Drivers_License.png")
    create_payslip_docx(raymond_folder / "Raymond_Payslip_Oct2026.docx", "Raymond Gudito", 95000)

    # 2. Maria Teresa Santos Bundle
    maria_folder = TARGET_DIR / "Maria Teresa Santos"
    create_umid_id(maria_folder / "Maria_UMID_Card.png")
    create_coe_docx(maria_folder / "Maria_Certificate_of_Employment.docx", "Maria Teresa Santos", "VP of Product Engineering")

    # 3. Juan Carlos Dela Cruz Bundle
    juan_folder = TARGET_DIR / "Juan Carlos Dela Cruz"
    create_passport(juan_folder / "Juan_Philippine_Passport.jpg")
    create_bir_2316_pdf(juan_folder / "Juan_BIR_Form_2316_ITR.pdf")

    # 4. Clarissa Ramos Bundle
    clarissa_folder = TARGET_DIR / "Clarissa Ramos"
    create_philsys_id(clarissa_folder / "Clarissa_PhilSys_National_ID.png")
    create_meralco_bill_pdf(clarissa_folder / "Clarissa_Meralco_Electric_Bill.pdf")

    # 5. Loose / Mixed Documents Directory
    loose_folder = TARGET_DIR / "Loose Applications Batch"
    create_tin_id(loose_folder / "Eduardo_Dizon_TIN_Card.png")
    create_postal_id(loose_folder / "Antonio_Luna_Postal_ID.png")
    create_philhealth_id(loose_folder / "Beatriz_Morales_PhilHealth.png")
    create_prc_id(loose_folder / "Angelika_Reyes_PRC_License.png")
    create_barangay_clearance(loose_folder / "Eduardo_Barangay_Clearance.png")
    create_nbi_clearance(loose_folder / "Beatriz_NBI_Clearance.png")
    create_voter_cert_pdf(loose_folder / "Antonio_Luna_Voters_Certification.pdf")

    print("\nDONE! All 15 unique IDs, documents, images, PDFs, and Word docs generated successfully!")

if __name__ == "__main__":
    main()
