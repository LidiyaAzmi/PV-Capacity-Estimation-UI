import os
import cv2
import flet as ft
import threading
from pages.homepage import home_view
from pages.next_page import next_view
from pages.result_page import result_view
from utils.uavImageStitching import stitch_images,create_low_res_preview
from utils.pv_calculator import RooftopAnalyzer

analyzer = RooftopAnalyzer("src/assets/best_model.pth")

def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.LIGHT
    page.title = "PV CAPACITY ESTIMATION CALCULATOR"
    page.bgcolor = ft.colors.GREY_200
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # --- Handle selected files ---
    def on_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            # Collect all selected file paths
            paths = [file.path for file in e.files]
            print("Selected files:", paths)
            go_next(paths)
        else:
            print("No file selected")

    # --- FilePicker (allow multiple) ---
    file_picker = ft.FilePicker(
        on_result=on_file_result
    )

    page.overlay.append(file_picker)

    # --- Navigation Functions ---

    def on_start_estimation(image_path, altitude, sensor_w, focal_l, p_width, p_height, p_wattage):
        
        # 1. SHOW THE LOADING SCREEN
        page.controls.clear()
        loading_screen = ft.Container(
            content=ft.Column([
                ft.ProgressRing(width=60, height=60, stroke_width=6, color=ft.colors.BLUE_700),
                ft.Container(height=20),
                ft.Text("Running DeepLabV3+ Inference...", size=24, weight="bold", color=ft.colors.WHITE),
                ft.Text("Segmenting rooftops and applying 1m setback.", size=16, color=ft.colors.WHITE70)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            bgcolor=ft.colors.BLUE_GREY_900,
            expand=True
        )
        page.add(loading_screen)
        page.update() # Force UI to draw the loading screen before the math starts

        # 2. RUN THE AI & PHYSICS MATH
        out_img, safe_area, panels, capacity = analyzer.analyze_stitched_roof(
            image_path=image_path,
            altitude=altitude,
            sensor_w=sensor_w,
            focal_l=focal_l,
            p_width=p_width,
            p_height=p_height,
            p_wattage=p_wattage
        )
        
        # 3. SHOW THE FINAL RESULTS
        page.controls.clear()
        page.add(
            result_view(
                on_back_click=go_home, # Using your original back navigation
                image_path=out_img,    # We pass the NEW image with the green mask
                area=safe_area, 
                panels=panels, 
                capacity=capacity
            )
        )
        page.update()

    def go_next(paths):
        page.controls.clear()

        # 1. UI while stitching
        loading_screen = ft.Column([
            ft.ProgressRing(width=50, stroke_width=5, color=ft.colors.BLUE_900),
            ft.Text("Stitching Drone Surveys...", size=20, weight="bold", color=ft.colors.GREY_900),
            ft.Text("Detecting SIFT features and running RANSAC...", italic=True, color=ft.colors.BLUE_GREY)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True)

        page.add(loading_screen)
        page.update()

        # 2. Setup safe absolute paths
        # Assuming this is in main.py located inside the 'src' folder
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        ASSETS_PATH = os.path.join(BASE_DIR, "assets") # Fixed to avoid src/src/assets

        if not os.path.exists(ASSETS_PATH):
            os.makedirs(ASSETS_PATH)

        # 3. The background task
        def run_stitching():
            # Stitch the images together
            result_np = stitch_images(paths) 
            
            if result_np is not None:
                # Save the panorama ONCE using the guaranteed absolute path
                output_path = os.path.join(ASSETS_PATH, "stitched_panorama.jpg")
                cv2.imwrite(output_path, result_np)
                
                # Navigate to next_page
                page.controls.clear()
                page.add(next_view(
                    page,
                    on_back_click=go_home, 
                    image_path=output_path,  # Pass the absolute path safely!
                    on_start_estimation=on_start_estimation
                ))
            else:
                # Handle failure gracefully
                page.controls.clear()
                page.add(ft.Column([
                    ft.Text("Error: Stitching failed. Please ensure the drone images overlap.", color=ft.colors.RED),
                    ft.ElevatedButton("Back", on_click=lambda _: go_home())
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True))
            
            page.update()

        # Start stitching in a background thread to keep the loading ring spinning
        threading.Thread(target=run_stitching, daemon=True).start()

        
    def go_home(e=None):
        page.controls.clear()
        page.add(
            home_view(
                on_upload_click=lambda _: file_picker.pick_files(
                    allow_multiple=True
                )
            )
        )
        page.update()

    # Initialize app
    go_home()

ft.app(target=main, assets_dir="src/assets")
