import os
import re
import requests
import sys
import json
import inspect
import subprocess
import zipfile
import shutil

class MagicpodApiClientWrapper:
    def __init__(self, secret_api_token, org_name, project_name, cmd_path, tmp_dir):
        self._secret_api_token = secret_api_token
        self._org_name = org_name
        self._project_name = project_name
        self._cmd_path = cmd_path
        self._tmp_dir = tmp_dir

    def _run_command(self, command):
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,  # テキストモードで出力を取得
                check=True  # エラーコードが非ゼロの場合に例外を発生させる
            )
            return result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return None, f"エラー: コマンドがエラーコード {e.returncode} で終了しました。"
        except FileNotFoundError:
            return None, "エラー: コマンドが見つかりませんでした。"

    def batch_run(self, setting):
        command = [
            self._cmd_path,
            "batch-run",
            "-t", self._secret_api_token,
            "-o", self._org_name,
            "-p", self._project_name,
            "-S", str(setting)
        ]
        stdout, stderr = self._run_command(command=command)
        print(command)
        print(stdout)
        print(stderr)
        return stdout

    def get_latest_batch_number(self, test_setting_name):
        latest_number = 0
        url = f"https://magic-pod.com/api/v1.0/{self._org_name}/{self._project_name}/batch-runs/"
        headers = {
            "Authorization": f"Token {self._secret_api_token}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
        for run in result['batch_runs']:
            if run['test_setting_name'] == test_setting_name:
                latest_number = run['batch_run_number']
                break
        return latest_number

    def get_batch_run(self, batch_run_number):
        url = f"https://magic-pod.com/api/v1.0/{self._org_name}/{self._project_name}/batch-run/{batch_run_number}"
        headers = {
            "Authorization": f"Token {self._secret_api_token}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            return result

    def get_screenshots(self, batch_run_number):
        temp_directory = self._tmp_dir + MAGICPOD_ORGANIZATION_NAME + "_" + MAGICPOD_PROJECT_NAME + "_" + str(batch_run_number)
        temp_zipfile = temp_directory + "/screenshots_" + str(batch_run_number) + ".zip"
        if not os.path.exists(temp_directory):
            os.makedirs(temp_directory)
        command = [
            self._cmd_path,
            "get-screenshots",
            "-t", self._secret_api_token,
            "-o", self._org_name,
            "-p", self._project_name,
            "-b", str(batch_run_number),
            "-d", temp_zipfile
        ]
        stdout, stderr = self._run_command(command)
        filelist = []
        with zipfile.ZipFile(temp_zipfile) as zf:
            filelist = zf.namelist()
            zf.extractall(temp_directory)
        return filelist

    def get_max_numbered_files(self, file_paths):
        # 各親フォルダごとに最も数字が大きいファイルのパスを格納するリスト
        max_numbered_file_paths = []
        # 親フォルダごとにファイルをグループ化
        grouped_files = {}
        for file_path in file_paths:
            folder_name = os.path.dirname(file_path)
            base_name = os.path.basename(file_path)
            # パスを正規化
            folder_name = os.path.normpath(folder_name)
            if folder_name not in grouped_files:
                grouped_files[folder_name] = []
            grouped_files[folder_name].append(base_name)
        # 各親フォルダ内のファイルで最も数字が大きいファイルを選択
        for folder_name, file_names in grouped_files.items():
            max_file = max(file_names, key=lambda x: int(os.path.splitext(x)[0]))
            max_numbered_file_path = os.path.join(folder_name, max_file)
            max_numbered_file_paths.append(max_numbered_file_path)
        return max_numbered_file_paths

    def update_testresults(self, json_data, file_paths):
        # ファイルパスからテストケースの情報を抽出し、辞書に格納
        screenshot_array = []
        for file_path in file_paths:
            # 正規表現を使用して数字と名前を抽出
            match = re.search(r'(\d+)_(.+?)[/\\]', file_path)  # / または \ にマッチ
            if match:
                screenshot = {}
                screenshot['number'] = match.group(1)
                screenshot['name'] = match.group(2)
                # パスを正規化
                base_dir = self._tmp_dir + ORGANIZATION_NAME + "_" + PROJECT_NAME + "_" + str(json_data['batch_run_number'])
                screenshot['screenshot'] = os.path.normpath(base_dir + "/" + file_path)
                screenshot_array.append(screenshot)
        # 2つ目のJSONデータを更新
        details = json_data.get("test_cases", {}).get("details", [])
        for result in details[0]['results']:
            number = result['test_case']['number']
            name   = result['test_case']['name'].replace(' ', '_')
            for screenshot in screenshot_array:
                if screenshot['number'] == str(number) and screenshot['name'] == name:
                    result["screenshot"] = screenshot['screenshot']
        return json_data

def run_magicpod(test_setting, output_filename, magicpod_api_client_path, temp_dir):
    if not temp_dir.endswith('/'):
        temp_dir += '/'
    MAGICPOD_API_TOKEN = os.environ.get("MAGICPOD_API_TOKEN")
    MAGICPOD_ORGANIZATION_NAME = os.environ.get("MAGICPOD_ORGANIZATION_NAME")
    MAGICPOD_PROJECT_NAME = os.environ.get("MAGICPOD_PROJECT_NAME")
    MAGICPOD_TEST_SETTING_LIST = os.environ.get("MAGICPOD_TEST_SETTING_LIST")
    client = MagicpodApiClientWrapper(secret_api_token=MAGICPOD_API_TOKEN, org_name=MAGICPOD_ORGANIZATION_NAME, project_name=MAGICPOD_PROJECT_NAME, cmd_path=magicpod_api_client_path, tmp_dir=temp_dir)
    # MagicPodテスト実行
    client.batch_run(test_setting)
    # テスト結果取得
    # test_setting_name = next((item['name'] for item in MAGICPOD_TEST_SETTING_LIST if item['id'] == test_setting), None)
    # latest_batch_number = client.get_latest_batch_number(test_setting_name)
    # test_results = client.get_batch_run(latest_batch_number)
    # screenshots = client.get_screenshots(latest_batch_number)
    # テスト結果加工
    # last_screenshots = client.get_max_numbered_files(screenshots)
    # magicpod_result = client.update_testresults(test_results, last_screenshots)
    # 結果をファイルに保存
    # with open(output_filename, "w", encoding='utf-8') as file:
    #     file.write(json.dumps(magicpod_result))

run_magicpod(test_setting=1, output_filename='./magicpod_result',magicpod_api_client_path='./magicpod-api-client', temp_dir='./')