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

ALERT_NONE = "none"
ALERT_MULTI_BLINK = "lselect"
GREEN_HUE = 25500
RED_HUE = 0
SATURATION = 150
BRIGHT_MAX = 254
BRIGHT_MIN = 1
LOSS_MAX = -30
GAINS_MAX = 40

SOURCE_TICKER = 1
SOURCE_BLOCKFOLIO = 2

MODE_24_HR = 1
MODE_DELTA = 2

CURRENT_DIR = os.path.dirname(__file__)
DELTA_FILE_PATH = os.path.join(CURRENT_DIR, 'crypto_delta.dat')


# default is daily mode (24 hour cumulative) of blockfolio account
mode = MODE_24_HR
source = SOURCE_BLOCKFOLIO

#only used if in ticker mode
ticker = ""

i = 0
while i < len(sys.argv):
	arg = sys.argv[i]
	if arg == "-24":
		mode = MODE_24_HR
	if arg == "-d":
		mode = MODE_DELTA
	if arg == "--ticker":
		source = SOURCE_TICKER
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

if not source == SOURCE_TICKER:
	blockfolio_token = config_dict["blockfolio_token"]
	request = "https://api-v0.blockfolio.com/rest/get_all_positions/%s?fiat_currency=USD&locale=en-US&use_alias=true" % blockfolio_token
	response_json = json.loads(requests.get(request).content)
	dailyPercent = float(response_json["portfolio"]["percentChangeFiat"].replace('%',''))
	currentTotal = float(response_json["portfolio"]["portfolioValueFiatString"].replace(',', ''))
else:
	request = "https://api.coinmarketcap.com/v1/ticker/%s/" % ticker
	response_json = json.loads(requests.get(request).content)
	dailyPercent = float(response_json[0]["percent_change_24h"])
	currentTotal = float(response_json[0]["market_cap_usd"])

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

saturation = SATURATION
down = percent < 0
brightness = 0
color = 0
alert = ALERT_NONE 

if down:
	color = RED_HUE
	brightness = 1 + int((percent/LOSS_MAX) * 254)
	if percent < LOSS_MAX:
		alert = ALERT_MULTI_BLINK
else:
	color = GREEN_HUE
	brightness = 1 + int((percent/GAINS_MAX) * 254)
	if percent > GAINS_MAX:
		alert = ALERT_MULTI_BLINK

light_state = {}
light_state["on"] = True
light_state["alert"] = alert
light_state["hue"] = color
light_state["bri"] = brightness
light_state["sat"] = saturation

light_state_change_url = "http://%s/api/%s/lights/%s/state" % (config_dict["hue_bridge_ip"], config_dict["hue_user_token"], config_dict["hue_light_id"])

requests.put(light_state_change_url, json.dumps(light_state))

