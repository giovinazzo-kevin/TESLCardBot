import unittest
import rtesl


class TestParsingFunctions(unittest.TestCase):

    def test_find_card_mentions(self):
        # Make sure the basic functioning works
        self.assertEqual(rtesl.find_card_mentions('{{Test}}'), ['Test'])
        self.assertEqual(rtesl.find_card_mentions('{{Test}} {{Blood Dragon}}'), ['Test', 'Blood Dragon'])
        # Make sure the repetition avoidance works
        self.assertEqual(rtesl.find_card_mentions('{{Test}} {{Blood Dragon}} ' * 4), ['Test', 'Blood Dragon'])

    def test_normalize_card_name(self):
        self.assertEqual(rtesl.normalize_card_name('Blood Dragon'), 'blooddragon')
        self.assertEqual(rtesl.normalize_card_name('Blood, ;_--"\'Dragon'), 'blooddragon')

if __name__ == '__main__':
    unittest.main()