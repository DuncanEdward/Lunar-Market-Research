import os
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from service import ResearchEngine, parse_tickers

class AppChecks(unittest.TestCase):
    def test_ticker_upload(self):
        self.assertEqual(parse_tickers('aapl, BRK.B',b'Ticker,Price\nMSFT,100\nAAPL,150\n'),['AAPL','BRK-B','MSFT'])
        with self.assertRaises(ValueError):
            parse_tickers(csv_bytes=b'Price\n100\n')

    def test_scan_reports_and_isolation(self):
        engine = ResearchEngine()
        other = ResearchEngine()
        index = pd.bdate_range(end='2026-09-30',periods=760)
        # Reproducible prices exercise real technical and all strategy layers offline.
        close = 50 + np.arange(760)*.13 + np.sin(np.arange(760)/9)*3
        frame = pd.DataFrame({'Open':close-.3,'High':close+1,'Low':close-1,'Close':close,'Volume':2500000},index=index)
        engine._original_fetch = lambda ticker, asof, years=3: frame.copy()
        engine.ns['full_lunar_session_clock'] = lambda *a, **k: self.fail('Eager lunar clock must not run during scan')
        state = engine.scan('2026-09-30',['AAPL'],long_only=True)
        self.assertEqual(state['mode'],'after_market')
        self.assertEqual([i['ticker'] for i in engine.ideas],['AAPL'])
        self.assertFalse(other.ideas)
        self.assertNotIn('lunar_session_clock_v101',engine.ideas[0])
        reports = engine.reports()
        self.assertTrue(reports['PDF'][1].startswith(b'%PDF'))
        self.assertIn(b'AAPL',reports['CSV'][1])
        self.assertIn(b'AAPL',reports['HTML'][1])
        self.assertTrue(engine.ideas[0]['lunar_session_clock_v101'])
        self.assertTrue(all((engine.output/name).is_file() for name,data in reports.values()))
        # An invalid upload cannot silently replace the good database.
        count = len(engine.ns['FIRST_TRADE_DB'])
        with self.assertRaises(ValueError):
            engine.replace_database(b'Ticker,Date\nAAPL,not-a-date\n')
        self.assertEqual(len(engine.ns['FIRST_TRADE_DB']),count)

    def test_streamlit_controls(self):
        from streamlit.testing.v1 import AppTest
        os.environ['APP_PASSWORD'] = 'local-test-password'
        app = AppTest.from_file(str(Path(__file__).with_name('app.py'))).run(timeout=30)
        self.assertFalse(app.exception)
        app.text_input[0].set_value('local-test-password')
        app.button[0].click().run(timeout=30)
        self.assertFalse(app.exception)
        self.assertTrue(any(b.label=='Run scan' for b in app.button))

if __name__ == '__main__':
    unittest.main()
