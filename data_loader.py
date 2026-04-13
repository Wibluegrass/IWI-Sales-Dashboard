"""
Data loader for Multibrand Daily Flash Reports.
Parses all Excel files in the folder and returns structured DataFrames.

Option A mode: Designed to work with a single Excel file that gets
replaced each time. The bracket number in the filename is ignored.
"""

import os
import re
import glob
import pandas as pd
from openpyxl import load_workbook
from datetime import datetime


def parse_date_from_cell(value):
    """Extract date from cell like 'Selected Date:2/22/2026'."""
    if not value:
        return None
    match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', str(value))
    if match:
        return datetime.strptime(match.group(1), '%m/%d/%Y').date()
    return None


def safe_float(val, default=0.0):
    """Safely convert value to float."""
    if val is None or val == '' or val == '-':
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_int(val, default=0):
    """Safely convert value to int."""
    if val is None or val == '' or val == '-':
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def parse_flash_report(filepath):
    """
    Parse a single Multibrand Flash Report Excel file.
    Returns a dict with DataFrames for each data section.
    """
    wb = load_workbook(filepath, data_only=True)
    ws = wb['Multibrand_DailyFlashReport']

    # Extract report date from cell A2
    report_date = parse_date_from_cell(ws['A2'].value)
    if not report_date:
        wb.close()
        return None

    # --- Section 1: Sales by Store (rows 8-15 in first section) ---
    sales_records = []
    for row_num in range(8, 16):  # rows 8–15
        store_name = ws.cell(row=row_num, column=1).value
        if not store_name or 'Totals' in str(store_name) or 'Brand' in str(store_name):
            continue
        sales_records.append({
            'date': report_date,
            'store': str(store_name).strip(),
            'day_sales_ty': safe_float(ws.cell(row=row_num, column=2).value),
            'day_sales_ly': safe_float(ws.cell(row=row_num, column=3).value),
            'day_sales_diff': safe_float(ws.cell(row=row_num, column=4).value),
            'day_sales_pct': safe_float(ws.cell(row=row_num, column=5).value),
            'wtd_sales_ty': safe_float(ws.cell(row=row_num, column=6).value),
            'wtd_sales_ly': safe_float(ws.cell(row=row_num, column=7).value),
            'wtd_sales_diff': safe_float(ws.cell(row=row_num, column=8).value),
            'wtd_sales_pct': safe_float(ws.cell(row=row_num, column=9).value),
            'ptd_sales_ty': safe_float(ws.cell(row=row_num, column=10).value),
            'ptd_sales_ly': safe_float(ws.cell(row=row_num, column=11).value),
            'ptd_sales_diff': safe_float(ws.cell(row=row_num, column=12).value),
            'ptd_sales_pct': safe_float(ws.cell(row=row_num, column=13).value),
            'ytd_sales_ty': safe_float(ws.cell(row=row_num, column=14).value),
            'ytd_sales_ly': safe_float(ws.cell(row=row_num, column=15).value),
            'ytd_sales_diff': safe_float(ws.cell(row=row_num, column=16).value),
            'ytd_sales_pct': safe_float(ws.cell(row=row_num, column=17).value),
            'r13_sales_ty': safe_float(ws.cell(row=row_num, column=18).value),
            'r13_sales_ly': safe_float(ws.cell(row=row_num, column=19).value),
            'r13_sales_diff': safe_float(ws.cell(row=row_num, column=20).value),
            'r13_sales_pct': safe_float(ws.cell(row=row_num, column=21).value),
        })

    # Brand totals (row 16)
    brand_total = {
        'date': report_date,
        'day_sales_ty': safe_float(ws.cell(row=16, column=2).value),
        'day_sales_ly': safe_float(ws.cell(row=16, column=3).value),
        'day_sales_diff': safe_float(ws.cell(row=16, column=4).value),
        'day_sales_pct': safe_float(ws.cell(row=16, column=5).value),
        'wtd_sales_ty': safe_float(ws.cell(row=16, column=6).value),
        'wtd_sales_ly': safe_float(ws.cell(row=16, column=7).value),
        'wtd_sales_diff': safe_float(ws.cell(row=16, column=8).value),
        'wtd_sales_pct': safe_float(ws.cell(row=16, column=9).value),
        'ptd_sales_ty': safe_float(ws.cell(row=16, column=10).value),
        'ptd_sales_ly': safe_float(ws.cell(row=16, column=11).value),
        'ptd_sales_diff': safe_float(ws.cell(row=16, column=12).value),
        'ptd_sales_pct': safe_float(ws.cell(row=16, column=13).value),
        'ytd_sales_ty': safe_float(ws.cell(row=16, column=14).value),
        'ytd_sales_ly': safe_float(ws.cell(row=16, column=15).value),
        'ytd_sales_diff': safe_float(ws.cell(row=16, column=16).value),
        'ytd_sales_pct': safe_float(ws.cell(row=16, column=17).value),
        'r13_sales_ty': safe_float(ws.cell(row=16, column=18).value),
        'r13_sales_ly': safe_float(ws.cell(row=16, column=19).value),
        'r13_sales_diff': safe_float(ws.cell(row=16, column=20).value),
        'r13_sales_pct': safe_float(ws.cell(row=16, column=21).value),
    }

    # --- Section 2: Transactions by Store (rows 54-61) ---
    trans_records = []
    for row_num in range(54, 62):
        store_name = ws.cell(row=row_num, column=1).value
        if not store_name or 'Totals' in str(store_name):
            continue
        trans_records.append({
            'date': report_date,
            'store': str(store_name).strip(),
            'day_trans_ty': safe_int(ws.cell(row=row_num, column=2).value),
            'day_trans_ly': safe_int(ws.cell(row=row_num, column=3).value),
            'day_trans_diff': safe_int(ws.cell(row=row_num, column=4).value),
            'day_trans_pct': safe_float(ws.cell(row=row_num, column=5).value),
            'wtd_trans_ty': safe_int(ws.cell(row=row_num, column=6).value),
            'wtd_trans_ly': safe_int(ws.cell(row=row_num, column=7).value),
            'wtd_trans_diff': safe_int(ws.cell(row=row_num, column=8).value),
            'wtd_trans_pct': safe_float(ws.cell(row=row_num, column=9).value),
            'ptd_trans_ty': safe_int(ws.cell(row=row_num, column=10).value),
            'ptd_trans_ly': safe_int(ws.cell(row=row_num, column=11).value),
            'ptd_trans_diff': safe_int(ws.cell(row=row_num, column=12).value),
            'ptd_trans_pct': safe_float(ws.cell(row=row_num, column=13).value),
            'ytd_trans_ty': safe_int(ws.cell(row=row_num, column=14).value),
            'ytd_trans_ly': safe_int(ws.cell(row=row_num, column=15).value),
            'ytd_trans_diff': safe_int(ws.cell(row=row_num, column=16).value),
            'ytd_trans_pct': safe_float(ws.cell(row=row_num, column=17).value),
            'r13_trans_ty': safe_int(ws.cell(row=row_num, column=18).value),
            'r13_trans_ly': safe_int(ws.cell(row=row_num, column=19).value),
            'r13_trans_diff': safe_int(ws.cell(row=row_num, column=20).value),
            'r13_trans_pct': safe_float(ws.cell(row=row_num, column=21).value),
        })

    # --- Section 3: Channel Mix (rows 66-73) ---
    channel_records = []
    for row_num in range(66, 74):
        store_name = ws.cell(row=row_num, column=1).value
        if not store_name or 'Totals' in str(store_name):
            continue
        channel_records.append({
            'date': report_date,
            'store': str(store_name).strip(),
            'avg_check_ty': safe_float(ws.cell(row=row_num, column=2).value),
            'avg_check_ly': safe_float(ws.cell(row=row_num, column=3).value),
            'avg_check_diff': safe_float(ws.cell(row=row_num, column=4).value),
            'avg_check_pct': safe_float(ws.cell(row=row_num, column=5).value),
            'dine_in_sales': safe_float(ws.cell(row=row_num, column=6).value),
            'dine_in_trans': safe_int(ws.cell(row=row_num, column=7).value),
            'dine_in_avg_check': safe_float(ws.cell(row=row_num, column=8).value),
            'dine_in_pct_sales': safe_float(ws.cell(row=row_num, column=9).value),
            'carry_out_sales': safe_float(ws.cell(row=row_num, column=10).value),
            'carry_out_trans': safe_int(ws.cell(row=row_num, column=11).value),
            'carry_out_avg_check': safe_float(ws.cell(row=row_num, column=12).value),
            'carry_out_pct_sales': safe_float(ws.cell(row=row_num, column=13).value),
            'delivery_sales': safe_float(ws.cell(row=row_num, column=14).value),
            'delivery_trans': safe_int(ws.cell(row=row_num, column=15).value),
            'delivery_avg_check': safe_float(ws.cell(row=row_num, column=16).value),
            'delivery_pct_sales': safe_float(ws.cell(row=row_num, column=17).value),
            'drive_thru_sales': safe_float(ws.cell(row=row_num, column=18).value),
            'drive_thru_trans': safe_int(ws.cell(row=row_num, column=19).value),
            'drive_thru_avg_check': safe_float(ws.cell(row=row_num, column=20).value),
            'drive_thru_pct_sales': safe_float(ws.cell(row=row_num, column=21).value),
        })

    # --- Section 4: Labor & 3rd Party (rows 78-85) ---
    labor_records = []
    for row_num in range(78, 86):
        store_name = ws.cell(row=row_num, column=1).value
        if not store_name or 'Totals' in str(store_name):
            continue
        labor_records.append({
            'date': report_date,
            'store': str(store_name).strip(),
            'labor_dollars': safe_float(ws.cell(row=row_num, column=2).value),
            'labor_pct': safe_float(ws.cell(row=row_num, column=3).value),
            'olo_sales': safe_float(ws.cell(row=row_num, column=4).value),
            'doordash': safe_float(ws.cell(row=row_num, column=5).value),
            'ubereats': safe_float(ws.cell(row=row_num, column=6).value),
            'grubhub': safe_float(ws.cell(row=row_num, column=7).value),
            'eatstreet': safe_float(ws.cell(row=row_num, column=8).value),
            'ezcater': safe_float(ws.cell(row=row_num, column=9).value),
            'total_3rd_party_dollars': safe_float(ws.cell(row=row_num, column=10).value),
            'total_3rd_party_pct': safe_float(ws.cell(row=row_num, column=11).value),
        })

    wb.close()

    return {
        'date': report_date,
        'sales': sales_records,
        'brand_total': brand_total,
        'transactions': trans_records,
        'channels': channel_records,
        'labor': labor_records,
    }


