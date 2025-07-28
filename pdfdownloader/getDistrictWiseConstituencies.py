import requests
import json
import time

# District mapping (value -> name)
districts = {
    "S2903": "Adilabad",
    "S2930": "Bhadradri",
    "S2928": "Hanumakonda",
    "S2917": "Hyderabad", #done
    "S2907": "Jagtial",
    "S2925": "Jangaon",
    "S2929": "Jayashankar Bhupalpalle",
    "S2921": "Jogulamba Gadwal",
    "S2906": "Kamareddy",
    "S2909": "Karimnagar",
    "S2931": "Khammam",
    "S2901": "Kumaram Bheem Asifabad",
    "S2926": "Mahabubabad",
    "S2918": "Mahabubnagar",
    "S2902": "Mancherial",
    "S2912": "Medak",
    "S2916": "Medchal Malkajgiri",
    "S2932": "Mulugu",
    "S2919": "Nagarkurnool",
    "S2922": "Nalgonda",
    "S2933": "Narayanpet",
    "S2904": "Nirmal",
    "S2905": "Nizamabad",
    "S2908": "Peddapalli",
    "S2910": "Rajanna Sircilla",
    "S2914": "Rangareddy",
    "S2911": "Sangareddy",
    "S2913": "Siddipet",
    "S2923": "Suryapet",
    "S2915": "Vikarabad",
    "S2920": "Wanaparthy",
    "S2927": "Warangal",
    "S2924": "Yadadri Bhongiri"
}

# Headers for the part list API
part_list_headers = {
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
    "sec-ch-ua-platform": '"Windows"'
}

base_url = "https://gateway-voters.eci.gov.in/api/v1/common/acs/"
part_list_url = "https://gateway-voters.eci.gov.in/api/v1/printing-publish/get-part-list"
results = []

for district_id, name in districts.items():
    url = base_url + district_id
    try:
        response = requests.get(url)
        response.raise_for_status()
        constituencies_data = response.json()

        # Process each constituency to get part lists
        constituencies_with_parts = []
        for constituency in constituencies_data:
            try:
                # Extract constituency details
                ac_number = constituency.get('asmblyNo')  # assembly number
                
                # Prepare payload for part list API
                payload = {
                    "stateCd": "S29",
                    "districtCd": district_id,
                    "acNumber": ac_number,
                    "pageNumber": 0,
                    "pageSize": 10000
                }
                
                # Make request to get part list
                part_response = requests.post(
                    part_list_url,
                    headers=part_list_headers,
                    json=payload
                )
                part_response.raise_for_status()
                part_list_data = part_response.json()
                
                # Add part list data to constituency
                constituency_with_parts = {
                    **constituency,
                    "partList": part_list_data
                }
                constituencies_with_parts.append(constituency_with_parts)
                
                print(f"Fetched part list for {name} - Constituency {ac_number}")
                
            except Exception as e:
                print(f"Failed to fetch part list for {name} - Constituency {constituency.get('asmblyNo', 'Unknown')}: {e}")
                # Add constituency without part list data
                constituencies_with_parts.append(constituency)
            
            time.sleep(0.5)  # delay between constituency requests

        # Append in the required format
        results.append({
            "id": district_id,
            "Name": name,
            "Constituencies": constituencies_with_parts
        })

        print(f"✅ Completed fetching for {name}")
    except Exception as e:
        print(f"Failed for {name} ({district_id}): {e}")
    time.sleep(1)  # delay between district requests

# Save to JSON file
with open("districts_with_constituencies_and_parts.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("✅ Done. Saved to districts_with_constituencies_and_parts.json")
