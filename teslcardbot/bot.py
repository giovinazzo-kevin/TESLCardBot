import requests
import random
import json
import praw
import re
import os


class Card:
    CARD_IMAGE_BASE_URL = 'http://www.legends-decks.com/img_cards/{}.png'
    JSON_DATA = []

    @staticmethod
    def preload_card_data(path='data/cards.json'):
        dir = os.path.dirname(__file__)
        filename = os.path.join(dir, path)

        with open(filename) as f:
            Card.JSON_DATA = json.load(f)

    @staticmethod
    def _escape_name(card):
        return re.sub(r'[\s_\-"\',;{\}]', '', card).lower()

    @staticmethod
    def _img_exists(url):
        req = requests.get(url)
        return req.headers['content-type'] == 'image/png'

    @staticmethod
    def get_info(name):
        name = Card._escape_name(name)

        if name == 'teslcardbot':  # I wonder...
            return Card('TESLCardBot', 'https://imgs.xkcd.com/comics/tabletop_roleplaying.png',
                        type='Bot',
                        attribute='Python',
                        rarity='Legendary',
                        cost='∞', power='∞', health='∞')

        # If JSON_DATA hasn't been populated yet, try to do it now or fail miserably.
        if len(Card.JSON_DATA) <= 0:
            Card.preload_card_data()
            assert(len(Card.JSON_DATA) > 0)

        data = next((c for c in Card.JSON_DATA if Card._escape_name(c['name']) == name), None)
        if data is None:
            return None

        img_url = Card.CARD_IMAGE_BASE_URL.format(name)
        # Unlikely, but possible?
        if not Card._img_exists(img_url):
            img_url = 'http://imgur.com/1Lxy3DA'

        name = data['name']
        type = data['type']
        attribute = data['attribute']
        rarity = data['rarity']
        cost = int(data['cost'])
        power = 'N/A'
        health = 'N/A'
        if type == 'Creature':
            power = int(data['attack'])
            health = int(data['health'])

        return Card(name=name,
                    img_url=img_url,
                    type=type,
                    attribute=attribute,
                    rarity=rarity,
                    cost=cost,
                    power=power,
                    health=health)

    def __init__(self, name, img_url, type='Creature', attribute='neutral',
                 rarity='Common', cost=0, power=0, health=0):
        self.name = name
        self.img_url = img_url
        self.type = type
        self.attribute = attribute
        self.rarity = rarity
        self.cost = cost
        self.power = power
        self.health = health

    def __str__(self):
        return '{name} [📷]({url}) | {type} | {mana} | {atk} | {hp} | {attr} | {rarity}'.format(
            attr=self.attribute,
            rarity=self.rarity,
            name=self.name,
            url=self.img_url,
            type=self.type,
            mana=self.cost,
            atk=self.power,
            hp=self.health
        )


class TESLCardBot:
    CARD_MENTION_REGEX = re.compile(r'\{\{((?:.*?)+)\}\}')

    @staticmethod
    def _remove_duplicates(seq):
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]

    @staticmethod
    def find_card_mentions(s):
        return TESLCardBot._remove_duplicates(TESLCardBot.CARD_MENTION_REGEX.findall(s))

    def _get_praw_instance(self):
        r = praw.Reddit('TES:L Card Fetcher by /u/{}.'.format(self.author))
        r.login(username=os.environ['REDDIT_USERNAME'], password=os.environ['REDDIT_PASSWORD'], disable_warning=True)
        return r

    def _process_submission(self, s):
        cards = TESLCardBot.find_card_mentions(s.selftext)
        if len(cards) > 0 and not s.saved:
            try:
                self.log('Commenting in {} about the following cards: {}'.format(s.title, cards))
                response = self.build_response(cards)
                s.add_comment(response)
                s.save()
                self.log('Done commenting and saved thread. ({})'.format(s.id))
            except:
                self.log('There was an error while trying to comment in: {}.'.format(s.id))
                raise

    def _process_comment(self, c):
        cards = TESLCardBot.find_card_mentions(c.body)
        if len(cards) > 0 and not c.saved and c.author != os.environ['REDDIT_USERNAME']:
            try:
                self.log('Replying to {} about the following cards: {}'.format(c.author, cards))
                response = self.build_response(cards)
                c.reply(response)
                c.save()
                self.log('Done replying and saved comment. ({})'.format(c.id))
            except:
                self.log('There was an error while trying to reply to: {}.'.format(c.id))
                raise

    # TODO: Make this template-able, maybe?
    def build_response(self, cards):
        response = 'Name | Type | Cost | Power | Health | Attribute | Rarity \n---|---|----|----|----|----|----\n'

        for name in cards:
            card = Card.get_info(name)
            if card is None:
                boolshit_values = ['None', 'Undefined', 'Null', 'False', '💩', '#ERR', '0']
                card = Card(name=name,
                            img_url='http://imgur.com/1Lxy3DA',
                            type='Typo',
                            attribute=random.choice(boolshit_values),
                            rarity=random.choice(boolshit_values),
                            cost=random.choice(boolshit_values),
                            power=random.choice(boolshit_values),
                            health=random.choice(boolshit_values))
            response += '{}\n'.format(str(card))

        response += '\n&nbsp;\n\n^(_I am a bot, and this action was performed automagically._)' \
                    '\n\n[Source Code](https://github.com/G3Kappa/TESLCardBot/) ' \
                    '| [Send PM](https://www.reddit.com/message/compose/?to={})'.format(self.author)
        return response

    def log(self, msg):
        print('TESLCardBot # {}'.format(msg))

    def start(self, batch_limit=10, buffer_size=1000):
        r = None
        try:
            r = self._get_praw_instance()
        except praw.errors.HTTPException:
            self.log('Reddit seems to be down! Aborting.')
            return

        already_done = []
        subreddit = r.get_subreddit(self.target_sub)
        while True:
            new_submissions = [s for s in subreddit.get_new(limit=batch_limit) if s.id not in already_done]
            for s in new_submissions:
                self._process_submission(s)
                # The bot will also save submissions it replies to to prevent double-posting.
                already_done.append(s.id)
            new_comments = [c for c in r.get_comments(subreddit) if c.id not in already_done]
            for c in new_comments:
                self._process_comment(c)
                # The bot will also save comments it replies to to prevent double-posting.
                already_done.append(c.id)

            # If we're using too much memory, remove the bottom elements
            if len(already_done) >= buffer_size:
                already_done = already_done[batch_limit:]

    def __init__(self, author='Anonymous', target_sub='all'):
        self.author = author
        self.target_sub = target_sub
