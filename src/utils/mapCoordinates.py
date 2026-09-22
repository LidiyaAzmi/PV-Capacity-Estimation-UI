import flet

def map_coordinates(img_control, original_width, original_height):
    """
    Maps Flet screen coordinates to original image pixel coordinates.
    img_control: The ft.Image object
    original_width/height: Dimensions of the high-res stitched panorama
    """
    # 1. Get the current scale and offsets from the UI
    # We use abs() because img.left/top are usually negative when panning
    current_scale = img_control.scale or 1.0
    offset_x = abs(img_control.left or 0)
    offset_y = abs(img_control.top or 0)

    # 2. Get the dimensions of the container (the 'window' the user sees)
    window_w = img_control.width or 800  # Default or dynamic width
    window_h = img_control.height or 600 # Default or dynamic height

    # 3. Calculate the center of the current view in screen pixels
    center_screen_x = offset_x + (window_w / 2)
    center_screen_y = offset_y + (window_h / 2)

    # 4. Map to original image pixels
    # We divide by scale because the screen pixels are 'stretched'
    pixel_x = int((center_screen_x / current_scale) * (original_width / window_w))
    pixel_y = int((center_screen_y / current_scale) * (original_height / window_h))

    # Ensure we stay within image boundaries
    pixel_x = max(0, min(pixel_x, original_width))
    pixel_y = max(0, min(pixel_y, original_height))

    return pixel_x, pixel_y