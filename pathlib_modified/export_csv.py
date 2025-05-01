import csv
import datetime
import shutil
import flet as ft
import pandas as pd
from pathlib import Path
from typing import Callable, Dict
import math
from fractions import Fraction
from io import StringIO
# グローバル変数
current_dir = Path("../csv_files")  # resolveを削除
current_file = None
directory_dropdown = None
filename_dropdown = None
save_button = None

def update_current_dir(page: ft.Page, new_dir: str):
    """ディレクトリを更新し、関連するUIコンポーネントを更新する"""
    global current_dir, directory_dropdown, filename_dropdown
    base_dir = Path("../csv_files")
    
    print(f"\nDebug - update_current_dir:")
    print(f"new_dir selected: {new_dir}")
    
    try:
        new_path = Path(new_dir)
        # パスの正規化
        if base_dir.name in new_path.parts:
            parts_after_base = new_path.parts[new_path.parts.index(base_dir.name)+1:]
            current_dir = base_dir.joinpath(*parts_after_base)
        else:
            current_dir = new_path
        
        print(f"Current directory updated to: {current_dir.as_posix()}")
        
        # UIの更新
        if directory_dropdown:
            directories = get_directory_hierarchy(str(base_dir), str(current_dir))
            directory_dropdown.options = [ft.dropdown.Option(text=dir) for dir in directories]
            directory_dropdown.value = str(current_dir)
            directory_dropdown.label = str(current_dir)
        
        # ファイル一覧の更新
        if filename_dropdown and current_dir.exists():
            files = [f.name for f in current_dir.iterdir() if f.is_file() and f.suffix == '.csv']
            print(f"CSV files found: {files}")
            filename_dropdown.options = [ft.dropdown.Option(text=file) for file in files]
            filename_dropdown.value = None
            filename_dropdown.update()
        
        page.update()
        
    except Exception as e:
        print(f"Error in update_current_dir: {e}")

def get_directory_hierarchy(base_dir: str, target_dir: str) -> list:
    base_path = Path(base_dir).resolve()  # 絶対パスに変換
    target_path = Path(target_dir).resolve()  # 絶対パスに変換
    
    directories = []
    current_path = target_path
    
    # base_pathに到達するまでの階層を取得
    while current_path != base_path and base_path in current_path.parents:
        directories.append(str(current_path))
        current_path = current_path.parent
    
    directories.append(str(base_path))
    directories.reverse()
    
    # サブディレクトリを追加（存在する場合のみ）
    if target_path.exists() and target_path.is_dir():
        sub_directories = [str(d) for d in target_path.iterdir() if d.is_dir()]
        directories.extend(sub_directories)
    
    return directories

def export_csv(page: ft.Page, dataframes: Dict[str, pd.DataFrame], directory: str, filename: str, sample_rate: int):
    directory_path = Path(directory)
    if not directory_path.exists():
        directory_path.mkdir(parents=True)
        directory_path.chmod(0o777)  # resolveを削除
    
    full_path = directory_path / filename
    export_to_csv(dataframes, full_path.as_posix(), format_type='scopy', sample_rate=sample_rate)
    
    snackbar = ft.SnackBar(content=ft.Text(f"CSV file exported to: {full_path.as_posix()}"), open=True)
    print("export_csv: CSV file exported to: ", full_path.as_posix())
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
    elif (current_dir / directory_textfield.value / f"{filename_textfield.value}.csv").exists():
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
        full_path = (current_dir / directory_textfield.value / f"{filename_textfield.value}.csv").as_posix()
        export_csv(page, dataframes, str(Path(current_dir) / directory_textfield.value), full_path.split('/')[-1], sample_rate)
        current_file = full_path
        if on_export_callback:
            on_export_callback()
        page.update()
        close_dialog(page)

def export_csv_dialog(page: ft.Page, dataframes: Dict[str, pd.DataFrame]):
    global directory_dropdown, filename_dropdown
    root_dir = Path("../csv_files")
    directories = get_directory_hierarchy(str(root_dir), str(current_dir))
    
    # directory_dropdownの初期化
    directory_dropdown = ft.Dropdown(
        label=str(current_dir),
        options=[ft.dropdown.Option(text=dir) for dir in directories],
        on_change=lambda e: update_current_dir(page, (Path(current_dir) / e.control.value).as_posix()),
        hint_text=str(current_dir),
    )
    
    main_dialog = None  # メインダイアログの参照を保持
    
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
        on_click=lambda e: perform_export(directory_textfield, filename_textfield, sample_rate_textfield, page, dataframes, None)
    )
    new_directory_button = ft.ElevatedButton(text="New Directory", on_click=lambda e: new_directory(page))
    def new_directory(page):
        if new_directory_button.text == "New Directory":
            new_directory_button.text = "Cancel"
            directory_textfield.visible = True
        else:
            new_directory_button.text = "New Directory"
            directory_textfield.visible = False
        new_directory_button.update()
        directory_textfield.update()
    
    main_dialog = ft.AlertDialog(
        title=ft.Text("Export CSV"),
        content=ft.Column([
            directory_dropdown,  # ここでdirectory_dropdownが使用される
            new_directory_button,
            directory_textfield,
            filename_textfield,
            sample_rate_textfield
        ], spacing=10),
        actions=[
            save_button,
            ft.TextButton("Cancel", on_click=lambda e: close_dialog(page))
        ],
        actions_alignment="end",
        modal=False
    )
    
    page.overlay.append(main_dialog)
    main_dialog.open = True
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
    directory_path = Path(directory).resolve()
    files = [f.name for f in directory_path.iterdir() if f.is_file() and f.suffix == '.csv']
    filename_dropdown.options = [ft.dropdown.Option(text=file) for file in files]

