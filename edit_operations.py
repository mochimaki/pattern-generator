import flet as ft
import copy

def copy_dataframe_dialog(page, channel_dropdown, dataframes, copy_dataframe):
    all_channels = [channel.text for channel in channel_dropdown.options]
    copy_channel_dropdown = ft.Dropdown(
        label="Copy from",
        options=[ft.DropdownOption(text=channel) for channel in all_channels if not dataframes[channel].empty and channel != channel_dropdown.value],
        hint_text="Select a channel",
    )
    def on_copy_click(e):
        if copy_channel_dropdown.value is None or channel_dropdown.value is None:
            snackbar = ft.SnackBar(content=ft.Text("Please select a channel from both dropdowns."), open=True)
            page.add(snackbar)
            return
        copy_dataframe(copy_channel_dropdown.value, page)
    dialog = ft.AlertDialog(
        title=ft.Text("Copy DataFrame"),
        content=ft.Column([copy_channel_dropdown], spacing=10),
        actions=[ft.TextButton(text="Copy", on_click=on_copy_click),
                 ft.TextButton(text="Cancel", on_click=lambda e: close_dialog(page))],
        actions_alignment="end",
        modal=False
    )
    
    page.overlay.append(dialog)
    dialog.open = True
    page.update()

def copy_dataframe(channel, page, dataframes, channel_dropdown, channel_dropdown_change):
    dataframes[channel_dropdown.value] = copy.deepcopy(dataframes[channel])
    close_dialog(page)
    channel_dropdown_change(channel_dropdown.value, page)

def close_dialog(page):
    if page.overlay and len(page.overlay) > 0:
        dialog = page.overlay.pop()
        dialog.open = False
        page.update()