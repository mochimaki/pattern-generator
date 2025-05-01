import flet as ft
import pandas as pd
import argparse
import chart_func as cgf
import export_csv as ec
from file_operations import save_dataframes, save_dialog, load_dialog, delete_pkl_dialog
import view_operations as vo
import edit_operations as eo
from export_csv import export_csv_dialog, delete_csv_dialog
from m2k_digital import enable_channels_dialog, play_dialog, channel_control_dialog

page = None
dataframes = {}  # チャネルごとのDataFrameを辞書で管理
selected_rows = [] # 選択された行のデータを保持するためのリスト
copied_rows = []    # コピーされた行のデータを保持するためのリスト
channel_to_display = [] # 表示するチャネルを保持するためのリスト
save_menu_item = None  # save_menu_itemをグローバル変数として追加
# グローバル変数としてUIコンポーネントを定義
channel_dropdown = None
state_dropdown = None
duration_textfield = None
unit_dropdown = None
data_table = None  # DataTableのグローバル参照
inputs_row = None # state_dropdown, duration_textfield, unit_dropdown, append_buttonを含むRow
insert_above_button = None
insert_below_button = None
invert_button = None
correct_button = None
append_button = None
copy_button = None
delete_button = None
position_info_text = None
repeat_info_text = None
selected_index = None
repeat_count_textfield = None
table_chart_row = None
range_slider = None
chart_container = None
chart_column = None
current_file = None
channel_colors = [
    "#FF6347",  # トマト
    "#FFD700",  # ゴールド
    "#90EE90",  # ライトグリーン
    "#00BFFF",  # ディープスカイベルー
    "#9370DB",  # ミディアムパープル
    "#FF4500",  # ンジレッド
    "#DA70D6",  # オーキッド
    "#EEE8AA",  # ペールゴールデンロッド
    "#98FB98",  # ペールグリーン
    "#AFEEEE",  # ペールターコイズ
    "#DB7093",  # ペールバイオレットレッド
    "#FFDAB9",  # ピーチパフ
    "#CD853F",  # ペルー
    "#FFC0CB",  # ピンク
    "#DDA0DD",  # プラム
    "#B0E0E6"   # ウダーブルー
]

def create_channel_dataframe(): # 初期値を持たない空のデータフレームを作成（データ型を明示してpandasの更新に対応）
    columns = {
        "state": pd.Series(dtype=str),
        "duration": pd.Series(dtype=float),
        "unit": pd.Series(dtype=str)
    }
    return pd.DataFrame(columns=columns)

def create_initial_dataframes(): # 16チャネル分の空のDataFrameを辞書で管理
    dataframes = {}
    for i in range(16):
        dataframes[f"Channel {i}"] = create_channel_dataframe()
    return dataframes

def rows_to_dataframe(rows):
    # DataRowからDataFrameを作成するためのデータを抽出
    data = {
        "state": [row.cells[1].content.value for row in rows],
        "duration": [float(row.cells[2].content.value) for row in rows],
        "unit": [row.cells[3].content.value for row in rows]
    }
    return pd.DataFrame(data)

