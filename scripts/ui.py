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

		@self.app.route("/update_config", methods=["POST"])
		def update_config():
			key = request.form.get("key")
			value = request.form.get("value")
			# Here you would update your config with the new value
			# send http request to message bus to update config
			http_response = requests.post("http://localhost:5001/message_bus", json={
				"listener": "config_manager",
				"event": "set",
				"data": {
					"key": key,
					"value": value
				}
			})
			return http_response

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