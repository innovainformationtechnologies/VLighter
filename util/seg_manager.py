import json
import datetime

class SegmentManager:
	def __init__(self, message_bus=None):
		self.config = None
		self.message_bus = message_bus
		self.all_segment_data = self._get_all_segment_data()
		self.message_bus.request("segment_manager", "logger", "debug", f"[segment_manager] All Segment Data: {self.all_segment_data}")
		self.todays_segments = self._get_today_segments()
		self.message_bus.request("segment_manager", "logger", "debug", f"[segment_manager] Todays Segments: {self.todays_segments}")
		self.current_segment = self._get_current_segment_data()
		self.message_bus.request("segment_manager", "logger", "debug", f"[segment_manager] Current Segment: {self.current_segment}")

		message_bus.listen("segment_manager", "get_current_segment_data", self.get_current_segment_data)
		message_bus.listen("segment_manager", "get_segment_data", self.get_segment_data)
		message_bus.listen("segment_manager", "set_segment_data", self.set_segment_data)
		message_bus.listen("segment_manager", "get_all_segment_data", self.get_all_segment_data)
		message_bus.listen("segment_manager", "run", self.run)

	def get_all_segment_data(self):
		return self.all_segment_data

	def _get_all_segment_data(self):
		config = self.message_bus.request("segment_manager","config_manager", "get", "segment_data")
		# print(f"[SegmentManager] Config for today: {config}")
		return config

	def _get_today_segments(self):
		today = datetime.datetime.now().strftime("%A")
		segments = self.message_bus.request("segment_manager", "schedule_manager", "get_for_day", today)
		return segments["segments"]
		
	def _get_current_segment_data(self):
		self.message_bus.request("segment_manager", "logger", "debug", f"[segment_manager] Getting current segment... Today: {datetime.date.today().weekday()}, {datetime.datetime.now()}")
		try:
			now = datetime.datetime.now().time()
			# print(f"[SegmentManager] TODAYS SEGMENTS: {self.todays_segments}")
			for segment in self.todays_segments:
				# check segment
				self.message_bus.request("segment_manager", "logger", "debug", f"[segment_manager] checking segment: {segment}")
				start = datetime.datetime.strptime(segment["start"], "%H:%M").time()
				end = datetime.datetime.strptime(segment["end"], "%H:%M").time()
				overlap = end < start
				tomorrow = None
				if overlap:
					tomorrow = datetime.date.today() + datetime.timedelta(days=1)
					print(f"[SegmentManager] TOMORROW: {end}")
					segment_length = (datetime.datetime.combine(tomorrow, end) - datetime.datetime.combine(datetime.date.today(), start)).total_seconds() / 3600
				else:
					segment_length = (datetime.datetime.combine(datetime.date.today(), end) - datetime.datetime.combine(datetime.date.today(), now)).total_seconds() / 3600
				# segment_length = (datetime.datetime.combine(datetime.date.today(), end) - datetime.datetime.combine(datetime.date.today(), start)).total_seconds() / 3600
				self.segment_length = segment_length
				self.message_bus.request("segment_manager", "logger", "debug", f"[segment_manager] Start: {start}, End: {end}, Now: {now}, Length: {segment_length}")
				if  overlap:
					start = datetime.datetime.combine(datetime.date.today(), start)
					now = datetime.datetime.combine(datetime.date.today(), now)
					end = datetime.datetime.combine(tomorrow, end)
					if now > start or now < end:
						segment_data = self.get_segment_data(segment["name"])
						self.message_bus.request("segment_manager", "logger", "debug", f"[segment_manager] FOUND CURRENT SEGMENT: {segment_data}")
						return segment_data
				if start <= now <= end:
					segment_data = self.get_segment_data(segment["name"])
					try:
						segment_data["reboot"] = segment["reboot"]
					except:
						segment_data["reboot"] = False
					self.message_bus.request("segment_manager", "logger", "debug", f"[segment_manager] FOUND CURRENT SEGMENT: {segment_data}")
					return segment_data
				else:
					self.message_bus.request("segment_manager", "logger", "debug", f"[segment_manager] CURRENT SEGMENT NOT FOUND")
				
		except Exception as e:
			print(f"[SegmentManager] Error occurred while getting current segment: {e}")
			return {
						"fallback": e,
						"stream_data":{
							"title": "Art, music, code - Onyx Live 24/7",
							"description": "Tune in for the latest content brought to you by Onyx Audio Tech \nPowered by Innova \nart,music, lofi hip-hop, ambient, jazz, trap, beats, afrobeats, study, relax, soundtrack, videogame music, breakbeat, house music, flow state, livestream",
							"privacy":"public"
						},
						"playlist":"\\\\192.168.0.4\\extreme_ssd\\onyx\\stream\\audio\\high_energy_2026_2_20.wav.xspf",
						"gallery":"\\\\192.168.0.4\\extreme_ssd\\onyx\\stream\\audio\\high_energy_2026_2_20.wav.xspf",
						"info_text":{
							"cta_1":"Comment your favorite song below!", 
							"cta_2":"Subscribe for more art, music, and interactive experiences!", 
							"promo_1":"At the intersection of art, music, and interactive technology", 
							"promo_2":"Powered by Innova", 
							"promo_3":"Art, music, code - Onyx Live 24/7"
						}
					}

	def get_current_segment_data(self, key=None):
		if not self.todays_segments:
			self.todays_segments = self._get_today_segments()
		if not self.current_segment:
			self.current_segment = self._get_current_segment_data()
		self.message_bus.request("segment_manager", "logger", "debug", f"[segment_manager] CURRENT SEGMENT DATA: {self.current_segment}")
		self.message_bus.request("segment_manager", "logger", "debug", f"[segment_manager] key: {key}")
		try:
			if key and isinstance(key, str):
				return self.current_segment[key]
		except Exception as e:
			self.message_bus.request("segment_manager", "logger", "debug", f"[segment_manager] Error occurred while getting current segment data: {e}")
			return f"error: {e}"
		return self.current_segment

	def get_segment_data(self, name):
		for segment in self.all_segment_data:
			if segment["name"] == name:
				self.current_segment = segment
		self.message_bus.request("segment_manager", "logger", "debug", f"[segment_manager] CURRENT SEGMENT DATA: {self.current_segment}")
		return self.current_segment
		
	def set_segment_data(self, name, data):
		self.current_segment = data
		self.all_segment_data[name] = self.current_segment
	
	def run(self, name):
		self.get_segment_data(name)
		self.message_bus.request("segment_manager", "logger", "debug", f"[segment_manager] Running Segment: {name} with data: {self.current_segment}")
		try:
			tasks = self.current_segment.get("task_list", [])
			self.message_bus.request("segment_manager", "logger", "debug", f"[segment_manager] Running tasks: {tasks}")
			for task in tasks:
				self.message_bus.request("segment_manager", "task_manager", "add_task", task)
				self.message_bus.request("segment_manager", "task_manager", "run_task", task)
		except Exception as e:
			self.message_bus.request("segment_manager", "logger", "error", f"[segment_manager] Error running task: {name}: {e}")