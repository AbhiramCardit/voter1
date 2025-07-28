import os
import pdfplumber
import re
import json
from collections import OrderedDict

# BBox definitions
bbox1 = (15,0,595,30) #topbar
bbox2 = (15,30,200,800) #1st column
bbox3 = (200,30,400,800) #2nd column
bbox4 = (390,30,595,800) #3rd column

key_order = [
    "serial_no", "voter_id", "name", "relation", "relation_name", "house_number", "age", "gender",
    "constituency_no_name", "part_no", "section_no_name"
]
def order_dict(d):
    return OrderedDict((k, d.get(k, None)) for k in key_order)

def parse_voters(text, constituency_no_name, part_no, section_no_name):
    text = re.sub(r"Photo", "", text)
    text = re.sub(r"Available", "", text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    voters = []
    i = 0
    while i < len(lines):
        m = re.match(r"(\d+)\s+([A-Z0-9]+)", lines[i])
        if not m:
            i += 1
            continue
        voter = {
            "serial_no": m.group(1),
            "voter_id": m.group(2),
            "constituency_no_name": constituency_no_name,
            "part_no": part_no,
            "section_no_name": section_no_name
        }
        i += 1
        # Name (may span multiple lines, but stop if next line is a relation field)
        name = ""
        if i < len(lines) and lines[i].startswith("Name :"):
            name = lines[i].split(":",1)[1].strip()
            i += 1
            while i < len(lines) and not (lines[i].startswith("Husbands Name:") or lines[i].startswith("Fathers Name:") or lines[i].startswith("Mothers Name:") or lines[i].startswith("House Number :") or lines[i].startswith("Age :") or lines[i].startswith("Others Name:") or lines[i].startswith("Other :") or lines[i].startswith("Others:") or lines[i].startswith("Others :")):
                name += " " + lines[i].strip()
                i += 1
            voter["name"] = name.strip()
        # Relation (Husband/Father/Mother/Others, may span multiple lines)
        relation = relation_name = ""
        relation_types = ["Husbands Name:", "Fathers Name:", "Mothers Name:", "Others Name:", "Other :", "Others:", "Others :"]
        if i < len(lines) and any(lines[i].startswith(rt) for rt in relation_types):
            rel_line = lines[i]
            for rt in relation_types:
                if rel_line.startswith(rt):
                    if rt in ["Husbands Name:", "Fathers Name:", "Mothers Name:"]:
                        relation = rt.split()[0][:-1]  # Husband, Father, Mother
                    else:
                        relation = "Other"
                    voter["relation"] = relation
                    relation_name = rel_line.split(":",1)[1].strip()
                    break
            i += 1
            while i < len(lines) and not (lines[i].startswith("House Number :") or lines[i].startswith("Age :") or lines[i].startswith("Name :") or any(lines[i].startswith(rt) for rt in relation_types)):
                relation_name += " " + lines[i].strip()
                i += 1
            voter["relation_name"] = relation_name.strip()
        # House Number (may span multiple lines)
        house_number = ""
        if i < len(lines) and lines[i].startswith("House Number :"):
            house_number = lines[i].split(":",1)[1].strip()
            i += 1
            while i < len(lines) and not (lines[i].startswith("Age :") or lines[i].startswith("Name :") or lines[i].startswith("Husbands Name:") or lines[i].startswith("Fathers Name:") or lines[i].startswith("Mothers Name:")):
                house_number += " " + lines[i].strip()
                i += 1
            voter["house_number"] = house_number.strip()
        # Age and Gender
        if i < len(lines) and lines[i].startswith("Age :"):
            age_gender = lines[i]
            m2 = re.match(r"Age :\s*(\d+)\s*Gender :\s*([A-Za-z]+)", age_gender)
            if m2:
                voter["age"] = m2.group(1)
                voter["gender"] = m2.group(2)
            i += 1
        voters.append(order_dict(voter))
    return voters

def process_folder(pdf_folder, json_folder):
    os.makedirs(json_folder, exist_ok=True)
    for root, dirs, files in os.walk(pdf_folder):
        # Only process the lowest-level folders (those containing PDFs)
        pdfs = [f for f in files if f.lower().endswith('.pdf')]
        if pdfs:
            rel_path = os.path.relpath(root, pdf_folder)
            out_dir = os.path.join(json_folder, rel_path)
            os.makedirs(out_dir, exist_ok=True)
            folder_name = os.path.basename(root)
            out_path = os.path.join(out_dir, f"{folder_name}.json")
            if os.path.exists(out_path):
                print(f"Skipping folder: {root} (JSON already exists: {out_path})")
                continue
            all_voters = []
            print(f"\nProcessing folder: {root}")
            print(f"PDF count: {len(pdfs)}")
            for idx, pdf_file in enumerate(pdfs, 1):
                pdf_path = os.path.join(root, pdf_file)
                pdf_voters = []
                try:
                    with pdfplumber.open(pdf_path) as pdf:
                        num_pages = len(pdf.pages)
                        pdf_voters_count = 0
                        for page_number in range(3, num_pages):
                            if page_number == num_pages:
                                continue
                            page = pdf.pages[page_number - 1]
                            topbar_text = page.within_bbox(bbox1).extract_text() or ""
                            constituency_no_name = part_no = section_no_name = None
                            m = re.search(r"Assembly Constituency No and Name\s*:\s*([^\n]+)\s*Part No\.\s*:\s*(\d+)", topbar_text)
                            if m:
                                constituency_no_name = m.group(1).strip()
                                part_no = m.group(2).strip()
                            m2 = re.search(r"Section No and Name\s*([\d\w\-]+-[^\n]+)", topbar_text)
                            if m2:
                                section_no_name = m2.group(1).strip()
                            for bbox in [bbox2, bbox3, bbox4]:
                                col_text = page.within_bbox(bbox).extract_text() or ""
                                voters = parse_voters(col_text, constituency_no_name, part_no, section_no_name)
                                pdf_voters.extend(voters)
                        pdf_voters_count = len(pdf_voters)
                        print(f"  [{idx}/{len(pdfs)}] {pdf_file} | Pages: {num_pages} | Extracted voters: {pdf_voters_count}")
                except Exception as e:
                    print(f"  Error processing {pdf_path}: {e}")
                all_voters.extend(pdf_voters)
            # Sort and write JSON for this folder
            all_voters_sorted = sorted(all_voters, key=lambda v: int(v["serial_no"]))
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(all_voters_sorted, f, ensure_ascii=False, indent=2)
            print(f"  Written {out_path} with {len(all_voters_sorted)} voters\n")
        # Recurse into subfolders
        for d in dirs:
            process_folder(os.path.join(root, d), os.path.join(json_folder, d))

if __name__ == "__main__":
    process_folder("PDFS", "JSONS") 