import json
class DailyConfig:
	def __init__(self, config, bus=None):
		print(f"[DailyConfig] Initializing daily config..., config: {config}")
		self.config = self.get_for_today(config)
		# print(f"[DailyConfig] segment_data: {self.segment_data}")
		self.todays_segments = self.config.get("segments") if isinstance(self.config, dict) else {}
		self.all_segment_data = config.get("segment_data")
		print(f"[DailyConfig] Segment data: {self.all_segment_data}")
		self.current_segment_data = self.get_current_segment(self.todays_segments)
		self.segment_length = None
		self.bus = bus
		if self.bus:
			self.bus.listen("daily_config", "get", self.get)
			self.bus.listen("daily_config", "get_segment_data", self.get_segment_data)
	
	def get_for_today(self, config):
		print(f"[DailyConfig] Getting daily config for today...")
		import datetime
		today = datetime.datetime.now().strftime("%A")
		weekly_schedule = config.get("weekly_schedule", {}) if isinstance(config, dict) else self.bus.request("config_manager", "get", "weekly_schedule")
		today_config = weekly_schedule.get(today, {})
		print(f"[DailyConfig] Config for today: {today_config}")
		return today_config

	def get_current_segment(self, segments):
		print(f"[DailyConfig] Getting current segment...")
		try:
			import datetime
			now = datetime.datetime.now().time()
			# print(f"[DailyConfig] {self.config}")
			for segment in segments:
				start = datetime.datetime.strptime(segment["start"], "%H:%M").time()
				end = datetime.datetime.strptime(segment["end"], "%H:%M").time()
				overlap = end < start
				if overlap:
					tomorrow = datetime.date.today() + datetime.timedelta(days=1)
					segment_length = (datetime.datetime.combine(tomorrow, end) - datetime.datetime.combine(datetime.date.today(), start)).total_seconds() / 3600
				else:
					segment_length = (datetime.datetime.combine(datetime.date.today(), end) - datetime.datetime.combine(datetime.date.today(), start)).total_seconds() / 3600
				# segment_length = (datetime.datetime.combine(datetime.date.today(), end) - datetime.datetime.combine(datetime.date.today(), start)).total_seconds() / 3600
				self.segment_length = segment_length
				if start <= now <= end:
					print(f"[DailyConfig] Current segment '{segment['name']}' with start {start} and end {end} (length: {segment_length} hours)")
					return self.get_segment_data(segment)
				
		except Exception as e:
			print(f"[DailyConfig] Error occurred while getting current segment: {e}")
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

	def get_segment_data(self, name):
		data = {}
		segment_name = name
		for seg in self.all_segment_data:
			if seg["name"] == segment_name:
				data = seg
		print(f"[DailyConfig] Data for segment '{segment_name}': {data}")
		return data

	def get(self, key):
		value = self.current_segment_data.get(key)
		print(f"[DailyConfig] Get '{key}': '{value}'")
		return json.dumps(data) if isinstance(data, dict) else data
		
	
if __name__ == "__main__":
	config = json.load(open("vconfig.json", "r"))
	daily_config = DailyConfig(config)
	# print(daily_config.get("stream_data"))