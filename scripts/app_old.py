import sys
import threading
import queue
import tempfile
import os
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response, send_file

sys.path.insert(0, str(Path(__file__).parent))
from timelapse_tool import download_video_clip, make_timelapse

app = Flask(__name__, root_path=os.path.join(os.getcwd(), "timelapse"), static_url_path='', static_folder='.', template_folder='comp')

log_queue: queue.Queue = queue.Queue()
job_running = False
output_file: str = None     # path to the finished timelapse, ready for download
temp_dir: str = None        # current job's temp directory


def log(msg: str):
    print(msg)
    log_queue.put(msg)


def run_pipeline(data: dict):
    global job_running, output_file, temp_dir

    job_running = True
    output_file = None

    temp_dir = os.path.join(tempfile.getcwd(), "timelapse") + "temp/"
    video_path = temp_dir + "video.mp4"
    clip_path      = temp_dir + "clip.mp4"
    timelapse_path = temp_dir + "timelapse.mp4"

    # Clean up temp dir from previous run
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    Path(temp_dir).mkdir(parents=True, exist_ok=True)

    try:
        log("▶ Downloading clip from YouTube…")
        download_video_clip(
            video_url = data["url"],
            start_time = data["start"],
            end_time = data["end"],
            output_path = clip_path,
        )

        log("▶ Rendering timelapse…")

        # two speed passes with the specified multiplier cut in half
        make_timelapse(
            output_path = video_path,
            clip_path = clip_path,
            speed_multiplier = data["speed"] / 2,
        )
        make_timelapse(
            output_path = timelapse_path,
            clip_path = video_path,
            speed_multiplier = data["speed"] / 2,
        )

        output_file = timelapse_path
        log("✓ Done — your download will start shortly.")

    except Exception as e:
        log(f"✗ Error: {e}")
        # Clean up temp dir on failure
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir = None

    finally:
        job_running = False
        log("__DONE__")
        


@app.route("/run", methods=["POST"])
def run():
    global output_file
    if job_running:
        return jsonify({"error": "A job is already running."}), 409
    output_file = None
    data = request.json
    thread = threading.Thread(target=run_pipeline, args=(data,), daemon=True)
    thread.start()
    return jsonify({"status": "started"})


@app.route("/logs")
def logs():
    def stream():
        while True:
            try:
                msg = log_queue.get(timeout=60)
                yield f"data: {msg}\n\n"
                if msg == "__DONE__":
                    break
            except queue.Empty:
                yield "data: \n\n"   # keepalive
    return Response(stream(), mimetype="text/event-stream")

@app.route("/status")
def status():
    return jsonify({"job_running": job_running, "output_file": output_file})

@app.route("/download")
def download():
    global output_file, temp_dir
    if not output_file or not os.path.exists(output_file):
        return "No file ready.", 404

    path = output_file
    tmp  = temp_dir

    return send_file(
        path,
        as_attachment=True,
        download_name="timelapse.mp4",
        mimetype="video/mp4",
    )


@app.route("/")
def index():
    return open("index.html", "r").read()


if __name__ == "__main__":
    print("Timelapse Tool → http://localhost:5000")
    print("On your network → http://<your-local-ip>:5000")
    app.run(host="0.0.0.0", port=5502, debug=False, threaded=True)
