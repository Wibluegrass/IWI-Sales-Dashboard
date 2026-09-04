#!/usr/bin/env python3
"""Ingest daily Multibrand Flash Reports: give each file its business date as a
name, then report what the folder actually holds and what is missing.

Standard library only -- this runs under macOS's system python3, which has no
openpyxl. The report date lives as text inside the workbook's sheet XML, so it
is read straight out of the .xlsx zip.

Browsers name repeat downloads Multibrand_FlashReport.nopag[184].xlsx, numbered
by download order rather than business date, which is why [184] can be Sep 1
while [185] is Aug 31. Renaming each new arrival to its business date makes the
filename mean something, makes a re-download replace the day it belongs to
instead of piling up beside it, and makes a missing day visible at a glance.

Existing numbered files are left alone; only new arrivals are renamed.

  python3 ingest_reports.py           # rename new arrivals, print status
  python3 ingest_reports.py --check   # status only, change nothing

Exit codes: 0 all good, 1 something needs a human.
"""
import datetime
import glob
import os
import re
import subprocess
import sys
import zipfile

try:
    from zoneinfo import ZoneInfo
except ImportError:                     # pragma: no cover - very old python
    ZoneInfo = None

# The stores run on US Central time. This script is run both from macOS (already
# Central) and from a UTC container, and a UTC clock rolls over five hours early
# -- which would report yesterday as missing while it is still today here.
BUSINESS_TZ = 'America/Chicago'

PREFIX = 'Multibrand_FlashReport'
PATTERN = PREFIX + '*.xlsx'
DATED = re.compile(r'\.(\d{4}-\d{2}-\d{2})\.xlsx$')
NUMBERED = re.compile(r'\[(\d+)\]\.xlsx$')
DATE_TEXT = re.compile(r'Selected Date:\s*(\d{1,2})/(\d{1,2})/(\d{4})')
STALE_DAYS = 2      # newest report older than this is called out
LOOKBACK = 30       # how far back to hunt for holes


def business_today():
    """Today's date where the stores are, not where this process runs."""
    if ZoneInfo is not None:
        try:
            return datetime.datetime.now(ZoneInfo(BUSINESS_TZ)).date()
        except Exception:
            pass
    return datetime.date.today()


def report_date(path):
    """Business date from inside the workbook, or None if unreadable."""
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            for member in ('xl/worksheets/sheet1.xml', 'xl/sharedStrings.xml'):
                if member not in names:
                    continue
                match = DATE_TEXT.search(z.read(member).decode('utf-8', 'replace'))
                if match:
                    mm, dd, yyyy = (int(g) for g in match.groups())
                    return datetime.date(yyyy, mm, dd)
    except (zipfile.BadZipFile, OSError, ValueError):
        return None
    return None


def dated_name(day):
    return '{}.{}.xlsx'.format(PREFIX, day.isoformat())


def already_committed(folder):
    """Filenames git is already tracking.

    These are the historical downloads. Renaming them would rewrite 180-odd
    paths in one commit for no gain and would churn the repo, so only files git
    has never seen -- genuinely new arrivals -- get renamed. Returns None when
    git cannot answer, which means: rename nothing.
    """
    try:
        out = subprocess.run(['git', '-C', folder, 'ls-files', PATTERN],
                             capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return set(os.path.basename(line) for line in out.stdout.splitlines() if line)


def rename_new_arrivals(folder):
    """Rename newly arrived browser-numbered files to their business date.

    Returns (renamed, replaced, unreadable).
    """
    renamed, replaced, unreadable = [], [], []
    tracked = already_committed(folder)
    if tracked is None:
        print('   !! git could not list tracked files -- renaming nothing.')
        return renamed, replaced, unreadable
    for path in sorted(glob.glob(os.path.join(folder, PATTERN))):
        name = os.path.basename(path)
        if DATED.search(name) or not NUMBERED.search(name):
            continue
        if name in tracked:          # historical download, leave it alone
            continue
        day = report_date(path)
        if day is None:
            unreadable.append(name)
            continue
        target = os.path.join(folder, dated_name(day))
        if os.path.abspath(target) == os.path.abspath(path):
            continue
        if os.path.exists(target):
            # A newer download of a day we already hold: the newer one wins,
            # matching how data_loader resolves duplicates.
            os.replace(path, target)
            replaced.append((name, os.path.basename(target)))
        else:
            os.rename(path, target)
            renamed.append((name, os.path.basename(target)))
    return renamed, replaced, unreadable


def survey(folder):
    """Every business date the folder holds, plus files it could not read."""
    days, unreadable = {}, []
    for path in glob.glob(os.path.join(folder, PATTERN)):
        day = report_date(path)
        if day is None:
            unreadable.append(os.path.basename(path))
        else:
            days.setdefault(day, []).append(os.path.basename(path))
    return days, unreadable


def main():
    check_only = '--check' in sys.argv
    folder = os.path.dirname(os.path.abspath(__file__))
    problems = []

    if not check_only:
        renamed, replaced, unreadable = rename_new_arrivals(folder)
        for old, new in renamed:
            print('   renamed  {}  ->  {}'.format(old, new))
        for old, new in replaced:
            print('   replaced {}  ->  {}  (newer download of a day already held)'
                  .format(old, new))
        if not renamed and not replaced:
            print('   no new report files to take in')
        for name in unreadable:
            print('   !! could not read a report date from {}'.format(name))
            problems.append('unreadable file: ' + name)

    days, unreadable = survey(folder)
    if not days:
        print('\n!! No readable reports in this folder at all.')
        return 1
    for name in unreadable:
        if name not in [p.split(': ', 1)[-1] for p in problems]:
            problems.append('unreadable file: ' + name)

    newest = max(days)
    today = business_today()
    behind = (today - newest).days

    print('\n   {} reports covering {} days, {} .. {}'
          .format(sum(len(v) for v in days.values()), len(days),
                  min(days).isoformat(), newest.isoformat()))
    print('   newest business date: {} ({} day{} behind today)'
          .format(newest.isoformat(), behind, '' if behind == 1 else 's'))

    # Today's business day has not closed, so the newest report you can
    # possibly hold is yesterday's. Hunt for holes up to there, not to today.
    last = today - datetime.timedelta(days=1)
    start = last - datetime.timedelta(days=LOOKBACK - 1)
    missing = [start + datetime.timedelta(days=i)
               for i in range((last - start).days + 1)
               if start + datetime.timedelta(days=i) not in days]
    if missing:
        # Each day's report is published the following morning, so the most
        # recent gap is usually just not out yet rather than a lost day.
        pending = missing[-1] if missing[-1] == last else None
        firm = [d for d in missing if d != pending]
        print('\n   MISSING in the last {} days:'.format(LOOKBACK))
        if firm:
            print('   ' + ', '.join(d.strftime('%b %-d %a') for d in firm))
        if pending:
            print('   ' + pending.strftime('%b %-d %a')
                  + '   (yesterday -- may not be published yet)')
        if firm:
            problems.append('{} missing day(s)'.format(len(firm)))
    else:
        print('\n   no gaps in the last {} days'.format(LOOKBACK))

    if behind > STALE_DAYS:
        problems.append('newest report is {} days old'.format(behind))

    dupes = {d: v for d, v in days.items() if len(v) > 1}
    if dupes:
        print('\n   {} day(s) still covered by more than one file '
              '(older numbered downloads):'.format(len(dupes)))
        for d in sorted(dupes)[:5]:
            print('     {}: {}'.format(d.isoformat(), ', '.join(sorted(dupes[d]))))

    if problems:
        print('\n   NEEDS ATTENTION: ' + '; '.join(problems))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
