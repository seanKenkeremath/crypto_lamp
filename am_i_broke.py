# Copyright [2017] [Sean Kenkeremath]

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import requests, json, os, sys
import urllib3

# Suppress the InsecureRequestWarning for requests to the Hue bridge
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BRIGHT_MAX = 254
BRIGHT_MIN = 1
LOSS_MAX = -10
GAINS_MAX = 10

MODE_24_HR = 1
MODE_DELTA = 2

SOURCE_CRYPTO = 1

CURRENT_DIR = os.path.dirname(__file__)
DELTA_FILE_PATH = os.path.join(CURRENT_DIR, 'crypto_delta.dat')


# default is daily mode (24 hour cumulative)
mode = MODE_24_HR
source = SOURCE_CRYPTO

ticker = ""

i = 0
while i < len(sys.argv):
	arg = sys.argv[i]
	if arg == "-24":
		mode = MODE_24_HR
	if arg == "-d":
		mode = MODE_DELTA
	if arg == "--crypto":
		source = SOURCE_CRYPTO
		ticker = sys.argv[i+1]
	i += 1


#NOTE requests must be installed. Run "pip install requests"
config_dict = {}

with open(os.path.join(CURRENT_DIR, 'crypto_lamp.config'), 'r') as config:
    config_data = config.read()
    config_values = config_data.split("\n")
    for i in range(len(config_values)):
    	config_pair = config_values[i].split("=")
    	if len(config_pair) < 2:
    		continue
    	config_dict[config_pair[0]] = config_pair[1]

currentTotal = 0
dailyPercent = 0

if source == SOURCE_CRYPTO:
	cmc_api_key = config_dict["cmc_api_key"]
	headers = {
		'X-CMC_PRO_API_KEY': cmc_api_key,
		'Accept': 'application/json'
	}
	
	request = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={ticker}"
	
	try:
		response = requests.get(request, headers=headers)
		response_json = json.loads(response.content)
		
		ticker_data = response_json['data'][ticker.upper()]
		dailyPercent = float(ticker_data['quote']['USD']['percent_change_24h'])
		currentTotal = float(ticker_data['quote']['USD']['market_cap'])
	except Exception as e:
		print(f"Error fetching data from CoinMarketCap: {e}")
		print("Response:", response.content if 'response' in locals() else "No response")
		sys.exit(1)

percent = 0

if mode == MODE_24_HR:
	# just use 24 hr diff returned by API
	percent = dailyPercent
elif mode == MODE_DELTA:
	# keep track of total portfolio value and calculate delta. base percent on total percent change since last run
	# note: the first time this runs, if the .dat file does not exist it will treat the previous value as $0
	oldTotal = 0
	if os.path.exists(DELTA_FILE_PATH):
		delta_file = open(DELTA_FILE_PATH, "r")
		oldTotal = float(delta_file.read())
		delta_file.close()

		# delete old .dat file
		os.remove(DELTA_FILE_PATH)

	# to avoid divide by zero
	if oldTotal > 0:
		percent = (currentTotal - oldTotal)/oldTotal

	# create .dat file for next time
	delta_file = open(DELTA_FILE_PATH, "w")
	delta_file.write(str(currentTotal))
	delta_file.close()

down = percent < 0
brightness = 0

# Use Hue API v2 for controlling lights
hue_bridge_ip = config_dict["hue_bridge_ip"]
hue_user_token = config_dict["hue_user_token"]
hue_light_id = config_dict["hue_light_id"]

light_state_change_url = f"https://{hue_bridge_ip}/clip/v2/resource/light/{hue_light_id}"

v2_light_state = {
	"on": {"on": True},
	"dimming": {"brightness": 0},
	"color": {
		"xy": {"x": 0, "y": 0}
	}
}

if down:
	brightness = 1 + int((percent/LOSS_MAX) * 254)
	if percent < LOSS_MAX:
		v2_light_state["alert"] = {"action": "breathe"}
	brightness = max(BRIGHT_MIN, min(BRIGHT_MAX, brightness))
	# xy values for red
	v2_light_state["color"]["xy"]["x"] = 0.675
	v2_light_state["color"]["xy"]["y"] = 0.322
else:
	brightness = 1 + int((percent/GAINS_MAX) * 254)
	if percent > GAINS_MAX:
		v2_light_state["alert"] = {"action": "breathe"}
	brightness = max(BRIGHT_MIN, min(BRIGHT_MAX, brightness))
	# xy values for green
	v2_light_state["color"]["xy"]["x"] = 0.408
	v2_light_state["color"]["xy"]["y"] = 0.517
v2_light_state["dimming"]["brightness"] = (brightness / BRIGHT_MAX) * 100

headers = {
	"hue-application-key": hue_user_token,
	"Content-Type": "application/json"
}

try:
	response = requests.put(light_state_change_url, headers=headers, data=json.dumps(v2_light_state), verify=False)
	if response.status_code != 200:
		print(f"Error updating light: {response.status_code}")
		print(response.content)
except Exception as e:
	print(f"Error communicating with Hue bridge: {e}")

