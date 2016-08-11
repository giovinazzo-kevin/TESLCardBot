import requests
import itertools
import praw
import re
import os


TEST_MODE = True

BOT_AUTHOR = 'G3Kappa'
TARGET_SUBREDDIT = 'elderscrollslegends'
TEST_SUBREDDIT = 'TESLCardBotTesting'
CARD_MENTION_REGEX = re.compile(r'\{\{((?:.*?)+)\}\}')
CARD_DATABASE_URL = 'http://www.legends-decks.com/img_cards/{}.png'


def _remove_duplicates(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def find_card_mentions(s):
    return _remove_duplicates(CARD_MENTION_REGEX.findall(s))


def escape_card_name(card):
    return re.sub(r'[\s_\-"\',;]', '', card).lower()


def build_response(cards):
    response = 'Here are the cards you mentioned: \n\n'
    for card in cards:
        card_name = escape_card_name(card)

        url = CARD_DATABASE_URL.format(card_name)
        # Check if the given card is a valid card
        r = requests.get(url)
        if r.headers['content-type'] == 'image/png':
            response += '- [{}]({})\n\n'.format(card.title(), url)
        else:
            response += '- {}: This card does not seem to exist. Possible typo?\n\n'.format(card)
    response += '&nbsp;\n\n___\n^(_I am a bot, and this action was performed automatically. ' \
                'For information or to submit a bug report, please contact /u/​G3Kappa._)'
    response += '\n\n[Source Code](https://github.com/G3Kappa/TESLCardBot/) ' \
                '| [Send PM](https://www.reddit.com/message/compose/?to={})'.format(BOT_AUTHOR)
    return response


def reply_to_comment(c, cards):
    print('Replying to {} about the following cards: {}'.format(c.author, cards))
    response = build_response(cards)
    c.reply(response)


def reply_to_submission(s, cards):
    print('Replying in {} about the following cards: {}'.format(s.title, cards))
    response = build_response(cards)
    s.add_comment(response)


if __name__ == '__main__':
    r = praw.Reddit('TES:L Card Fetcher by /u/{}.'.format(BOT_AUTHOR))
    r.login(username=os.environ['REDDIT_USERNAME'], password=os.environ['REDDIT_PASSWORD'], disable_warning=True)
    print('TESLCardBot started! ({} MODE)'.format('PRODUCTION' if not TEST_MODE else 'DEVELOPMENT'))

    if not TEST_MODE:
        streams = itertools.chain(praw.helpers.comment_stream(r, TARGET_SUBREDDIT),
                                  praw.helpers.submission_stream(r, TARGET_SUBREDDIT))
    else:
        streams = itertools.chain(praw.helpers.comment_stream(r, TEST_SUBREDDIT),
                                  praw.helpers.submission_stream(r, TEST_SUBREDDIT))

    for s in streams:
        cards = []
        is_submission = hasattr(s, 'selftext')
        if is_submission:
            print(s.selftext)
            cards = find_card_mentions(s.selftext)
        else:
            cards = find_card_mentions(s.body)

        if len(cards) > 0 and not s.saved:
            try:
                if is_submission:
                    reply_to_submission(s, cards)
                else:
                    reply_to_comment(s, cards)
                s.save()  # Exploiting Reddit's servers has never been this easy!
                print('Done replying and saved post. ({})'.format(s.id))
            except:
                print('There was an error while trying to reply to: {}.'.format(s.id))