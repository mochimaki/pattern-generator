import csv
import datetime
import os
import shutil
import flet as ft
import pandas as pd
from typing import Callable, Dict
import math
from fractions import Fraction
from io import StringIO
import base64
from pathlib import Path
# グローバル変数
current_dir = Path("../csv_files")  # 相対パスをPathオブジェクトとして保持
current_file = None
directory_dropdown = None
filename_dropdown = None
save_button = None

def update_current_dir(page: ft.Page, new_dir: str):
    """ディレクトリを更新し、関連するUIコンポーネントを更新する"""
    global current_dir, directory_dropdown, filename_dropdown
    base_dir = Path("../csv_files")
    
    try:
        # 新しいパスをPathオブジェクトに変換
        new_path = Path(new_dir)
        
        # パスが有効かチェック
        if not str(new_path).startswith(str(base_dir)):
            print(f"Invalid path: {new_path} does not start with {base_dir}")
            return
            
        # パスが実在するディレクトリかチェック
        if not new_path.exists() or not new_path.is_dir():
            print(f"Invalid path: {new_path} does not exist or is not a directory")
            return
            
        current_dir = new_path
        print(f"Current directory updated to: {current_dir}")
        
        # UIの更新
        if directory_dropdown:
            directories = get_directory_hierarchy(str(base_dir), str(current_dir))
            directory_dropdown.options = [ft.DropdownOption(text=str(dir)) for dir in directories]
            directory_dropdown.value = str(current_dir)
            directory_dropdown.label = str(current_dir)
        
        # ファイル一覧の更新
        if filename_dropdown and current_dir.exists():
            files = [f.name for f in current_dir.iterdir() if f.is_file() and f.suffix == '.csv']
            filename_dropdown.options = [ft.DropdownOption(text=file) for file in files]
            filename_dropdown.value = None
            filename_dropdown.update()
        
        page.update()
        
    except Exception as e:
        print(f"Error in update_current_dir: {e}")
        # エラーの詳細をログに出力
        import traceback
        traceback.print_exc()

def get_directory_hierarchy(base_dir: str, target_dir: str) -> list:
    # パスをPlatform非依存の形式に正規化
    def normalize_path(p):
        return str(Path(p)).replace('\\', '/')
    
    base_path = Path(base_dir)
    target_path = Path(target_dir)
    directories = []
    
    # ベースディレクトリまでのパスを取得
    current = target_path
    base_str = normalize_path(base_path)
    while normalize_path(current).startswith(base_str):
        directories.append(str(current))
        if normalize_path(current) == base_str:
            break
        current = current.parent
    
    directories.reverse()
    
    # サブディレクトリを追加
    if target_path.exists():
        for d in target_path.iterdir():
            if d.is_dir():
                # 相対パスのまま追加
                directories.append(str(d))
    
    # パスが../csv_filesで始まり、中間に..を含まないものだけを保持
    filtered_directories = []
    for d in directories:
        normalized_path = normalize_path(d)
        if normalized_path.startswith("../csv_files/"):
            parts = Path(normalized_path).parts
            if '..' not in parts[2:]:  # '../csv_files' の後に '..' が含まれていないことを確認
                filtered_directories.append(d)
        elif normalized_path == "../csv_files":
            filtered_directories.append(d)
    
    # 重複を削除し、ソート（プラットフォーム固有のパス区切り文字を保持）
    filtered_directories = sorted(set(filtered_directories))
    
    return filtered_directories

def export_csv(page: ft.Page, dataframes: Dict[str, pd.DataFrame], directory: str, filename: str, sample_rate: int):
    # 文字列をPathオブジェクトに変換
    dir_path = Path(directory)
    if not dir_path.exists():
        dir_path.mkdir(parents=True)
        dir_path.chmod(0o777)
    
    full_path = dir_path / filename
    
    # StringIOオブジェクトを取得してファイルに書き込み
    export_to_csv(dataframes, str(full_path), format_type='scopy', sample_rate=sample_rate)
    
    # ファイルのパーミッション設定
    full_path.chmod(0o666)
    
    snackbar = ft.SnackBar(content=ft.Text(f"CSV file exported to: {full_path}"), open=True)
    print("export_csv: CSV file exported to: ", full_path)
    page.add(snackbar)
    close_dialog(page)

