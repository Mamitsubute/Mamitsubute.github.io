#!/bin/bash -e
# (-eで、コマンドがエラーになった行で処理を終了させる)

# magicpod-apiクライアントの最新版を現在のディレクトリにダウンロード・解凍
# セキュリティのため、MAGICPOD_API_TOKENはGitHubの環境変数で設定
OS=mac 　# Windowsマシン上でのビルドの場合はwindows、Linuxはlinuxを指定
FILENAME=magicpod-api-client 　# 任意のファイル名
curl -L "https://app.magicpod.com/api/v1.0/magicpod-clients/api/${OS}/latest/" -H "Authorization: Token ${MAGICPOD_API_TOKEN}" --output ${FILENAME}.zip
unzip -q ${FILENAME}.zip

# MagicPodで使う各種環境変数を設定
export MAGICPOD_ORGANIZATION=MagicPod-ishii
export MAGICPOD_PROJECT=testrail

# 一括実行設定番号を使ってテスト一括実行
TEST_SETTING_NUMBER=1
./magicpod-api-client batch-run -S ${TEST_SETTING_NUMBER}