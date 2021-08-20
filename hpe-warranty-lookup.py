import sys
import urllib.parse
import requests
from bs4 import BeautifulSoup
import argparse


def get_warranty_HTML(serial):
    params = urllib.parse.urlencode({
        'rows[0].item.serialNumber': serial,
        'rows[0].item.countryCode': "US",
        # 'rows[0].item.productNumber': "719064-B21"
        })
    headers = {"Content-type": "application/x-www-form-urlencoded"}

    response = requests.post("https://support.hpe.com/hpsc/wc/public/find", params=params, headers=headers)
    
    if not response.ok:
        sys.exit(response.status_code, response.content)

    data = response.content
    # print(data)
    return extract_warranty_info(data)
    # return data


def extract_warranty_info(html):
    active_warranties = []
    soup = BeautifulSoup(html, 'html.parser')
    active = soup.find_all("td", attrs={"style": 'color: Green'}, string="Active")
    expired = soup.find_all("td", attrs={"style": 'color: Red'}, string="Expired")

    for td in active:
        warranty = {
            "service_type" : td.previous_sibling.previous_sibling.previous_sibling.get_text(strip=True),
            "start_date"   : td.previous_sibling.previous_sibling.string,
            "end_date"     : td.previous_sibling.string
        }
        active_warranties.append(warranty)
    for td in expired:
        warranty = {
            "service_type" : td.previous_sibling.previous_sibling.previous_sibling.get_text(strip=True),
            "start_date"   : td.previous_sibling.previous_sibling.string,
            "end_date"     : td.previous_sibling.string
        }
        active_warranties.append(warranty)

    return active_warranties


if __name__ == "__main__":
    import json
    parser = argparse.ArgumentParser(usage="Small tool to retrieve HPE harware warranty status, using the serial number")
    parser.add_argument("serial", type=str, help="serial number of the HPE hardware", nargs="+")
    # parser.add_argument("--model", type=str, help="model number of HPE harware")
    args = parser.parse_args()

    systems = {}
    for serial in args.serial:
        # print(serial)

        systems[serial] = get_warranty_HTML(serial)

    print(json.dumps(systems))

    # main(sys.argv)