def perform_export(directory_textfield: ft.TextField, filename_textfield: ft.TextField, sample_rate_textfield: ft.TextField, page: ft.Page, dataframes: Dict[str, pd.DataFrame], on_export_callback: Callable = None):
    global current_dir, current_file
    invalid_chars = set('.<>:"/\\|?*')
    invalid_chars_directory = set(c for c in invalid_chars if c in directory_textfield.value)
    invalid_chars_filename = set(c for c in invalid_chars if c in filename_textfield.value)
    error_message = ""
    
    # ディレクトリ名とファイル名のバリデーション
    if invalid_chars_directory:
        error_message = f"Invalid characters in directory name: [ {', '.join(invalid_chars_directory)} ]"
        directory_textfield.error_text = error_message
    else:
        directory_textfield.error_text = ""
    if invalid_chars_filename:
        error_message = f"Invalid characters in filename: [ {', '.join(invalid_chars_filename)} ]"
        filename_textfield.error_text = error_message
    else:
        filename_textfield.error_text = ""
    if directory_textfield.visible:
        if not directory_textfield.value:
            error_message = "Directory name is required"
            directory_textfield.error_text = error_message
        elif (current_dir / directory_textfield.value).exists():
            error_message = "Directory already exists"
            directory_textfield.error_text = error_message
        else:
            directory_textfield.error_text = ""
    else:
        directory_textfield.value = ""
    if not filename_textfield.value:
        error_message = "Filename is required"
        filename_textfield.error_text = error_message
    elif (current_dir / directory_textfield.value / (filename_textfield.value + ".csv")).exists():
        error_message = "File already exists"
        filename_textfield.error_text = error_message
    else:
        filename_textfield.error_text = ""
    # サンプリングレートのバリデーション
    try:
        sample_rate = int(sample_rate_textfield.value)
        if sample_rate <= 0:
            error_message = "Sample rate must be a positive integer"
            sample_rate_textfield.error_text = error_message
        else:
            sample_rate_textfield.error_text = ""
    except ValueError:
        error_message = "Sample rate must be a valid integer"
        sample_rate_textfield.error_text = error_message
    
    if error_message:
        snackbar = ft.SnackBar(content=ft.Text(error_message), open=True)
        page.add(snackbar)
    else:
        save_path = current_dir / directory_textfield.value / (filename_textfield.value + ".csv")
        export_csv(page, dataframes, str(save_path.parent), save_path.name, sample_rate)
        current_file = save_path
        if on_export_callback:
            on_export_callback()
        page.update()
        close_dialog(page)

def export_csv_dialog(page: ft.Page, dataframes: Dict[str, pd.DataFrame], on_export_callback: Callable = None):
    global directory_dropdown, filename_dropdown, save_button
    base_dir = Path("../csv_files")
    
    print("\nDebug - export_csv_dialog:")
    print(f"current_dir: {current_dir}")
    
    directory_textfield = ft.TextField(
        label="New Directory Name", 
        hint_text="New Directory Name", 
        visible=False
    )
    filename_textfield = ft.TextField(
        label="Enter filename", 
        hint_text="e.g., my_data"
    )
    sample_rate_textfield = ft.TextField(
        label="Sample Rate (Hz)", 
        hint_text="e.g., 1000000", 
        value=str(calculate_optimal_sample_rate(dataframes))
    )
    save_button = ft.ElevatedButton(
        text="Export", 
        on_click=lambda e: perform_export(directory_textfield, filename_textfield, sample_rate_textfield, page, dataframes, on_export_callback)
    )
    
    # ディレクトリ階層を取得
    directories = get_directory_hierarchy(str(base_dir), str(current_dir))
    print(f"available directories: {directories}")
    
    directory_dropdown = ft.Dropdown(
        label=str(current_dir),
        options=[ft.DropdownOption(text=dir) for dir in directories],
        on_change=lambda e: update_current_dir(page, e.control.value),  # 直接値を渡す
        hint_text=str(current_dir),
    )
    
    new_directory_button = ft.ElevatedButton(
        text="New Directory", 
        on_click=lambda e: new_directory(page)
    )
    
    def new_directory(page):
        if new_directory_button.text == "New Directory":
            new_directory_button.text = "Cancel"
            directory_textfield.visible = True
        else:
            new_directory_button.text = "New Directory"
            directory_textfield.visible = False
        new_directory_button.update()
        directory_textfield.update()
    
    dialog = ft.AlertDialog(
        title=ft.Text("Export CSV"),
        content=ft.Column([
            directory_dropdown, 
            new_directory_button, 
            directory_textfield, 
            filename_textfield, 
            sample_rate_textfield
        ], spacing=10),
        actions=[
            save_button,
            ft.TextButton(text="Cancel", on_click=lambda e: close_dialog(page))
        ],
        actions_alignment="end",
        modal=False
    )
    
    page.overlay.append(dialog)
    dialog.open = True
    page.update()

