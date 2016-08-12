import unittest
from teslcardbot.bot import TESLCardBot


class TestParsingFunctions(unittest.TestCase):

    # def setUp(self):
    #    self.bot = TESLCardBot(author='TestParsingFunctions', target_sub='TESLCardBotTesting')

    def test_find_card_mentions(self):
        # Make sure the basic functioning works
        self.assertEqual(TESLCardBot.find_card_mentions('{{Test}}'), ['Test'])
        self.assertEqual(TESLCardBot.find_card_mentions('{{Test}} {{Blood Dragon}}'), ['Test', 'Blood Dragon'])
        # Make sure the repetition avoidance works
        self.assertEqual(TESLCardBot.find_card_mentions('{{Test}} {{Blood Dragon}} ' * 4), ['Test', 'Blood Dragon'])

    def test_escape_card_name(self):
        self.assertEqual(TESLCardBot.escape_card_name('Blood Dragon'), 'blooddragon')
        self.assertEqual(TESLCardBot.escape_card_name('Bl-ood, _-"\' Drag;on'), 'blooddragon')
        self.assertEqual(TESLCardBot.escape_card_name('{{{HOHO}}}}}'), 'hoho')


if __name__ == '__main__':
    unittest.main()
