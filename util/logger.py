import logging, os
# console colors

class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKCYAN = '\033[96m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

class Logger:
	def __init__(self, log_file, bus=None, debug=False):
		self.log_file = log_file
		if not os.path.exists(os.path.dirname(log_file)):
			os.makedirs(os.path.dirname(log_file))
		logging.basicConfig(
			filename=log_file,
			level=logging.DEBUG,
			format="%(asctime)s - %(message)s"
		)
		self.bus = bus
		bus.listen("logger", "info", self.info)
		bus.listen("logger", "warning", self.warning)
		bus.listen("logger", "error", self.error)
		bus.listen("logger", "success", self.success)
		if debug:
			bus.listen("logger", "debug", self.debug)
		bus.listen("logger", "read", self.read_log)
		bus.listen("logger", "clear", self.clear_log)
		logging.info("Logger initialized")

	def debug(self, message):
		message = bcolors.OKCYAN + "[DEBUG] " + bcolors.ENDC + message
		if self.debug:
			print(message)
		logging.debug(message)

	def info(self, message):
		message = bcolors.OKBLUE + "[INFO] " + bcolors.ENDC + message
		print(message)
		logging.info(message)
	
	def warning(self, message):
		message = bcolors.WARNING + "[WARNING] " + bcolors.ENDC + message
		print(message)
		logging.warning(message)

	def error(self, message):
		message = bcolors.FAIL + "[ERROR] " + bcolors.ENDC + message
		print(message)
		logging.error(message)
	
	def success(self, message):
		message = bcolors.OKGREEN + "[SUCCESS] " + bcolors.ENDC + message
		print(message)
		logging.info(message)

	def read_log(self, kwargs={}):
		with open(self.log_file, "r") as f:
			return f.read()
	
	def clear_log(self, kwargs={}):
		with open(self.log_file, "w") as f:
			f.write("")