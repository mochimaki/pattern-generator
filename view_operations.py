import flet as ft

# グローバル変数として定義
temp_channel_to_display = []

def sort_channels_dialog(page, channel_to_display, channel_dropdown, dataframes, channel_colors, chart_update_func):
    global temp_channel_to_display
    temp_channel_to_display = channel_to_display.copy()

    if channel_dropdown.value:
        if channel_dropdown.value not in channel_to_display:
            channel_to_display.insert(0, channel_dropdown.value)
        existing_channels_dropdowns = []
        all_channels = [channel.text for channel in channel_dropdown.options]
        
        for channel in channel_to_display:
            options = [ft.dropdown.Option(text=ch) for ch in channel_to_display]
            if channel != channel_dropdown.value:
                options.append(ft.dropdown.Option(text="Hide"))
            channel_number = int(channel.split()[-1])
            color = channel_colors[channel_number % len(channel_colors)]
            dropdown = ft.Dropdown(
                options=options,
                value=channel,
                color=color,
                on_change=lambda e, dropdowns=existing_channels_dropdowns: update_channel_selection(dropdowns, temp_channel_to_display, channel_dropdown, channel_to_display, channel_colors)
            )
            if channel == channel_dropdown.value:
                dropdown.border_color = color
                dropdown.border_width = 2
            existing_channels_dropdowns.append(dropdown)

        scrollable_column = ft.Column(
            controls=existing_channels_dropdowns,
            scroll=ft.ScrollMode.ALWAYS,
            height=300,
            width=300
        )

        add_channel_dropdown = ft.Dropdown(
            label="Channel to add",
            options=[ft.dropdown.Option(text=channel) for channel in all_channels if channel not in channel_to_display and not dataframes[channel].empty],
            hint_text="Select a channel",
        )

        dialog = ft.AlertDialog(
            title=ft.Text("Sort Channels"),
            content=ft.Column(controls=[scrollable_column, ft.Divider(color="white"), add_channel_dropdown], spacing=10),
            actions=[
                ft.TextButton(text="Apply", on_click=lambda e: apply_sort(e)),
                ft.TextButton(text="Cancel", on_click=lambda e: close_dialog(page))
            ],
            actions_alignment="end",
            modal=False
        )
        
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def apply_sort(e):
        global temp_channel_to_display  # nonlocalをglobalに変更
        channel_to_display[:] = temp_channel_to_display
        dialog.open = False
        page.update()
        chart_update_func()

def select_channels_dialog(page, channel_to_display, channel_dropdown, chart_update):
    if channel_dropdown.value:
        def on_select_all_change(e):
            for checkbox in channel_checkboxes:
                checkbox.value = e.control.value
            update_select_all_checkbox()
            page.update()

        def on_checkbox_change(e):
            update_select_all_checkbox()

        def update_select_all_checkbox():
            select_all_checkbox.value = all(checkbox.value for checkbox in channel_checkboxes)

        select_all_checkbox = ft.Checkbox(
            label="Select All",
            value=all(f"Channel {i}" in channel_to_display for i in range(16) if f"Channel {i}" != channel_dropdown.value),
            on_change=on_select_all_change
        )

        channel_checkboxes = []
        for i in range(16):
            if f"Channel {i}" != channel_dropdown.value:
                checkbox = ft.Checkbox(
                    label=f"Channel {i}",
                    value=f"Channel {i}" in channel_to_display,
                    on_change=on_checkbox_change
                )
                channel_checkboxes.append(checkbox)

        scrollable_column = ft.Column(
            controls=[select_all_checkbox, ft.Divider()] + channel_checkboxes,
            scroll=ft.ScrollMode.ALWAYS,
            height=300,
            width=300
        )

        def apply_channel_selection():
            channel_to_display.clear()
            channel_to_display.append(channel_dropdown.value)
            for checkbox in channel_checkboxes:
                if checkbox.value:
                    channel_to_display.append(checkbox.label)
            chart_update()
            close_dialog(page)

        dialog = ft.AlertDialog(
            title=ft.Text("Select Channels"),
            content=scrollable_column,
            actions=[
                ft.TextButton(text="Apply", on_click=lambda e: apply_channel_selection()),
                ft.TextButton(text="Cancel", on_click=lambda e: close_dialog(page))
            ],
            actions_alignment="end",
            modal=False
        )
        
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

def update_channel_selection(existing_channels_dropdowns, temp_channel_to_display, channel_dropdown, channel_to_display, channel_colors):
    ii = 0
    while temp_channel_to_display[ii] == existing_channels_dropdowns[ii].value and ii < len(temp_channel_to_display) - 1:
        ii += 1
    if existing_channels_dropdowns[ii].value != "Hide":
        index = temp_channel_to_display.index(existing_channels_dropdowns[ii].value)
        existing_channels_dropdowns[index].value = temp_channel_to_display[ii]
    
    for jj in range(len(temp_channel_to_display)):
        temp_channel_to_display[jj] = existing_channels_dropdowns[jj].value

    for jj in range(len(channel_to_display)):   
        options = [ft.dropdown.Option(text=ch) for ch in channel_to_display]
        if existing_channels_dropdowns[jj].value != channel_dropdown.value:
            options.append(ft.dropdown.Option(text="Hide"))
        existing_channels_dropdowns[jj].options = options
        channel_number = int(existing_channels_dropdowns[jj].value.split()[-1])
        color = channel_colors[channel_number % len(channel_colors)]
        existing_channels_dropdowns[jj].color = color
        if existing_channels_dropdowns[jj].value == channel_dropdown.value:
            existing_channels_dropdowns[jj].border_color = color
            existing_channels_dropdowns[jj].border_width = 2
        else:
            existing_channels_dropdowns[jj].border_color = None
            existing_channels_dropdowns[jj].border_width = None
        existing_channels_dropdowns[jj].update()

def apply_changes(dropdowns, add_channel_dropdown, page, channel_to_display, temp_channel_to_display, chart_update):
    channel_to_display.clear()
    for dropdown in dropdowns:
        if dropdown.value != "Hide":
            channel_to_display.append(dropdown.value)
    if add_channel_dropdown.value:
        channel_to_display.append(add_channel_dropdown.value)
    page.update()
    close_dialog(page)
    temp_channel_to_display[:] = channel_to_display[:]
    chart_update()

def close_dialog(page):
    if page.overlay and len(page.overlay) > 0:
        dialog = page.overlay.pop()
        dialog.open = False
        page.update()