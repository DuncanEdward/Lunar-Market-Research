import hmac
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st
from service import ResearchEngine, parse_tickers

st.set_page_config(page_title='Lunar Market Research', page_icon='◐', layout='wide')
st.title('Lunar Market Research')
st.caption('Bucholtz · Bill Meridian · Louise McWhirter | V10.1')
password = os.environ.get('APP_PASSWORD','')
if not password:
    st.error('Set APP_PASSWORD in the hosting environment before using this app.')
    st.stop()
if not st.session_state.get('authenticated'):
    with st.form('login'):
        entered = st.text_input('Your app password',type='password')
        submitted = st.form_submit_button('Sign in')
    if submitted:
        if hmac.compare_digest(entered.encode(), password.encode()):
            st.session_state['authenticated'] = True
            st.rerun()
        st.error('Incorrect password.')
    st.stop()

if 'engine' not in st.session_state:
    with st.spinner('Loading research engine and first-trade database…'):
        st.session_state['engine'] = ResearchEngine()
engine = st.session_state['engine']
st.info('Research tool. Financial astrology is not scientifically established as a forecasting method. Scores describe model evidence; price confirmation and risk controls determine whether a setup is actionable.')

with st.sidebar:
    st.header('Scan settings')
    day = st.date_input('Research date', datetime.now(ZoneInfo('America/New_York')).date())
    category = st.selectbox('Markets',['Stocks','Commodities','Both'])
    long_only = st.checkbox('Long ideas only',True)
    top_n = st.slider('Shortlist per market',3,15,8)
    st.caption('The full lunar clock runs only for shortlisted candidates. Session labels are checked against New York time.')
    st.divider()
    st.subheader('First-trade database')
    st.caption(f"{len(engine.ns['FIRST_TRADE_DB']):,} bundled records available. Exact times and date-only records remain separately labelled.")
    database = st.file_uploader('Replace first-trade database (CSV)',type=['csv'],key='database')
    if st.button('Use uploaded database',disabled=database is None):
        try:
            engine.replace_database(database.getvalue())
            st.success('Database replaced for this session.')
        except Exception as exc:
            st.error(str(exc))
    if st.button('Restore bundled database'):
        engine.restore_database()
        st.rerun()
    st.download_button('Download first-trade database',engine.ns['FIRST_TRADE_DB'].drop(columns=['_parsed_date'],errors='ignore').to_csv(index=False),'first_trades.csv','text/csv')
    st.download_button('Download Bucholtz trigger calendar',engine.ns['V10_BUCHOLTZ_CALENDAR'].to_csv(index=False),'bucholtz_calendar_2026_2030.csv','text/csv')

st.subheader('Choose stocks')
text = st.text_area('Tickers, separated by commas or spaces',placeholder='AAPL, MSFT, NVDA',disabled=category=='Commodities')
watchlist = st.file_uploader('Upload Finviz watchlist or screener export (CSV)',type=['csv'],key='watchlist',disabled=category=='Commodities')
st.caption('Ticker entry and CSV tickers are combined. Leave both empty to scan the original liquid-stock universe. Maximum 120 symbols.')
if st.button('Run scan',type='primary'):
    try:
        tickers = parse_tickers(text,watchlist.getvalue() if watchlist else None)
        with st.spinner('Scanning market data and strategy evidence. Larger lists take longer…'):
            state = engine.scan(day.isoformat(),tickers,category,long_only,top_n)
        if engine.ideas:
            st.success('Scan complete. Review the decision and price-data dates below.')
        else:
            st.warning('No candidates returned. Check data diagnostics: missing price data and failed filters can both cause an empty scan.')
    except Exception as exc:
        st.error(f'Scan failed: {exc}')

state = engine.ns['LAST_SCAN_RESULTS']
if state.get('date'):
    st.subheader(f"Results · {state['date']}")
    st.caption(state.get('mode_note',''))
    if engine.ideas:
        st.dataframe(engine.summary(),hide_index=True,use_container_width=True)
        col1,col2 = st.columns(2)
        with col1:
            if st.button('Calculate shortlisted lunar clocks'):
                with st.spinner('Calculating applying, exact and separating lunar contacts…'):
                    try:
                        engine.lunar()
                        st.success('Lunar clocks calculated.')
                    except Exception as exc:
                        st.error(f'Lunar calculation failed: {exc}')
        with col2:
            if st.button('Prepare PDF, CSV and HTML reports'):
                with st.spinner('Calculating lunar clocks and preparing reports…'):
                    try:
                        engine.reports()
                    except Exception as exc:
                        st.error(f'Report generation failed: {exc}')
        for label,(name,data) in engine.last_downloads.items():
            mime = {'PDF':'application/pdf','CSV':'text/csv','HTML':'text/html'}[label]
            st.download_button(f'Download {label} report',data,name,mime,key=f'download_{label}')
        for idea in engine.ideas:
            with st.expander(f"{idea['ticker']} · {idea.get('status','')} · {idea.get('bias','')}"):
                st.text(engine.ns['format_idea'](idea))
                if idea.get('lunar_session_clock'):
                    st.write('Full lunar session clock')
                    st.json(idea['lunar_session_clock'])
                st.json(idea,expanded=False)
    with st.expander('Scan data diagnostics'):
        st.write(engine.history_status)
        returned = {i['ticker'] for i in engine.ideas}
        st.write('Requested stocks absent from the shortlist:',[t for t in engine.last_universe if t not in returned])
        st.caption('Stocks may be omitted because market data is unavailable, technical filters fail, or they rank below the shortlist limit. NO TRADE is a valid model decision when usable data exists.')

with st.expander('Source rules and model interpretation'):
    st.dataframe(engine.ns['MCWHIRTER_CHAPTERS'],hide_index=True)
    st.caption('Chapter IV is explicitly a first-trade adaptation. Date-only charts use modelling assumptions. The generated calendar applies source-derived trigger rules; it is not a calendar published by Bucholtz. Daily Yahoo data is intended for research, not a live execution feed or a point-in-time backtest.')
