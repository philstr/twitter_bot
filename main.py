import datetime
import os
import time
from twitter import OAuth, Twitter

def print_with_timestamp(s):
    datetime_string = str(datetime.datetime.now())
    print(datetime_string + "  " + s)

def load_credentials(path):
    credentials = {}
    with open(path, 'r') as fp:
        for line in fp:
            if "=" in line:
                stripped = line.rstrip()
                credentials[stripped.split("=")[0]] = stripped.split("=")[1]
    return credentials

def get_twitter_client(credentials):
    return Twitter(auth=OAuth(credentials["ACCESS_TOKEN"], credentials["ACCESS_TOKEN_SECRET"], credentials["API_KEY"], credentials["API_SECRET_KEY"]))

def tweet(client, tweet):
    client.statuses.update(status=tweet)

def seems_tweetable(contents):
    return len(contents) <= 280

def get_next_tweet():
    tweet_dir = "./new_tweets/" 
    sorted_tweet_files = sorted([(file, os.stat(tweet_dir+file).st_mtime) for file in os.listdir(tweet_dir)], key=lambda x: x[1])
    for tweet_file in sorted_tweet_files:
        if "ignore" in tweet_file[0]:
            continue
        filepath = tweet_dir+tweet_file[0]
        with open(filepath, 'r') as fp:
            contents = fp.read()
            if not seems_tweetable(contents):
                print_with_timestamp('Skipping tweet {0} as it doesn\'t seem tweetable.'.format(filepath))
                continue
            os.remove(filepath)
            return [contents, True]
    return ["", False]

if __name__ == '__main__':
    client = get_twitter_client(load_credentials("./API_INFO"))
    print_with_timestamp("Waking up!")
    contents, success = get_next_tweet()
    if success:
        print_with_timestamp("Tweeting: " + contents)
        tweet(client, contents)
    else:
        print_with_timestamp("Could not get next tweet.")