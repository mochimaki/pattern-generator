import os
import pickle
import shutil
import flet as ft
from pathlib import Path

# グローバル変数の宣言
current_dir = Path("../pkl_files")  # 相対パスをPathオブジェクトとして保持
current_file = None
directory_dropdown = None
filename_dropdown = None
save_button = None

def save_dataframes(page, dataframes, directory=None, filename=None):
    global current_file, current_dir
    if filename:
        save_path = Path(directory) if directory else current_dir
        if not save_path.exists():
            save_path.mkdir(parents=True)  # ディレクトリが存在しない場合は作成
            save_path.chmod(0o777)  # ディレクトリには777を設定
        full_path = save_path / filename
        current_file = full_path
        current_dir = save_path
    elif current_file is None:
        # 現在のファイルが設定されていない場合は、save_dialog を呼び出す
        save_dialog(page, dataframes)
        return
    else:
        full_path = current_file

    with open(full_path, 'wb') as f:
        pickle.dump(dataframes, f)
    
    # pklファイルに666パーミッションを設定
    full_path.chmod(0o666)
    
    snackbar = ft.SnackBar(content=ft.Text(f"File saved: {full_path}"), open=True)
    print("save_dataframes: File saved: ", full_path)
    page.add(snackbar)

def perform_save(directory_textfield, filename_textfield, page, dataframes, on_save_callback=None):
    global current_dir, current_file
    
    # current_dirが文字列の場合はPathオブジェクトに変換
    if isinstance(current_dir, str):
        current_dir = Path(current_dir)
    
    invalid_chars = set('.<>:"/\\|?*')
    invalid_chars_directory = set(c for c in invalid_chars if c in directory_textfield.value)
    invalid_chars_filename = set(c for c in invalid_chars if c in filename_textfield.value)
    error_message = ""
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
    elif (current_dir / (directory_textfield.value or "") / (filename_textfield.value + ".pkl")).exists():
        error_message = "File already exists"
        filename_textfield.error_text = error_message
    else:
        filename_textfield.error_text = ""
    if error_message:
        snackbar = ft.SnackBar(content=ft.Text(error_message), open=True)
        page.add(snackbar)
    else: # エラーメッセージがない場合はデータを保存
        save_dir = current_dir
        if directory_textfield.value:
            save_dir = current_dir / directory_textfield.value
        save_path = save_dir / (filename_textfield.value + ".pkl")
        save_dataframes(page, dataframes, str(save_path.parent), save_path.name)
        current_file = save_path
        # タブ名を更新
        page.title = filename_textfield.value
        if on_save_callback:
            on_save_callback()  # コールバック関数を呼び出す
        page.update()
        close_dialog(page)

def update_current_dir(page: ft.Page, new_dir: str):
    """ディレクトリを更新し、関連するUIコンポーネントを更新する"""
    global current_dir, directory_dropdown, filename_dropdown
    base_dir = Path("../pkl_files")
    
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
            files = [f.name for f in current_dir.iterdir() if f.is_file() and f.suffix == '.pkl']
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
    
    # パスが../pkl_filesで始まり、中間に..を含まないものだけを保持
    filtered_directories = []
    for d in directories:
        normalized_path = normalize_path(d)
        if normalized_path.startswith("../pkl_files/"):
            parts = Path(normalized_path).parts
            if '..' not in parts[2:]:  # '../pkl_files' の後に '..' が含まれていないことを確認
                filtered_directories.append(d)
        elif normalized_path == "../pkl_files":
            filtered_directories.append(d)
    
    # 重複を削除し、ソート（プラットフォーム固有のパス区切り文字を保持）
    filtered_directories = sorted(set(filtered_directories))
    
    print(f"Debug - get_directory_hierarchy:")
    print(f"base_dir: {base_dir}")
    print(f"target_dir: {target_dir}")
    print(f"found directories: {filtered_directories}")
    
    return filtered_directories

