"""Weekly personalized hotel summaries. Default is SAFE preview, no delivery."""
import argparse, os, re
from datetime import date, timedelta
from pathlib import Path
from dotenv import load_dotenv
from src.source import fetch_data
from src.analytics import assess_hotels
from src.ai import create_message
from src.mailer import send_test_email
from src.logging_db import DispatchLog

def previous_iso_week(today: date) -> str:
    last_week = today - timedelta(days=7)
    y, w, _ = last_week.isocalendar()
    return f'{y}-W{w:02d}'

def main():
    load_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument('--source', choices=['excel', 'sheets'], default=os.getenv('DATA_SOURCE', 'excel'))
    p.add_argument('--period', default=os.getenv('REPORT_PERIOD', '').strip())
    p.add_argument('--send', action='store_true', help='Send only when SEND_ENABLED=true and TEST_RECIPIENT is set')
    args = p.parse_args()
    period = args.period or previous_iso_week(date.today())
    if not re.fullmatch(r'\d{4}-W\d{2}', period):
        raise ValueError('Period must be like 2026-W42')
    if args.source == 'excel' and not args.period:
        print('WARNING: Excel Sheet1 lacks dates; --period is a label, NOT an actual date filter.')
    if args.source == 'sheets' and not args.period:
        raise ValueError('For Sheets, specify REPORT_PERIOD: Sheet1 has no dated rows.')
    if args.send and os.getenv('SEND_ENABLED', '').lower() != 'true':
        raise ValueError('Refusing email delivery: set SEND_ENABLED=true explicitly')
    recipient = os.getenv('TEST_RECIPIENT', '').strip()
    if args.send and (not recipient or '@' not in recipient or recipient.endswith('@example.com')):
        raise ValueError('Refusing email delivery without a valid TEST_RECIPIENT')
    df = fetch_data(args.source, os.getenv('EXCEL_PATH', 'data/hotel_mock_data.xlsx'),
                    os.getenv('GOOGLE_SHEET_ID', ''), os.getenv('GOOGLE_SHEET_TAB', 'Sheet1'))
    hotels = assess_hotels(df)
    log = DispatchLog(os.getenv('DB_PATH', 'dispatch_log.sqlite3'))
    preview_dir = Path('previews'); preview_dir.mkdir(exist_ok=True)
    print(f'Period={period}; hotels={len(hotels)}; mode={"SEND TO TEST RECIPIENT" if args.send else "PREVIEW ONLY"}')
    failures = 0
    for idx, hotel in enumerate(hotels, 1):
        key = f'{period}|{hotel["hotel"].casefold()}'
        if args.send and log.sent(key):
            print(f'SKIPPED already-sent: {hotel["hotel"]}')
            continue
        subject = f'Weekly Hotel Performance | {hotel["hotel"]} | {period}'
        body, ai_status = create_message(hotel, period)
        (preview_dir / f'{idx:02d}_{period}.txt').write_text(
            f'To (test-only): {recipient or "NOT SET"}\nOriginal owner (NOT used): {hotel["owner_email"]}\n'
            f'Subject: {subject}\nAI status: {ai_status}\n\n{body}\n', encoding='utf-8')
        status, msg_id, err = 'PREVIEW_ONLY', '', ''
        if args.send:
            try:
                msg_id = send_test_email(recipient, subject, body)
                status = 'SENT'
            except Exception as exc:
                status, err = 'FAILED', f'{type(exc).__name__}: {exc}'
                failures += 1
        log.record(key, hotel['hotel'], period, status, recipient, subject, body, ai_status, msg_id, err)
        print(f'{idx:02d} | {hotel["classification"]:18s} | {status:12s} | {hotel["hotel"]}')
    if failures:
        raise RuntimeError(f'{failures} message(s) failed; see SQLite dispatch log')

if __name__ == '__main__':
    main()