def edit_dataframe(e, page, dataframes, action):
    global channel_dropdown, state_dropdown, duration_textfield, unit_dropdown, data_table, selected_rows, selected_index, copied_rows, repeat_count_textfield
    channel = channel_dropdown.value
    state = state_dropdown.value
    duration = duration_textfield.value
    unit = unit_dropdown.value

    if action == "correct" and correct_button.color == ft.Colors.BLUE_200:
        if len(selected_rows) == 1:
            # 選択された行のデータを更新
            for row in selected_rows:
                index = row.data  # 選択された行のインデックス
                dataframes[channel].loc[index, 'state'] = state
                dataframes[channel].loc[index, 'duration'] = float(duration)
                dataframes[channel].loc[index, 'unit'] = unit
    
    elif action == "delete" and delete_button.color == ft.Colors.BLUE_200:
        if selected_rows:
            indices_to_delete = [row.data for row in selected_rows] # 選択されたすべての行のインデックスを取得
            dataframes[channel] = dataframes[channel].drop(indices_to_delete).reset_index(drop=True) # 選択され行を削除
            range_slider.start_value = 0 # レンジをリセット
            range_slider.end_value = len(dataframes[channel]) # レンジをリセット

    elif action == "invert" and invert_button.color == ft.Colors.BLUE_200:
        if selected_rows:
            for row in selected_rows:
                index = row.data  # 選択された行のインデックス
                current_state = dataframes[channel].loc[index, 'state']
                # 状態を反転
                new_state = 'low' if current_state == 'high' else 'high'
                dataframes[channel].loc[index, 'state'] = new_state
            
    if copied_rows: # コピーされた行がある場合
        repeat_count = int(repeat_count_textfield.value)
        new_copied_rows = []
        for _ in range(repeat_count):
            new_copied_rows.extend(list(copied_rows))
        # copied_rowsからDataFrameを作成
        copied_data = rows_to_dataframe(new_copied_rows)

        if action == "above" and insert_above_button.color == ft.Colors.BLUE_200:
            dataframes[channel] = pd.concat([dataframes[channel].iloc[:selected_index], copied_data, dataframes[channel].iloc[selected_index:]], ignore_index=True)

        elif action == "below" and insert_below_button.color == ft.Colors.BLUE_200:
            dataframes[channel] = pd.concat([dataframes[channel].iloc[:selected_index + 1], copied_data, dataframes[channel].iloc[selected_index + 1:]], ignore_index=True)
            
        copied_rows = []
        copy_button.text = "Copy"
        copy_button.color = ft.Colors.BLUE_200
        copy_button.update()
        position_info_text.visible = False
        position_info_text.update() 
        repeat_info_text.visible = False
        repeat_count_textfield.value = "1"
        repeat_info_text.update()
        repeat_count_row.visible = False
        repeat_count_row.update()
        range_slider.start_value = 0 # レンジをリセット
        range_slider.end_value = len(dataframes[channel]) # レンジをリセット
            
    # 入力値の検証（コピーされた行がない場合）
    elif action == "append" or action == "below" or action == "above":
        missing_inputs = []
        if not channel:
            missing_inputs.append("Channel")
            channel_dropdown.error_text = "Channel is required!"
        else:
            channel_dropdown.error_text = ""
        if not state:
            missing_inputs.append("State")
            state_dropdown.error_text = "State is required!"
        else:
            state_dropdown.error_text = ""
        if not duration:
            missing_inputs.append("Duration")
            duration_textfield.error_text = "Duration is required!"
        else:
            duration_textfield.error_text = ""
        if not unit:
            missing_inputs.append("Unit")
            unit_dropdown.error_text = "Unit is required!"
        else:
            unit_dropdown.error_text = ""
        if missing_inputs:
            page.update()
            return
        # 新しい行を作成
        new_row = pd.DataFrame({"state": [state], "duration": [float(duration)], "unit": [unit]})
        # 対象の DataFrame が空の場合は新しい DataFrame を直接代入（pandasの仕様変更に応）
        if dataframes[channel].empty: # 空のdataframeに対しconcatで行を追加する場合
            dataframes[channel] = new_row
        else: # nullが含まれる行をconcat追加することまたはnullを含dataframeに対し新たな行をconcatで追加することは将来的に非推奨になる。
            if action == "append" and append_button.color == ft.Colors.BLUE_200:
                dataframes[channel] = pd.concat([dataframes[channel], new_row], ignore_index=True)
            elif action == "below" and insert_below_button.color == ft.Colors.BLUE_200:
                selected_index = selected_rows[0].data if selected_rows else len(dataframes[channel])
                dataframes[channel] = pd.concat([dataframes[channel].iloc[:selected_index + 1], new_row, dataframes[channel].iloc[selected_index + 1:]], ignore_index=True)
            elif action == "above" and insert_above_button.color == ft.Colors.BLUE_200:
                selected_index = selected_rows[0].data if selected_rows else 0
                dataframes[channel] = pd.concat([dataframes[channel].iloc[:selected_index], new_row, dataframes[channel].iloc[selected_index:]], ignore_index=True)
        range_slider.start_value = 0 # レンジをリセット
        range_slider.end_value = len(dataframes[channel]) # レンジをリセット
    channel_dropdown_change(channel, page) # UIを更新

