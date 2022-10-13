import sys
import urllib.parse
import requests
from bs4 import BeautifulSoup
import argparse
from time import sleep


def get_warranty_HTML(serials, country_code="US", product_number=None, iteration=0):
    """Gets the HTML from HPE warranty page

    Parameters
    ----------
    serial : list
        list of serial numbers, as strings
    country_code : str, optional
        contry code, by default "US"
    product_number : str, optional
        HPE product number, by default None
    iteration : int, optional
        iteration number, used when a captcha is found, by default 0

    Returns
    -------
    list
        list of dicts containing the warranty info
    """
    data = {}
    for i, serial in enumerate(serials):
        data[f"rows[{i}].item.serialNumber"] = serial
        data[f"rows[{i}].item.countryCode"] = country_code
    # if product_number is not None:
    #     data["rows[0].item.productNumber"] = product_number
    params = urllib.parse.urlencode(data)
    headers = {"Content-type": "application/x-www-form-urlencoded"}

    response = requests.post("https://support.hpe.com/hpsc/wc/public/find", params=params, headers=headers)
    
    if not response.ok:
        sys.exit(response.status_code, response.content)

    data = response.content
 
    with open("test.html", "w") as f:
        f.write(str(data))
    return extract_warranty_info(data, serials, iteration)


def extract_warranty_info(html, serials, iteration):
    """Extracts the warranty information from the HTML

    Parameters
    ----------
    html : str
        HTML content
    serial : list
        list of serial numbers, as strings
    iteration : int
        iteration number, used when a captcha is found, by default 0

    Returns
    -------
    list
        list of dicts containing the warranty info
    """

    max_iterations = 10
    active_warranties = {}
    soup = BeautifulSoup(html, 'html.parser')
    is_capcha = soup.find_all("title", string="Session confirmation - HPE Support Center")
    active = soup.find_all("td", attrs={"style": 'color: Green'}, string="Active")
    expired = soup.find_all("td", attrs={"style": 'color: Red'}, string="Expired")

    captcha_sleep_incr = 30
    if len(is_capcha) != 0:
        if iteration > max_iterations:
            print(f"Stopping after {iteration} iterations")
            return active_warranties
        print(f"Got captcha, try #{iteration}")
        sleep(iteration * captcha_sleep_incr)
        iteration += 1
        return get_warranty_HTML(serials, iteration=iteration)

    for td in active:
        serial = td.parent.parent.parent.parent.get('id').split("_")[2]

        warranty = {
            "service_type" : td.previous_sibling.previous_sibling.previous_sibling.get_text(strip=True),
            "start_date"   : td.previous_sibling.previous_sibling.string,
            "end_date"     : td.previous_sibling.string
        }
        if serial not in active_warranties:
            active_warranties[serial] = [warranty, ]
        else:
            active_warranties[serial].append(warranty)

    for td in expired:
        serial = td.parent.parent.parent.parent.get('id').split("_")[2]
        warranty = {
            "service_type" : td.previous_sibling.previous_sibling.previous_sibling.get_text(strip=True),
            "start_date"   : td.previous_sibling.previous_sibling.string,
            "end_date"     : td.previous_sibling.string
        }
        # active_warranties.append(warranty)
        if serial not in active_warranties:
            active_warranties[serial] = [warranty, ]
        else:
            active_warranties[serial].append(warranty)

    return active_warranties


def lookup_warranties(serials):
    """Gets warranties status from a list of serial numbers

    Parameters
    ----------
    serial : list
        list of serial numbers, as strings

    Returns
    -------
    list
        list of dicts containing the warranty info
    """

    systems = {}
    warranties = get_warranty_HTML(serials)
    # print(warranties)
    # for i, serial in enumerate(warranties):
    #     systems[serial] = warranties[serial]

    return warranties


if __name__ == "__main__":
    import json
    parser = argparse.ArgumentParser(usage="Small tool to retrieve HPE harware warranty status, using the serial number")
    parser.add_argument("serial", type=str, help="serial number of the HPE hardware", nargs="+")
    # parser.add_argument("--model", type=str, help="model number of HPE harware")
    args = parser.parse_args()

    systems = lookup_warranties(args.serial)
    print(json.dumps(systems))
