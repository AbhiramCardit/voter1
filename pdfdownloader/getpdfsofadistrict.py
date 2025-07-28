import requests
import os
import google.generativeai as genai
from PIL import Image
import io
import base64
import time
import json
import re

def sanitize_filename(filename):
    """Remove or replace invalid characters for Windows filenames"""
    # Remove or replace invalid characters including newlines, tabs, and other whitespace
    invalid_chars = r'[<>:"/\\|?*\n\r\t]'
    filename = re.sub(invalid_chars, '_', filename)
    # Replace multiple consecutive underscores with a single one
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing spaces, dots, and underscores
    filename = filename.strip(' ._')
    # Limit length to avoid path too long errors
    if len(filename) > 200:
        filename = filename[:200]
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"
    return filename

def get_pdfs_for_district(district_id):
    """
    Fetch PDFs for all constituencies and their part lists in a given district.
    Args:
        district_id (str): The district ID (e.g., "S2917" for Hyderabad)
    """
    # Load the districts data
    try:
        with open("districts_with_constituencies_and_parts.json", "r", encoding="utf-8") as f:
            districts_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: districts_with_constituencies_and_parts.json not found")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in districts_with_constituencies_and_parts.json")
        return
    
    # Find the district
    district = None
    for d in districts_data:
        if d["id"] == district_id:
            district = d
            break
    
    if not district:
        print(f"Error: District with ID {district_id} not found")
        return
    
    district_name = district['Name'].strip().replace(' ', '_')
    print(f"Processing district: {district['Name']} ({district_id})")
    print(f"Found {len(district['Constituencies'])} constituencies")
    
    # Process each constituency
    for constituency in district['Constituencies']:
        constituency_name = constituency['asmblyName'].strip().replace(' ', '_')
        ac_number = constituency['asmblyNo']
        district_cd = constituency['districtCd']
        
        print(f"\n{'='*50}")
        print(f"Processing constituency: {constituency['asmblyName']} (AC: {ac_number})")
        print(f"{'='*50}")
        
        # Get part list for this constituency
        part_list = constituency.get('partList', {}).get('payload', [])
        if not part_list:
            print(f"No part list found for constituency {constituency['asmblyName']}")
            continue
        
        print(f"Found {len(part_list)} parts in constituency {constituency['asmblyName']}")
        
        # Prepare output directory
        out_dir = os.path.join('PDFS', district_name, constituency_name)
        os.makedirs(out_dir, exist_ok=True)
        
        # Gather all part numbers and names
        part_numbers = [part['partNumber'] for part in part_list]
        part_names = {part['partNumber']: sanitize_filename(part['partName'].strip().replace(' ', '_')) for part in part_list}
        max_retries = 20
        for attempt in range(1, max_retries + 1):
            print(f"Attempt {attempt} for Constituency {constituency['asmblyName']}...")
            # Step 1: Get captcha from ECI
            url = "https://gateway-voters.eci.gov.in/api/v1/captcha-service/generateCaptcha/EROLL"
            headers = {
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "Origin": "https://voters.eci.gov.in",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "applicationname": "VSP",
                "appname": "VSP",
                "atkn_bnd": "null",
                "channelidobo": "VSP",
                "platform-type": "ECIWEB",
                "rtkn_bnd": "null",
                "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            }
            print("Getting captcha...")
            response = requests.get(url, headers=headers)
            data = response.json()
            captcha_b64 = data.get("captcha")
            if not captcha_b64:
                print("No captcha found in response.")
                continue
            captcha_bytes = base64.b64decode(captcha_b64)
            image = Image.open(io.BytesIO(captcha_bytes))
            api_key = os.getenv("GOOGLE_API_KEY") or "AIzaSyBJNxQnB5qHQHmLdNMTWgWEklkMbdGhgPo"
            if api_key == "YOUR_API_KEY_HERE":
                print("Please set your Gemini API key in the script or as the GOOGLE_API_KEY environment variable.")
                continue
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = "What is the text in this captcha image? Only return the text, no explanation."
            print("Recognizing captcha with Gemini...")
            response = model.generate_content([prompt, image])
            captcha_text = response.text.strip()
            print(f"Captcha recognized: {captcha_text}")
            captcha_id = data.get("id")
            if not captcha_id:
                print("No captchaId found in the first response.")
                continue
            publish_url = "https://gateway-voters.eci.gov.in/api/v1/printing-publish/generate-published-eroll"
            publish_headers = {
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "Origin": "https://voters.eci.gov.in",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "applicationname": "VSP",
                "atkn_bnd": "null",
                "channelidobo": "VSP",
                "content-type": "application/json",
                "platform-type": "ECIWEB",
                "rtkn_bnd": "null",
                "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            }
            payload = {
                "stateCd": "S29",
                "districtCd": district_cd,
                "acNumber": ac_number,
                "partNumberList": part_numbers,
                "captcha": captcha_text,
                "captchaId": captcha_id,
                "langCd": "ENG",
                "isSupplement": False
            }
            print("Requesting PDF generation for all parts in this constituency...")
            publish_response = requests.post(publish_url, headers=publish_headers, json=payload)
            if publish_response.status_code == 200:
                publish_json = publish_response.json()
                print(f"API Response: {publish_json}")
                if publish_json.get("statusCode") == 200 and publish_json.get("payload") and len(publish_json["payload"]) > 0:
                    if isinstance(publish_json.get("payload"), list):
                        for idx, file_info in enumerate(publish_json["payload"]):
                            # Skip None values in the payload
                            if file_info is None:
                                print(f"Skipping None file_info at index {idx}")
                                continue
                            
                            # Check if required keys exist
                            if "fileUuid" not in file_info or "bucketName" not in file_info:
                                print(f"Skipping file_info at index {idx} - missing required keys: {file_info}")
                                continue
                                
                            image_path = file_info["fileUuid"]
                            bucket_name = file_info["bucketName"]
                            get_file_url = f"https://gateway-voters.eci.gov.in/api/v1/printing-publish/get-published-file?imagePath={image_path}&bucketName={bucket_name}"
                            get_file_headers = {
                                "Accept": "application/json",
                                "Accept-Language": "en-US,en;q=0.9",
                                "Connection": "keep-alive",
                                "CurrentRole": "citizen",
                                "Origin": "https://voters.eci.gov.in",
                                "PLATFORM-TYPE": "ECIWEB",
                                "Sec-Fetch-Dest": "empty",
                                "Sec-Fetch-Mode": "cors",
                                "Sec-Fetch-Site": "same-site",
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                                "applicationName": "VSP",
                                "channelidobo": "VSP",
                                "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                                "sec-ch-ua-mobile": "?0",
                                "sec-ch-ua-platform": '"Windows"',
                            }
                            print(f"Downloading file {idx+1}...")
                            get_file_response = requests.get(get_file_url, headers=get_file_headers)
                            part_num = file_info.get('partNumber') or part_numbers[idx]
                            part_name = part_names.get(part_num, f"Part{part_num}")
                            base_filename = f"{part_num}_{part_name}"
                            pdf_filename = os.path.join(out_dir, f"{base_filename}.pdf")
                            json_filename = os.path.join(out_dir, f"{base_filename}.json")
                            
                            # Ensure directory exists
                            os.makedirs(os.path.dirname(pdf_filename), exist_ok=True)
                            
                            try:
                                file_json = get_file_response.json()
                                with open(json_filename, "w", encoding="utf-8") as jf:
                                    json.dump(file_json, jf, ensure_ascii=False, indent=2)
                                if isinstance(file_json.get("payload"), str):
                                    pdf_bytes = base64.b64decode(file_json["payload"])
                                    with open(pdf_filename, "wb") as f:
                                        f.write(pdf_bytes)
                                    print(f"Saved base64-decoded PDF to {pdf_filename}")
                                else:
                                    with open(pdf_filename, "wb") as f:
                                        f.write(get_file_response.content)
                                    print(f"Saved raw PDF to {pdf_filename}")
                                print(f"Saved JSON response to {json_filename}")
                            except Exception as e:
                                with open(pdf_filename, "wb") as f:
                                    f.write(get_file_response.content)
                                print(f"Saved raw PDF to {pdf_filename} (exception: {e})")
                    else:
                        print("Unexpected payload format")
                    break
                else:
                    print("No valid payload found in generate-published-eroll response. Retrying...")
            else:
                print("generate-published-eroll did not return status code 200. Retrying...")
            time.sleep(2)
        else:
            print(f"Failed to fetch PDFs for Constituency {constituency['asmblyName']} after {max_retries} attempts. Skipping.")
        time.sleep(2)

if __name__ == "__main__":
    # Example usage
    district_id = "S2909"  
    get_pdfs_for_district(district_id) 