def close_dialog(page):
    global directory_dropdown, filename_dropdown
    directory_dropdown = None
    filename_dropdown = None
    if page.overlay and len(page.overlay) > 0:
        dialog = page.overlay.pop()
        dialog.open = False
        page.update()

def update_filename_options(directory, filename_dropdown):
    dir_path = Path(directory)
    files = [f.name for f in dir_path.iterdir() if f.is_file() and f.suffix == '.csv']
    filename_dropdown.options = [ft.DropdownOption(text=file) for file in files]

def delete_csv_dialog(page: ft.Page):
    global directory_dropdown, filename_dropdown, current_dir
    root_dir = Path("../csv_files")
    
    # current_dirが文字列の場合はPathオブジェクトに変換
    if isinstance(current_dir, str):
        current_dir = Path(current_dir)
    
    directories = get_directory_hierarchy(str(root_dir), str(current_dir))
    
    def update_filename_options():
        if isinstance(current_dir, str):
            dir_path = Path(current_dir)
        else:
            dir_path = current_dir
            
        if dir_path.exists():
            files = [f.name for f in dir_path.iterdir() if f.is_file() and f.suffix == '.csv']
            filename_dropdown.options = [ft.DropdownOption(text=file) for file in files]
            filename_dropdown.value = None
    
    def on_delete_click(e):
        selected_dir = directory_dropdown.value
        selected_file = filename_dropdown.value

        if not selected_dir:
            page.add(ft.SnackBar(content=ft.Text("Select a directory")))
            return

        delete_path = Path(selected_dir)
        if selected_file:
            delete_path = delete_path / selected_file

        # ルートディレクトリの削除を防ぐ
        if str(delete_path).startswith(str(root_dir)):
            if delete_path.resolve() == root_dir.resolve():
                page.add(ft.SnackBar(content=ft.Text("Cannot delete the root directory")))
                return

            if selected_file:
                if delete_path.is_file():
                    confirmation_message = f"Delete file {delete_path}?"
                else:
                    page.add(ft.SnackBar(content=ft.Text("Selected file does not exist")))
                    return
            else:
                if delete_path.is_dir():
                    confirmation_message = f"Delete directory {delete_path} and its contents?"
                else:
                    page.add(ft.SnackBar(content=ft.Text("Selected directory does not exist")))
                    return
                
            def confirm_delete(e):
                if e.control.text == "Yes":
                    try:
                        if selected_file:
                            try:
                                delete_path.unlink(missing_ok=True)  # ファイルが存在しない場合もエラーを発生させない
                                page.add(ft.SnackBar(content=ft.Text(f"File {delete_path} has been deleted")))
                            except IsADirectoryError:
                                page.add(ft.SnackBar(content=ft.Text(f"Error: {delete_path} is a directory")))
                                return
                        else:
                            try:
                                shutil.rmtree(delete_path)  # ディレクトリの削除はshutil.rmtreeを使用
                                page.add(ft.SnackBar(content=ft.Text(f"Directory {delete_path} and its contents have been deleted")))
                            except PermissionError:
                                page.add(ft.SnackBar(content=ft.Text(f"Error: Permission denied to delete {delete_path}")))
                                return
                        
                        # 親ディレクトリに移動
                        parent_dir = delete_path.parent
                        update_current_dir(page, str(parent_dir))
                        update_filename_options()
                        filename_dropdown.update()
                    except Exception as e:
                        page.add(ft.SnackBar(content=ft.Text(f"Error during deletion: {str(e)}")))
                    close_dialog(page)

            confirmation_dialog = ft.AlertDialog(
                title=ft.Text("Delete Confirmation"),
                content=ft.Text(confirmation_message),
                actions=[
                    ft.TextButton("Yes", on_click=confirm_delete),
                    ft.TextButton("Cancel", on_click=lambda _: close_dialog(page)),
                ],
                actions_alignment="end",
            )
            
            page.overlay.append(confirmation_dialog)
            confirmation_dialog.open = True
            page.update()
        else:
            page.add(ft.SnackBar(content=ft.Text("Invalid path selected")))
    
    directory_dropdown = ft.Dropdown(
        label=str(current_dir),
        options=[ft.DropdownOption(text=str(dir)) for dir in directories],
        on_change=lambda e: update_current_dir(page, e.control.value),
        hint_text=str(current_dir),
        value=str(current_dir)
    )
    
    filename_dropdown = ft.Dropdown(
        label="Filename",
        options=[],
        hint_text="Select a file to delete",
    )

    dialog = ft.AlertDialog(
        title=ft.Text("Delete CSV"),
        content=ft.Column([directory_dropdown, filename_dropdown]),
        actions=[
            ft.ElevatedButton("Delete", on_click=on_delete_click),
            ft.TextButton("Cancel", on_click=lambda _: close_dialog(page))
        ],
        actions_alignment="end",
    )
    
    page.overlay.append(dialog)
    dialog.open = True
    
    # ダイアログをページに追加してから更新
    update_filename_options()
    page.update()

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def lcm(a, b):
    return abs(a * b) // math.gcd(a, b)

