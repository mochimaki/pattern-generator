# m2k_digital.py

import libm2k
import pandas as pd
from typing import Dict, List, TYPE_CHECKING
from export_csv import export_to_string_io, calculate_optimal_sample_rate
import csv
from io import StringIO
import flet as ft
import asyncio
import time
from asyncio import Event
import json

# グローバル変数
enabled_channels = []
global_buffer = None
global_sample_rate = None
global_repeat_count = 1
global_interval_seconds = 0
global_repeat_enabled = False
global_m2k = None
global_cyclic_enabled = False
global_cycle_count = 1
global_infinite_cycle_enabled = False
global_m2k_ip = None

def load_containers_info(): # app_info.jsonからIPアドレスを読み込む
    global global_m2k_ip
    try:
        with open('../app_info.json', 'r') as f:
            app_info = json.load(f)
            global_m2k_ip = f"ip:{app_info['devices']['m2k']['target'][0]}"
    except Exception as e:
        print(f"Error loading settings: {e}")
        global_m2k_ip = "ip:192.168.3.1"  # デフォルト値

class M2KDigital:
    def __init__(self, uri="ip:192.168.3.1"):
        try:
            self.ctx = libm2k.m2kOpen(uri)
            if self.ctx is None:
                raise ConnectionError(f"No ADALM2000 device available/connected at {uri}")
            self.dig = self.ctx.getDigital()
            self.dig.reset()
        except Exception as e:
            print(f"Error initializing M2KDigital: {str(e)}")
            raise

    def setup_channels(self, sample_rate: int):
        global enabled_channels, global_sample_rate
        
        if not isinstance(sample_rate, int) or sample_rate <= 0:
            raise ValueError(f"Invalid sample rate: {sample_rate}")
        
        self.dig.setSampleRateOut(sample_rate)
        global_sample_rate = sample_rate

        for i in range(16):  # ADALM2000 has 16 digital channels
            if i in enabled_channels:
                self.dig.setDirection(i, libm2k.DIO_OUTPUT)
                self.dig.enableChannel(i, True)
                self.dig.setValueRaw(i, libm2k.LOW)
            else:
                self.dig.setDirection(i, libm2k.DIO_INPUT)

    async def send_pattern(self, buffer: List[int], stop_event: asyncio.Event):
        global global_sample_rate, global_cyclic_enabled, global_cycle_count, global_infinite_cycle_enabled
        
        if not isinstance(global_sample_rate, int) or global_sample_rate <= 0:
            raise ValueError(f"Invalid global sample rate: {global_sample_rate}")

        sleep_duration = len(buffer) / global_sample_rate
        if global_cyclic_enabled and not global_infinite_cycle_enabled:
            sleep_duration *= global_cycle_count

        elapsed_time = 0
        self.dig.setCyclic(global_cyclic_enabled)
        count_step = 0.1
        start_time = time.time()
        self.dig.push(buffer)

        while True:  # 無限ループに変更
            if stop_event.is_set():
                print("Pattern output interrupted")
                break
            await asyncio.sleep(count_step)
            elapsed_time += count_step
            
            if not global_infinite_cycle_enabled and elapsed_time >= sleep_duration:
                break  # 無限サイクルでない場合のみ、指定時間経過後にループを抜ける

        self.dig.stopBufferOut()
        
        total_time = time.time() - start_time
        print(f"Total send_pattern time: {total_time:.6f} seconds")

    def _csv_to_buffer(self, csv_content: StringIO) -> tuple:
        csv_content.seek(0)  # ファイルポインタを先頭に戻す
        reader = csv.reader(csv_content)
    
        buffer = []
        sample_rate = None
        total_samples = None
    
        for i, row in enumerate(reader):
            if i == 3:  # 4行目: サンプル数
                total_samples = int(row[1])
            elif i == 4:  # 5行目: サンプルレート
                sample_rate = int(row[1])
            elif i >= 8:  # 9行目降: データ
                # 最初の列（サンププし、残りを2進数に変換
                state = sum(int(val) << i for i, val in enumerate(row[1:]))
                buffer.append(state)
    
        if sample_rate is None or total_samples is None:
            raise ValueError("Sample rate or total samples not found in CSV data")
    
        if len(buffer) != total_samples:
            raise ValueError(f"Expected {total_samples} samples, but got {len(buffer)}")
    
        return buffer, sample_rate

    def close(self):
        print("Entering close method")
        if self.dig:
            try:
                self.dig.stopBufferOut()
            except Exception as e:
                print(f"Error stopping buffers: {str(e)}")

            try:
                self.reset()
            except Exception as e:
                print(f"Error resetting device: {str(e)}")

            print("M2KDigital connection closed.")
        else:
            print("M2KDigital connection already closed or not initialized.")

    def reset(self):
        if self.dig:
            self.dig.reset()
        else:
            print("self.dig is None in reset method")
        if self.ctx:
            self.ctx.reset()
        else:
            print("self.ctx is None in reset method")

    async def stop_and_close(self):
        global enabled_channels
        if self.dig:
            try:
                self.dig.stopBufferOut()
                if enabled_channels:
                    zero_buffer = [0] * 4
                    try:
                        self.dig.push(zero_buffer)
                        print("Zero buffer pushed successfully")
                    except Exception as e:
                        print(f"Error pushing zero buffer: {e}")
                    time.sleep(1 / global_sample_rate)
            except Exception as e:
                print(f"Error in stop_and_close: {e}")
            finally:
                try:
                    self.dig.reset()
                except Exception as e:
                    print(f"Error resetting M2KDigital device: {e}")
        else:
            print("self.dig is None in stop_and_close")

    def enable_channel(self, channel: int, enable: bool):
        self.dig.enableChannel(channel, enable)

    def set_direction(self, channel: int, direction: int):
        self.dig.setDirection(channel, direction)

    def set_value_raw(self, channel: int, value: int):
        self.dig.setValueRaw(channel, value)

    def get_value_raw(self, channel: int) -> int:
        return self.dig.getValueRaw(channel)

def channel_control_dialog(page: ft.Page):
    global global_m2k, global_m2k_ip
    
    load_containers_info()
    
    if global_m2k:  # Noneでない場合のみclose()を実行
        global_m2k.close()
    
    global_m2k = M2KDigital(global_m2k_ip)

    channel_controls = {}

    def on_master_switch_change(e):
        for channel in range(16):
            global_m2k.enable_channel(channel, e.control.value)
            global_m2k.set_direction(channel, libm2k.DIO_OUTPUT)
            new_value = libm2k.HIGH if e.control.value else libm2k.LOW
            global_m2k.set_value_raw(channel, new_value)
            update_channel_controls(channel)

    def on_value_change(e):
        channel = e.control.data["channel"]
        enabled = e.control.value
        global_m2k.enable_channel(channel, enabled)
        global_m2k.set_direction(channel, libm2k.DIO_OUTPUT)
        new_value = libm2k.HIGH if enabled else libm2k.LOW
        global_m2k.set_value_raw(channel, new_value)
        update_channel_controls(channel)
        update_master_switch()

    def update_channel_controls(channel):
        value_switch = channel_controls[channel]

        enabled = global_m2k.get_value_raw(channel) == libm2k.HIGH
        value_switch.value = enabled
        value_switch.active_color = ft.Colors.RED if enabled else ft.Colors.RED_900
        value_switch.thumb_color = ft.Colors.WHITE

        page.update()

    def update_master_switch():
        all_on = all(global_m2k.get_value_raw(channel) == libm2k.HIGH for channel in range(16))
        master_switch.value = all_on
        page.update()

    master_switch = ft.CupertinoSwitch(
        value=False,
        active_color=ft.Colors.BLUE,
        track_color=ft.Colors.GREY,
        thumb_color=ft.Colors.WHITE,
        on_change=on_master_switch_change,
    )

    master_row = ft.Row([
        ft.Text("All Channels", width=100),
        ft.Text("OFF", width=40),
        master_switch,
        ft.Text("ON", width=40)
    ])

    separator = ft.Divider(height=1, color=ft.Colors.GREY_400)

    for i in range(16):
        value_switch = ft.CupertinoSwitch(
            value=False,
            active_color=ft.Colors.RED,
            track_color=ft.Colors.GREY,
            thumb_color=ft.Colors.WHITE,
            on_change=on_value_change,
            data={"channel": i}
        )

        channel_controls[i] = value_switch

    channel_rows = [
        ft.Row([
            ft.Text(f"Channel {i}", width=100),
            ft.Text("OFF", width=40),
            channel_controls[i],
            ft.Text("ON", width=40)
        ])
        for i in range(16)
    ]

    content = ft.Column(
        [
            master_row,
            separator,
            ft.Column(channel_rows)
        ],
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
    )

    dialog = ft.AlertDialog(
        title=ft.Text("Channel Control"),
        content=content,
        actions=[
            ft.TextButton("Close", on_click=lambda _: close_dialog(page))
        ],
        actions_alignment="end",
    )

    for channel in range(16):
        update_channel_controls(channel)
    update_master_switch()

    page.overlay.append(dialog)
    dialog.open = True
    page.update()

