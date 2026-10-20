
from flask import Flask, Response, render_template_string, request
from picamera2 import Picamera2
import cv2
import numpy as np
import threading
import time

# ---------------- CONFIGURATION ----------------

WIDTH = 320
HEIGHT = 240
JPEG_QUALITY = 75

app = Flask(__name__)

camera_lock = threading.Lock()

# ---------------- CAMERA SETUP ----------------

camera = Picamera2()

camera_config = camera.create_video_configuration(
    main={
        "size": (WIDTH, HEIGHT),
        "format": "RGB888"
    },
    buffer_count=2
)

camera.configure(camera_config)
camera.start()
time.sleep(2)

print("Camera initialized successfully.", flush=True)


# ---------------- CAMERA CAPTURE ----------------

def capture_frame():
    with camera_lock:
        return camera.capture_array()


# ---------------- COMPUTER VISION ----------------

def process_frame(frame, stage, threshold, roi_percent):
    """
    Stages:
    original -> gray -> roi -> threshold -> denoise -> centroid
    """

    # Convert camera RGB image to OpenCV BGR format
    original = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

    height, width = gray.shape

    # ROI start position measured from the top of the image
    roi_start = int(height * roi_percent / 100)

    roi = gray[roi_start:height, :]

    # Binary inverse threshold: black line becomes white
    _, binary = cv2.threshold(
        roi,
        threshold,
        255,
        cv2.THRESH_BINARY_INV
    )

    # Remove small noise and isolated white pixels
    kernel = np.ones((3, 3), np.uint8)

    denoised = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        kernel
    )

    # Original camera image
    if stage == "original":
        return original

    # Grayscale image
    elif stage == "gray":
        return gray

    # Display only the selected ROI
    elif stage == "roi":
        output = np.zeros_like(gray)
        output[roi_start:height, :] = roi
        return output

    # Threshold result
    elif stage == "threshold":
        output = np.zeros_like(gray)
        output[roi_start:height, :] = binary
        return output

    # Noise-filtered threshold result
    elif stage == "denoise":
        output = np.zeros_like(gray)
        output[roi_start:height, :] = denoised
        return output

    # Detect line centroid
    elif stage == "centroid":
        output = original.copy()

        # Draw ROI boundary
        cv2.line(
            output,
            (0, roi_start),
            (width - 1, roi_start),
            (0, 255, 255),
            1
        )

        moments = cv2.moments(denoised)

        if moments["m00"] > 0:
            # Centroid relative to the full image
            cx = int(moments["m10"] / moments["m00"])
            cy = roi_start + int(
                moments["m01"] / moments["m00"]
            )

            # Error relative to image center
            error = cx - width // 2

            cv2.circle(
                output,
                (cx, cy),
                6,
                (0, 0, 255),
                -1
            )

            cv2.line(
                output,
                (width // 2, roi_start),
                (width // 2, height - 1),
                (255, 0, 0),
                1
            )

            cv2.putText(
                output,
                f"Centroid: {cx}",
                (5, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 255, 0),
                1
            )

            cv2.putText(
                output,
                f"Error: {error}",
                (5, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 255, 0),
                1
            )

        else:
            cv2.putText(
                output,
                "Line not detected",
                (5, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 0, 255),
                1
            )

        return output

    # Fallback for an invalid stage
    return original


# ---------------- VIDEO STREAM GENERATOR ----------------

def generate_stream(stage, threshold, roi_percent):
    while True:
        try:
            frame = capture_frame()

            output = process_frame(
                frame,
                stage,
                threshold,
                roi_percent
            )

            ok, encoded = cv2.imencode(
                ".jpg",
                output,
                [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
            )

            if not ok:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + encoded.tobytes()
                + b"\r\n"
            )

        except GeneratorExit:
            break

        except Exception as exc:
            print(
                "Frame processing error:",
                exc,
                flush=True
            )
            time.sleep(0.1)


# ---------------- WEB DASHBOARD ----------------

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1">

    <title>Raspberry Pi Line Follower CV</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f1f3f5;
            color: #202124;
            margin: 0;
            padding: 16px;
        }

        .container {
            max-width: 850px;
            margin: auto;
        }

        h2 {
            margin-bottom: 6px;
        }

        .panel {
            background: white;
            border-radius: 10px;
            padding: 16px;
            margin: 14px 0;
            box-shadow: 0 2px 8px #00000012;
        }

        label {
            display: block;
            font-weight: bold;
            margin-top: 12px;
            margin-bottom: 6px;
        }

        select, input {
            width: 100%;
            box-sizing: border-box;
        }

        select {
            padding: 9px;
            font-size: 16px;
        }

        input[type=range] {
            cursor: pointer;
        }

        .value {
            font-weight: normal;
            color: #1769aa;
        }

        img {
            width: 100%;
            height: auto;
            background: #222;
            display: block;
            border-radius: 6px;
        }

        .note {
            color: #555;
            font-size: 13px;
        }
    </style>
</head>

<body>
<div class="container">

    <h2>Line Follower — Computer Vision</h2>
    <p class="note">
        Raspberry Pi Zero 2 W | IMX219 Camera |
        320 × 240
    </p>

    <div class="panel">
        <label for="stage">Processing stage</label>

        <select id="stage">
            <option value="original">1. Original camera</option>
            <option value="gray">2. Grayscale</option>
            <option value="roi">3. Region of interest (ROI)</option>
            <option value="threshold">4. Threshold</option>
            <option value="denoise">5. Noise removal</option>
            <option value="centroid">6. Centroid and error</option>
        </select>

        <label for="threshold">
            Threshold: <span id="thresholdValue"
                             class="value">75</span>
        </label>

        <input type="range"
               id="threshold"
               min="0"
               max="255"
               value="75">

        <label for="roi">
            ROI start: <span id="roiValue"
                             class="value">55%</span>
        </label>

        <input type="range"
               id="roi"
               min="10"
               max="90"
               value="55">
    </div>

    <div class="panel">
        <h3>Live processing output</h3>

        <img id="feed"
             src="/stream?stage=original&threshold=75&roi=55"
             alt="Camera stream">

        <p class="note">
            If the line is not detected, adjust the threshold
            and ROI position. The ROI percentage is measured
            from the top of the image.
        </p>
    </div>

</div>

<script>
    const stageInput = document.getElementById("stage");
    const thresholdInput = document.getElementById("threshold");
    const roiInput = document.getElementById("roi");

    const thresholdValue = document.getElementById("thresholdValue");
    const roiValue = document.getElementById("roiValue");
    const feed = document.getElementById("feed");

    function updateStream() {
        const stage = stageInput.value;
        const threshold = thresholdInput.value;
        const roi = roiInput.value;

        thresholdValue.textContent = threshold;
        roiValue.textContent = roi + "%";

        const url = "/stream?stage=" +
            encodeURIComponent(stage) +
            "&threshold=" + threshold +
            "&roi=" + roi +
            "&t=" + Date.now();

        feed.src = url;
    }

    stageInput.addEventListener("change", updateStream);
    thresholdInput.addEventListener("input", updateStream);
    roiInput.addEventListener("input", updateStream);
</script>

</body>
</html>
"""


# ---------------- ROUTES ----------------

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)


@app.route("/stream")
def stream():
    # Read parameters inside the route, not the generator.
    stage = request.args.get("stage", "original")

    valid_stages = {
        "original",
        "gray",
        "roi",
        "threshold",
        "denoise",
        "centroid"
    }

    if stage not in valid_stages:
        stage = "original"

    try:
        threshold = max(
            0,
            min(255, int(request.args.get("threshold", 75)))
        )
    except (ValueError, TypeError):
        threshold = 75

    try:
        roi_percent = max(
            10,
            min(90, int(request.args.get("roi", 55)))
        )
    except (ValueError, TypeError):
        roi_percent = 55

    return Response(
        generate_stream(stage, threshold, roi_percent),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# ---------------- START SERVER ----------------

if __name__ == "__main__":
    try:
        app.run(
            host="0.0.0.0",
            port=5000,
            threaded=True,
            debug=False
        )
    finally:
        camera.stop()
