import unittest
from teslcardbot.bot import TESLCardBot, Card


class TestParsingFunctions(unittest.TestCase):

    def setUp(self):
        self.bot = TESLCardBot(author='TestParsingFunctions', target_sub='TESLCardBotTesting')

    def test_find_card_mentions(self):
        # Make sure the basic functioning works
        self.assertEqual(TESLCardBot.find_card_mentions('{{Test}}'), ['Test'])
        self.assertEqual(TESLCardBot.find_card_mentions('{{Test}} {{Blood Dragon}}'), ['Test', 'Blood Dragon'])
        # Make sure the repetition avoidance works
        self.assertEqual(TESLCardBot.find_card_mentions('{{Test}} {{Blood Dragon}} ' * 4), ['Test', 'Blood Dragon'])

    def test_escape_card_name(self):
        self.assertEqual(Card._escape_name('Blood Dragon'), 'blooddragon')
        self.assertEqual(Card._escape_name('Bl-ood, _-"\' Drag;on'), 'blooddragon')
        self.assertEqual(Card._escape_name('{{{HOHO}}}}}'), 'hoho')

    def test_get_info(self):
        Card.preload_card_data()
        self.assertEqual(str(Card.get_info('tyr')), '[📖](https://www.reddit.com/message/compose/?'
                                                    'subject=Prophecy%2C%20Breakthrough%2C%20Guard) '
                                                    '[📷](http://www.legends-decks.com/img_cards/tyr.png) Tyr '
                                                    '| Creature | 4 - 5/4 | Prophecy, Breakthrough, Guard '
                                                    '| Strength/Willpower | Legendary')

        self.assertEqual(str(Card.get_info('lesser ward')), '[📖](https://www.reddit.com/message/compose/?'
                                                            'subject=Give%20a%20creature%20a%20Ward.) '
                                                            '[📷](http://www.legends-decks.com/img_cards/'
                                                            'lesserward.png) Lesser Ward | Action | 0 | None | '
                                                            'Intelligence | Common')

    def test_extract_keywords(self):
        self.assertEqual(Card._extract_keywords('Charge'),['Charge'])
        self.assertEqual(Card._extract_keywords('Charge, Pilfer'),['Charge', 'Pilfer'])
        self.assertEqual(Card._extract_keywords('cHaRge. dRaIn'),['Charge', 'Drain'])
        self.assertEqual(Card._extract_keywords('Summon: Ayy lmao'),['Summon'])
        self.assertEqual(Card._extract_keywords('Charge. Last Gasp: rip 2016'),['Charge', 'Last Gasp'])
        self.assertEqual(Card._extract_keywords('Summon: Summon a minion with Guard.'),['Summon'])


if __name__ == '__main__':
    unittest.main()
