"""Session-isolated adapter around the original notebook engine."""
from pathlib import Path
from tempfile import TemporaryDirectory
import io
import html
import json
import re
import threading
import pandas as pd

ENGINE_LOCK = threading.RLock()  # Swiss Ephemeris and Yahoo clients share native/global state.
CORE_CODE = compile(Path(__file__).with_name('engine_core.py').read_text(), 'engine_core.py', 'exec')


def parse_tickers(text='', csv_bytes=None):
    values = re.split(r'[\s,;]+', text.strip()) if text.strip() else []
    if csv_bytes:
        frame = pd.read_csv(io.BytesIO(csv_bytes), dtype=str)
        columns = {str(c).strip().lower(): c for c in frame.columns}
        key = columns.get('ticker', columns.get('symbol'))
        if key is None:
            raise ValueError('The watchlist CSV needs a Ticker or Symbol column.')
        values.extend(frame[key].dropna().tolist())
    out = []
    for value in values:
        value = str(value).strip().upper().replace('.', '-')
        if not value:
            continue
        if not re.fullmatch(r'[A-Z0-9^][A-Z0-9^=\-]{0,19}', value):
            raise ValueError(f'Invalid ticker: {value}')
        if value not in out:
            out.append(value)
    if len(out) > 120:
        raise ValueError('Please scan at most 120 tickers at a time.')
    return out


class ResearchEngine:
    def __init__(self):
        self.temp = TemporaryDirectory(prefix='lunar-research-')
        self.output = Path(self.temp.name)
        self.ns = {'__name__': 'research_core', 'OUTPUT_DIR': self.output}
        with ENGINE_LOCK:
            exec(CORE_CODE, self.ns)
        # The notebook's V10.1 wrapper called V10's eager clock and then discarded it.
        # Bypass that eager wrapper; the cached clock is explicitly calculated below.
        def enrich(idea):
            idea = self.ns['_V95_enrich_v9'](idea)
            rec = self.ns['lookup_first_trade_record'](idea.get('ticker'))
            idea['v10_first_trade_record'] = rec if rec.get('quality') in ('VERIFIED_TIME','VERIFIED_DATE') else None
            return idea
        self.ns['enrich_v9'] = enrich
        # Each function retains this namespace, so state is never shared across users.
        self.ns['display'] = lambda *args, **kwargs: None
        self.last_downloads = {}
        self.history_status = {}
        self.last_universe = []
        self._original_fetch = self.ns['fetch_history']
        def fetch(ticker, asof, years=3):
            frame = self._original_fetch(ticker, asof, years)
            self.history_status[ticker] = 'No market data returned' if frame.empty else f'{len(frame)} price rows'
            return frame
        self.ns['fetch_history'] = fetch
        self.validate_database()

    def validate_database(self):
        bad = [t for t in ['BA','GE','HD','WMT','SBUX','COIN','COST','MSTR']
               if self.ns['lookup_first_trade_record'](t).get('quality') not in ('VERIFIED_TIME','VERIFIED_DATE')]
        if bad:
            raise ValueError('First-trade sanity check failed: ' + ', '.join(bad))

    def replace_database(self, data):
        frame = pd.read_csv(io.BytesIO(data), dtype=str, keep_default_na=False)
        frame.columns = [c.strip() for c in frame.columns]
        if not {'Ticker','Date'}.issubset(frame.columns):
            raise ValueError('The first-trade database needs Ticker and Date columns.')
        if frame.empty or pd.to_datetime(frame['Date'], errors='coerce').isna().any():
            raise ValueError('The database must contain usable dates on every row.')
        path = self.output / 'uploaded_first_trades.csv'
        frame.to_csv(path,index=False)
        with ENGINE_LOCK:
            self.ns['load_first_trade_database'](path)
        self.ns['LAST_SCAN_RESULTS'] = {'date':None,'mode':None,'stocks':[],'commodities':[]}
        self.last_downloads = {}

    def restore_database(self):
        with ENGINE_LOCK:
            self.ns['load_first_trade_database']()
            self.validate_database()
        self.ns['LAST_SCAN_RESULTS'] = {'date':None,'mode':None,'stocks':[],'commodities':[]}
        self.last_downloads = {}

    def scan(self, date, tickers=None, category='Stocks', long_only=True, top_n=8):
        self.last_downloads = {}
        self.history_status = {}
        self.last_universe = list(tickers or self.ns['DEFAULT_STOCKS']) if category != 'Commodities' else []
        with ENGINE_LOCK:
            mode, note = self.ns['_validated_market_mode'](date, 'before_market')
            state = {'date':date,'mode':mode,'requested_mode':'before_market','mode_note':note,'stocks':[],'commodities':[]}
            self.ns['LAST_SCAN_RESULTS'] = state
            previous = self.ns['DEFAULT_STOCKS']
            try:
                if tickers:
                    self.ns['DEFAULT_STOCKS'] = tickers
                if category in ('Stocks','Both'):
                    state['stocks'] = self.ns['scan_stocks'](date,'liquid',long_only,top_n,120,mode,True)
                if category in ('Commodities','Both'):
                    state['commodities'] = self.ns['scan_commodities'](date,long_only,top_n,mode,True)
            except Exception:
                self.ns['LAST_SCAN_RESULTS'] = {'date':None,'mode':None,'stocks':[],'commodities':[]}
                raise
            finally:
                self.ns['DEFAULT_STOCKS'] = previous
        return state

    @property
    def ideas(self):
        state = self.ns['LAST_SCAN_RESULTS']
        return list(state.get('stocks',[])) + list(state.get('commodities',[]))

    def summary(self):
        return self.ns['summary_dataframe'](self.ideas)

    def lunar(self):
        with ENGINE_LOCK:
            self.ns['compute_lunar_clocks_for_selected_results']()
        self.last_downloads = {}

    def reports(self):
        if not self.ideas:
            raise ValueError('Run a successful scan before generating reports.')
        with ENGINE_LOCK:
            self.lunar()
            files = {}
            for label, name in [('PDF','make_pdf_report'),('CSV','make_csv_report'),('HTML','make_html_report')]:
                path = Path(self.ns[name]())
                if label == 'HTML':
                    # The original HTML exporter predates the McWhirter/full-clock PDF.
                    # Append all final evidence so the browser report retains those layers.
                    additions = '<h2>Complete V10.1 evidence and lunar clocks</h2>'
                    for idea in self.ideas:
                        additions += '<h3>' + html.escape(idea['ticker']) + '</h3><pre style="white-space:pre-wrap">'
                        additions += html.escape(json.dumps(idea,default=str,indent=2)) + '</pre>'
                    source = path.read_text()
                    source = source.replace('</body>', additions + '</body>') if '</body>' in source else source + additions
                    path.write_text(source)
                files[label] = (path.name, path.read_bytes())
            self.last_downloads = files
        return files