def delete_csv_dialog(page: ft.Page):
    global directory_dropdown, filename_dropdown, current_dir
    root_dir = Path("../csv_files")
    directories = get_directory_hierarchy(str(root_dir), str(current_dir))
    
    print("\nDebug - delete_csv_dialog:")
    print(f"current_dir: {current_dir}")
    print(f"available directories: {directories}")
    
    directory_dropdown = ft.Dropdown(
        label=str(current_dir),
        options=[ft.dropdown.Option(text=dir) for dir in directories],
        on_change=lambda e: update_current_dir(page, e.control.value),
        hint_text=str(current_dir),
    )
    filename_dropdown = ft.Dropdown(
        label="Filename",
        options=[],
        hint_text="Select a file to delete",
    )
    
    main_dialog = None  # メインダイアログの参照を保持

    def on_delete_click(e):
        selected_dir = directory_dropdown.value
        selected_file = filename_dropdown.value

        if selected_dir is None:
            page.add(ft.SnackBar(content=ft.Text("Select a directory to delete")))
            return

        delete_path = Path(current_dir)
        if selected_file:
            delete_path = delete_path / selected_file

        if delete_path.absolute() == root_dir.absolute():
            page.add(ft.SnackBar(content=ft.Text("Cannot delete the root directory")))
            return

        if selected_file:
            if delete_path.is_file():
                confirmation_message = f"Delete file {delete_path.as_posix()}?"
            else:
                page.add(ft.SnackBar(content=ft.Text(f"Selected file {delete_path.as_posix()} does not exist")))
                return
        else:
            if delete_path.is_dir():
                confirmation_message = f"Delete directory {delete_path.as_posix()} and its contents?"
            else:
                page.add(ft.SnackBar(content=ft.Text(f"Selected directory {delete_path.as_posix()} does not exist")))
                return
            
        def confirm_delete(e):
            if e.control.text == "Yes":
                if selected_file:
                    try:
                        delete_path.unlink()
                        page.add(ft.SnackBar(content=ft.Text(f"File {delete_path.as_posix()} has been deleted")))
                        print("delete_dialog: File deleted: ", delete_path)
                    except FileNotFoundError:
                        page.add(ft.SnackBar(content=ft.Text(f"File {delete_path.as_posix()} not found")))
                        print("delete_dialog: File not found: ", delete_path)
                else:
                    try:
                        shutil.rmtree(delete_path)
                        page.add(ft.SnackBar(content=ft.Text(f"Directory {delete_path.as_posix()} and its contents have been deleted")))
                        print("delete_dialog: Directory deleted: ", delete_path)
                    except FileNotFoundError:
                        page.add(ft.SnackBar(content=ft.Text(f"Directory {delete_path.as_posix()} not found")))
                        print("delete_dialog: Directory not found: ", delete_path)
                update_current_dir(page, delete_path.parent.as_posix())
                
                # 確認ダイアログを閉じる
                if page.overlay and len(page.overlay) > 0:
                    confirmation_dialog = page.overlay.pop()
                    confirmation_dialog.open = False
                
                # メインダイアログを閉じる
                if main_dialog in page.overlay:
                    page.overlay.remove(main_dialog)
                    main_dialog.open = False
                
                page.update()
            else:
                # キャンセルの場合は確認ダイアログのみを閉じる
                if page.overlay and len(page.overlay) > 0:
                    confirmation_dialog = page.overlay.pop()
                    confirmation_dialog.open = False
                    page.update()

        confirmation_dialog = ft.AlertDialog(
            title=ft.Text("Delete Confirmation"),
            content=ft.Text(confirmation_message),
            actions=[
                ft.TextButton("Yes", on_click=confirm_delete),
                ft.TextButton("Cancel", on_click=confirm_delete),  # Cancelもconfirm_deleteを使用
            ],
            actions_alignment="end",
        )
        
        page.overlay.append(confirmation_dialog)
        confirmation_dialog.open = True
        page.update()

    main_dialog = ft.AlertDialog(
        title=ft.Text("Delete CSV"),
        content=ft.Column([directory_dropdown, filename_dropdown]),
        actions=[
            ft.ElevatedButton("Delete", on_click=on_delete_click),
            ft.TextButton("Cancel", on_click=lambda e: close_dialog(page))
        ],
        actions_alignment="end",
    )
    
    page.overlay.append(main_dialog)
    main_dialog.open = True
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
    csv_content = export_to_string_io(dataframes, format_type, sample_rate)
    
    file_path = Path(file_path)
    with open(file_path, 'w', newline='') as csvfile:
        csvfile.write(csv_content.getvalue())
    
    file_path.chmod(0o666)  # resolveを削除
    print(f"Data exported to {file_path.as_posix()} in {format_type} format.")

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