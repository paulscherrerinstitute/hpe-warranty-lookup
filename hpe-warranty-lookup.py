import sys
import urllib.parse
import requests
from bs4 import BeautifulSoup


def get_warranty_HTML(serial):
    params = urllib.parse.urlencode({
        'rows[0].item.serialNumber': serial,
        'rows[0].item.countryCode': "US"
        })
    headers = {"Content-type": "application/x-www-form-urlencoded"}

    response = requests.post("https://support.hpe.com/hpsc/wc/public/find", params=params, headers=headers)
    
    if not response.ok:
        sys.exit(response.status_code, response.content)

    data = response.content
    return data


def extract_warranty_info(html):
    active_warranties = []
    soup = BeautifulSoup(html, 'html.parser')
    active = soup.find_all("td", attrs={"style": 'color: Green'}, string="Active")

    for td in active:
        warranty = {
            "service_type" : td.previous_sibling.previous_sibling.previous_sibling.get_text(strip=True),
            "start_date"   : td.previous_sibling.previous_sibling.string,
            "end_date"     : td.previous_sibling.string
        }
        active_warranties.append(warranty)

    return active_warranties


def main(argv):
    if len(argv) < 2:
        sys.exit("ERROR: A valid HPE Serial Number must be specified as an argument to this script")

    warranty_html = get_warranty_HTML(argv[1])
    print(extract_warranty_info(warranty_html))
 
if __name__ == "__main__":
    main(sys.argv)
