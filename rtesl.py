import requests
import itertools
import praw
import re
import os


CARD_MENTION_REGEX = re.compile(r'\{\{((?:.*?)+)\}\}')
CARD_DATABASE_URL = 'http://www.legends-decks.com/img_cards/{}.png'


def find_card_mentions(s):
    return CARD_MENTION_REGEX.findall(s)


def build_response(cards):
    already_mentioned = []

    response = 'Here are the cards you mentioned: \n\n'
    for card in cards:
        card_name = re.sub(r'[\s_\-"\',;]', '', card).lower()
        if card_name in already_mentioned:
            continue
        already_mentioned.append(card_name)

        url = CARD_DATABASE_URL.format(card_name)
        # Check if the given card is a valid card
        r = requests.get(url)
        if r.headers['content-type'] == 'image/png':
            response += '- [{}]({})\n\n'.format(card, url)
        else:
            response += '- {}: This card does not seem to exist. Possible typo?\n\n'.format(card)
    response += '&nbsp;\n\n___\n^(_I am a bot, and this action was performed automatically. ' \
                'For information or to submit a bug report, please contact /u/​G3Kappa._)'
    response += '\n\n[Source Code](https://github.com/G3Kappa/TESLCardBot/) ' \
                '| [Send PM](https://www.reddit.com/message/compose/?to=G3Kappa)'
    return response


def reply_to(c, cards):
    print('Replying to {} about the following cards: {}'.format(c.author, cards))
    response = build_response(cards)
    c.reply(response)


if __name__ == '__main__':
    r = praw.Reddit('TES:L Card Fetcher by /u/G3Kappa. ')
    r.login(username=os.environ['REDDIT_USERNAME'], password=os.environ['REDDIT_PASSWORD'], disable_warning=True)
    print('TESLCardBot started!')

    streams = itertools.chain(praw.helpers.comment_stream(r, 'elderscrollslegends'),
              praw.helpers.submission_stream(r, 'elderscrollslegends'))

    for s in streams:
        cards = find_card_mentions(s.body)
        if len(cards) > 0 and not s.saved:
            try:
                reply_to(s, cards)
                s.save() # Exploiting Reddit's servers has never been this easy!
            except:
                print('There was an error while trying to reply to: {}.'.format(s.id))
            print('Done replying and saved post. ({})'.format(s.id))