import requests
import random
import json
import re
import argparse
from argparse import RawTextHelpFormatter
import sys
import time
import ast
import unidecode
from datetime import datetime
import urllib.parse
import threading
import csv
from urllib.parse import urlparse

# You may store your session cookie here persistently
li_at = "YOUR-COOKIE-VALUE"

# Converting German umlauts
special_char_map = {ord('ä'):'ae', ord('ü'):'ue', ord('ö'):'oe', ord('ß'):'ss'}

format_examples = '''
--email-format '{0}.{1}@example.com' --> john.doe@example.com
--email-format '{0[0]}.{1}@example.com' --> j.doe@example.com
--email-format '{1}@example.com' --> doe@example.com
--email-format '{0}@example.com' --> john@example.com
--email-format '{0[0]}{1[0]}@example.com' --> jd@example.com
'''

parser = argparse.ArgumentParser("linkedindumper.py", formatter_class=RawTextHelpFormatter)
parser.add_argument("--url", metavar='<linkedin-url>', help="A LinkedIn company url - https://www.linkedin.com/company/<company>", type=str, required=True)
parser.add_argument("--cookie", metavar='<cookie>', help="LinkedIn 'li_at' session cookie", type=str, required=False)
parser.add_argument("--include-private-profiles", help="Show private accounts too", required=False, action='store_true')
parser.add_argument("--include-contact-infos", help="Query each employee and retrieve contact infos", required=False, action='store_true')
parser.add_argument("--jitter", help="Add a random jitter to HTTP requests", required=False, action='store_true')
parser.add_argument("--email-format", help="Python string format for emails; for example:"+format_examples, metavar="<mail-format>", required=False, type=str)
parser.add_argument("--output-json", help="Store results in json output file", metavar="<json-file>", type=str, required=False)
parser.add_argument("--output-csv", help="Store results in csv output file", metavar="<csv-file>", type=str, required=False)

args = parser.parse_args()
url = args.url

# Optional CSRF token, not needed for GET requests but still defined to be sure
JSESSIONID = "ajax:5739908118104050450"

# Overwrite variables if set via CLI
if args.cookie:
    li_at = args.cookie

mailformat = args.email_format if args.email_format else False

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0',
    'Content-type': 'application/json',
    'Csrf-Token': JSESSIONID
}
cookies_dict = {"li_at": li_at, "JSESSIONID": JSESSIONID}

def print_logo():
    print("""\

 ██▓     ██▓ ███▄    █  ██ ▄█▀▓█████ ▓█████▄  ██▓ ███▄    █ ▓█████▄  █    ██  ███▄ ▄███▓ ██▓███  ▓█████  ██▀███  
▓██▒    ▓██▒ ██ ▀█   █  ██▄█▒ ▓█   ▀ ▒██▀ ██▌▓██▒ ██ ▀█   █ ▒██▀ ██▌ ██  ▓██▒▓██▒▀█▀ ██▒▓██░  ██▒▓█   ▀ ▓██ ▒ ██▒
▒██░    ▒██▒▓██  ▀█ ██▒▓███▄░ ▒███   ░██   █▌▒██▒▓██  ▀█ ██▒░██   █▌▓██  ▒██░▓██    ▓██░▓██░ ██▓▒▒███   ▓██ ░▄█ ▒
▒██░    ░██░▓██▒  ▐▌██▒▓██ █▄ ▒▓█  ▄ ░▓█▄   ▌░██░▓██▒  ▐▌██▒░▓█▄   ▌▓▓█  ░██░▒██    ▒██ ▒██▄█▓▒ ▒▒▓█  ▄ ▒██▀▀█▄  
░██████▒░██░▒██░   ▓██░▒██▒ █▄░▒████▒░▒████▓ ░██░▒██░   ▓██░░▒████▓ ▒▒█████▓ ▒██▒   ░██▒▒██▒ ░  ░░▒████▒░██▓ ▒██▒
░ ▒░▓  ░░▓  ░ ▒░   ▒ ▒ ▒ ▒▒ ▓▒░░ ▒░ ░ ▒▒▓  ▒ ░▓  ░ ▒░   ▒ ▒  ▒▒▓  ▒ ░▒▓▒ ▒ ▒ ░ ▒░   ░  ░▒▓▒░ ░  ░░░ ▒░ ░░ ▒▓ ░▒▓░
░ ░ ▒  ░ ▒ ░░ ░░   ░ ▒░░ ░▒ ▒░ ░ ░  ░ ░ ▒  ▒  ▒ ░░ ░░   ░ ▒░ ░ ▒  ▒ ░░▒░ ░ ░ ░  ░      ░░▒ ░      ░ ░  ░  ░▒ ░ ▒░
  ░ ░    ▒ ░   ░   ░ ░ ░ ░░ ░    ░    ░ ░  ░  ▒ ░   ░   ░ ░  ░ ░  ░  ░░░ ░ ░ ░      ░   ░░          ░     ░░   ░ 
    ░  ░ ░           ░ ░  ░      ░  ░   ░     ░           ░    ░       ░            ░               ░  ░   ░     
                                      ░                      ░                                         ░ by LRVT      
    """)

