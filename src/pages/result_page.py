import flet as ft
import os
import time
import base64

print(os.getcwd())                          # where Python is running from
print(os.path.exists("assets/utp_logo.png"))  # is it actually finding the file?

def result_view(on_back_click, image_path, area, panels, capacity):
    
    # We read the image file from the hard drive and turn it into raw data
    with open(image_path, "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode('utf-8')
    
    # --- 1. Background Layer: The Interactive Image ---
    img = ft.Image(
        src_base64=img_b64,
        fit="contain",
        scale=1.0,
        left=0,
        top=0,
    )

    def on_pan_update(e: ft.DragUpdateEvent):
        img.left = (img.left or 0) + e.delta_x
        img.top = (img.top or 0) + e.delta_y
        img.update()

    def change_zoom(zoom_in=True):
        factor = 1.1 if zoom_in else 0.9
        new_scale = (img.scale or 1.0) * factor
        
        # Keep scale between 0.5x and 5.0x for your Asus A416J screen
        img.scale = max(0.5, min(5.0, new_scale))
        img.update()

    image_viewer = ft.GestureDetector(
        mouse_cursor=ft.MouseCursor.MOVE,
        on_pan_update=on_pan_update,
        on_scroll=lambda e: change_zoom(zoom_in=e.scroll_delta_y < 0),
        expand=True,
        content=ft.Stack([img])
    )

    # --- 2. UI Layers: Floating Elements ---
    return ft.Stack([
        # The Image Background
        ft.Container(content=image_viewer, expand=True),

        # Zoom Controls (+ / -) (Right Side)
        ft.Column([
            ft.IconButton(icon=ft.icons.ADD_CIRCLE, icon_color=ft.colors.WHITE, icon_size=40, on_click=lambda _: change_zoom(zoom_in=True)), 
            ft.IconButton(icon=ft.icons.REMOVE_CIRCLE, icon_color=ft.colors.WHITE, icon_size=40, on_click=lambda _: change_zoom(zoom_in=False)),
        ], right=20, top=0, bottom=0, alignment=ft.MainAxisAlignment.CENTER),

        # Central Panel Selector & Button (Left Side/Center)
        ft.Column([
            ft.Row([
                ft.Container(
                    padding=30,
                    bgcolor=ft.colors.with_opacity(0.85, ft.colors.BLUE_GREY_100), # Added background for readability
                    border_radius=20,
                    content=ft.Column(
                        controls=[
                            ft.Column([
                                ft.Text("Safe Rooftop Area:", size=16, color=ft.colors.BLACK54, weight="w500"),
                                ft.Text(f"{float(area):.2f} m²", size=32, color=ft.colors.WHITE70, weight="bold") # Uses math variable
                            ], spacing=2),

                            ft.Column([
                                ft.Text("Total Panels Capacity:", size=16, color=ft.colors.BLACK54, weight="w500"),
                                ft.Text(f"{panels} panels", size=32, color=ft.colors.WHITE70, weight="bold") # Uses math variable
                            ], spacing=2),
                            
                            ft.Column([
                                ft.Text("Estimated PV Capacity:", size=16, color=ft.colors.BLACK, weight="w500"),
                                # Changed to kWp (Kilowatt peak), the standard engineering unit for solar capacity
                                ft.Text(f"{capacity} kWp", size=32, color=ft.colors.GREEN_400, weight="bold") # Uses math variable
                            ], spacing=2),
                            
                            ft.Container(height=15), # Spacer
                            
                            ft.ElevatedButton(
                                text="Start New Estimation",
                                width=250,
                                height=50,
                                bgcolor=ft.colors.BLUE_900,
                                color=ft.colors.WHITE,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30)),
                                on_click=on_back_click,
                            ),
                        ], 
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
                        alignment=ft.MainAxisAlignment.CENTER, 
                        spacing=20, 
                        tight=True
                    ),
                ),
            ],
            expand=True, alignment=ft.MainAxisAlignment.START
            )
        ], left=40, top=0, bottom=0, alignment=ft.MainAxisAlignment.CENTER, expand=True),
                
        # Bottom Logos (UTP / EEE)
        ft.Container(
            content=ft.Row([
                # Replace with your actual logo paths
                ft.Image(src="/utp_logo.png", height=40) if os.path.exists("src/assets/utp_logo.png") else ft.Text("UTP", color=ft.colors.ORANGE, weight="bold"),
                ft.Image(src="/eee_logo.png", height=100) if os.path.exists("src/assets/eee_logo.png") else ft.Text("EEE", color=ft.colors.BLUE_900, weight="bold"),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing = 20),
            bottom=20,
            left=0,
            right=0,
        ) 
    ], expand=True)