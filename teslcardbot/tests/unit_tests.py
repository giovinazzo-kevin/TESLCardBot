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
        self.assertEqual(str(Card.get_info('tyr')), 'strength/willpower | Legendary '
                                               '| Tyr [📷](http://www.legends-decks.com/img_cards/tyr.png) '
                                               '| Creature | 4 | 5 | 4')


if __name__ == '__main__':
    unittest.main()
