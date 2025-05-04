# Pattern Generator 環境構築手順書

## 1. 概要
Pattern Generatorアプリケーションを実行するための環境構築手順をまとめています。

## 2. 前提条件
- Anaconda3がインストールされていること
- Windows 10以上の環境であること

## 3. 環境構築手順

### 3.1. Conda環境の作成
```bash
# 新しい環境を作成（Python 3.11を使用）
conda create -n pattern_generator python=3.11
conda activate pattern_generator
```

### 3.2. Fletパッケージのインストール
```bash
# Flet関連パッケージをインストール（バージョン0.26.0を指定）
pip install flet-cli==0.26.0  # flet 0.26.0も同時にインストールされます
pip install flet-desktop==0.26.0
pip install flet-web==0.26.0
```

### 3.3. 必要なパッケージのインストール
```bash
# conda-forgeチャンネルを使用して必要なパッケージをインストール
conda install pandas matplotlib numpy libm2k -c conda-forge
```

このコマンドで以下のパッケージとその依存関係がインストールされます：
- pandas
- matplotlib
- numpy
- libm2k
- その他の依存パッケージ（qt, mkl等）

## 4. ディレクトリ構造の準備
アプリケーションの実行には以下のディレクトリ構造が必要です：

```
project_directory/
├── pattern_generator/        # アプリケーションルート（app root）
│   ├── pattern_generator.py  # メインアプリケーション
│   ├── chart_func.py         # チャート関連の関数
│   ├── edit_operations.py    # 編集操作関連の関数
│   ├── export_csv.py         # CSVエクスポート関連の関数
│   ├── file_operations.py    # ファイル操作関連の関数
│   ├── m2k_digital.py        # ADALM2000デバイス制御関連の関数
│   └── view_operations.py    # ビュー操作関連の関数
├── pkl_files/                # データルート（data root）の一部
├── csv_files/                # データルート（data root）の一部
└── app_info.json             # アプリケーション設定ファイル
```

### 4.1. ディレクトリ構造の説明
このプロジェクトでは、アプリケーションとデータを明確に分離する設計を採用しています：

- **アプリケーションルート（app root）**
  - `pattern_generator/`ディレクトリがアプリケーションルートとなります
  - アプリケーションの実行に必要なすべてのPythonプログラムが格納されます
  - メインプログラム（`pattern_generator.py`）と同じ名前を持つディレクトリです

- **データルート（data root）**
  - `pkl_files/`と`csv_files/`ディレクトリがデータルートとなります
  - アプリケーションがアクセスできる最上位の階層です
  - プログラムはデータルートより上の階層にはアクセスできません

この設計には以下の利点があります：
- コンテナ環境での使用を想定しており、アプリケーションとデータのマウント方法を柔軟に制御できます
- デスクトップアプリとして実行する場合も、シンボリックリンクでデータルートとアプリケーションルートの関係を作成できます
- 同じ構造を持つ複数のプロジェクトを開発することで、複数のアプリケーションを連携するシステムを構築できます

必要なディレクトリを作成：
```bash
mkdir pattern_generator pkl_files csv_files
```

### 4.2. app_info.jsonの作成
`app_info.json`はADALM2000デバイスの接続設定を格納するファイルです。以下の内容で作成してください：

```json
{
    "devices": {
        "m2k": {
            "target": ["192.168.2.1"]
        }
    }
}
```

このファイルはプロジェクトディレクトリの直下に配置してください。`target`のIPアドレスは、接続するADALM2000デバイスの実際のIPアドレスに変更してください。

## 5. 動作確認
```bash
cd pattern_generator
python pattern_generator.py
```

正常に起動すると以下のメッセージが表示されます：
```bash
Error loading settings: [Errno 2] No such file or directory: '../app_info.json'
チャンネルリストが空です。空のチャートを返します。
```
※これは初回起動時の正常なメッセージです。

## 6. 注意事項
- Fletのバージョンは0.26.0を使用します（`Colors`属性の互換性のため）
- パッケージのインストールはconda-forgeチャンネルを使用してください
- `pkl_files`と`csv_files`ディレクトリは自動では作成されないため、手動で作成が必要です
- `app_info.json`はリポジトリには含めず、ローカル環境で作成してください
- すべてのPythonファイルは`pattern_generator`ディレクトリに配置する必要があります
- アプリケーションはデータルートより上の階層にはアクセスできません

## 7. トラブルシューティング
- モジュールが見つからないエラーが発生した場合は、該当するパッケージを個別にインストールしてください
- パス関連のエラーが発生した場合は、必要なディレクトリ構造が正しく作成されているか確認してください
- ファイル操作で権限エラーが発生した場合は、ディレクトリのパーミッションを確認してください
- ADALM2000デバイスに接続できない場合は、`app_info.json`のIPアドレスが正しいか確認してください
- 必要なPythonファイルが`pattern_generator`ディレクトリに存在するか確認してください
- データアクセスエラーが発生した場合は、データルートのディレクトリ構造を確認してください

## 8. 参考情報
- Flet公式ドキュメント: https://flet.dev/
- Conda-forge: https://conda-forge.org/
- Libm2k documentation: https://analogdevicesinc.github.io/libm2k/

## 9. 更新履歴
- 2024-03-27: 初版作成
- 2024-03-27: Fletパッケージのインストール手順を修正
- 2024-05-03: app_info.jsonの設定内容を追加
- 2024-05-04: ディレクトリ構造を正しい構成に修正
- 2024-05-04: アプリケーションルートとデータルートの概念と目的について説明を追加