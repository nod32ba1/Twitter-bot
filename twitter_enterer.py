import tweepy
import utils
import random

CONFIG_FILENAME = "config.json"


class Enterer():
    # Get the language as argument in the constructor to know what language must be used to run
    def __init__(self, language, key):

        config = utils.load_configfile(CONFIG_FILENAME)
        credentials = config["credentials"][key]

        self.client = tweepy.Client(credentials[utils.BEARER_TOKEN], credentials[utils.CONSUMER_KEY],
                                    credentials[utils.CONSUMER_SECRET], credentials[utils.ACCESS_KEY], credentials[utils.ACCESS_SECRET], wait_on_rate_limit=True)
        
        self.banned_words = config[utils.BANNED_WORDS]
        self.banned_users = config[utils.BANNED_USERS]
        self.research = config[utils.RESEARCH]
        self.tag_sentences = config[utils.TAG_SENTENCES]
        self.tag_users = config[utils.TAG_USERS]
        self.eth_addr = config[utils.ETH_ADDR]
        self.sol_addr = config[utils.SOL_ADDR]

        self.language = language

    # Action to execute if the tweet is a contest -> follow, like, retweet, tag frieds, comment crypto wallet address

    def tweet_action(self, tweet):
        tweet_content = tweet.text.lower()
        tweet_content = utils.remove_emoji(tweet_content)

        self.client.retweet(tweet.id)
        self.client.like(tweet.id)
        self.client.follow(tweet.author_id)
        users_to_follow = self.get_users_mentioned(tweet)
        for user in users_to_follow:
            self.client.follow(user)
        self.tag_friend(tweet)

        # check if solana or ethereum adresse is required
        if (any(word in tweet_content for word in ["drop", "comment", "put", "reply"])) and (any(w in tweet_content for w in ["address", "wallet", "$eth", "$sol","eth","sol"])):

            if(any(w in tweet_content for w in ["sol", "solana"])):
                reply = random.choice(["SOL address : {}".format(self.sol_addr)," sol : {}".format(self.sol_addr), self.sol_addr ])
            else:
                reply = random.choice(["ETH address : {}".format(self.eth_addr)," eth : {}".format(self.eth_addr), self.eth_addr ])
            self.client.create_tweet(text=reply, in_reply_to_tweet_id=tweet.id)

    # check if one the banned words is in the tweet
    def check_contains_bannedwords(self, tweet):
        contain = False
        for word in self.banned_words:
            if word in tweet.lower():
                contain = True
                break
        return contain

    # Return a list of the id of the users mentionned in the tweet + the id of the original poster
    def tag_friend(self, tweet):
        tweet_content = tweet.text.lower()
        tweet_content = utils.remove_emoji(tweet_content)
        nb_of_friends = 0
        nb_of_friends_found = False

        if (("tag" in tweet_content)):
            # Check how many people must be tagged
            words = tweet_content.split()
            index = words.index("tag")
            words = words[index:]
            for word in words:
                if word.isdigit():
                    nb_of_friends = int(word)
                    nb_of_friends_found = True
                    break
            #If no number of friends found or if the number of friends does not make sense
            if (nb_of_friends_found == False) or (nb_of_friends > 5):
                nb_of_friends = 2
            reply = random.choice(self.tag_sentences[self.language])
            friends = random.sample(self.tag_users, nb_of_friends)
            for friend in friends:
                reply += " @"+friend
            self.client.create_tweet(text=reply, in_reply_to_tweet_id=tweet.id)

    # return a list of every user mentionned in the tweet + the original poster
    def get_users_mentioned(self, tweet):
        id_users = []
        if (tweet.entities != None and "mentions" in tweet.entities):
            users = tweet.entities["mentions"]
            for u in users:
                id_users.append(u["id"])
        return id_users

    # check contain certain words to know if it's a contest
    def check_is_contest(self, tweet):
        is_contest = False
        if (any(word in tweet.lower() for word in ["rt", "retweet"])) and ("follow" in tweet.lower()) and ("like" in tweet.lower()):
            is_contest = True
        return is_contest

    def run(self):
        # build query depending on language and exlcude retweet and reply
        research = self.research[self.language]
        research += " -is:retweet -is:reply"

        response = self.client.search_recent_tweets(
            query=research, max_results=100, tweet_fields=["entities", "created_at"], user_fields=['profile_image_url'], expansions=['author_id'])

        for tweet in response.data:
            is_contest = self.check_is_contest(tweet.text)
            contains_bannedword = self.check_contains_bannedwords(tweet.text)
            if (is_contest and not contains_bannedword):
                print(tweet)
                # self.tweet_action(tweet)
                # Handle potential error coming from twitter serves being over capacity
                try:
                    self.tweet_action(tweet)
                except tweepy.TweepyException as e:
                    print("Error code : {}".format(e.__dict__))
                    continue