def channel_dropdown_change(channel, page):
    global dataframes, channel_dropdown, state_dropdown, duration_textfield, unit_dropdown, data_table, inputs_row, table_chart_row, channel_to_display, button_row, position_info_text, repeat_count_row, repeat_info_text, copied_rows, copy_button, append_button, correct_button, range_slider, selected_rows
    # button_row、position_info_text、repeat_count_row、repeat_info_textを非表示にする。
    button_row.visible = False
    position_info_text.visible = False
    repeat_count_row.visible = False
    repeat_info_text.visible = False
    # コピーされた行があればリリースする。
    if copied_rows:
        copied_rows = []
        copy_button.text = "Copy"
        copy_button.color = ft.Colors.BLUE_200
        copy_button.update()
    # channelが選択されていない場合、inputs_rowとdata_tableを非表示にする
    if not channel:
        inputs_row.visible = False
        if data_table:
            data_table.visible = False
            table_chart_row.visible = False
        page.update()
        return
    # channelが選択されている場合、inputs_rowとdata_tableを表示
    inputs_row.visible = True
    if data_table:
        data_table.visible = True
        table_chart_row.visible = True

    channel_dropdown.color = channel_colors[int(channel_dropdown.value.split()[-1])]
    # state, duration, unitのウィジェットの値をリセット
    state_dropdown.value = None
    duration_textfield.value = ""
    unit_dropdown.value = None
    button_row.visible = False

    append_button.color = ft.Colors.GREY_800
    correct_button.color = ft.Colors.GREY_800
    # UIの更新
    state_dropdown.update()
    duration_textfield.update()
    unit_dropdown.update()
    # 選択したチャネルのデータを取得
    df = dataframes[channel]
    
    data_table.columns = [
        ft.DataColumn(label=ft.Text("Index")),
        ft.DataColumn(label=ft.Text("State")),
        ft.DataColumn(label=ft.Text("Duration"), numeric=True),
        ft.DataColumn(label=ft.Text("Unit"))
    ]
    data_table.rows = [
        ft.DataRow(cells=[
            ft.DataCell(ft.Text(str(index))),
            ft.DataCell(ft.Text(row["state"])),
            ft.DataCell(ft.Text(str(row["duration"]))),
            ft.DataCell(ft.Text(row["unit"]))
        ], 
        on_select_changed=lambda e: row_select_changed(e, df, data_table, page),
        data=index)  # インデックスをdata属性に保存
        for index, row in df.iterrows()
    ]
    page.update()

    if channel not in channel_to_display: # 編集中のチャネルのみの表示にするならこのif文は不要
        channel_to_display.append(channel)

    range_slider.min = 0
    range_slider.max = len(df['duration'])
    range_slider.divisions = len(df['duration'])
    range_slider.start_value = 0
    range_slider.end_value = len(df['duration'])
    range_slider.update()
    if range_slider.start_value > len(df['duration']):
        range_slider.start_value = 0
    if range_slider.end_value > len(df['duration']):
        range_slider.end_value = len(df['duration'])
    range_slider.update()
    selected_rows = []
    chart_update(channel_changed=True)
    #cgf.chart_update(dataframes, channel_to_display, channel_dropdown.value, page, selected_rows, channel_colors, channel_changed=True)

def update_global_dataframes(loaded_dataframes, file_name): # ファイルを読み込んだときに呼び出す
    global dataframes, channel_to_display, page
    dataframes = loaded_dataframes
    # print(f"Updated dataframes: {dataframes}")  # デバッグ用出力を追加
    channel_to_display = []  # チャンネルリストを初期化
    # ここで必要に応じて他のグローバル変数や UI の更新を行う
    # 例: チャンネルドロップダウンの更新など
    update_channel_dropdown()
    chart_update()
    # タブ名を更新
    if page:  # pageが設定されている場合のみ更新
        page.title = file_name if file_name else "Pattern Generator"
        update_save_menu_visibility()
        page.update()

def update_channel_dropdown():
    global channel_dropdown
    channel_dropdown.options = [ft.dropdown.Option(text=f"Channel {i}") for i in range(16) if f"Channel {i}" in dataframes]
    channel_dropdown.value = None
    channel_dropdown_change(None, page)

