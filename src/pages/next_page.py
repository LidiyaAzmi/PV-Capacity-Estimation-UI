import flet as ft
import cv2
import os
from utils.mapCoordinates import map_coordinates
import time

def next_view(page: ft.Page, on_back_click, image_path, on_start_estimation):
    """ full_img_temp = None
    # Retry loop: wait up to 2 seconds for the file to be "ready"
    for _ in range(20): 
        if os.path.exists(image_path):
            full_img_temp = cv2.imread(image_path)
            if full_img_temp is not None:
                break
        time.sleep(0.1) 

    if full_img_temp is None:
        # Fallback for DJI Neo 4:3 standard if file load fails
        ORIG_H, ORIG_W = 3000, 4000 
    else:
        ORIG_H, ORIG_W = full_img_temp.shape[:2]
        del full_img_temp  """
    
    filename_only = os.path.basename(image_path)

    # --- 2. Core Image Control ---
    # Use a unique key for the image to force Flet to reload the src from disk
    img = ft.Image(
        src=filename_only,
        key=str(time.time()), 
        fit="contain",
        scale=1.0,
        left=0,
        top=0,
    )

    """ 
    # --- 3. ROI Logic (Separated for Clarity) ---
    def get_high_res_roi(x_center, y_center, zoom_level):
        Extracts a high-res crop based on coordinate mapping.
        full_img = cv2.imread(image_path)
        
        # Calculate crop window size based on zoom
        crop_w, crop_h = int(ORIG_W / zoom_level), int(ORIG_H / zoom_level)
        
        # Calculate top-left corner and clamp to image boundaries
        x1 = max(0, min(int(x_center - crop_w // 2), ORIG_W - crop_w))
        y1 = max(0, min(int(y_center - crop_h // 2), ORIG_H - crop_h))
        
        roi = full_img[y1:y1+crop_h, x1:x1+crop_w]
        
        roi_path = "assets/current_zoom_roi.jpg"
        cv2.imwrite(roi_path, roi) # Use high-quality JPG for PV estimation
        return roi_path

    def update_view_roi():
        Decides whether to show the preview or a high-res ROI tile.
        current_scale = img.scale or 1.0
        
        if current_scale > 1.5:
            # Dynamically resolve coordinates using the map_coordinates utility
            real_x, real_y = map_coordinates(
                img, 
                ORIG_W, ORIG_H, 
                page.window_width, page.window_height
            )

            roi_src = get_high_res_roi(real_x, real_y, current_scale)

            img.src = f"{roi_src}?{time.time()}"
        else:
            img.src = f"stitched_panorama.jpg?{time.time()}"
            
        # Force Flet to reload the image by changing the key
        img.key = str(time.time())
        img.update()
        """
    DRONE_DATABASE = {
        "DJI Neo": {"sensor_w": 6.3, "focal_l": 2.8}, 
        
        "DJI Mini 3 Pro": {"sensor_w": 6.4, "focal_l": 6.7}
    }

    PANEL_DATABASE = {
        "Longi Hi-MO 6 Scientist": {"width": 1.134, "height": 1.762, "wattage": 445},
        "JA Solar JAM54D40": {"width": 1.134, "height": 1.762, "wattage": 445},
        "Trina Solar Vertex S+": {"width": 1.134, "height": 1.722, "wattage": 445}
    }

    panel_dropdown = ft.Dropdown(
        label="Panel Provider", label_style=ft.TextStyle(color=ft.colors.BLUE_900, weight="bold"),width=250, color=ft.colors.BLACK,
        options=[
            ft.dropdown.Option("Longi Hi-MO 6 Scientist"),
            ft.dropdown.Option("JA Solar JAM54D40"),
            ft.dropdown.Option("Trina Solar Vertex S+")
        ],
        value="Longi Hi-MO 6 Scientist"
    )

    drone_dropdown = ft.Dropdown(
        label="Drone Camera", label_style=ft.TextStyle(color=ft.colors.BLUE_900, weight="bold"), width=250,color=ft.colors.BLACK,
        options=[
            ft.dropdown.Option("DJI Neo"),
            ft.dropdown.Option("DJI Mini 3 Pro")
        ],
        value="DJI Neo" # Your FYP drone
    )

    height_input = ft.TextField(label="Flying Height (m)", label_style=ft.TextStyle(color=ft.colors.BLUE_900, weight="bold"), width=250, color=ft.colors.BLACK, value="50")

    def handle_estimation_click(e):
        try:
            altitude = float(height_input.value)
        except ValueError:
            altitude = 50.0 
            
        # 1. Lookup the physical specs based on the dropdown string
        d_specs = DRONE_DATABASE.get(drone_dropdown.value, DRONE_DATABASE["DJI Neo"])
        p_specs = PANEL_DATABASE.get(panel_dropdown.value, PANEL_DATABASE["Longi Hi-MO 6 Scientist"])
        
        # 2. Pass the raw math variables back to main.py
        on_start_estimation(
            image_path, 
            altitude, 
            d_specs["sensor_w"], 
            d_specs["focal_l"], 
            p_specs["width"], 
            p_specs["height"], 
            p_specs["wattage"]
        )
    # --- 4. Event Handlers ---
    def on_pan_update(e: ft.DragUpdateEvent):
        img.left = (img.left or 0) + e.delta_x
        img.top = (img.top or 0) + e.delta_y
        img.update()

    def change_zoom(zoom_in=True):
        factor = 1.1 if zoom_in else 0.9
        new_scale = (img.scale or 1.0) * factor
        img.scale = max(0.5, min(5.0, new_scale)) # Bound scale for your Asus screen
        #update_view_roi()
        img.update()

    # --- 5. UI Layout ---
    image_viewer = ft.GestureDetector(
        mouse_cursor=ft.MouseCursor.MOVE,
        on_pan_update=on_pan_update,
        #on_pan_end=lambda _: update_view_roi(), # Snap to high-res after panning
        on_scroll=lambda e: change_zoom(zoom_in=e.scroll_delta_y < 0),
        content=ft.Stack([img])
    )

    return ft.Stack([
        # Background Viewer
        ft.Container(content=image_viewer, expand=True),
        # Floating Navigation (Top Left)
        ft.Container(
            content=ft.TextButton(
                content=ft.Row([
                    # Set the icon color to white
                    ft.Icon(ft.icons.ARROW_BACK, color=ft.colors.WHITE), 
                    # Set the text color to white
                    ft.Text("Back", color=ft.colors.WHITE)
                ]),
                on_click=on_back_click
            ),
            left=20, top=20
        ),

        ft.Container(
            content=
                # Parameters Panel (Center-Right)
                ft.Container(
                    padding=20, 
                    bgcolor=ft.colors.with_opacity(0.9, ft.colors.WHITE),
                    border_radius=20,
                    width=300,
                    content=ft.Column([
                        drone_dropdown,
                        panel_dropdown,
                        height_input,
                        ft.Row([
                            ft.ElevatedButton(
                                "Continue Estimation", 
                                bgcolor=ft.colors.BLUE_900, 
                                color=ft.colors.WHITE,
                                on_click=handle_estimation_click
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    ], spacing=15, tight=True)
                ),
                left=40,                   # distance from left edge
                top=0,
                bottom=0,
                # vertically center it
                alignment=ft.alignment.center_left,
            ),

            ft.Container(
                 content=
                 # Zoom Sidebar (Right)
                 ft.Column([
                    ft.IconButton(ft.icons.ADD_CIRCLE, icon_color=ft.colors.WHITE, icon_size=40, on_click=lambda _: change_zoom(True)),
                    ft.IconButton(ft.icons.REMOVE_CIRCLE, icon_color=ft.colors.WHITE, icon_size=40, on_click=lambda _: change_zoom(False)),
                ], spacing=8, tight=True),
                right=20,                  # distance from right edge
                top=0, bottom=0,
                alignment=ft.alignment.center_right,
            ),

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