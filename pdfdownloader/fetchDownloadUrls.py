import requests
import os
import google.generativeai as genai
from PIL import Image
import io
import base64
import time

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

print("\n--- Captcha Request ---")
print("URL:", url)
print("Headers:", headers)

response = requests.get(url, headers=headers)
print("ECI Response:", response.text)
data = response.json()

# Step 2: Decode captcha image from base64
captcha_b64 = data.get("captcha")
if not captcha_b64:
    print("No captcha found in response.")
    exit(1)

captcha_bytes = base64.b64decode(captcha_b64)
image = Image.open(io.BytesIO(captcha_bytes))

# Step 3: Send image to Gemini for recognition
# Configure Gemini API
api_key = os.getenv("GOOGLE_API_KEY") or "AIzaSyBJNxQnB5qHQHmLdNMTWgWEklkMbdGhgPo"  # Replace with your API key or set env var
if api_key == "YOUR_API_KEY_HERE":
    print("Please set your Gemini API key in the script or as the GOOGLE_API_KEY environment variable.")
    exit(1)
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-2.5-flash')
prompt = "What is the text in this captcha image? Only return the text, no explanation."

print("\n--- Gemini LLM Request ---")
print("Prompt:", prompt)
print("Image: <PIL.Image object, not shown>")

# Gemini expects a PIL Image object
response = model.generate_content([prompt, image])
print("Gemini Captcha Recognition Response:", response.text)

# Step 4: Send request to generate-published-eroll
captcha_text = response.text.strip()
captcha_id = data.get("id")

if not captcha_id:
    print("No captchaId found in the first response.")
    exit(1)

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
    "districtCd": "S2917",
    "acNumber": 59,
    "partNumberList": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236],
    "captcha": captcha_text,
    "captchaId": captcha_id,
    "langCd": "ENG",
    "isSupplement": False
}

print("\n--- generate-published-eroll Request ---")
print("URL:", publish_url)
print("Headers:", publish_headers)
print("Payload:", payload)

publish_response = requests.post(publish_url, headers=publish_headers, json=payload)
print("generate-published-eroll Response:", publish_response.text)

# Step 5: If status code is 200, download the published file
if publish_response.status_code == 200:
    publish_json = publish_response.json()
    if publish_json.get("statusCode") == 200 and publish_json.get("payload") and len(publish_json["payload"]) > 0:
        # Save to timestamped file in 'files' folder
        os.makedirs("files", exist_ok=True)
        import json
        import base64
        # If payload is a list, process all
        if isinstance(publish_json.get("payload"), list):
            for idx, file_info in enumerate(publish_json["payload"]):
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
                print(f"\n--- get-published-file Request {idx+1} ---")
                print("URL:", get_file_url)
                print("Headers:", get_file_headers)
                get_file_response = requests.get(get_file_url, headers=get_file_headers)
                print("get-published-file Response Status:", get_file_response.status_code)
                ts = int(time.time())
                filename = f"files/eroll_{idx+1}_{ts}.pdf"
                json_filename = f"files/eroll_{idx+1}_{ts}.json"
                try:
                    file_json = get_file_response.json()
                    with open(json_filename, "w", encoding="utf-8") as jf:
                        json.dump(file_json, jf, ensure_ascii=False, indent=2)
                    if isinstance(file_json.get("payload"), str):
                        pdf_bytes = base64.b64decode(file_json["payload"])
                        with open(filename, "wb") as f:
                            f.write(pdf_bytes)
                        print(f"Saved base64-decoded PDF to {filename}")
                    else:
                        with open(filename, "wb") as f:
                            f.write(get_file_response.content)
                        print(f"Saved raw PDF to {filename}")
                    print(f"Saved JSON response to {json_filename}")
                except Exception as e:
                    with open(filename, "wb") as f:
                        f.write(get_file_response.content)
                    print(f"Saved raw PDF to {filename} (exception: {e})")
        else:
            # Single object fallback (previous logic)
            file_info = publish_json["payload"][0]
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
            print("\n--- get-published-file Request ---")
            print("URL:", get_file_url)
            print("Headers:", get_file_headers)
            get_file_response = requests.get(get_file_url, headers=get_file_headers)
            print("get-published-file Response Status:", get_file_response.status_code)
            filename = f"files/eroll_{int(time.time())}.pdf"
            json_filename = f"files/eroll_{int(time.time())}.json"
            try:
                file_json = get_file_response.json()
                with open(json_filename, "w", encoding="utf-8") as jf:
                    json.dump(file_json, jf, ensure_ascii=False, indent=2)
                if isinstance(file_json.get("payload"), str):
                    pdf_bytes = base64.b64decode(file_json["payload"])
                    with open(filename, "wb") as f:
                        f.write(pdf_bytes)
                    print(f"Saved base64-decoded PDF to {filename}")
                else:
                    with open(filename, "wb") as f:
                        f.write(get_file_response.content)
                    print(f"Saved raw PDF to {filename}")
                print(f"Saved JSON response to {json_filename}")
            except Exception as e:
                with open(filename, "wb") as f:
                    f.write(get_file_response.content)
                print(f"Saved raw PDF to {filename} (exception: {e})")
    else:
        print("No valid payload found in generate-published-eroll response.")
else:
    print("generate-published-eroll did not return status code 200.")