def calculate_optimal_sample_rate(dataframes: Dict[str, pd.DataFrame]):
    time_factors = {'sec.': 1, 'msec.': 1e-3, 'microsec.': 1e-6}
    all_durations = []
    
    for df in dataframes.values():
        for duration, unit in zip(df['duration'], df['unit']):
            all_durations.append(Fraction(duration * time_factors[unit]).limit_denominator())
    
    # 重複を削除し、ソートする
    unique_durations = sorted(set(all_durations))
    
    # 最大公約数を計算
    gcd_value = unique_durations[0]
    for duration in unique_durations[1:]:
        gcd_value = Fraction(gcd(gcd_value.numerator, duration.numerator), 
                             lcm(gcd_value.denominator, duration.denominator))
    
    # サンプリングレートを計算（最大1,000,000 Hz）
    optimal_rate = int(min(1 / gcd_value, 1000000))
    return max(optimal_rate, 1)  # 最小値を1に設定

def convert_to_seconds(duration, unit):
    if unit == 'sec.':
        return duration
    elif unit == 'msec.':
        return duration / 1000
    elif unit == 'microsec.':
        return duration / 1000000
    else:
        raise ValueError(f"Unknown unit: {unit}")

def calculate_channel_samples(df, sample_rate):
    return sum(int(convert_to_seconds(row['duration'], row['unit']) * sample_rate) for _, row in df.iterrows())

def export_to_csv(dataframes: Dict[str, pd.DataFrame], file_path: str, format_type='scopy', sample_rate=1000000):
    # StringIOオブジェクトを取得
    csv_content = export_to_string_io(dataframes, format_type, sample_rate)
    
    # ファイルに書き込み
    file_path = Path(file_path)
    with open(file_path, 'w', newline='') as csvfile:
        csvfile.write(csv_content.getvalue())
    
    # csvファイルに666パーミッションを設定
    file_path.chmod(0o666)

    print(f"Data exported to {file_path} in {format_type} format.")

