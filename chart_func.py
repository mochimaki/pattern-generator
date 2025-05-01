import matplotlib
matplotlib.use('Agg')  # GUIバックエンドを使用しない設定
import matplotlib.pyplot as plt
from flet.matplotlib_chart import MatplotlibChart
import numpy as np

# start_indexおよびend_indexをインデックスで受け取る関数
def generate_timing_chart(dataframes, channel_to_display, editing_channel, channel_colors, start_index=0, end_index=None, selected_periods=None):
    if not channel_to_display:
        print("チャンネルリストが空です。空のチャートを返します。")
        fig, ax = plt.subplots(figsize=(10, 1.2))
        ax = create_empty_chart(fig, "Channel 0")
        return MatplotlibChart(fig)
    try:
        time_factors = {'sec.': 1, 'msec.': 1e-3, 'microsec.': 1e-6}
        df_editing = dataframes.get(editing_channel, None)

        if end_index is None:
            if df_editing is None or df_editing.empty:
                print("編集中のチャンネルにデータがありません。空のチャートを返します。")
                fig, ax = plt.subplots(figsize=(10, 1.2))
                ax = create_empty_chart(fig, "Editing Channel")
                return MatplotlibChart(fig)
            end_index = len(df_editing['duration'])
        # 累積時間を計算
        times = [0]
        for duration, unit in zip(df_editing['duration'], df_editing['unit']):
            times.append(times[-1] + duration * time_factors[unit])
        # 選択されたデータのインデックスを使用して、start_timeとend_timeを計算
        end_time = times[end_index]
        start_time = times[start_index]
        # start_timeからend_timeの時間をもとに時間軸の単位を選定
        if end_time - start_time < 1e-3:
            unit_label = "time [μs]"
            scale_factor = 1e6  
        elif end_time - start_time < 1:
            unit_label = "time [ms]"
            scale_factor = 1e3
        else:
            unit_label = "time [s]"
            scale_factor = 1
        # ダークテーマを使用
        plt.style.use('dark_background')
        # チャネル数に応じてサイズを指定しチャートを作成
        fig, axs = plt.subplots(len(channel_to_display), 1, figsize=(10, (np.sqrt(len(channel_to_display)) * 1.7)), sharex=True)
        # axsがnp.ndarrayでない場合（チャネル数が1の場合）はリストに変換
        if not isinstance(axs, np.ndarray):
            axs = [axs]

        for idx, channel in enumerate(channel_to_display):
            df = dataframes.get(channel, None)
            if df is None or df.empty:
                print(f"チャンネル {channel} のdfが空です。空のチャートを表示します。")
                axs[idx].clear()
                axs[idx].set_yticks([]) # y軸の目盛りを非表示に設定
                axs[idx].set_ylim([-0.1 + idx, 1.1 + idx]) # y軸の範囲を設定
                axs[idx].set_ylabel("Ch" + channel.split()[-1]) # y軸のラベルを設定
                continue

            states = df['state'].apply(lambda x: 1 if x == 'high' else 0).tolist()
            if not states:
                print(f"チャンネル {channel} のstatesが空です。空のチャートを表示します。")
                axs[idx].clear()
                axs[idx] = create_empty_chart(fig, channel)
                continue

            durations = df['duration'].apply(float).tolist()
            if not durations:
                print(f"チャンネル {channel} のdurationsが空です。空のチャートを表示します。")
                axs[idx].clear()
                axs[idx] = create_empty_chart(fig, channel)
                continue

            units = df['unit'].tolist()
            times = [0]
            for duration, unit in zip(durations, units): # 累積時間を計算
                times.append(times[-1] + duration * time_factors[unit])
            # timesの中で、start_timeよりも値が等しいか大きくなる最初のインデックスを取得
            sub_start_index = next((i for i, t in enumerate(times) if t >= start_time), None)
            if sub_start_index is None:
                sub_start_index = 0
            # timesの中で、end_timeよりも値が等しいか大きくなる最初のインデックスを取得
            sub_end_index = next((i for i, t in enumerate(times) if t >= end_time), None)
            if sub_end_index is None:
                sub_end_index = len(times) - 1
            # 選択された期間の時間とステートを取得
            sub_times = times[sub_start_index:sub_end_index]
            sub_states = states[sub_start_index:sub_end_index]  
            
            if not sub_times:
                print(f"チャンネル {channel} の選択された期間がないです。空のチャートを表示します。")
                axs[idx].clear()
                axs[idx] = create_empty_chart(fig, channel)
                continue
            # 選択された期間の開始時間がstart_timeと異なる場合は、start_timeを追加
            if sub_times[0] != start_time:
                sub_times.insert(0, start_time)
                sub_states.insert(0, states[sub_start_index - 1])
            # 選択された期間の終了時間がend_timeと異なる場合は、end_timeを追加
            if sub_times[-1] != end_time:
                sub_times.append(end_time)
                sub_states.append(states[sub_end_index - 1])

            adjusted_states = [s + idx for s in sub_states] # チャンネルのインデックスをステートに加算
            color = channel_colors[int(channel.split()[-1])] # チャンネルの色を取得

            # sub_times の各要素に scale_factor を乗算
            scaled_times = [t * scale_factor for t in sub_times]
            axs[idx].step(scaled_times, adjusted_states, where='post', color=color) # チャンネルのステートを表示
            axs[idx].set_yticks([]) # y軸の目盛りを非表示に設定
            axs[idx].set_ylim([-0.1 + idx, 1.1 + idx]) # y軸の範囲を設定
            axs[idx].set_ylabel("Ch" + channel.split()[-1]) # y軸のラベルを設定

            if channel == editing_channel: # 編集中のチャンネルを赤線で表示
                axs[idx].axhline(y=idx + 0.5, color='red', linestyle='--') # 編集中のチャンネルを赤線で表示
                # selected_periodsを使用して、selected_periodsの範囲を赤色で表示
                if selected_periods: # data_tableで選択された期間を赤色で表示
                    for period in selected_periods:
                        if period - start_index < 0 or period - start_index > len(times) - 2:
                            continue

                        start_period = times[period - start_index] # 選択された期間の開始時間
                        end_period = times[period + 1 - start_index] # 選択された期間の終了時間
                        axs[idx].axvspan(start_period, end_period, color='red', alpha=0.3) # 選択された期間を赤色で表示
        for ax in axs:
            ax.set_xlim([start_time * scale_factor, end_time * scale_factor])
            ax.grid(True, which='both', axis='x', color='gray', linestyle='-', linewidth=0.5)

        plt.xlabel(unit_label)
        plt.tight_layout()
        plt.close(fig)
        chart = MatplotlibChart(fig)
        chart.width = 1200
        chart.height = np.sqrt(len(channel_to_display)) * 150
        return chart
    
    except KeyError as e:
        print(f"KeyError: {e}")
        return None
    
def create_empty_chart(fig, channel):
    plt.switch_backend('Agg')  # 必要に応じてバックエンドを切り替え
    ax = fig.add_subplot(1, 1, 1)  # 新しい ax を追加
    ax.set_yticks([])  # y軸の目盛りを非表示に設定
    ax.set_ylim([-0.1, 1.1])  # y軸の範囲を設定
    ax.set_ylabel("Ch" + channel.split()[-1])  # チャンネル名をy軸のラベルとして設定
    return ax  # ax を返す