def load_all_reports(folder_path=None):
    """
    Load all Multibrand Flash Report Excel files from the given folder.

    Option A mode: Reads ALL matching Excel files found, using the newest
    file when multiple files share the same date. The bracket number in
    the filename is completely ignored — just replace the file in GitHub
    and it will always pick up the latest data.
    """
    if folder_path is None:
        folder_path = os.path.dirname(os.path.abspath(__file__))

    pattern = os.path.join(folder_path, 'Multibrand_FlashReport*.xlsx')
    files = glob.glob(pattern)

    if not files:
        print(f"No matching Excel files found in: {folder_path}")

    # Parse every file, group by date, keep newest mtime per date
    parsed_by_date = {}  # date → (result, mtime)

    for filepath in files:
        try:
            result = parse_flash_report(filepath)
            if result is None:
                continue
            rdate = result['date']
            mtime = os.path.getmtime(filepath)

            # Keep the file with the newest modification time for each date
            if rdate not in parsed_by_date or mtime > parsed_by_date[rdate][1]:
                parsed_by_date[rdate] = (result, mtime)

        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
            continue

    # Combine all winning results into DataFrames
    all_sales = []
    all_brand_totals = []
    all_transactions = []
    all_channels = []
    all_labor = []

    for rdate, (result, _) in parsed_by_date.items():
        all_sales.extend(result['sales'])
        all_brand_totals.append(result['brand_total'])
        all_transactions.extend(result['transactions'])
        all_channels.extend(result['channels'])
        all_labor.extend(result['labor'])

    data = {
        'sales': pd.DataFrame(all_sales) if all_sales else pd.DataFrame(),
        'brand_totals': pd.DataFrame(all_brand_totals) if all_brand_totals else pd.DataFrame(),
        'transactions': pd.DataFrame(all_transactions) if all_transactions else pd.DataFrame(),
        'channels': pd.DataFrame(all_channels) if all_channels else pd.DataFrame(),
        'labor': pd.DataFrame(all_labor) if all_labor else pd.DataFrame(),
    }

    # Sort by date
    for key in data:
        if not data[key].empty and 'date' in data[key].columns:
            data[key] = data[key].sort_values('date').reset_index(drop=True)

    return data


if __name__ == '__main__':
    # Quick test
    data = load_all_reports()
    for key, df in data.items():
        print(f"\n{key}: {len(df)} rows")
        if not df.empty:
            print(df.head())
