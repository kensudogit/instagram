import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import logging
import time
import os
import schedule
import argparse
from decouple import config

# Google Sheets APIの設定
# Google Sheetsにアクセスするためのスコープを定義
scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]
# 認証情報を読み込み、Google Sheetsにアクセス
creds = ServiceAccountCredentials.from_json_keyfile_name('path/to/credentials.json', scope)
client = gspread.authorize(creds)

# Google Sheetを開く
sheet = client.open('Instagram Automation').sheet1

# 機密データの管理にpython-decoupleを使用
# アクセストークンとユーザーIDを.envファイルから読み込む
ACCESS_TOKEN = config('INSTAGRAM_ACCESS_TOKEN', default='your_access_token')
USER_ID = config('INSTAGRAM_USER_ID', default='your_user_id')

# ログの設定
# ログファイルに情報を記録
logging.basicConfig(filename='instagram_automation.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Instagramにメディアをアップロードする関数
# エラーハンドリングとリトライ機能を含む
def upload_media(media_url, caption, retries=3):
    for attempt in range(retries):
        try:
            # ステップ1: メディアをアップロード
            upload_url = f"{INSTAGRAM_GRAPH_API_URL}{USER_ID}/media"
            payload = {
                'image_url': media_url,
                'caption': caption,
                'access_token': ACCESS_TOKEN
            }
            response = requests.post(upload_url, data=payload)
            response.raise_for_status()  # エラーがある場合は例外を発生
            media_id = response.json().get('id')

            # ステップ2: メディアを公開
            if media_id:
                publish_url = f"{INSTAGRAM_GRAPH_API_URL}{USER_ID}/media_publish"
                publish_payload = {
                    'creation_id': media_id,
                    'access_token': ACCESS_TOKEN
                }
                publish_response = requests.post(publish_url, data=publish_payload)
                publish_response.raise_for_status()
                logging.info(f"Successfully published media: {media_id}")
                return publish_response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2)  # リトライ前に待機
    logging.error("All attempts to upload media failed.")
    return None

# アップロードをスケジュールする関数
def schedule_upload(media_url, caption, time):
    schedule.every().day.at(time).do(upload_media, media_url, caption)
    while True:
        schedule.run_pending()
        time.sleep(1)

# コマンドライン引数を解析する関数
def parse_arguments():
    parser = argparse.ArgumentParser(description='Instagram Feed Post Automation')
    parser.add_argument('--media_url', type=str, help='URL of the media to post', required=True)
    parser.add_argument('--caption', type=str, help='Caption for the media', required=True)
    parser.add_argument('--schedule_time', type=str, help='Time to schedule the post (HH:MM)', required=True)
    return parser.parse_args()

# スクリプトを実行するメイン関数
def main():
    args = parse_arguments()
    schedule_upload(args.media_url, args.caption, args.schedule_time)

if __name__ == '__main__':
    main() 