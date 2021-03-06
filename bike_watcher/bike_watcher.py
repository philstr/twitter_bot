import craigslist
import csv
import datetime
import time
import uuid

QUERIES_FILE = "./QUERIES"
SEEN_LISTINGS_SIZE = 100
TWEET_FILE_PATH = "../main/new_tweets/"

def print_with_timestamp(s):
    datetime_string = str(datetime.datetime.now())
    print(datetime_string + "  " + s)

def get_listings():
    listings = []
    with open(QUERIES_FILE, newline='') as fp:
        reader = csv.reader(fp)
        for row in reader:
            if len(row) < 3:
                continue
            # Lines in the queries csv file should be of the format
            # <location>,<category code>,<search term>
            # e.g., boston,bip,nitto
            listings += craigslist.get_ads_sorted_by_date(row[0], row[1], row[2])
    return listings

def already_seen(listing, seen_listings):
    return listing.key in seen_listings

def submit_listing(listing, seen_listings):
    filepath = TWEET_FILE_PATH + "craigslist_" + str(uuid.uuid4())
    contents = build_tweet(listing)
    with open(filepath, 'w') as fp:
        fp.write(contents)

    # Since this might be run in a loop forever, enforce a max size on the list for now.
    seen_listings.insert(0, listing.key)
    if len(seen_listings) > SEEN_LISTINGS_SIZE:
        seen_listings.pop()
    
def build_tweet(listing):
    return "{0} - ${1}   {2}".format(listing.title, listing.price, listing.url)

if __name__ == '__main__':
    print_with_timestamp("Starting Bike Watcher program.")
    seen_listings = []
    while True:
        print_with_timestamp("waking up!")
        listings = get_listings()
        for listing in listings:
            if already_seen(listing, seen_listings):
                print_with_timestamp("Skipping listing [{0}], already seen.".format(listing.title))
                continue
            print_with_timestamp("Submitting listing [{0}].".format(listing.title))
            submit_listing(listing, seen_listings)

        # Sleep for an hour.
        time.sleep(3600)
