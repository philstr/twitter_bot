from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
import threading

# Would be cool to refactor this to maybe spread the code across multiple files (for example, one that scrapes, one that parses, or something like that)

TEST_LOCATION_CODE = "boston"
TEST_CATEGORY_CODE = "bia"
TEST_QUERY = "tv"
TEST_ZIP_CODE = "02139"
TEST_DISTANCE = "1"


class Result:
    def __init__(self, title, datetime, price, location, url, key):
        self.title = title
        self.datetime = datetime
        self.price = price
        self.location = location
        self.url = url
        self.key = key

    def __str__(self):
        return "Datetime: {0}  Price: {1}  Title: {2}".format(self.datetime, self.price, self.title)


class SeenSet:
    # Basic wrapper of a set to allow threads to track which results have been seen

    def __init__(self):
        self.seen_set = set()
        self.lock = threading.Lock()

    def add(self, result):
        self.seen_set.add(result.key)

    def contains(self, result):
        return result.key in self.seen_set

    def get_lock(self):
        return self.lock


def get_ads(location_code, category_code, query=None, postal=None, distance=None):
    query_string = "?query="+query.replace(" ", "+") if query is not None else ""
    url_base = "https://" + location_code + \
        ".craigslist.org/search/" + category_code + query_string
    return get_result_list(url_base)


def get_ads_sorted_by_date(location_code, category_code, query=None):
    results = get_ads(location_code, category_code, query)
    results.sort(key=lambda x: x.datetime)
    return results


def get_ads_sorted_by_price(location_code, category_code, query=None):
    results = get_ads(location_code, category_code, query)
    results.sort(key=lambda x: x.price)
    return results


def get_result_list(url_base):
    top_soup = get_soup(url_base)
    rangeTo = top_soup.find("span", class_="rangeTo")
    if rangeTo == None:
        return []  # Return emtpy list if no results found
    highest_first_page_index = int(rangeTo.text)
    total_count = int(top_soup.find("span", class_="totalcount").text)
    number_of_pages = get_number_of_pages(
        highest_first_page_index, total_count)
    # Not completely sure this is a safe assumption
    url_divider = "&" if "?" in url_base else "?"
    result_list = []
    seen_set = SeenSet()
    threads = []

    for page in range(number_of_pages):
        s = page*highest_first_page_index
        url = url_base + url_divider + "s=" + str(s)
        thread = threading.Thread(
            target=thread_action, args=(url, result_list, seen_set))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

    return result_list


def thread_action(url, result_list, seen_set):
    soup = get_soup(url)
    for entry in soup.find_all("li", class_="result-row"):
        result = get_result_from_entry(entry)
        if result is not None:
            seen_set.get_lock().acquire()
            if not seen_set.contains(result):
                result_list.append(result)
                seen_set.add(result)
            seen_set.get_lock().release()


def get_result_from_entry(entry):
    # this seems like really bad practice just silencing exceptions here, should handle them more gracefully, maybe at the getter level
    #try:
    title = get_title(entry)
    datetime = get_datetime(entry)
    price = get_price(entry)
    location = get_location(entry)
    url = get_url(entry)
    key = toSetKey(title, price)
    return Result(title, datetime, price, location, url, key)
    # except:
    #    return None


def get_title(entry):
    result_title = entry.find(class_="result-title")
    return result_title.text if result_title is not None else ""


def get_datetime(entry):
    return entry.find(class_="result-date")["datetime"]


def get_price(entry):
    price = entry.find(class_="result-price")
    if price is None:
        return -1
    return int(price.text[1:].replace(",", ""))


def get_location(entry):
    neighborhood = entry.find(class_="result-hood")
    if neighborhood is not None:
        return neighborhood.text.strip()
    nearby = entry.find(class_="nearby")
    if nearby is not None:
        return nearby.text.strip()
    return ""


def get_url(entry):
    result_title = entry.find(class_="result-title")
    if result_title is None:
        return ""
    return result_title["href"]


def toSetKey(title, price):
    return title + str(price)


def get_number_of_pages(highest_first_page_index, total_count):
    if highest_first_page_index == 0:
        return 0
    extra = 1 if total_count % highest_first_page_index > 0 else 0
    return int(total_count/highest_first_page_index + extra)


def get_soup(url):
    req = Request(url, headers={'User-Agent': "Magic Browser"})
    html = urlopen(req).read()
    soup = BeautifulSoup(html, "html.parser")
    return soup


if __name__ == "__main__":
    results = get_ads(TEST_LOCATION_CODE, TEST_CATEGORY_CODE)
    for result in results:
        print(result.url)