def inputs_row_change(e, page):
    global state_dropdown, unit_dropdown, duration_textfield, append_button
    # state_dropdown, unit_dropdown が選択されているか、および duration_textfield が空でないかをチェック
    if state_dropdown.value and unit_dropdown.value and duration_textfield.value:
        append_button.color = ft.Colors.BLUE_200
    else:
        append_button.color = ft.Colors.GREY_800
    # UIの更新
    page.update()

def row_select_changed(e, df, data_table, page):
    global selected_rows, copied_rows, selected_index, table_chart_row  # selected_rowsをグローバル変数として扱う
    # DataRowのselected属を反転させる
    e.control.selected = not e.control.selected
    # 選された行を得
    selected_rows = [row for row in data_table.rows if row.selected]

    # ボタンの表示を更新
    button_row.visible = len(selected_rows) > 0
    # 選択された行のインデックスを取
    selected_indices = [df.index.get_loc(row.data) for row in selected_rows]
    if not copied_rows: # コピーされた行がない場合
        # Correctボタンのテキスト色変更
        if len(selected_rows) == 1: # 選択された行が1つの場合
            append_button.color = ft.Colors.BLUE_200
            correct_button.color = ft.Colors.BLUE_200
            insert_above_button.color = ft.Colors.BLUE_200  
            insert_below_button.color = ft.Colors.BLUE_200
            copy_button.color = ft.Colors.BLUE_200
            delete_button.color = ft.Colors.BLUE_200
            invert_button.color = ft.Colors.BLUE_200
            # input_rowの内容を変更
            state_dropdown.value = selected_rows[0].cells[1].content.value
            duration_textfield.value = selected_rows[0].cells[2].content.value
            unit_dropdown.value = selected_rows[0].cells[3].content.value
        elif len(selected_rows) > 1: # 選択された行が複数の場合
            append_button.color = ft.Colors.GREY_800
            correct_button.color = ft.Colors.GREY_800
            insert_above_button.color = ft.Colors.GREY_800  
            insert_below_button.color = ft.Colors.GREY_800
            invert_button.color = ft.Colors.BLUE_200
            # input_rowの内容をリセット
            state_dropdown.value = None
            duration_textfield.value = ""
            unit_dropdown.value = None
            # 選択された行が連続している場合はコピーボタンを有効にする
            if all(x + 1 == y for x, y in zip(selected_indices, selected_indices[1:])):
                copy_button.color = ft.Colors.BLUE_200
            else:
                copy_button.color = ft.Colors.GREY_800
        else: # 選択された行がない場合
            append_button.color = ft.Colors.GREY_800
            correct_button.color = ft.Colors.GREY_800
            button_row.visible = False
            # input_rowの内容をリセット
            state_dropdown.value = None
            duration_textfield.value = ""
            unit_dropdown.value = None
        page.update()
    else: # コピーされた行がある場合
        data_table.update()
        selected_index = selected_rows[0].data
        selected_rows = []
        # 行の選択を解除
        for row in data_table.rows:
            row.selected = False

        insert_above_button.color = ft.Colors.BLUE_200 
        insert_below_button.color = ft.Colors.BLUE_200
        insert_above_button.update()
        insert_below_button.update()
        return
    chart_update()

def on_select_all(e):
    global data_table, selected_rows, copied_rows
    if not copied_rows:
        all_selected = all(row.selected for row in data_table.rows)
        if all_selected:
            # すべての行の択を解除
            for row in data_table.rows:
                row.selected = False
                row.update()
            button_row.visible = False
            button_row.update()
            selected_rows = []
        else:
            # すべての行を選択
            for row in data_table.rows:
                row.selected = True
                row.update()
            button_row.visible = True
            copy_button.color = ft.Colors.BLUE_200
            delete_button.color = ft.Colors.BLUE_200
            insert_above_button.color = ft.Colors.GREY_800
            insert_below_button.color = ft.Colors.GREY_800
            invert_button.color = ft.Colors.BLUE_200
            button_row.update()
            selected_rows = [row for row in data_table.rows if row.selected]
        
            if len(selected_rows) == 1: # 選択された行が1つの場合
                append_button.color = ft.Colors.BLUE_200
                correct_button.color = ft.Colors.BLUE_200
                insert_above_button.color = ft.Colors.BLUE_200
                insert_below_button.color = ft.Colors.BLUE_200
                # input_rowの内容を変更
                state_dropdown.value = selected_rows[0].cells[1].content.value
                duration_textfield.value = selected_rows[0].cells[2].content.value
                unit_dropdown.value = selected_rows[0].cells[3].content.value
            else: # 選択された行が複数の場合
                append_button.color = ft.Colors.GREY_800
                correct_button.color = ft.Colors.GREY_800
                # input_rowの内容をリセット
                state_dropdown.value = None
                duration_textfield.value = ""
                unit_dropdown.value = None
            inputs_row.update()
            button_row.update()
        chart_update()

