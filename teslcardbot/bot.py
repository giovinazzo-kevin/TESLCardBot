import requests
import urllib.parse
import random
import json
import praw
import re
import os


def remove_duplicates(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


class Card:
    CARD_IMAGE_BASE_URL = 'http://www.legends-decks.com/img_cards/{}.png'
    CARD_IMAGE_404_URL = 'http://imgur.com/1Lxy3DA'
    JSON_DATA = []
    KEYWORDS = ['Prophecy', 'Breakthrough', 'Guard', 'Regenerate', 'Charge', 'Ward', 'Shackle',
                'Lethal', 'Pilfer', 'Last Gasp', 'Summon', 'Drain']

    @staticmethod
    def get_random_card(name):
        boolshit_values = ['None', 'Undefined', 'Null', 'False', '💩', '#ERR', '0', '???', '!?']

        def rv(v=boolshit_values):
            if random.random() < 0.01:
                return 'help'  # Not really
            return random.choice(v)

        return Card(name=name,
                    img_url=Card.CARD_IMAGE_404_URL,
                    type='Typo',
                    attribute_1=rv(),
                    attribute_2=rv() if random.random() < 0.5 else '',
                    rarity=rv(),
                    cost=rv(),
                    power=rv(),
                    health=rv())

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
    def _extract_keywords(text):
        expr = re.compile(r'(\w+(?:\sGasp)?)', re.I)
        words = expr.findall(text)
        # Keywords are extracted until a non-keyword word is found
        keywords = []
        for word in words:
            word = word.title()
            if word in Card.KEYWORDS:
                keywords.append(word)
            else:
                break
        return remove_duplicates(keywords)

    @staticmethod
    def get_info(name):
        name = Card._escape_name(name)

        if name == 'teslcardbot':  # I wonder...
            return Card('TESLCardBot', 'https://imgs.xkcd.com/comics/tabletop_roleplaying.png',
                        type='Bot',
                        attribute_1='Python',
                        attribute_2='JSON',
                        rarity='Legendary',
                        text='If your have more health than your opponent, win the game.',
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
            img_url = Card.CARD_IMAGE_404_URL

        name = data['name']
        type = data['type']
        attr_1 = data['attribute_1']
        attr_2 = data['attribute_2']
        rarity = data['rarity']
        cost = int(data['cost'])
        text = data['text']
        power = ''
        health = ''
        if type == 'creature':
            power = int(data['attack'])
            health = int(data['health'])

        return Card(name=name,
                    img_url=img_url,
                    type=type,
                    attribute_1=attr_1,
                    attribute_2=attr_2,
                    rarity=rarity,
                    cost=cost,
                    power=power,
                    health=health,
                    text=text)

    def __init__(self, name, img_url, type='Creature', attribute_1='neutral',
                 attribute_2='', text='', rarity='Common', cost=0, power=0, health=0):
        self.name = name
        self.img_url = img_url
        self.type = type
        self.attributes = [attribute_1.title(), attribute_2.title()] if len(attribute_2) > 0 else [attribute_1.title()]
        self.rarity = rarity
        self.cost = cost
        self.power = power
        self.health = health
        self.text = text
        self.keywords = Card._extract_keywords(text)

    def __str__(self):
        template = '[📷]({url} "{text}") {name} ' \
                   '| {type} | {stats} | {keywords} | {attrs} | {rarity}'

        return template.format(
            attrs='/'.join(map(str, self.attributes)),
            rarity=self.rarity.title(),
            name=self.name,
            url=self.img_url,
            type=self.type.title(),
            mana=self.cost,
            stats='{} - {}/{}'.format(self.cost, self.power, self.health) if self.type == 'creature' else self.cost,
            keywords=', '.join(map(str, self.keywords)) + '' if len(self.keywords) > 0 else 'None',
            text=self.text if len(self.text) > 0 else 'This card\'s name isn\'t in the database. Possible typo?'
        )


class TESLCardBot:
    CARD_MENTION_REGEX = re.compile(r'\{\{((?:.*?)+)\}\}')

    @staticmethod
    def find_card_mentions(s):
        return remove_duplicates(TESLCardBot.CARD_MENTION_REGEX.findall(s))

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
        response = 'Name | Type | M&nbsp;-&nbsp;ATK/HP | Keywords | Attribute | ' \
                   'Rarity \n--|--|--|--|--|--|--\n'

        for name in cards:
            card = Card.get_info(name)
            if card is None:
                card = Card.get_random_card(name)
            response += '{}\n'.format(str(card))

        auto_word = random.choice(['automatically', 'automagically'])
        response += '\n&nbsp;\n\n_Did you know? Hover the camera emoji to read a card\'s text!_' \
                    '\n\n^(_I am a bot, and this action was performed {}. Made by user G3Kappa. ' \
                    'Special thanks to Jeremy at legends-decks._)' \
                    '\n\n[Source Code](https://github.com/G3Kappa/TESLCardBot/) ' \
                    '| [Send PM](https://www.reddit.com/message/compose/?to={})'.format(auto_word, self.author)
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
            try:
                new_submissions = [s for s in subreddit.get_new(limit=batch_limit) if s.id not in already_done]
                new_comments = [c for c in r.get_comments(subreddit) if c.id not in already_done]
            except praw.errors.HTTPException:
                self.log('Reddit seems to be down! Aborting.')
                return
            
            for s in new_submissions:
                self._process_submission(s)
                # The bot will also save submissions it replies to to prevent double-posting.
                already_done.append(s.id)
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
