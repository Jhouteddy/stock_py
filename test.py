import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import time
import os
import argparse

def get_stock_data(date, stock_no):
    url = f'https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date}&stockNo={stock_no}'
    response = requests.get(url)
    if response.status_code == 200:
        content = json.loads(response.text)
        if 'data' in content and 'fields' in content:
            return pd.DataFrame(data=content['data'], columns=content['fields'])
    return None


def convert_date(tw_date):
    year = int(tw_date.split('/')[0]) + 1911
    month = tw_date.split('/')[1]
    day = tw_date.split('/')[2]
    return f'{year}-{month}-{day}'


def process_and_save_monthly(date, stock_no, output_file):
    date_str = date.strftime('%Y%m%d')
    print(f"正在抓取 {date_str} 的資料...")

    df = get_stock_data(date_str, stock_no)

    if df is not None:
        # 轉換欄位名稱並選擇需要的欄位
        df_processed = pd.DataFrame({
            'Date': df['日期'].apply(convert_date),
            'Open': df['開盤價'].str.replace(',', ''),
            'High': df['最高價'].str.replace(',', ''),
            'Low': df['最低價'].str.replace(',', ''),
            'Close': df['收盤價'].str.replace(',', ''),
            'Volume': df['成交股數'].str.replace(',', '')
        })

        # 如果檔案不存在，寫入標頭；如果存在，追加資料
        if not os.path.exists(output_file):
            df_processed.to_csv(output_file, index=False, mode='w')
        else:
            df_processed.to_csv(output_file, index=False, mode='a', header=False)

        return True
    return False


def get_last_date_from_file(output_file):
    if os.path.exists(output_file):
        # 讀取檔案的最後一行
        df = pd.read_csv(output_file)
        last_date = df['Date'].iloc[-1]  # 取得最後一筆日期
        last_datetime = datetime.strptime(last_date, '%Y-%m-%d')
        # 返回下個月的第一天
        next_month = (last_datetime.replace(day=1) + timedelta(days=32)).replace(day=1)
        return next_month
    return None


def fetch_stock_data(start_date, stock_no, output_file):
    # 檢查是否有現有檔案並取得最後日期
    last_date = get_last_date_from_file(output_file)

    if last_date:
        print(f"檢測到現有資料，最後日期為 {last_date.strftime('%Y-%m-%d')}，從下個月開始抓取")
        current_date = last_date
    else:
        print("沒有現有資料，從指定開始日期抓取")
        current_date = datetime.strptime(start_date, '%Y%m%d')

    end_date = datetime.now()

    while current_date <= end_date:
        success = process_and_save_monthly(current_date, stock_no, output_file)
        if success:
            print(f"{current_date.strftime('%Y-%m')} 資料處理完成")
        else:
            print(f"{current_date.strftime('%Y-%m')} 無資料或抓取失敗")

        # 移到下個月
        current_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)
        time.sleep(1)  # 避免過快請求


def main():
    # 設定命令列參數
    parser = argparse.ArgumentParser(description='抓取台灣證交所股票歷史資料')
    parser.add_argument('--stock_no', type=str, required=True, help='指定股票代號，例如 00631L')
    parser.add_argument('--start_date', type=str, default='20140101', help='開始日期，格式 YYYYMMDD，預設 20140101')

    # 解析參數
    args = parser.parse_args()

    stock_no = args.stock_no
    start_date = args.start_date
    output_file = f'stock_{stock_no}_data.csv'

    print(f"開始抓取股票 {stock_no} 的資料...")
    fetch_stock_data(start_date, stock_no, output_file)
    print(f"所有資料已儲存至 {output_file}")


if __name__ == "__main__":
    main()