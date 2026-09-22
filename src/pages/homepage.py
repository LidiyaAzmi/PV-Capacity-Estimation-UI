import flet as ft
import os

def home_view(on_upload_click):

    return ft.Column(
        [
            # Spacer — pushes logos to bottom
            ft.Container(expand=True),
            
            ft.Container(
                content=ft.Text(
                    "PV CAPACITY ESTIMATION CALCULATOR",
                    size=32,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.colors.BLACK45,
                    weight=ft.FontWeight.W_900,
                ),
                width=500,
                padding=30,
                alignment=ft.alignment.center,
            ),

            ft.Container(
                width=463,
                height=174,
                bgcolor=ft.colors.WHITE,
                border=ft.border.all(1, ft.colors.GREY_500),
                border_radius=30,
                alignment=ft.alignment.center,
                on_click=on_upload_click,
                content=ft.Column(
                    [
                        ft.ElevatedButton(
                            content=ft.Text(
                                "Upload Image(s)",
                                color=ft.colors.WHITE,
                                size=16,
                            ),
                            bgcolor=ft.colors.BLUE_900,
                            width=200,
                            height=50,
                            on_click=on_upload_click,
                        ),
                        ft.Text(
                            "Select one or multiple rooftop images",
                            color=ft.colors.BLACK,
                            size=16,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),

            # Spacer — pushes logos to bottom
            ft.Container(expand=True),

            # Bottom Logos (UTP / EEE)
            ft.Container(
                content=ft.Row([
                    # Replace with your actual logo paths
                    ft.Image(src="/utp_logo.png", height=40) if os.path.exists("src/assets/utp_logo.png") else ft.Text("UTP", color=ft.colors.ORANGE, weight="bold"),
                    ft.Image(src="/eee_logo.png", height=100) if os.path.exists("src/assets/eee_logo.png") else ft.Text("EEE", color=ft.colors.BLUE_900, weight="bold"),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing = 20),
                padding=ft.padding.only(bottom=20),
                alignment=ft.alignment.bottom_center,
            ) 
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )
