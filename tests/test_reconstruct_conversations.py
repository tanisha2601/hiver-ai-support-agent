"""
Unit tests for conversation reconstruction and relationship analysis.
Verifies graph traversal, parent linking, cycle handling, and metric computations.
"""

import unittest
import pandas as pd
import numpy as np
from src.data.reconstruct_conversations import (
    reconstruct_conversation_trees,
    compute_brand_metrics,
    parse_twitter_dates,
    extract_conversation_samples
)

class TestConversationReconstruction(unittest.TestCase):

    def setUp(self):
        """Build a synthetic dataset fixture with known conversation structures."""
        self.sample_data = pd.DataFrame([
            # Conversation 1: 3-turn thread (Cust -> AppleSupport -> Cust)
            {
                'tweet_id': 101,
                'author_id': 'user_A',
                'inbound': True,
                'created_at': 'Tue Oct 31 10:00:00 +0000 2017',
                'text': 'My iPhone battery dies at 20%',
                'response_tweet_id': '102',
                'in_response_to_tweet_id': np.nan
            },
            {
                'tweet_id': 102,
                'author_id': 'AppleSupport',
                'inbound': False,
                'created_at': 'Tue Oct 31 10:05:00 +0000 2017',
                'text': 'We would like to help. What iOS version are you running?',
                'response_tweet_id': '103',
                'in_response_to_tweet_id': 101.0
            },
            {
                'tweet_id': 103,
                'author_id': 'user_A',
                'inbound': True,
                'created_at': 'Tue Oct 31 10:10:00 +0000 2017',
                'text': 'I am running iOS 11.1 on iPhone 7',
                'response_tweet_id': np.nan,
                'in_response_to_tweet_id': 102.0
            },

            # Conversation 2: 2-turn thread (Cust -> SpotifyCares)
            {
                'tweet_id': 201,
                'author_id': 'user_B',
                'inbound': True,
                'created_at': 'Tue Oct 31 11:00:00 +0000 2017',
                'text': 'Cannot log into my Spotify premium family account',
                'response_tweet_id': '202',
                'in_response_to_tweet_id': np.nan
            },
            {
                'tweet_id': 202,
                'author_id': 'SpotifyCares',
                'inbound': False,
                'created_at': 'Tue Oct 31 11:15:00 +0000 2017',
                'text': 'Hey there! Send us a DM with your account email.',
                'response_tweet_id': np.nan,
                'in_response_to_tweet_id': 201.0
            },

            # Conversation 3: Unanswered Customer Tweet
            {
                'tweet_id': 301,
                'author_id': 'user_C',
                'inbound': True,
                'created_at': 'Tue Oct 31 12:00:00 +0000 2017',
                'text': 'Is AppleSupport down today?',
                'response_tweet_id': np.nan,
                'in_response_to_tweet_id': np.nan
            },

            # Edge Case 1: Orphan Tweet with parent not in dataset
            {
                'tweet_id': 401,
                'author_id': 'AppleSupport',
                'inbound': False,
                'created_at': 'Tue Oct 31 13:00:00 +0000 2017',
                'text': 'DM us your serial number.',
                'response_tweet_id': np.nan,
                'in_response_to_tweet_id': 99999.0  # missing parent ID
            },

            # Edge Case 2: Self-referential / cyclic parent loop
            {
                'tweet_id': 501,
                'author_id': 'user_D',
                'inbound': True,
                'created_at': 'Tue Oct 31 14:00:00 +0000 2017',
                'text': 'Loop test tweet A',
                'response_tweet_id': '502',
                'in_response_to_tweet_id': 502.0
            },
            {
                'tweet_id': 502,
                'author_id': 'user_D',
                'inbound': True,
                'created_at': 'Tue Oct 31 14:05:00 +0000 2017',
                'text': 'Loop test tweet B',
                'response_tweet_id': '501',
                'in_response_to_tweet_id': 501.0
            }
        ])

    def test_reconstruct_conversation_trees(self):
        """Test that conversation roots and groups are formed accurately."""
        tweet_to_root, conv_to_tweets = reconstruct_conversation_trees(self.sample_data)

        # In conversation 1, all 3 tweets should resolve to root 101
        self.assertEqual(tweet_to_root[101], 101)
        self.assertEqual(tweet_to_root[102], 101)
        self.assertEqual(tweet_to_root[103], 101)
        self.assertEqual(len(conv_to_tweets[101]), 3)

        # In conversation 2, tweets 201 & 202 should resolve to root 201
        self.assertEqual(tweet_to_root[201], 201)
        self.assertEqual(tweet_to_root[202], 201)
        self.assertEqual(len(conv_to_tweets[201]), 2)

        # Single unanswered tweet resolves to itself
        self.assertEqual(tweet_to_root[301], 301)
        self.assertEqual(len(conv_to_tweets[301]), 1)

        # Orphan tweet with missing parent becomes its own root
        self.assertEqual(tweet_to_root[401], 401)
        self.assertEqual(len(conv_to_tweets[401]), 1)

    def test_cycle_resilience(self):
        """Test that cyclic parent links do not cause infinite loops or crashes."""
        tweet_to_root, conv_to_tweets = reconstruct_conversation_trees(self.sample_data)
        # Should terminate cleanly and assign a valid root
        self.assertIn(501, tweet_to_root)
        self.assertIn(502, tweet_to_root)

    def test_date_parsing(self):
        """Test that Twitter date format parses correctly into Timestamp."""
        dates = parse_twitter_dates(self.sample_data['created_at'])
        self.assertEqual(dates.isna().sum(), 0)
        self.assertEqual(dates.iloc[0].year, 2017)
        self.assertEqual(dates.iloc[0].month, 10)
        self.assertEqual(dates.iloc[0].day, 31)

    def test_brand_metrics_calculation(self):
        """Test brand metrics calculation on synthetic dataset."""
        metrics_df = compute_brand_metrics(self.sample_data, ['AppleSupport', 'SpotifyCares'])
        
        # AppleSupport row verification
        apple_row = metrics_df[metrics_df['Brand'] == 'AppleSupport'].iloc[0]
        self.assertEqual(apple_row['Total Messages (Brand)'], 2)  # tweet 102 & 401
        self.assertEqual(apple_row['Customer->Brand Links'], 1)   # tweet 102 replying to 101
        self.assertEqual(apple_row['Brand->Customer Links'], 1)   # tweet 103 replying to 102
        self.assertEqual(apple_row['Conversations With Both Sides'], 1) # root 101
        self.assertEqual(apple_row['Cust Messages With Brand Reply'], 1) # tweet 101 received reply

        # SpotifyCares row verification
        spotify_row = metrics_df[metrics_df['Brand'] == 'SpotifyCares'].iloc[0]
        self.assertEqual(spotify_row['Total Messages (Brand)'], 1) # tweet 202
        self.assertEqual(spotify_row['Customer->Brand Links'], 1)  # tweet 202 replying to 201
        self.assertEqual(spotify_row['Brand->Customer Links'], 0)
        self.assertEqual(spotify_row['Conversations With Both Sides'], 1)

    def test_extract_conversation_samples(self):
        """Test extraction of sample conversation rows to CSV."""
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            sample_df = extract_conversation_samples(
                self.sample_data,
                brand='AppleSupport',
                output_path=tmp_path,
                sample_size=10
            )
            self.assertGreaterEqual(len(sample_df), 1)
            self.assertIn('conversation_id', sample_df.columns)
            self.assertIn('turn_index', sample_df.columns)
            self.assertIn('text', sample_df.columns)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == '__main__':
    unittest.main()
