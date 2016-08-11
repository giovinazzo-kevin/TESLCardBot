import requests
import threading
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
    return re.sub(r'[\s_\-"\',;\{\}]', '', card).lower()


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


def get_praw():
    r = praw.Reddit('TES:L Card Fetcher by /u/{}.'.format(BOT_AUTHOR))
    r.login(username=os.environ['REDDIT_USERNAME'], password=os.environ['REDDIT_PASSWORD'], disable_warning=True)
    return r


def monitor_submissions():
    r = get_praw()
    for s in praw.helpers.submission_stream(r, TEST_SUBREDDIT if TEST_MODE else TARGET_SUBREDDIT):
        cards = find_card_mentions(s.selftext)
        if len(cards) > 0 and not s.saved:
            try:
                print('Commenting in {} about the following cards: {}'.format(s.title, cards))
                response = build_response(cards)
                s.add_comment(response)
                s.save()
                print('Done commenting and saved thread. ({})'.format(s.id))
            except:
                print('There was an error while trying to comment in: {}.'.format(s.id))
    print('Submission stream exhausted!!')


def monitor_comments():
    r = get_praw()
    for c in praw.helpers.comment_stream(r, TEST_SUBREDDIT if TEST_MODE else TARGET_SUBREDDIT):
        cards = find_card_mentions(c.body)
        if len(cards) > 0 and not c.saved and c.author != os.environ['REDDIT_USERNAME']:
            try:
                print('Replying to {} about the following cards: {}'.format(c.author, cards))
                response = build_response(cards)
                c.reply(response)
                c.save()
                print('Done replying and saved comment. ({})'.format(c.id))
            except:
                print('There was an error while trying to reply to: {}.'.format(c.id))
    print('Comment stream exhausted!!')


if __name__ == '__main__':
    print('TESLCardBot started! ({} MODE)'.format('PRODUCTION' if not TEST_MODE else 'DEVELOPMENT'))

    submissions_thread = threading.Thread(target=monitor_submissions)
    comments_thread = threading.Thread(target=monitor_comments)

    # submissions_thread.start()
    # print('Started monitoring submissions.')
    comments_thread.start()
    print('Started monitoring comments.')

    submissions_thread.join()
    comments_thread.join()
