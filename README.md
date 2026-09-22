# Rooftop PV estimate desk. app.

## Run the app

### uv

Run as a desktop app:

```
uv run flet run
```

Run as a web app:

```
uv run flet run --web
```

For more details on running the app, refer to the [Getting Started Guide](https://docs.flet.dev/).

### macOS

```
flet build macos -v
```

For more details on building macOS package, refer to the [macOS Packaging Guide](https://docs.flet.dev/publish/macos/).

### Linux

```
flet build linux -v
```

For more details on building Linux package, refer to the [Linux Packaging Guide](https://docs.flet.dev/publish/linux/).

### Windows

```
flet build windows -v
```

For more details on building Windows package, refer to the [Windows Packaging Guide](https://docs.flet.dev/publish/windows/).

## Flow of app

1. After running the app, it will prompt you to upload images. This prompt is for users to upload drone images taken prior to the estimation.
<img width="1440" height="1024" alt="Image Upload" src="https://github.com/user-attachments/assets/efcf4705-b76a-4225-afa6-2e87bfe002c7" />

2. The app will stitch the images together and create a panorama. Images with less than 80% overlap will produce an error or a disoriented panorama. A sample of a successful stitched image can be seen as below.
<img width="480" height="341" alt="stitched_panorama" src="https://github.com/user-attachments/assets/70e1f8f8-bde5-4b02-a567-db0f5e6398bd" />

This panorama can be found in the assets folder after stitching.

5. Users are given a review of the panorama before proceeding with the estimation. You can choose to re-upload images if the result panorama is not reaching your standard.
<img width="1440" height="1024" alt="Stitched image" src="https://github.com/user-attachments/assets/7e12e120-a8be-410c-ade1-bc9a40ede1a7" />

6. The 
