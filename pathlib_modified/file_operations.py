import os
import pickle
import shutil
import flet as ft
from pathlib import Path  # Pathをインポート

# グローバル変数の宣言
current_dir = Path("../pkl_files")  # resolveを削除
current_file = None
directory_dropdown = None
filename_dropdown = None
save_button = None

def save_dataframes(page, dataframes, directory=None, filename=None):
    global current_file, current_dir
    if filename:
        directory_path = Path(directory)
        if not directory_path.exists():
            directory_path.mkdir(parents=True)
            directory_path.chmod(0o777)
        full_path = directory_path / filename
        current_file = full_path
        current_dir = directory_path
    elif current_file is None:
        save_dialog(page, dataframes)
        return
    else:
        full_path = current_file

    with open(full_path, 'wb') as f:
        pickle.dump(dataframes, f)
    
    # pklファイルに666パーミッションを設定
    Path(full_path).chmod(0o666)
    
    snackbar = ft.SnackBar(content=ft.Text(f"File saved: {full_path.as_posix()}"), open=True)
    print("save_dataframes: File saved: ", full_path.as_posix())
    page.add(snackbar)

def perform_save(directory_textfield, filename_textfield, page, dataframes, on_save_callback=None):
    global current_dir, current_file
    invalid_chars = set('.<>:"/\\|?*')
    error_message = ""
    
    # ディレクトリ名のバリデーション（ディレクトリテキストフィールドが表示されている場合のみ）
    if directory_textfield.visible and directory_textfield.value:
        invalid_chars_directory = set(c for c in invalid_chars if c in directory_textfield.value)
        if invalid_chars_directory:
            # 先頭が../または..\の場合は特別に許可
            if directory_textfield.value.startswith("../") or directory_textfield.value.startswith("..\\"):
                # ../または..\以外の部分に不正な文字がないかチェック
                remaining_path = directory_textfield.value[3:]  # ../または..\を除いた部分
                remaining_invalid_chars = set(c for c in invalid_chars if c in remaining_path)
                if remaining_invalid_chars:
                    error_message = f"Invalid characters in directory name: [ {', '.join(remaining_invalid_chars)} ]"
                    directory_textfield.error_text = error_message
            else:
                error_message = f"Invalid characters in directory name: [ {', '.join(invalid_chars_directory)} ]"
                directory_textfield.error_text = error_message
        elif (current_dir / directory_textfield.value).exists():
            error_message = "Directory already exists"
            directory_textfield.error_text = error_message
        else:
            directory_textfield.error_text = ""
    
    # ファイル名のバリデーション
    if not filename_textfield.value:
        error_message = "Filename is required"
        filename_textfield.error_text = error_message
    else:
        invalid_chars_filename = set(c for c in invalid_chars if c in filename_textfield.value)
        if invalid_chars_filename:
            error_message = f"Invalid characters in filename: [ {', '.join(invalid_chars_filename)} ]"
            filename_textfield.error_text = error_message
        elif (current_dir / directory_textfield.value / f"{filename_textfield.value}.pkl").exists():
            error_message = "File already exists"
            filename_textfield.error_text = error_message
        else:
            filename_textfield.error_text = ""
    
    if error_message:
        snackbar = ft.SnackBar(content=ft.Text(error_message), open=True)
        page.add(snackbar)
    else:
        # 保存処理
        save_dir = current_dir
        if directory_textfield.visible and directory_textfield.value:
            save_dir = current_dir / directory_textfield.value
        
        full_path = (save_dir / f"{filename_textfield.value}.pkl").as_posix()
        save_dataframes(page, dataframes, str(save_dir), f"{filename_textfield.value}.pkl")
        
        current_file = full_path
        page.title = filename_textfield.value
        if on_save_callback:
            on_save_callback()
        page.update()
        close_dialog(page)

def get_directory_hierarchy(base_dir: str, target_dir: str) -> list:
    base_path = Path(base_dir)  # ../pkl_files
    target_path = Path(target_dir)  # ../pkl_files/examples など
    
    # ベースディレクトリからの相対パスのみを扱う
    directories = [str(base_path)]  # まずベースディレクトリを追加
    
    try:
        # ターゲットパスがベースパスのサブディレクトリである場合
        if target_path != base_path:
            # パスを正規化して重複を除去
            parts = []
            for part in target_path.parts:
                if part == "..":
                    if parts:
                        parts.pop()
                else:
                    parts.append(part)
            
            # 正規化されたパスを構築
            current = base_path
            for part in parts[parts.index("pkl_files")+1:]:
                current = current / part
                directories.append(str(current))
        
        # サブディレクトリを追加
        if target_path.exists() and target_path.is_dir():
            sub_directories = [str(d) for d in target_path.iterdir() if d.is_dir()]
            directories.extend(sorted(sub_directories))
            
    except Exception as e:
        print(f"Error in get_directory_hierarchy: {e}")
    
    return directories

