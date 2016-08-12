import requests
import praw
import re
import os


class TESLCardBot:
    CARD_MENTION_REGEX = re.compile(r'\{\{((?:.*?)+)\}\}')
    CARD_DATABASE_URL = 'http://www.legends-decks.com/img_cards/{}.png'

    @staticmethod
    def _remove_duplicates(seq):
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]

    @staticmethod
    def find_card_mentions(s):
        return TESLCardBot._remove_duplicates(TESLCardBot.CARD_MENTION_REGEX.findall(s))

    @staticmethod
    def escape_card_name(card):
        return re.sub(r'[\s_\-"\',;\{\}]', '', card).lower()

    @staticmethod
    def get_card_info(card):
        return TESLCardBot.CARD_DATABASE_URL.format(card)

    @staticmethod
    def is_valid_info(card_info):
        req = requests.get(card_info)
        return req.headers['content-type'] == 'image/png'

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
                
    # TODO: Make this template-able, maybe?
    def build_response(self, cards):
        response = 'Here are the cards you mentioned: \n\n'
        for card in cards:
            card = card.title()
            card_name = TESLCardBot.escape_card_name(card)
            if len(card_name) <= 0:
                continue

            info = TESLCardBot.get_card_info(card_name)
            # Check if the given card is a valid card
            if TESLCardBot.is_valid_info(info):
                response += '- [{}]({})\n\n'.format(card, info)
            else:
                response += '- {}: This card does not seem to exist. Possible typo?\n\n'.format(card)
        response += '&nbsp;\n\n___\n^(_I am a bot, and this action was performed automatically. ' \
                    'For information or to submit a bug report, please contact /u/​G3Kappa._)'
        response += '\n\n[Source Code](https://github.com/G3Kappa/TESLCardBot/) ' \
                    '| [Send PM](https://www.reddit.com/message/compose/?to={})'.format(self.author)
        return response

    def log(self, msg):
        print('TESLCardBot# {}'.format(msg))

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
