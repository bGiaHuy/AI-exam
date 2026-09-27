import os
from PIL import Image

screenshots_dir = r"deliverables\ha_noi\screenshots"
os.makedirs(screenshots_dir, exist_ok=True)

# 1. Base full monitor image
full_img_path = os.path.join(screenshots_dir, "live_monitor_initial.png")
multi_cam_path = os.path.join(screenshots_dir, "live_monitor_multi_cam.png")

if os.path.exists(full_img_path):
    img = Image.open(full_img_path)
    img.save(multi_cam_path)
    print(f"Saved {multi_cam_path} ({img.size})")

    # Crop Right Panel: Incident Matrix
    # Image size is (1600, 1000)
    w, h = img.size
    # Right panel starts around x = 1200
    incident_box = (int(w * 0.74), int(h * 0.06), w, h)
    incident_img = img.crop(incident_box)
    incident_path = os.path.join(screenshots_dir, "incident_matrix_panel.png")
    incident_img.save(incident_path)
    print(f"Saved {incident_path} ({incident_img.size})")

    # Crop Multi-Camera Feeds area
    cam_box = (0, int(h * 0.06), int(w * 0.74), h)
    cam_img = img.crop(cam_box)
    cam_path = os.path.join(screenshots_dir, "camera_monitoring_grid.png")
    cam_img.save(cam_path)
    print(f"Saved {cam_path} ({cam_img.size})")

print("Screenshot processing complete.")