def update_current_dir(page: ft.Page, new_dir: str):
    global current_dir, directory_dropdown, filename_dropdown
    print("update_current_dir: current_dir(before) :", current_dir.as_posix())
    
    base_dir = Path("../pkl_files")
    new_path = Path(new_dir)
    
    try:
        # パスを正規化して重複を除去
        parts = []
        for part in new_path.parts:
            if part == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(part)
        
        # pkl_filesを基準にパスを再構築
        if "pkl_files" in parts:
            idx = parts.index("pkl_files")
            current_dir = base_dir / "/".join(parts[idx+1:])
        else:
            current_dir = base_dir
        
        print("update_current_dir: current_dir(after) :", current_dir.as_posix())
        
        # ディレクトリ一覧を更新
        directories = get_directory_hierarchy(str(base_dir), str(current_dir))
        print("update_current_dir: directories", directories)
        
        if directory_dropdown:
            directory_dropdown.options = [ft.dropdown.Option(text=dir) for dir in directories]
            directory_dropdown.value = str(current_dir)
            directory_dropdown.label = str(current_dir)
        
        if filename_dropdown:
            update_filename_options(str(current_dir), filename_dropdown)
        
        page.update()
        
    except Exception as e:
        print(f"Error in update_current_dir: {e}")

def save_dialog(page: ft.Page, dataframes, on_save_callback=None):
    global directory_dropdown, filename_dropdown, save_button
    
    # ディレクトリ選択用のドロップダウンを初期化
    directory_dropdown = ft.Dropdown(
        label=current_dir.as_posix(),
        options=[ft.dropdown.Option(text=dir) for dir in get_directory_hierarchy("../pkl_files", str(current_dir))],
        on_change=lambda e: update_current_dir(page, e.control.value),
        hint_text=current_dir.as_posix(),
    )
    
    # 新規ディレクトリ作成用のテキストフィールド
    directory_textfield = ft.TextField(
        label="Directory name",
        hint_text="Enter new directory name",
        value="",  # 空の値で初期化
        visible=False
    )
    
    # ファイル名入力用のテキストフィールド
    filename_textfield = ft.TextField(
        label="Enter filename", 
        hint_text="e.g., my_data"
    )
    
    def new_directory(page):
        if new_directory_button.text == "New Directory":
            new_directory_button.text = "Cancel"
            directory_textfield.visible = True
            directory_dropdown.visible = False
            # テキストフィールドを空にする
            directory_textfield.value = ""
        else:
            new_directory_button.text = "New Directory"
            directory_textfield.visible = False
            directory_dropdown.visible = True
            # ドロップダウンの値を現在のディレクトリに戻す
            directory_dropdown.value = current_dir.as_posix()
        new_directory_button.update()
        directory_textfield.update()
        directory_dropdown.update()
    
    # 保存ボタン
    save_button = ft.ElevatedButton(
        text="Save", 
        on_click=lambda e: perform_save(directory_textfield, filename_textfield, page, dataframes, on_save_callback)
    )
    
    # 新規ディレクトリボタン
    new_directory_button = ft.ElevatedButton(
        text="New Directory", 
        on_click=lambda e: new_directory(page)
    )
    
    # ダイアログの作成
    dialog = ft.AlertDialog(
        title=ft.Text("Save As"),
        content=ft.Column(
            controls=[
                directory_dropdown,
                new_directory_button,
                directory_textfield,
                filename_textfield
            ],
            spacing=10
        ),
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
    directory_path = Path(directory)
    files = [f.name for f in directory_path.iterdir() if f.is_file() and f.suffix == '.pkl']
    # filename_dropdownのオプションを更新
    filename_dropdown.options = [ft.dropdown.Option(text=file) for file in files]

def load_dataframes(page: ft.Page, file_path: str):
    global current_dir
    try:
        file_path = Path(file_path)
        base_dir = Path("../pkl_files")
        
        # ファイルの親ディレクトリを更新
        parent_dir = file_path.parent
        if parent_dir.name == base_dir.name:
            current_dir = parent_dir
        elif base_dir.name in parent_dir.parts:
            # pkl_filesより後のパスを取得
            idx = parent_dir.parts.index(base_dir.name)
            # ../pkl_filesを基準にパスを構築
            current_dir = base_dir.joinpath(*parent_dir.parts[idx+1:])
        
        with open(file_path, 'rb') as f:
            dataframes = pickle.load(f)
        
        print("load_dataframes: File loaded: ", file_path.as_posix())
        return dataframes
    except Exception as e:
        print(f"Error loading file: {e}")
        return {}

def load_dialog(page: ft.Page, inputs_row, table_chart_row, channel_dropdown, on_load_callback):
    global directory_dropdown, filename_dropdown
    directories = get_directory_hierarchy("../pkl_files", current_dir)
    directory_dropdown = ft.Dropdown(
        label=current_dir,
        options=[ft.dropdown.Option(text=dir) for dir in directories],
        on_change=lambda e: update_current_dir(page, e.control.value),
        hint_text=current_dir,
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
            file_path = Path(current_dir) / filename_dropdown.value
            loaded_dataframes = load_dataframes(page, str(file_path))
            
            if loaded_dataframes:
                # UIの更新
                inputs_row.visible = True
                table_chart_row.visible = True
                channel_dropdown.options = [
                    ft.dropdown.Option(text=f"Channel {i}") 
                    for i in range(16) 
                    if f"Channel {i}" in loaded_dataframes
                ]
                channel_dropdown.value = None
                channel_dropdown.update()
                
                # 成功メッセージ
                snackbar = ft.SnackBar(content=ft.Text(f"File loaded: {file_path}"), open=True)
                page.add(snackbar)
                
                # コールバック実行
                if on_load_callback:
                    on_load_callback(loaded_dataframes, file_path.stem, page)
                
            close_dialog(page)
            page.update()

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
def delete_dialog(page: ft.Page):
    global directory_dropdown, filename_dropdown, current_dir
    root_dir = Path("../pkl_files")
    directories = get_directory_hierarchy(str(root_dir), str(current_dir))
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

    def on_delete_click(e):
        selected_dir = directory_dropdown.value
        selected_file = filename_dropdown.value

        if selected_dir is None:
            page.show_snack_bar(ft.SnackBar(content=ft.Text("Select a directory to delete")))
            return

        delete_path = Path(current_dir)
        if selected_file:
            delete_path = delete_path / selected_file

        if delete_path.absolute() == root_dir.absolute():
            page.add(ft.SnackBar(content=ft.Text("Cannot delete the root directory")))
            return

        if selected_file:
            if delete_path.is_file():
                confirmation_message = f"Delete file {delete_path}?"
            else:
                page.show_snack_bar(ft.SnackBar(content=ft.Text("Selected file does not exist")))
                return
        else:
            if delete_path.is_dir():
                confirmation_message = f"Delete directory {delete_path} and its contents?"
            else:
                page.show_snack_bar(ft.SnackBar(content=ft.Text("Selected directory does not exist")))
                return

        def confirm_delete(e):
            if e.control.text == "Yes":
                if selected_file:
                    try:
                        delete_path.unlink()
                        page.add(ft.SnackBar(content=ft.Text(f"File {delete_path.as_posix()} has been deleted")))
                    except FileNotFoundError:
                        page.add(ft.SnackBar(content=ft.Text(f"File {delete_path.as_posix()} not found")))
                else:
                    try:
                        shutil.rmtree(delete_path)
                        page.add(ft.SnackBar(content=ft.Text(f"Directory {delete_path.as_posix()} and its contents have been deleted")))
                    except FileNotFoundError:
                        page.add(ft.SnackBar(content=ft.Text(f"Directory {delete_path.as_posix()} not found")))
                update_current_dir(page, delete_path.parent.as_posix())
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

    dialog = ft.AlertDialog(
        title=ft.Text("Delete"),
        content=ft.Column([directory_dropdown, filename_dropdown], spacing=10),
        actions=[
            ft.TextButton(text="Delete", on_click=on_delete_click),
            ft.TextButton(text="Cancel", on_click=lambda e: close_dialog(page))
        ],
        actions_alignment="end",
        modal=False
    )
    
    page.overlay.append(dialog)
    dialog.open = True
    page.update()