def close_dialog(page):
    global global_m2k
    if global_m2k:
        for channel in range(16):
            global_m2k.enable_channel(channel, False)
            global_m2k.set_value_raw(channel, libm2k.LOW)
    if page.overlay and len(page.overlay) > 0:
        dialog = page.overlay.pop()
        dialog.open = False
        page.update()

def enable_channels_dialog(page: ft.Page):
    global enabled_channels

    def on_checkbox_change(e):
        channel = int(e.control.label.split()[-1])
        if e.control.value:  # チェックされた場合
            if channel not in enabled_channels:
                enabled_channels.append(channel)
        else:  # チェックが外れた場合
            if channel in enabled_channels:
                enabled_channels.remove(channel)
        enabled_channels.sort()
        update_select_all_checkbox()

    def on_select_all_change(e):
        for i, checkbox in enumerate(channel_checkboxes):
            checkbox.value = e.control.value
            if e.control.value:
                if i not in enabled_channels:
                    enabled_channels.append(i)
            else:
                if i in enabled_channels:
                    enabled_channels.remove(i)
        enabled_channels.sort()
        page.update()

    def update_select_all_checkbox():
        select_all_checkbox.value = len(enabled_channels) == 16
        page.update()

    select_all_checkbox = ft.Checkbox(
        label="Select All",
        value=len(enabled_channels) == 16,
        on_change=on_select_all_change
    )

    separator = ft.Divider()

    channel_checkboxes = [
        ft.Checkbox(label=f"Channel {i}", value=(i in enabled_channels), on_change=on_checkbox_change)
        for i in range(16)
    ]

    dialog = ft.AlertDialog(
        title=ft.Text("Enable Channels"),
        content=ft.Column(
            [select_all_checkbox, separator] + channel_checkboxes,
            scroll=ft.ScrollMode.AUTO
        ),
        actions=[
            ft.ElevatedButton("OK", on_click=lambda _: close_dialog(page))
        ],
        actions_alignment="end",
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()

def play_dialog(page: ft.Page, get_dataframes_func):
    global global_sample_rate, global_repeat_count, global_interval_seconds, global_repeat_enabled, enabled_channels
    global global_cyclic_enabled, global_cycle_count, global_infinite_cycle_enabled, global_m2k_ip
    
    # ダイアログを開く際にIPアドレスを再読み込み
    load_containers_info()
    
    def get_current_dataframes():
        return get_dataframes_func()
    
    optimal_sample_rate = calculate_optimal_sample_rate(get_current_dataframes())
    global_sample_rate = optimal_sample_rate  # グローバル変数を更新
    
    interval_value = ft.Ref[ft.Text]()
    
    def handle_timer_picker_change(e):
        global global_interval_seconds
        seconds = int(e.data)
        time_str = time.strftime("%H:%M:%S", time.gmtime(seconds))
        interval_value.current.value = time_str
        global_interval_seconds = seconds
        page.update()

    sample_rate_field = ft.TextField(
        label="Sample Rate",
        value=str(optimal_sample_rate),
        keyboard_type=ft.KeyboardType.NUMBER,
        on_change=lambda _: validate_sample_rate(sample_rate_field)
    )

    def validate_sample_rate(field):
        global global_sample_rate
        try:
            value = int(field.value)
            if value <= 0:
                field.error_text = "Sample rate must be a positive integer"
            else:
                field.error_text = None
                global_sample_rate = value
        except ValueError:
            field.error_text = "Please enter a valid integer"
        page.update()

    def validate_cycle_count(e):
        global global_cycle_count
        try:
            value = int(e.control.value)
            if value <= 0:
                e.control.error_text = "Cycle count must be a positive integer"
            else:
                e.control.error_text = None
                global_cycle_count = value
        except ValueError:
            e.control.error_text = "Please enter a valid integer"
        page.update()

    def update_repeat_and_interval_visibility():
        is_visible = not (global_cyclic_enabled and infinite_cycle_checkbox.value)
        repeat_row.visible = is_visible
        interval_row.visible = is_visible and global_repeat_enabled
        interval_picker.visible = False  # interval_pickerは常に非表示にし、必要なときだけ表示する

    def toggle_cyclic_options(e):
        global global_cyclic_enabled
        global_cyclic_enabled = cyclic_checkbox.value
        cycle_count_field.visible = cyclic_checkbox.value and not infinite_cycle_checkbox.value
        infinite_cycle_checkbox.visible = cyclic_checkbox.value
        update_repeat_and_interval_visibility()
        page.update()

    def toggle_infinite_cycle(e):
        global global_infinite_cycle_enabled
        global_infinite_cycle_enabled = e.control.value
        cycle_count_field.visible = not e.control.value
        update_repeat_and_interval_visibility()
        page.update()

    def toggle_repeat_options(e):
        global global_repeat_enabled
        global_repeat_enabled = repeat_checkbox.value
        repeat_count_field.visible = repeat_checkbox.value
        update_repeat_and_interval_visibility()
        page.update()

    cyclic_checkbox = ft.Checkbox(
        label="Enable cyclic pattern",
        value=global_cyclic_enabled,
        on_change=toggle_cyclic_options
    )

    cycle_count_field = ft.TextField(
        label="Cycle Count",
        value=str(global_cycle_count),
        keyboard_type=ft.KeyboardType.NUMBER,
        visible=global_cyclic_enabled,
        on_change=validate_cycle_count,
        width=120
    )

    infinite_cycle_checkbox = ft.Checkbox(
        label="Infinite",
        value=False,
        on_change=toggle_infinite_cycle,
        visible=global_cyclic_enabled
    )

    cyclic_row = ft.Row([
        cyclic_checkbox,
        cycle_count_field,
        infinite_cycle_checkbox
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    # セパレータを追加
    separator = ft.Divider(height=1, color=ft.Colors.GREY_400)

    repeat_checkbox = ft.Checkbox(
        label="Repeat at set interval",
        value=global_repeat_enabled,
        on_change=toggle_repeat_options
    )

    def update_repeat_count(e):
        global global_repeat_count
        try:
            value = int(e.control.value)
            if value > 0:
                global_repeat_count = value
                e.control.error_text = None
            else:
                e.control.error_text = "Repeat count must be a positive integer"
        except ValueError:
            e.control.error_text = "Please enter a valid integer"
        page.update()

    repeat_count_field = ft.TextField(
        label="Repeat Count",
        value=str(global_repeat_count),
        keyboard_type=ft.KeyboardType.NUMBER,
        visible=global_repeat_enabled,
        on_change=update_repeat_count,
        width=120  # 幅を制限して横に配置しやすくする
    )

    repeat_row = ft.Row([
        repeat_checkbox,
        repeat_count_field
    ], alignment=ft.MainAxisAlignment.START)

    interval_picker = ft.CupertinoTimerPicker(
        value=global_interval_seconds,
        second_interval=1,
        minute_interval=1,
        mode=ft.CupertinoTimerPickerMode.HOUR_MINUTE_SECONDS,
        on_change=handle_timer_picker_change,
        visible=False,
    )

    interval_text = ft.Text(
        ref=interval_value,
        value=time.strftime("%H:%M:%S", time.gmtime(global_interval_seconds)),
        size=16,
        color=ft.Colors.BLUE,
    )

    def toggle_interval_picker(_):
        if not (global_cyclic_enabled and infinite_cycle_checkbox.value):
            interval_picker.visible = not interval_picker.visible
            page.update()

    interval_button = ft.ElevatedButton(
        "Set Interval",
        on_click=toggle_interval_picker,
    )

    interval_row = ft.Row([
        interval_button,
        interval_text
    ], alignment=ft.MainAxisAlignment.START, visible=global_repeat_enabled)

    # 現在の出力回数を表示するためのテキストフィールドを追加
    current_iteration_text = ft.Text("", style=ft.TextThemeStyle.BODY_LARGE)

    # カウントダウンを表示するためのテキストフィールド
    countdown_text = ft.Text("", visible=False)

    # current_iteration_text と countdown_text 横に並べる
    status_row = ft.Row([
        current_iteration_text,
        countdown_text
    ], alignment=ft.MainAxisAlignment.START)

    # IPアドレス表示フィールドを追加
    ip_address_display = ft.TextField(
        label="ADALM2000 IP Address",
        value=global_m2k_ip.split(':')[1],  # "ip:"を除去
        read_only=True
    )

    stop_flag = False
    is_running = False

    def update_play_button_state():
        play_stop_button.disabled = len(enabled_channels) == 0
        if len(enabled_channels) == 0:
            play_stop_button.tooltip = "Please enable at least one channel"
        else:
            play_stop_button.tooltip = None
        page.update()

    async def on_play_stop(_):
        global global_sample_rate, global_repeat_count, global_interval_seconds, global_repeat_enabled, global_m2k, current_task
        nonlocal stop_flag, is_running

        if not is_running:
            if sample_rate_field.error_text:
                return

            if global_repeat_enabled and repeat_count_field.error_text:
                return

            if global_cyclic_enabled and cycle_count_field.error_text:
                return

            if len(enabled_channels) == 0: # 出力チャネルが選択されていない場合
                page.snack_bar = ft.SnackBar(content=ft.Text("Please enable at least one channel"))
                page.snack_bar.open = True
                page.update()
                return # チャネルが選択されていない場合は処理を中断

            # パターン出力開始のための前処理
            stop_flag = False
            is_running = True
            play_stop_button.text = "Stop"
            play_stop_button.style = ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)
            page.update()

            try:
                sample_rate = global_sample_rate
                repeat_count = global_repeat_count if global_repeat_enabled else 1
                cycle_count = global_cycle_count if global_cyclic_enabled else 1
                interval_seconds = global_interval_seconds if global_repeat_enabled else 0
                print(f"Play button clicked - Sample rate: {sample_rate}, Repeat count: {repeat_count}, Cycle count: {cycle_count}, Interval: {interval_seconds} seconds")

                for i in range(repeat_count):
                    if stop_flag:
                        print("Pattern output stopped by user")
                        break

                    # 出力回数の表示を更新
                    current_iteration_text.value = f"Iteration: {i+1}/{repeat_count}"
                    countdown_text.value = ""  # カウントダウンテキストをクリア
                    page.update()

                    start_time = time.time()
                    print(f"Starting pattern {i+1}/{repeat_count}")
                    try:
                        stop_event = asyncio.Event()
                        # パターン出力の直前に最新のdataframesを取得する関数を渡す
                        current_task = asyncio.create_task(output_to_m2k(get_dataframes_func, stop_event, sample_rate))
                        await current_task
                        print(f"Pattern {i+1}/{repeat_count} sent")
                    except Exception as error:
                        print(f"Error during pattern {i+1}: {str(error)}")
                        break

                    # 次のパターン出力までの待ち時間（カウントダウン）
                    if i < repeat_count - 1 and not stop_flag: # １回パターンを出力した後、Stopボタンがクリックされていない場合に実行される
                        print("Entering interval period")
                        if global_m2k:
                            await global_m2k.stop_and_close() # バッファーの転送中断、ゼロバッファーのプッシュおよびsleepを含むが効果なし
                        
                        elapsed_time = time.time() - start_time
                        remaining_interval = max(0, interval_seconds - elapsed_time)
                        print(f"Waiting for next pattern. Interval: {remaining_interval:.1f}s")
                        countdown_text.visible = True
                        page.update()
                        for remaining in range(int(remaining_interval), 0, -1):
                            if stop_flag:
                                break
                            countdown_message = f"Next pattern in {remaining}s"
                            print(countdown_message)
                            countdown_text.value = countdown_message
                            countdown_text.visible = True
                            page.update()
                            await asyncio.sleep(1)

                        countdown_text.visible = False
                        page.update()

                if not stop_flag:
                    print("All patterns sent.")
                    page.snack_bar = ft.SnackBar(content=ft.Text("Pattern sent to ADALM2000 successfully"))
                else:
                    page.snack_bar = ft.SnackBar(content=ft.Text("Pattern output stopped by user"))
                page.snack_bar.open = True
            except Exception as error:
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Error: {str(error)}"))
                page.snack_bar.open = True
            finally:
                is_running = False
                stop_flag = False
                play_stop_button.text = "Play"
                play_stop_button.style = None
                current_iteration_text.value = ""
                update_play_button_state()
                page.update()
        else: # is_runningがTrueの場合 -> ユーザーの操作によるパターン出力の中断
            if not stop_flag:
                stop_flag = True
                if current_task:
                    current_task.cancel()
                if global_m2k:
                    await global_m2k.stop_and_close() # ADALM2000に対する操作はこれが最後

                print("Stop requested by user")
                page.snack_bar = ft.SnackBar(content=ft.Text("Stopping pattern output..."))
                page.snack_bar.open = True
                page.update()

    play_stop_button = ft.ElevatedButton("Play", on_click=on_play_stop)
    update_play_button_state()

    # 初期状態の設定
    update_repeat_and_interval_visibility()

    dialog = ft.AlertDialog(
        title=ft.Text("Play Pattern"),
        content=ft.Container(
            content=ft.Column(
                [
                    ip_address_display,  # IPドレス表示フィールドを追加
                    sample_rate_field,
                    separator,
                    cyclic_row,
                    separator,
                    repeat_row,
                    interval_row,
                    interval_picker,
                    status_row,
                    separator,
                    play_stop_button
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=10,  # 要素間のスペースを追加
                height=400
            ),
            width=500,  # ダイアログの幅を設定
            padding=20,  # コンテンツの内側の余白を追加
        ),
        content_padding=ft.padding.all(0),  # ダイアログのデフォルトパディングを削除
        actions=[
            ft.TextButton("Close", on_click=lambda _: close_dialog(page)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()

async def output_to_m2k(get_dataframes_func, stop_event: Event, sample_rate: int = None):
    global enabled_channels, global_buffer, global_sample_rate, global_m2k, global_cyclic_enabled, global_m2k_ip
    
    start_time = time.time()
    print(f"{time.time():.3f}: Starting output_to_m2k")
    
    # パターン出力の直前に最新のdataframesを取得（新しく開いたファイルのdataframesが反映される）
    dataframes = get_dataframes_func()
    
    if not enabled_channels:
        raise ValueError("No channels are enabled. Please select channels first.")

    print(f"{time.time():.3f}: Preparing buffer and sample rate")
    if sample_rate is None:
        sample_rate = calculate_optimal_sample_rate(dataframes)
    # ToDo：global_cyclic_enabledがTrueの場合はサンプル数を４の倍数に調整する
    global_sample_rate = sample_rate  # グローバル変数を更新
    # dataframesをcsv形式のオブジェクトに変換
    csv_content = export_to_string_io(dataframes, format_type='scopy', sample_rate=sample_rate, cyclic=global_cyclic_enabled)
    # パターン出力にかかる時間を計算
    csv_content.seek(0)
    csv_lines = csv_content.readlines()
    data_lines = len(csv_lines) - 8
    theoretical_duration = data_lines / sample_rate
    print(f"Theoretical pattern duration: {theoretical_duration:.3f} seconds")
    print(f"CSV data lines: {data_lines}, Sample rate: {sample_rate}")
    
    global_m2k = None # M2KDigitalオブジェクトの初期化（m2kはグローバル変数）
    pattern_send_start = time.time()
    try:
        #m2k_create_start = time.time()
        #print(f"{time.time():.3f}: Creating M2KDigital object")
        global_m2k = M2KDigital(global_m2k_ip) # M2KDigitalオブジェクトの生成
        #m2k_create_time = time.time() - m2k_create_start
        #print(f"M2KDigital creation time: {m2k_create_time:.6f} seconds")
        # csv形式のオブジェクトからバッファーとサンプルレートを計算
        #csv_to_buffer_start = time.time()
        #print(f"{time.time():.3f}: Converting CSV to buffer")
        global_buffer, global_sample_rate = global_m2k._csv_to_buffer(csv_content)
        #csv_to_buffer_time = time.time() - csv_to_buffer_start
        #print(f"CSV to buffer conversion time: {csv_to_buffer_time:.6f} seconds")

        if global_sample_rate != sample_rate: # global_cyclic_enabledがTrueの場合にはあり得る
            print(f"Warning: CSV sample rate ({global_sample_rate}) differs from specified rate ({sample_rate})")
        # パターンを出力するチャネルの設定
        #setup_start = time.time()
        #print(f"{time.time():.3f}: Setting up channels")
        global_m2k.setup_channels(global_sample_rate)
        #setup_time = time.time() - setup_start
        #print(f"Channel setup time: {setup_time:.6f} seconds")
        # ADALM2000への転送
        print(f"{time.time():.3f}: Sending pattern")
        #send_start_time = time.time()
        await global_m2k.send_pattern(global_buffer, stop_event)
        #send_end_time = time.time()
        #actual_duration = send_end_time - send_start_time
        #print(f"{time.time():.3f}: Pattern sent to M2K device successfully. Sample rate: {global_sample_rate}")
        #print(f"Actual pattern send duration: {actual_duration:.6f} seconds")
        #print(f"Enabled channels: {enabled_channels}")
    except asyncio.CancelledError: # エラー処理
        print("Pattern output cancelled")
    except Exception as e: # エラー処理
        print(f"Error occurred during pattern output: {str(e)}")
        if global_m2k:
            global_m2k.reset() # エラーが発生したらADALM2000をリセット
        raise
    finally: # パターン出力後の処理
        if global_m2k:
            #close_start = time.time()
            #print(f"{time.time():.3f}: Closing M2KDigital object")
            await global_m2k.stop_and_close() # 最後に残ったデータの吐き出しを含む（awaitで実行するとなぜかエラーが発生 <- でも動作に悪影響はない）
            #close_time = time.time() - close_start
            #print(f"M2KDigital close time: {close_time:.6f} seconds")

    pattern_send_time = time.time() - pattern_send_start
    print(f"Total pattern send time: {pattern_send_time:.6f} seconds")

    total_time = time.time() - start_time
    print(f"{time.time():.3f}: output_to_m2k completed")
    print(f"Total output_to_m2k time: {total_time:.6f} seconds")

load_containers_info()  # コンテナ情報を読み込む