def copy_selected_rows():
    global copied_rows, position_info_text, repeat_info_text, selected_rows

    if copy_button.color == ft.Colors.BLUE_200:
        copied_rows = list(selected_rows)  # 選択された行のデータをコピー
        copy_button.text = "Cancel"
        copy_button.color = ft.Colors.GREEN_500
        copy_button.update()
        inputs_row.visible = False
        inputs_row.update()
        repeat_count_row.visible = True
        repeat_count_row.update()
        repeat_info_text.visible = True
        repeat_info_text.update()
        delete_button.color = ft.Colors.GREY_800
        delete_button.update()
        # コピーされた行のインデックスを取得
        if copied_rows:
            indices = [row.data for row in copied_rows]
            if len(indices) > 1:
                position_info = f"rows ({indices[0]} - {indices[-1]}) are"
            else:
                position_info = f"row ({indices[0]}) is"
            
            position_info_text.value = "Select from the data table the position in which the copied " + position_info + " to be inserted."
            position_info_text.visible = True
            position_info_text.update()

            for row in selected_rows:
                row.color = ft.Colors.GREEN_900 # 行の色を変更
                row.selected = False
                row.update()

        selected_rows = []
        
        insert_above_button.color = ft.Colors.GREY_800
        insert_below_button.color = ft.Colors.GREY_800
        insert_above_button.update()
        insert_below_button.update()
        invert_button.color = ft.Colors.GREY_800
        invert_button.update()

    elif copy_button.color == ft.Colors.GREEN_500:
        copied_rows = []
        copy_button.text = "Copy"
        copy_button.color = ft.Colors.BLUE_200 
        copy_button.update()
        inputs_row.visible = True
        inputs_row.update()
        position_info_text.visible = False
        position_info_text.update()
        repeat_count_row.visible = False
        repeat_count_row.update()
        repeat_info_text.visible = False
        repeat_info_text.update()
        # data_tableの行の選択をすべて解除
        for row in data_table.rows:
            row.selected = False
            row.color = None # 行の色を変更
            row.update()
        data_table.update()
        selected_rows = []
        button_row.visible = False
        button_row.update()

######### File操作関連 #########
# 関数はfile_operations.pyに移動しました
def new_file():
    global current_file, dataframes
    current_file = None
    dataframes = create_initial_dataframes()
    # タブ名をデフォルトに戻す
    page.title = "Pattern Generator"
    update_save_menu_visibility()
    channel_dropdown.value = None
    channel_dropdown_change(None, page) # UI更新

def update_save_menu_visibility():
    global page, save_menu_item
    if page.title == "Pattern Generator":
        save_menu_item.visible = False
    else:
        save_menu_item.visible = True
    page.update()

#########　Chart関連 #########
# 関数はchart_func.pyに移動しました
def chart_update(channel_changed=None):
    global table_chart_row, chart_column, data_table, selected_rows, channel_dropdown, dataframes, range_slider
    # 選択されたデータのインデックスを格納
    indices = []
    for ii in selected_rows:
        indices.append(data_table.rows.index(ii))
    # チャートを生成
    start_index = int(range_slider.start_value)
    end_index = int(range_slider.end_value)
    new_chart = cgf.generate_timing_chart(dataframes, channel_to_display, channel_dropdown.value, channel_colors, start_index, end_index, indices)
    chart_container.content = new_chart
    chart_container.update()
    if channel_changed:
        range_slider.max = len(data_table.rows) # スライダーの最大値をデータの行数に設定
        range_slider.divisions = len(data_table.rows) # スライダーの分割数をデータの行数に設定
        range_slider.update()
    if len(data_table.rows) == 0: # データがない場合はチャートを非表示
        chart_column.visible = False
    else: # データがある場合はチャートを表示
        chart_column.visible = True
    chart_column.update()