def export_to_string_io(dataframes: Dict[str, pd.DataFrame], format_type='scopy', sample_rate=None, cyclic=False):
    if sample_rate is None:
        sample_rate = calculate_optimal_sample_rate(dataframes)
    
    csv_content = StringIO()
    writer = csv.writer(csv_content)
    # サンプル数を計算
    original_total_samples = max(calculate_channel_samples(df, sample_rate) for df in dataframes.values())
    
    # cyclicがTrueの場合はサンプル数が４の倍数になるように調整
    if cyclic == True: # cyclicがTrueの場合
        if original_total_samples % 4 == 0: # original_total_samplesが４の倍数
            pass # 何もしない
        elif original_total_samples % 2 == 0: # original_total_samplesが偶数の場合
            original_total_samples *= 2 # ２をかけて４の倍数とする
            sample_rate *= 2
        else: # original_total_samplesが奇数の場合
            original_total_samples *= 4 # ４をかけて４の倍数とする
            sample_rate *= 4

    # ADALM2000の制約に合わせてtotal_samplesを調整（digital.pyでテストの結果、4以上の４の倍数が適切）
    #total_samples = max(16, ((original_total_samples + 3) // 4) * 4) # 16以上の4の倍数
    #total_samples = max(16, ((original_total_samples + 15) // 16) * 16) # 16以上の16の倍数
    #total_samples = max(8, ((original_total_samples + 3) // 4) * 4) # ８以上の４の倍数
    total_samples = max(4, ((original_total_samples + 3) // 4) * 4) # 4以上の４の倍数
    
    # original_total_samplesが既に4の倍数の場合、4サンプル追加（ゼロ埋め用領域）
    #この処理はすべてのチャネルのdataframeの末尾のstateが'low'になっていない場合に実行する。
    # 空のチャネルは'low'とみなす。
    # cyclicがFalseの場合のみ実行する。
    if total_samples == original_total_samples and cyclic == False and any(df['state'].iloc[-1] != 'low' if not df.empty else False for df in dataframes.values()):
    #if total_samples == original_total_samples and all(df['state'].iloc[-1] != 'low' for df in dataframes.values() if not df.empty): # 空のチャネルの扱いが不適切
    #if total_samples == original_total_samples: # 元の条件式
        total_samples += 4
    
    if format_type == 'scopy':
        # メタデータ（セミコロンで始まる行）
        writer.writerow([';Scopy version', 'your_version_here'])
        writer.writerow([';Exported on', datetime.datetime.now().strftime('%a %b %d/%m/%Y')])
        writer.writerow([';Device', 'M2K'])
        writer.writerow([';Nr of samples', str(total_samples)])  # 調整後のtotal_samplesを使用
        writer.writerow([';Sample rate', str(sample_rate)])
        writer.writerow([';Tool', 'Logic Analyzer'])
        writer.writerow([';Additional Information', ''])
        
        # チャンネルヘッダー
        header = ['Sample'] + [f'Channel {i}' for i in range(len(dataframes))]
        writer.writerow(header)
    
    channel_states = {}
    for channel, df in dataframes.items():
        channel_states[channel] = {
            'iterator': df.iterrows(),
            'current_state': 0,
            'remaining_samples': 0
        }
    # dataframesを元にデータ部分を書き込み
    for sample_index in range(original_total_samples):
        row = [sample_index] if format_type == 'scopy' else []
        for channel in dataframes.keys():
            state = channel_states[channel]
            if state['remaining_samples'] == 0:
                try:
                    _, current_row = next(state['iterator'])
                    state['current_state'] = 1 if current_row['state'] == 'high' else 0
                    duration_seconds = convert_to_seconds(current_row['duration'], current_row['unit'])
                    state['remaining_samples'] = int(duration_seconds * sample_rate)
                except StopIteration:
                    pass  # Keep the last state if we've run out of data
            
            row.append(state['current_state'])
            state['remaining_samples'] = max(0, state['remaining_samples'] - 1)

        writer.writerow(row)

    # ゼロ埋めを追加
    ####### secCycleをTrueにした場合は実行しない（ToDo）
    for sample_index in range(original_total_samples, total_samples):
        row = [sample_index] if format_type == 'scopy' else []
        row.extend([0] * len(dataframes))
        writer.writerow(row)

    csv_content.seek(0)
    return csv_content

# 使用例
# export_to_csv(dataframes, 'output_simple.csv', format_type='simple', sample_rate=1000000)
# export_to_csv(dataframes, 'output_scopy.csv', format_type='scopy', sample_rate=1000000)
def download_csv(e, dataframes):
    print("download_csv function called")
    # 最適なサンプルレートを計算
    optimal_sample_rate = calculate_optimal_sample_rate(dataframes)
    print(f"Optimal sample rate: {optimal_sample_rate}")
    # CSVデータを生成
    csv_content = export_to_string_io(dataframes, format_type='scopy', sample_rate=optimal_sample_rate)
    # Base64エンコードしたCSVデータを作成
    csv_base64 = base64.b64encode(csv_content.getvalue().encode()).decode()
    # ダウンロードリンクを生成
    download_link = f"data:text/csv;base64,{csv_base64}"
    # ダウンロードリンクを開く
    e.page.launch_url(download_link)