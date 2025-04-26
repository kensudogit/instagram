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

# フィード投稿を一括で自動化する関数
# 複数のメディアURLとキャプションを受け取り、順次投稿を行う
# エラーハンドリングとリトライ機能を含む
def bulk_upload_media(media_urls, captions, retries=3):
    for media_url, caption in zip(media_urls, captions):
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
                    break  # 成功した場合は次のメディアに進む
            except requests.exceptions.RequestException as e:
                logging.error(f"Attempt {attempt + 1} failed for media {media_url}: {e}")
                time.sleep(2)  # リトライ前に待機
        else:
            logging.error(f"All attempts to upload media {media_url} failed.")

# ストーリーを一括で自動化する関数
# 複数のメディアURLを受け取り、順次ストーリーとして投稿を行う
# エラーハンドリングとリトライ機能を含む
def bulk_upload_stories(media_urls, retries=3):
    for media_url in media_urls:
        for attempt in range(retries):
            try:
                # ステップ1: ストーリー用メディアをアップロード
                upload_url = f"{INSTAGRAM_GRAPH_API_URL}{USER_ID}/media"
                payload = {
                    'image_url': media_url,
                    'is_story': True,  # ストーリーとして投稿するためのフラグ
                    'access_token': ACCESS_TOKEN
                }
                response = requests.post(upload_url, data=payload)
                response.raise_for_status()  # エラーがある場合は例外を発生
                media_id = response.json().get('id')

                # ステップ2: ストーリーを公開
                if media_id:
                    publish_url = f"{INSTAGRAM_GRAPH_API_URL}{USER_ID}/media_publish"
                    publish_payload = {
                        'creation_id': media_id,
                        'access_token': ACCESS_TOKEN
                    }
                    publish_response = requests.post(publish_url, data=publish_payload)
                    publish_response.raise_for_status()
                    logging.info(f"Successfully published story: {media_id}")
                    break  # 成功した場合は次のメディアに進む
            except requests.exceptions.RequestException as e:
                logging.error(f"Attempt {attempt + 1} failed for story {media_url}: {e}")
                time.sleep(2)  # リトライ前に待機
        else:
            logging.error(f"All attempts to upload story {media_url} failed.")

# DMを一括で送信する関数
# 複数のユーザーIDとメッセージを受け取り、順次DMを送信する
# エラーハンドリングとリトライ機能を含む
def bulk_send_dm(user_ids, message, retries=3):
    for user_id in user_ids:
        for attempt in range(retries):
            try:
                # DM送信用のエンドポイントにリクエストを送信
                dm_url = f"{INSTAGRAM_GRAPH_API_URL}me/messages"
                payload = {
                    'recipient': {'id': user_id},
                    'message': {'text': message},
                    'access_token': ACCESS_TOKEN
                }
                response = requests.post(dm_url, json=payload)
                response.raise_for_status()  # エラーがある場合は例外を発生
                logging.info(f"Successfully sent DM to user: {user_id}")
                break  # 成功した場合は次のユーザーに進む
            except requests.exceptions.RequestException as e:
                logging.error(f"Attempt {attempt + 1} failed for user {user_id}: {e}")
                time.sleep(2)  # リトライ前に待機
        else:
            logging.error(f"All attempts to send DM to user {user_id} failed.")

# ユーザーを一括でフォローする関数
# 複数のユーザーIDを受け取り、順次フォローを行う
# エラーハンドリングとリトライ機能を含む
def bulk_follow_users(user_ids, retries=3):
    for user_id in user_ids:
        for attempt in range(retries):
            try:
                # フォロー用のエンドポイントにリクエストを送信
                follow_url = f"{INSTAGRAM_GRAPH_API_URL}{USER_ID}/following"
                payload = {
                    'user_id': user_id,
                    'access_token': ACCESS_TOKEN
                }
                response = requests.post(follow_url, data=payload)
                response.raise_for_status()  # エラーがある場合は例外を発生
                logging.info(f"Successfully followed user: {user_id}")
                break  # 成功した場合は次のユーザーに進む
            except requests.exceptions.RequestException as e:
                logging.error(f"Attempt {attempt + 1} failed for user {user_id}: {e}")
                time.sleep(2)  # リトライ前に待機
        else:
            logging.error(f"All attempts to follow user {user_id} failed.")

# 投稿に一括で「いいね」を送信する関数
# 複数の投稿IDを受け取り、順次「いいね」を送信する
# エラーハンドリングとリトライ機能を含む
def bulk_like_posts(post_ids, retries=3):
    for post_id in post_ids:
        for attempt in range(retries):
            try:
                # 「いいね」用のエンドポイントにリクエストを送信
                like_url = f"{INSTAGRAM_GRAPH_API_URL}{post_id}/likes"
                payload = {
                    'access_token': ACCESS_TOKEN
                }
                response = requests.post(like_url, data=payload)
                response.raise_for_status()  # エラーがある場合は例外を発生
                logging.info(f"Successfully liked post: {post_id}")
                break  # 成功した場合は次の投稿に進む
            except requests.exceptions.RequestException as e:
                logging.error(f"Attempt {attempt + 1} failed for post {post_id}: {e}")
                time.sleep(2)  # リトライ前に待機
        else:
            logging.error(f"All attempts to like post {post_id} failed.")

# 投稿に一括でコメントを送信する関数
# 複数の投稿IDとコメントを受け取り、順次コメントを送信する
# エラーハンドリングとリトライ機能を含む
def bulk_comment_posts(post_ids, comments, retries=3):
    for post_id, comment in zip(post_ids, comments):
        for attempt in range(retries):
            try:
                # コメント用のエンドポイントにリクエストを送信
                comment_url = f"{INSTAGRAM_GRAPH_API_URL}{post_id}/comments"
                payload = {
                    'message': comment,
                    'access_token': ACCESS_TOKEN
                }
                response = requests.post(comment_url, data=payload)
                response.raise_for_status()  # エラーがある場合は例外を発生
                logging.info(f"Successfully commented on post: {post_id}")
                break  # 成功した場合は次の投稿に進む
            except requests.exceptions.RequestException as e:
                logging.error(f"Attempt {attempt + 1} failed for post {post_id}: {e}")
                time.sleep(2)  # リトライ前に待機
        else:
            logging.error(f"All attempts to comment on post {post_id} failed.")

if __name__ == '__main__':
    main()

media_urls = ['http://example.com/image1.jpg', 'http://example.com/image2.jpg']
captions = ['Caption for image 1', 'Caption for image 2']
bulk_upload_media(media_urls, captions) 