def clean_data(data):
    emoj = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
                      "\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
                      "\U00002500-\U00002BEF\U00002702-\U000027B0"
                      "\U000024C2-\U0001F251\U0001f926-\U0001f937"
                      "\U00010000-\U0010ffff\u2640-\u2642\u2600-\u2B55"
                      "\u200d\u23cf\u23e9\u231a\ufe0f\u3030]+", re.UNICODE)
    cleaned = re.sub(emoj, '', data).strip()
    cleaned = cleaned.replace('Ü','Ue').replace('Ä','Ae').replace('Ö','Oe').replace('ü','ue').replace('ä','ae').replace('ö','oe')
    cleaned = cleaned.replace(',', '').replace(';', ',')
    cleaned = unidecode.unidecode(cleaned)
    return cleaned.strip()

def parse_employee_results(results):
    employee_dict = []
    for employee in results:
        try:
            account_name = clean_data(employee["itemUnion"]['entityResult']["title"]["text"]).split(" ")
            badwords = ['Prof.', 'Dr.', 'M.A.', ',', 'LL.M.']
            for word in list(account_name):
                if word in badwords:
                    account_name.remove(word)
            firstname = ' '.join(account_name[:-1]) if len(account_name) > 2 else account_name[0]
            lastname = account_name[-1]
        except:
            continue

        try:
            position = clean_data(employee["itemUnion"]['entityResult']["primarySubtitle"]["text"])
        except:
            position = "N/A"

        gender = "N/A"

        try:
            location = employee["itemUnion"]['entityResult']["secondarySubtitle"]["text"]
        except:
            location = "N/A"

        try:
            profile_link = employee["itemUnion"]['entityResult']["navigationUrl"].split("?")[0]
        except:
            profile_link = "N/A"

        if args.include_private_profiles or (firstname != "LinkedIn" and lastname != "Member"):

            if args.include_contact_infos and profile_link != "N/A":
                username = profile_link.rstrip("/").split("/")[-1]
                full_details = get_employee_contact_infos(username)

            employee_dict.append({
                "firstname": firstname,
                "lastname": lastname,
                "position": position,
                "gender": gender,
                "location": location,
                "profile_link": profile_link,
                "contact_info": full_details
            })

    return employee_dict

def get_company_id(company):
    company_encoded = urllib.parse.quote(company)
    api1 = f"https://www.linkedin.com/voyager/api/voyagerOrganizationDashCompanies?decorationId=com.linkedin.voyager.dash.deco.organization.MiniCompany-10&q=universalName&universalName={company_encoded}"
    r = requests.get(api1, headers=headers, cookies=cookies_dict, timeout=200)
    return r.json()["elements"][0]["entityUrn"].split(":")[-1]

def get_employee_data(company_id, start, count=10):
    api2 = f"https://www.linkedin.com/voyager/api/search/dash/clusters?decorationId=com.linkedin.voyager.dash.deco.search.SearchClusterCollection-165&origin=COMPANY_PAGE_CANNED_SEARCH&q=all&query=(flagshipSearchIntent:SEARCH_SRP,queryParameters:(currentCompany:List({company_id}),resultType:List(PEOPLE)),includeFiltersInResponse:false)&count={count}&start={start}"
    r = requests.get(api2, headers=headers, cookies=cookies_dict, timeout=200)
    return r.json()

def get_employee_contact_infos(username):
    api3 = f"https://www.linkedin.com/voyager/api/graphql?includeWebMetadata=true&variables=(memberIdentity:{username})&queryId=voyagerIdentityDashProfiles.c7452e58fa37646d09dae4920fc5b4b9"
    r = requests.get(api3, headers=headers, cookies=cookies_dict, timeout=200)
    
    try:
        data = r.json()
    except Exception as e:
        print("[!] Failed to decode JSON:", e)
        return None

    # Init default values
    full_name = email = birthdate = address = phone = None

    elements = data.get("data", {}) \
               .get("identityDashProfilesByMemberIdentity", {}) \
               .get("elements", [])

    # Pick the first profile if it exists
    if elements:
        profile = elements[0]

        first = profile.get("firstName")
        last = profile.get("lastName")
        
        # Email
        email_data = profile.get("emailAddress")
        email = email_data.get("emailAddress") if isinstance(email_data, dict) else None

        # Address
        address = profile.get("address")

        # Birthdate
        birth = profile.get("birthDateOn")
        if isinstance(birth, dict):
            day = birth.get("day")
            month = birth.get("month")
            birthdate = f"{day}. {month_to_string(month)}" if day and month else None
        else:
            birthdate = None

        # Phone
        phone = None
        phones = profile.get("phoneNumbers", [])
        if phones and isinstance(phones, list):
            phone_obj = phones[0].get("phoneNumber")
            if isinstance(phone_obj, dict):
                phone = phone_obj.get("number")

    return {
        "firstname": first,
        "lastname": last,
        "email": email,
        "birthdate": birthdate,
        "address": address,
        "phone": phone
    }

