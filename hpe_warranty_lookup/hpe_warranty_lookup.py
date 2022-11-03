import sys
import urllib.parse
import requests
from bs4 import BeautifulSoup
import argparse
from time import sleep
import re
from datetime import datetime


def get_first_and_last_date(entries):
    """Read a dictionary with multiple warranties, and pick up the earliest and latest date

    Expected format for entries:
        [{"CZXXXXXXXX": [{"service_type": "HPE Hardware Maintenance Onsite Support", "start_date": "Sep 1, 2020", "end_date": "Aug 31, 2021"}, 
         {"service_type": "HPE Collaborative Remote Support", "start_date": "Sep 1, 2020", "end_date": "Aug 31, 2021"}]}]

    Parameters
    ----------
    entries : dict
        dict of lists, each entry is a system indexed by serial number

    Returns
    ----------
    early_date, last_date: str
    """
    start_date = datetime.strptime("9999-12-31", "%Y-%m-%d")
    end_date = datetime.strptime("1970-01-11", "%Y-%m-%d")
    for entry in entries:
        t_start = datetime.strptime(entry["start_date"], "%b %d, %Y")
        t_end = datetime.strptime(entry["end_date"], "%b %d, %Y")
        if t_start < start_date:
            start_date = t_start
        if t_end > end_date:
            end_date = t_end
    
    return datetime.strftime(start_date, "%Y-%m-%d"), datetime.strftime(end_date, "%Y-%m-%d")


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

    wrong_serials_raw = soup.find_all(text=re.compile("This product cannot be identified by serial number alone."))
    if len(wrong_serials_raw) != 0:
        wrong_serials = []
        for res in wrong_serials_raw:
            serial = res.find_parent("tr").previous_sibling.previous_sibling.find_all("td")[1].input.get("value")
            wrong_serials.append(serial)
            serials.remove(serial)
        print(f"The following serials are wrong / incomplete: {wrong_serials}")
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


def lookup_warranties(serials, verbose=False):
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

    if verbose:
        return warranties
    else:
        output = {}
        for serial in warranties:
            start_date, end_date = get_first_and_last_date(warranties[serial])
            output[serial] = [start_date, end_date]
        return output

def main():
    import json
    parser = argparse.ArgumentParser(usage="Small tool to retrieve HPE harware warranty status, using the serial number")
    parser.add_argument("serial", type=str, help="serial number of the HPE hardware", nargs="+")
    parser.add_argument('--verbose', '-v', action="store_true", dest='verbose', default=False,
                        required=False, help="Verbose")  
    # parser.add_argument("--model", type=str, help="model number of HPE harware")
    args = parser.parse_args()

    systems = lookup_warranties(args.serial, verbose=args.verbose)
    print(json.dumps(systems))

if __name__ == "__main__":
    main()