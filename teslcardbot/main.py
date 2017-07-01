from teslcardbot.bot import TESLCardBot
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='The Elder Scrolls: Legends bot for Reddit.')
    # No default value to prevent accidental mayhem
    parser.add_argument('-s', '--target_sub', required=True, help='What subreddit will this instance monitor?')

    args = parser.parse_args()

    print('TESLCardBot started! (/r/{})'.format(args.target_sub))
    bot = TESLCardBot(author='G3Kappa', target_sub=args.target_sub)
    bot.start(batch_limit=10, buffer_size=1000)
    print('TESLCardBot stopped running.')