import flask, requests
from flask import send_from_directory, request
import flask_cors
import os


class UI:
	def __init__(self):
		self.app = flask.Flask(
			__name__, 
			static_url_path='', 
			static_folder='.', # Or the folder containing your frontend files
			template_folder='comp', 
			root_path= os.path.join(os.getcwd(), "ui")
		)
		flask_cors.CORS(self.app)
		self.setup_routes()
		self.run()

	def setup_routes(self):
		
		@self.app.route("/")
		def index():
			return self.app.send_static_file("index.html")
		@self.app.route("/get_cta")
		def get_cta():
			# Here you would update your config with the new value
			# send http request to message bus to update config
			res = requests.post("http://localhost:5500/message_bus", json={
				"listener": "config_manager",
				"event": "get",
				"data": "cta_url"
			})	
			return res.text
		@self.app.route("/log", methods=["POST"])
		def log():
			# Here you would update your config with the new value
			# send http request to message bus to update config
			http_response = requests.post("http://localhost:5500/message_bus", json={
				"listener": "logger",
				"event": "read",
				"data": {
				}
			})
			return http_response.text

	def run(self):
		#open browser
		host = "0.0.0.0"
		port = 5502
		f = f"http://{host}:{port}"
		import webbrowser
		webbrowser.open(f)
		self.app.run(host=host, port=port, debug=False)

	def stop(self):
		self.app.stop()
	
if __name__ == "__main__":
	UI()