import sys,requests
import threading
import queue
import tempfile
import os, datetime, json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response, send_file
import flask_cors

sys.path.insert(0, str(Path(__file__).parent))
from vlighter_tool import run_pipeline

log_queue: queue.Queue = queue.Queue()
job_running = False
output_file: str = None     # path to the finished timelapse, ready for download
temp_dir: str = None        # current job's temp directory

def log(msg: str):
	http_response = requests.post("http://localhost:5500/message_bus", json={
		"listener": "logger",
		"event": "info",
		"data": msg
	})
	return http_response


class UI:
	def __init__(self):
		self.app = Flask(
			__name__, 
			static_url_path='', 
			static_folder='.', # Or the folder containing your frontend files
			template_folder='comp', 
			root_path= os.path.join(os.getcwd(), "vlighter")
		)
		flask_cors.CORS(self.app)
		self.setup_routes()
		self.run()

	def run_pipeline(self,data):
		global job_running, output_file, temp_dir
		log("▶ Running pipeline…")
		job_running = True
		output_file = None

		temp_dir = os.path.join(os.getcwd(), "temp", f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
		video_path = os.path.join(temp_dir, "video.mp4")
		clip_path      = os.path.join(temp_dir, "clip.mp4")
		timelapse_path = os.path.join(temp_dir, "timelapse.mp4")

		# Clean up temp dir from previous run
		# import shutil
		# shutil.rmtree(temp_dir, ignore_errors=True)
		# Path(temp_dir).mkdir(parents=True, exist_ok=True)

		try:
			run_pipeline(data, temp_dir)
			# log("▶ Downloading clip from YouTube…")
			# download_video_clip(
			# 	video_url = data["url"],
			# 	start_time = data["start"],
			# 	end_time = data["end"],
			# 	output_path = clip_path,
			# )

			# log("▶ Rendering timelapse…")

			# # two speed passes with the specified multiplier cut in half
			# make_timelapse(
			# 	output_path = video_path,
			# 	clip_path = clip_path,
			# 	speed_multiplier = data["speed"] / 2,
			# )
			# make_timelapse(
			# 	output_path = timelapse_path,
			# 	clip_path = video_path,
			# 	speed_multiplier = data["speed"] / 2,
			# )

			# output_file = timelapse_path
			# log("✓ Done — your download will start shortly.")

		except Exception as e:
			log(f"✗ Error: {e}")
			# Clean up temp dir on failure
			import shutil
			shutil.rmtree(temp_dir, ignore_errors=True)
			temp_dir = None

		finally:
			job_running = False
			return {"job_running": job_running, "output_file": output_file, "temp_dir": temp_dir}
			
        


	def setup_routes(self):
		log("initializing routes...")
		
		@self.app.route("/")
		def index():
			return self.app.send_static_file("index.html")

		@self.app.route("/run", methods=["POST"])
		def run():
			log("receiving run request...")
			global output_file, job_running,temp_dir
			if job_running:
				return jsonify({"error": "A job is already running."}), 409
			output_file = None
			data = request.json
			thread = threading.Thread(target=self.run_pipeline, args=(data,), daemon=True)
			thread.start()
			return {"job_running": job_running, "output_file": output_file, "temp_dir": temp_dir}


		@self.app.route("/log")
		def get_log():
			res = requests.post("http://localhost:5500/message_bus", json={
				"listener": "logger",
				"event": "read",
				"data": ""
			})	
			return {"logs": res.text}	

		@self.app.route("/clear_log")
		def clear_log():
			res = requests.post("http://localhost:5500/message_bus", json={
				"listener": "logger",
				"event": "clear",
				"data": ""
			})	
			return {"logs": res.text}

		@self.app.route("/status")
		def status():
			log("receiving status request...")
			status = {"job_running": job_running, "output_file": output_file, "temp_dir": temp_dir}
			log("status: " + str(status))
			return status

		@self.app.route("/download")
		def download():
			log("downloading file...")
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

	def run(self):
		#open browser
		host = "0.0.0.0"
		port = 5501
		f = f"http://{host}:{port}"
		# import webbrowser
		# webbrowser.open(f)
		self.app.run(host=host, port=port, debug=True)

	def stop(self):
		self.app.stop()
	
if __name__ == "__main__":
	UI()