def month_to_string(month):
    months = {
        1: "Januar", 2: "Februar", 3: "März", 4: "April",
        5: "Mai", 6: "Juni", 7: "Juli", 8: "August",
        9: "September", 10: "Oktober", 11: "November", 12: "Dezember"
    }
    return months.get(month, f"Monat {month}")

def progressbar(it, prefix="", size=60, out=sys.stdout):
    count = len(it)
    def show(j):
        x = int(size * j / count)
        print("{}[{}{}] {}/{}".format(prefix, "#" * x, "." * (size - x), j, count), end='\r', file=out, flush=True)
    show(0)
    for i, item in enumerate(it):
        yield item
        show(i + 1)
    print("\n", flush=True, file=out)

def main():
    if url.startswith('https://www.linkedin.com/company/'):
        try:
            company = url.partition('company/')[2].split('/')[0]
            company_id = get_company_id(company)
            response = get_employee_data(company_id, 0)
            paging_total = response["paging"]["total"]
            required_pagings = -(-paging_total // 10)

            if args.include_contact_infos:
                args.output_json = str(company) + ".json"

            employee_dict = []

            print_logo()

            print("[i] Company Name: " + company)
            print("[i] Company X-ID: " + company_id)
            print("[i] LN Employees: " + str(paging_total) + " employees found")
            print("[i] Dumping Date: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            if mailformat:
                print("[i] Email Format: " + mailformat)

            if args.output_csv or args.output_json:
                print()
            for page in progressbar(range(required_pagings), "Progress: ", 40):
                if args.jitter:
                    time.sleep(random.choice([0.5, 1, 0.8, 0.3, 3, 1.5, 5]))
                data = get_employee_data(company_id, page * 10)
                for i in range(3):
                    try:
                        results = data["elements"][i]["items"]
                        employee_dict.extend(parse_employee_results(results))
                    except:
                        pass

            seen = set()
            unique_employees = []
            for d in employee_dict:
                dedupe_key = (d.get("firstname"), d.get("lastname"), d.get("profile_link"))
                if dedupe_key not in seen:
                    seen.add(dedupe_key)
                    unique_employees.append(d)
            employee_dict = unique_employees

            if mailformat:
                for person in employee_dict:
                    firstname_clean = person["firstname"].replace(".", "").lower().translate(special_char_map)
                    lastname_clean = person["lastname"].replace(".", "").lower().translate(special_char_map)
                    person["email"] = mailformat.format(firstname_clean, lastname_clean)

            if mailformat:
                legend = "Firstname;Lastname;Email;Position;Gender;Location;Profile"
            else:
                legend = "Firstname;Lastname;Position;Gender;Location;Profile"

            if not args.output_csv and not args.output_json:
                print(legend)
                for person in employee_dict:
                    if mailformat:
                        print(f"{person['firstname']};{person['lastname']};{person['email']};{person['position']};{person['gender']};{person['location']};{person['profile_link']}")                        
                    else:
                        print(";".join(person.values()))
                print()

            if args.output_json:
                try:
                    output_data = {
                        "company_id": company_id,
                        "company_url": url,
                        "company_slug": company,
                        "timestamp": datetime.now().isoformat(),
                        "employees": employee_dict
                    }
                    with open(args.output_json, 'w', encoding='utf-8') as f:
                        json.dump(output_data, f, ensure_ascii=False, indent=4)
                    print(f"[i] Results written to JSON: {args.output_json}")
                except Exception as e:
                    print(f"[!] Error writing JSON: {e}")

            if args.output_csv:
                try:
                    with open(args.output_csv, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f, delimiter=';')
                        if mailformat:
                            writer.writerow(["Firstname", "Lastname", "Email", "Position", "Gender", "Location", "Profile"])
                            for p in employee_dict:
                                writer.writerow([p['firstname'], p['lastname'], p['email'], p['position'], p['gender'], p['location'], p['profile_link']])
                        else:
                            writer.writerow(["Firstname", "Lastname", "Position", "Gender", "Location", "Profile"])
                            for p in employee_dict:
                                writer.writerow([p['firstname'], p['lastname'], p['position'], p['gender'], p['location'], p['profile_link']])
                    print(f"[i] Results written to CSV: {args.output_csv}")
                except Exception as e:
                    print(f"[!] Error writing CSV: {e}")

            print(f"[i] Successfully crawled {len(employee_dict)} unique {company} employee(s). Hurray ^_-")

        except Exception as e:
            print("[!] Exception. Either API has changed and this script is broken or authentication failed.")
            print("    > Set 'li_at' variable permanently in script or use the '--cookie' CLI flag!")
            print(f"[debug] {e}")
    else:
        print("\n[!] Invalid URL provided.")
        print("[i] Example URL: 'https://www.linkedin.com/company/apple'")

if __name__ == "__main__":
    main()