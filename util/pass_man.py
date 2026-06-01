import json, os
class PassMan:
	def __init__(self, bus=None, cred_file= "credentials.json", config=None):
		self.debug = False
		self.passwords = {}
		self.cred_file = cred_file
		self.cred_path = os.path.join(os.getcwd(), "static", cred_file)
		if os.path.exists(self.cred_path):
			with open(cred_path, "r") as f:
				self.passwords = json.load(f)
		else:
			self.read_passwords_from_cred_file()
		if bus:
			self.bus = bus
			self.debug = bus.request("pass_man","config_manager", "get", "debug")
			self.bus.listen("pass_man", "get", self.get_password)
			self.bus.listen("pass_man", "set", self.set_password)

	def set_password(self, key, value):
		if self.debug:
			print(f"[PassMan] Setting password for key '{key}'")
		self.passwords[key] = value
	
	def get_password(self, key):
		if self.debug:
			print(f"[PassMan] Getting password for key '{key}'")
		return self.passwords.get(key)
		
	def read_passwords_from_cred_file(self):
		if self.debug:
			print("[PassMan] Reading passwords from credentials.json")
		if os.path.exists(self.cred_path):
			with open(self.cred_path, "r") as f:
				creds = json.load(f)
				#decrypt
		else:
			creds = {}
		for key, value in creds.items():
			self.set_password(key, value)

	def write_passwords_to_cred_file(self):
		if self.debug:
			print("[PassMan] Reading passwords from credentials.json")
		if os.path.exists(self.cred_path):
			with open(self.cred_path, "r") as f:
				creds = json.load(f)
		else:
			creds = {}
		with open(self.cred_path, "w") as f:
			json.dump(self.passwords, f)
			#encrypt with aes
			


		