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
import time

try:
	import yfinance as yf
except ImportError:
	print("yfinance library not found. Please install it with 'pip install yfinance'")
	sys.exit(1)

try:
	import schedule
except ImportError:
	print("schedule library not found. Please install it with 'pip install schedule'")
	sys.exit(1)

# Suppress the InsecureRequestWarning for requests to the Hue bridge
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BRIGHT_MAX = 254
BRIGHT_MIN = 1
LOSS_MAX = -10
GAINS_MAX = 10

MODE_24_HR = 1
MODE_DELTA = 2

SOURCE_CRYPTO = 1
SOURCE_STOCK = 2

CURRENT_DIR = os.path.dirname(__file__)
DELTA_FILE_PATH = os.path.join(CURRENT_DIR, 'crypto_delta.dat')

# Add recurring mode constants
RECURRING_INTERVAL_MINUTES = 15  # Default interval in minutes

# default is daily mode (24 hour cumulative)
mode = MODE_24_HR
source = -1
verbose = False
recurring = False
interval_minutes = RECURRING_INTERVAL_MINUTES

ticker = ""

i = 0
while i < len(sys.argv):
	arg = sys.argv[i]
	if arg == "-24":
		mode = MODE_24_HR
	if arg == "-d":
		mode = MODE_DELTA
	if arg == "-v":
		verbose = True
	if arg == "--crypto":
		source = SOURCE_CRYPTO
		ticker = sys.argv[i+1]
		i += 1
	if arg == "--stock":
		source = SOURCE_STOCK
		ticker = sys.argv[i+1]
		i += 1
	if arg == "--recurring":
		recurring = True
		if i+1 < len(sys.argv) and sys.argv[i+1].isdigit():
			interval_minutes = int(sys.argv[i+1])
			i += 1
	i += 1

if source == -1:
	print("Error: No valid source specified.")
	print("Usage: python am_i_broke.py [OPTIONS] --crypto SYMBOL or --stock SYMBOL")
	print("Options:")
	print("  -24         Use 24-hour mode (default)")
	print("  -d          Use delta mode")
	print("  -v          Verbose output")
	print("  --crypto    Use cryptocurrency data (requires symbol)")
	print("  --stock     Use stock data (requires symbol)")
	print("  --recurring [MINUTES]  Run the script repeatedly at specified interval (default: 15 minutes)")
	sys.exit(1)

config_dict = {}
def update_light():
	global config_dict
	
	# Load config if not already loaded
	if not config_dict:
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
	
	# Fetch data based on source (crypto or stock)
	if source == SOURCE_CRYPTO:
		# Existing crypto code...
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
			
			if verbose:
				current_price = float(ticker_data['quote']['USD']['price'])
				print(f"Crypto: {ticker.upper()}")
				print(f"Current Price: ${current_price:.2f}")
				print(f"Current Market Cap: ${currentTotal:.2f}")
				print(f"24h Change: {dailyPercent:.2f}%")
			
		except Exception as e:
			print(f"Error fetching data from CoinMarketCap: {e}")
			print("Response:", response.content if 'response' in locals() else "No response")
			if not recurring:
				sys.exit(1)
			return
	elif source == SOURCE_STOCK:
		# Existing stock code...
		try:
			# Get stock data using yfinance
			stock = yf.Ticker(ticker)
			hist = stock.history(period="2d")  # Get last 2 days of data
			
			if len(hist) < 2:
				print(f"Error: Not enough historical data for stock {ticker}")
				if not recurring:
					sys.exit(1)
				return
				
			# Calculate percent change between yesterday's close and today's close
			yesterday_close = hist.iloc[-2]['Close']
			today_close = hist.iloc[-1]['Close']
			
			dailyPercent = ((today_close - yesterday_close) / yesterday_close) * 100
			currentTotal = today_close * stock.info.get('sharesOutstanding', 1)  # Market cap or just price if shares not available
			
			# Only print detailed information in verbose mode
			if verbose:
				print(f"Stock: {ticker}")
				print(f"Current Price: ${today_close:.2f}")
				print(f"24h Change: {dailyPercent:.2f}%")
			
		except Exception as e:
			print(f"Error fetching stock data for {ticker}: {e}")
			if not recurring:
				sys.exit(1)
			return
	
	percent = 0
	
	if mode == MODE_24_HR:
		# just use 24 hr diff returned by API
		percent = dailyPercent
	elif mode == MODE_DELTA:
		# Existing delta mode code...
		oldTotal = 0
		if os.path.exists(DELTA_FILE_PATH):
			delta_file = open(DELTA_FILE_PATH, "r")
			oldTotal = float(delta_file.read())
			delta_file.close()
	
			# delete old .dat file
			os.remove(DELTA_FILE_PATH)
	
		# to avoid divide by zero
		if oldTotal > 0:
			percent = (currentTotal - oldTotal)/oldTotal * 100  # Convert to percentage
	
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
		response = requests.put(
			light_state_change_url,
			headers=headers,
			json=v2_light_state,
			verify=False
		)
		
		if verbose:
			print(f"Light update response: {response.status_code}")
			if response.status_code != 200:
				print(f"Error: {response.text}")
			else:
				print(f"Light updated successfully. Percent change: {percent:.2f}%")
				if recurring:
					print(f"Next update in {interval_minutes} minutes")
	except Exception as e:
		print(f"Error updating light: {e}")

# Run the script once or in recurring mode
if recurring:
	print(f"Running in recurring mode every {interval_minutes} minutes. Press Ctrl+C to stop.")
	# Run once immediately
	update_light()
	# Schedule recurring runs
	schedule.every(interval_minutes).minutes.do(update_light)
	
	try:
		while True:
			schedule.run_pending()
			time.sleep(1)
	except KeyboardInterrupt:
		print("\nRecurring mode stopped by user.")
else:
	# Run once and exit
	update_light()