def save_dialog(page: ft.Page, dataframes, on_save_callback=None):
    global directory_dropdown, filename_dropdown, save_button
    directory_textfield = ft.TextField(
        label="New Directory Name", 
        hint_text="New Directory Name", 
        visible=False
    )
    filename_textfield = ft.TextField(
        label="Enter filename", 
        hint_text="e.g., my_data"
    )
    save_button = ft.ElevatedButton(
        text="Save", 
        on_click=lambda e: perform_save(directory_textfield, filename_textfield, page, dataframes, on_save_callback)
    )
    # current_dirからbase_dirまでのディレクトリ階層を取得
    directories = get_directory_hierarchy("../pkl_files", current_dir)
    directory_dropdown = ft.Dropdown(
        label=str(current_dir),
        options=[ft.DropdownOption(text=str(dir)) for dir in directories],
        on_change=lambda e: update_current_dir(page, e.control.value),
        hint_text=str(current_dir),
        value=str(current_dir)
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
    
    dialog = ft.AlertDialog(
        title=ft.Text("Save As"),
        content=ft.Column([directory_dropdown, new_directory_button, directory_textfield, filename_textfield], spacing=10),
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
    if page and page.overlay and len(page.overlay) > 0:
        dialog = page.overlay.pop()
        dialog.open = False
        page.update()
    else:
        print("No dialog to close")

def update_filename_options(directory, filename_dropdown):
    # 指定されたディレクトリ内のファイルをリストアップ
    dir_path = Path(directory)
    files = [f.name for f in dir_path.iterdir() if f.is_file() and f.suffix == '.pkl']
    # filename_dropdownのオプションを更新
    filename_dropdown.options = [ft.DropdownOption(text=file) for file in files]

def load_dataframes(page, file_path, inputs_row, table_chart_row, channel_dropdown):
    global current_file, current_dir
    try:
        file_path = Path(file_path)
        with open(file_path, 'rb') as f:
            loaded_dataframes = pickle.load(f)
        
        inputs_row.visible = True
        table_chart_row.visible = True
        channel_dropdown.options = [ft.DropdownOption(text=f"Channel {i}") for i in range(16) if f"Channel {i}" in loaded_dataframes]
        channel_dropdown.value = None  # 値をリセット
        channel_dropdown.update()
        
        current_file = file_path
        current_dir = file_path.parent
        
        snackbar = ft.SnackBar(content=ft.Text(f"File loaded: {file_path}"), open=True)
        print("load_dataframes: File loaded: ", file_path)
        page.add(snackbar)
        
        # ファイル名（拡張子なし）を取得
        file_name = file_path.stem
        
        page.update()  # ページの更新を追加
        return loaded_dataframes, file_name
    except Exception as e:
        snackbar = ft.SnackBar(content=ft.Text(f"Error loading file: {str(e)}"), open=True)
        page.add(snackbar)
        print(f"Error loading file: {str(e)}")  # エラーログを追加
        return None, None

def load_dialog(page: ft.Page, inputs_row, table_chart_row, channel_dropdown, on_load_callback):
    global directory_dropdown, filename_dropdown
    base_dir = Path("../pkl_files")
    
    print("\nDebug - load_dialog:")
    print(f"current_dir: {current_dir}")
    
    # current_dirからbase_dirまでのディレクトリ階層を取得
    directories = get_directory_hierarchy(str(base_dir), str(current_dir))
    print(f"available directories: {directories}")
    
    directory_dropdown = ft.Dropdown(
        label=str(current_dir),
        options=[ft.DropdownOption(text=dir) for dir in directories],
        on_change=lambda e: update_current_dir(page, e.control.value),  # 直接値を渡す
        hint_text=str(current_dir),
    )
    
    filename_dropdown = ft.Dropdown(
        label="Filename",
        options=[],
        hint_text="Select a file",
    )

    def on_open_click(e):
        if not filename_dropdown.value:
            filename_dropdown.error_text = "Select a file"
            filename_dropdown.update()
        else:
            file_path = current_dir / filename_dropdown.value
            loaded_dataframes, file_name = load_dataframes(
                page, 
                str(file_path), 
                inputs_row, 
                table_chart_row, 
                channel_dropdown
            )
            if loaded_dataframes is not None:
                on_load_callback(loaded_dataframes, file_name, page)
            close_dialog(page)
            
    dialog = ft.AlertDialog(
        title=ft.Text("Open"),
        content=ft.Column([directory_dropdown, filename_dropdown], spacing=10),
        actions=[
            ft.TextButton(text="Open", on_click=on_open_click),
            ft.TextButton(text="Cancel", on_click=lambda e: close_dialog(page))
        ],
        actions_alignment="end",
        modal=False
    )
    
    page.overlay.append(dialog)
    dialog.open = True
    page.update()

# ファイル削除用のダイアログ
def delete_pkl_dialog(page: ft.Page):
    global directory_dropdown, filename_dropdown, current_dir
    root_dir = Path("../pkl_files")
    
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
            files = [f.name for f in dir_path.iterdir() if f.is_file() and f.suffix == '.pkl']
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
                            os.remove(delete_path)
                            page.add(ft.SnackBar(content=ft.Text(f"File {delete_path} has been deleted")))
                        else:
                            shutil.rmtree(delete_path)
                            page.add(ft.SnackBar(content=ft.Text(f"Directory {delete_path} and its contents have been deleted")))
                        
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
        title=ft.Text("Delete"),
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