######### View関連 #########
def sort_channels_dialog(page):
    vo.sort_channels_dialog(page, channel_to_display, channel_dropdown, dataframes, channel_colors, chart_update)

def select_channels_dialog(page):
    vo.select_channels_dialog(page, channel_to_display, channel_dropdown, chart_update)

######## main関数の前にargparseの設定を追加 ########
def parse_arguments():
    parser = argparse.ArgumentParser(description='Pattern Generator Application')
    parser.add_argument('--view', type=str, 
                       choices=["web_browser", "flet_app", "flet_app_web", "flet_app_hidden"],
                       default="web_browser",
                       help='アプリケーションの表示モード (デフォルト: web_browser)')
    
    # Webモード用の引数グループを作成
    web_group = parser.add_argument_group('Web mode options')
    web_group.add_argument('--port', type=int, default=8550,
                          help='Webモード時のポート番号 (デフォルト: 8550)')
    web_group.add_argument('--host', type=str, default='127.0.0.1',
                          help='Webモード時のホストアドレス (デフォルト: 127.0.0.1)')
    web_group.add_argument('--route-strategy', type=str, choices=['hash', 'path'], 
                          default='hash',
                          help='URLルーティング方式 (デフォルト: hash)')
    return parser.parse_args()

######### Main関数 #########
def main(page_arg: ft.Page):
    global page, dataframes, channel_dropdown, state_dropdown, duration_textfield, unit_dropdown, data_table, inputs_row, button_row, append_button, correct_button, insert_above_button, insert_below_button, copy_button, delete_button, repeat_count_row, position_info_text, repeat_info_text, repeat_count_textfield, table_chart_row, range_slider, chart_container, chart_column, invert_button, save_menu_item
    
    page = page_arg  # グローバル変数 page に引数の page を代入
    page.title = "Pattern Generator" # デフォルトのページタイトルの表示
    page.scroll = True  # ページ全体をスクロール可能に設定
    page.theme_mode = ft.ThemeMode.DARK  # Apply dark theme

    # file_menuに追加するSaveメニューを作成
    save_menu_item = ft.MenuItemButton(
        content=ft.Text("Save"),
        on_click=lambda e: save_dataframes(page, dataframes)
    )

    # Fileメニューの作成（popupmenubuttonにする？）
    file_menu = ft.SubmenuButton(
        content=ft.Text("File"),
        controls=[
            ft.MenuItemButton(
                content=ft.Text("New"),
                on_click=lambda e: new_file()
            ),
            ft.MenuItemButton(
                content=ft.Text("Save As..."),
                on_click=lambda e: save_dialog(page, dataframes, update_save_menu_visibility)
            ),
            save_menu_item,  # Save メニュー項目を追加（表示・非表示を切り替えて使用）
            ft.MenuItemButton(
                content=ft.Text("Open..."),
                on_click=lambda e: load_dialog(page, inputs_row, table_chart_row, channel_dropdown, 
                                                lambda loaded_dataframes, file_name, _: update_global_dataframes(loaded_dataframes, file_name))
            ),
            ft.MenuItemButton(
                content=ft.Text("Delete..."),
                on_click=lambda e: delete_pkl_dialog(page)
            ),  
            
            #ft.MenuItemButton( # デスクトップアプリとして実行する場合は有効
            #    content=ft.Text("Exit"), 
            #    on_click=lambda _: page.window_close()
            #),
        ]
    )
    edit_menu = ft.SubmenuButton(
        content=ft.Text("Edit"),
        controls=[
            ft.MenuItemButton(
                content=ft.Text("Copy dataframe from another channel"),
                on_click=lambda e: eo.copy_dataframe_dialog(page, channel_dropdown, dataframes, lambda channel, page: eo.copy_dataframe(channel, page, dataframes, channel_dropdown, channel_dropdown_change))
            ),
        ]
    )
    view_menu = ft.SubmenuButton(
        content=ft.Text("View"),
        controls=[
            ft.MenuItemButton(  # 新しいメニューアイテムの追加
                content=ft.Text("Select Channels"),
                on_click=lambda e: select_channels_dialog(page)
            ),
            ft.MenuItemButton(
                content=ft.Text("Sort Channels"),
                on_click=lambda e: sort_channels_dialog(page)
            ),
        ]
    )
    csv_menu = ft.SubmenuButton(
        content=ft.Text("CSV"),
        controls=[
            ft.MenuItemButton(
                content=ft.Text("Export CSV..."), 
                on_click=lambda _: export_csv_dialog(page, dataframes)
            ),
            ft.MenuItemButton(
                content=ft.Text("Delete CSV..."), 
                on_click=lambda _: delete_csv_dialog(page)
            ),
        ]
    )
    play_menu = ft.SubmenuButton(
        content=ft.Text("Play"),
        controls=[
            ft.MenuItemButton(
                content=ft.Text("Choose channels"),
                on_click=lambda e: enable_channels_dialog(page)
            ),
            ft.MenuItemButton(
                content=ft.Text("Play"),
                on_click=lambda e: play_dialog(page, get_current_dataframes)
            ),
            ft.MenuItemButton(
                content=ft.Text("Manual"),
                on_click=lambda e: channel_control_dialog(page)
            )
        ]
    )
    # MenuBarにFileメニューを追加
    menubar = ft.MenuBar(
        controls=[
            file_menu, 
            edit_menu, 
            view_menu, 
            csv_menu,
            play_menu
        ]
    )
    # MenuBarをページに追加
    page.add(menubar)
    # Channel selection dropdown
    dropdown_items = [ft.dropdown.Option(text=f"Channel {i}") for i in range(16)]
    channel_dropdown = ft.Dropdown(
        label="Channel",  # Updated label
        hint_text="Select channel",
        text_size=18,
        width=150,
        options=dropdown_items,
        on_change=lambda e: channel_dropdown_change(e.control.value, page)
    )
    # State選択のドロップダウン
    state_dropdown = ft.Dropdown(
        width=150,
        label="State",  # Updated label
        options=[
            ft.dropdown.Option(text="low"),
            ft.dropdown.Option(text="high")
        ],
        hint_text="Select state",
        on_change=lambda e: inputs_row_change(e, page)
    )
    # Duration入力のテキストフィールド
    duration_textfield = ft.TextField(
        width=150,
        label="Duration",
        hint_text="Enter duration",
        input_filter=ft.InputFilter(allow=True, 
                                    regex_string=r"^[0-9]*\.?[0-9]*$",
                                    replacement_string=""),
        on_submit=lambda e: inputs_row_change(e, page),
        on_blur=lambda e: inputs_row_change(e, page)
    )
    # Duration単位のドロップダウン
    unit_dropdown = ft.Dropdown(
        width=150,
        label="Unit",  # Updated label
        options=[
            ft.dropdown.Option(text="sec."),
            ft.dropdown.Option(text="msec."),
            ft.dropdown.Option(text="microsec.")
        ],
        hint_text="Select unit",
        on_change=lambda e: inputs_row_change(e, page)
    )
    # Appendボタンの追加
    append_button = ft.ElevatedButton(text="Append", on_click=lambda e: edit_dataframe(e, page, dataframes, "append"))
    append_button.color = ft.Colors.GREY_800
    # Correctボタンの追加
    correct_button = ft.ElevatedButton(text="Correct", on_click=lambda e: edit_dataframe(e, page, dataframes, "correct"))
    correct_button.color = ft.Colors.GREY_800
    # Create a row for state, duration, unit widgets and the append button
    inputs_row = ft.Row(
        controls=[
            state_dropdown,
            duration_textfield,
            unit_dropdown,
            append_button,
            correct_button
        ],
        alignment=ft.MainAxisAlignment.START,
        visible=False  # 初期状態では非表示
    )
    # ページにコントロールを追加
    page.add(channel_dropdown)
    page.add(inputs_row)
    copy_button = ft.ElevatedButton(
        text="Copy", 
        on_click=lambda e: copy_selected_rows())
    delete_button = ft.ElevatedButton(
        text="Delete", 
        on_click=lambda e: edit_dataframe(e, page, dataframes, "delete")
    )
    insert_above_button = ft.ElevatedButton(
        text="Insert Above",
        on_click=lambda e: edit_dataframe(e, page, dataframes, "above")
    )
    insert_below_button = ft.ElevatedButton(
        text="Insert Below",
        on_click=lambda e: edit_dataframe(e, page, dataframes, "below")
    )
    invert_button = ft.ElevatedButton(
        text="Invert",
        on_click=lambda e: edit_dataframe(e, page, dataframes, "invert")
    )
    copy_button.color = ft.Colors.GREY_800
    delete_button.color = ft.Colors.GREY_800
    insert_above_button.color = ft.Colors.GREY_800
    insert_below_button.color = ft.Colors.GREY_800
    invert_button.color = ft.Colors.GREY_800
    # ボタンを含む行の設定
    button_row = ft.Row(
        controls=[copy_button, 
                  delete_button, 
                  insert_above_button, 
                  insert_below_button, 
                  ft.VerticalDivider(width=5, color="white", thickness=3),  # VerticalDividerを挿入
                  invert_button],
        visible=False  # 初期状態では非表示
    )
    # ページにコントロールを追加
    page.add(button_row)
    position_info_text = ft.Text("", size=15, color=ft.Colors.GREEN_500, italic=True)
    page.add(position_info_text)
    # Repeat count row
    repeat_count_text = ft.Text(value="Repeat count")
    repeat_count_textfield = ft.TextField(value="1", input_filter=ft.InputFilter(allow=True, regex_string=r"^[1-9][0-9]*$"))
    repeat_count_row = ft.Row(
        controls=[repeat_count_text, repeat_count_textfield],
        visible=False  # 初期状態では非表示
    )
    page.add(repeat_count_row) 
    repeat_info_text = ft.Text("Specify the number of repetitions.", size=15, color=ft.Colors.GREEN_500, italic=True, visible=False)
    page.add(repeat_info_text)
    # DataTableの作成
    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Index")),
            ft.DataColumn(ft.Text("State")),
            ft.DataColumn(ft.Text("Duration")),
            ft.DataColumn(ft.Text("Unit"))
        ],
        visible=False,  # 初期状態では非表示
        show_checkbox_column=True, 
        on_select_all=on_select_all,
        data_row_max_height=30,
        data_row_min_height=30,
        heading_text_style=ft.TextStyle(size=16, italic=True)
    ) 
    # コンテントの作成と設定
        # Columnの作成と設定
    data_table_column = ft.Column(
        controls=[data_table],
        expand=True,
        width=350,  # 適な幅を設定
        height=450,  # 6行分の高さを設定
        scroll=ft.ScrollMode.ALWAYS  # 常にスクロールバーを表示
    )
    # RangeSliderの設定
    range_slider = ft.RangeSlider(
        min=0,
        max=1,  # 仮の最大値
        start_value=0,
        end_value=1,
        divisions=1,
        label="{value}",
        on_change=chart_update
    )
    # チャートを表示するコンテナ
    chart_container = ft.Container()
    # チャートとRangeSliderを含むColumnの作成
    chart_column = ft.Column(
        controls=[
            chart_container,
            range_slider
        ],
        width=800,  # 適切な幅に調整してください
        alignment=ft.MainAxisAlignment.START
    )
    chart_column.visible = False
    # データテーブルとチャートColumnを横に並べるRowの作成
    table_chart_row = ft.Row(
        controls=[
            data_table_column,
            chart_column
        ],
        alignment=ft.MainAxisAlignment.START
    )
    # ページにRowを追加
    page.add(table_chart_row)
    # 初期チャートの表示
    if range_slider is not None:
        chart_update()
    # チャネルごとのDataFrameを作成
    dataframes = create_initial_dataframes()

    # ページを更新
    page.update()

def get_current_dataframes():
    global dataframes
    return dataframes

if __name__ == "__main__":
    args = parse_arguments()
    
    # AppViewの対応関係を定義
    view_mapping = {
        "web_browser": ft.AppView.WEB_BROWSER,
        "flet_app": ft.AppView.FLET_APP,
        "flet_app_web": ft.AppView.FLET_APP_WEB,
        "flet_app_hidden": ft.AppView.FLET_APP_HIDDEN
    }
    
    if args.view == "web_browser":
        ft.app(
            target=main,
            view=ft.AppView.WEB_BROWSER,
            route_url_strategy=args.route_strategy,
            port=args.port,
            host=args.host
        )
    else:  # flet_app, flet_app_web, flet_app_hidden
        ft.app(
            target=main,
            view=view_mapping[args.view]
        )
