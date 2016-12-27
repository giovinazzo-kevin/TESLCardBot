# TESLCardBot
TESLCardBot is a Reddit bot that fetches info about _The Elder Scrolls: Legends_ cards.

It defaults to /r/elderscrollslegends, but it can run on any subreddit. It is summoned by enclosing one or more cards' names in double brackets, like this: `{{Blood Dragon}}`. It will then reply with a table containing detailed information and a picture for each card.

The files _Procfile_ and _runtime.txt_ are required by [Heroku](https://dashboard.heroku.com/), the platform this bot runs on.

#Running Locally
Be sure to set your environment variables. On linux:
export REDDIT_USERNAME=<your_reddit_username>
export REDDIT_PASSWORD=<reddit_username_password>

Run with:
python teslcardbot/main.py --target_sub <subreddit_to_watch>

#Contributing
Feel free to contribute! Any pull request is welcome, just remember to add your name to *CONTRIBUTORS.md*.
