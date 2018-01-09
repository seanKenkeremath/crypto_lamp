# crypto_lamp
A python script for smart lightbulbs that shows how badly you're losing money in crypto. Glows green when you're up, red when you're down.

The script can be set to track either your portfolio (using Blockfolio) or the value of an individual coin

## You will need:
* Phillips Hue Color Bulb + a Hue Bridge
* The Blockfolio app (free, iOS/Android) if tracking portfolio
* A lamp
* A computer capable of running Python. A raspberry pi would work fine

## Setup

#### Lightbulb setup
* Set up your Hue bridge + bulb. Make sure it's plugged in
* Find the IP of your Hue bridge and add it to the `crypto_lamp.config` file under `hue_bridge_ip`
* Go to `http://<bridge ip address>/debug/clip.html`
* Follow the instructions [here](https://www.developers.meethue.com/documentation/getting-started) to obtain a user token to use the Hue API. Add it to `crypto_lamp.config` under `hue_user_token`
* In that same Getting Started page on the Hue website, follow the instructions to obtain the ID for the lightbulb (a GET request to `http://<bridge ip address>/api/<user_token>/lights`). Add the lightbulb ID (should be a number) to `crypto_lamp.config` under `hue_light_id`

#### Blockfolio setup (if tracking portfolio)
* Download the Blockfolio app
* Update your portfolio
* Go to settings and find your user token at the bottom of the screen. Copy it and add it to `crypto_lamp.config` under `blockfolio_token`

#### Ticker setup (if tracking individual coin)
To track a coin, the script uses Coin Market Cap's [API](https://coinmarketcap.com/api/). Unfortunately, the API needs an ID different than the standard ticker. It is usually the full name of the coin. For instance Bitcoin is "bitcoin" instead of "BTC". You can use [This API call](https://api.coinmarketcap.com/v1/ticker/) to find the ID. You will use this ID as a parameter for the script.

## Running the script
You will need a computer capable of running Python. You can download python on any OS (a lot of OSes come packaged with it).

To run the script, navigate to the root folder of this project in your terminal and enter `python am_i_broke.py`.

There are two data sources you can run and two ways to calculate gains. By default, the script will use the 24 hour percentage change of your blockfolio account

#### Tracking an individual coin
Using the ID you found from the Ticker Setup section, run `python am_i_broke.py --ticker {insert coin id}`.

#### Using Blockfolio Data
This is how you track your portfolio. This is the default setting and does not require an extra command line argument.

#### Delta Mode
This calculates the percent delta between each time your run the script. The first time you run the script in this mode will always treat the percent change as 0 since there was no previous data. The previous balance is stored in a `crypto_delta.dat` file. If you modify this file the script may not run properly. Deleting the file will remove previous data. add the `-d` argument to the script to run in delta mode. This can be used when tracking both portfolio or an individual coin, i.e. `python am_i_broke.py -d --ticker raiblocks`. If switching from portfolio to ticker it is probably a good idea to delete `crypto_delta.dat`.

#### 24 Hour Mode
This uses the 24hr percent change on your Blockfolio portfolio (number at the top right) or the 24hr change Coin Market Cap returns from a coin depending on which you are using. This is the default and does not require additional command line arguments.

## Scheduling
If you are running the script from a Linux device or Mac, use `cron` to schedule the script. Not sure the best way on Windows, but I'm sure there's plenty

## Adjust parameters
There are a few parameters in the script you can tweak. Edit `am_i_broke.py` to change them. 

* `SATURATION` - By default I left it at 125 (max). you can lower it if you want a more white hue of green/red
* `GAINS_MAX` - What percent gains should make the light shine brightest. It will increase from brightness from 0% to whatever this value is. If it goes pass this value it will start flashing. You should tweak this based on how often you are running the script. For example if you are running it daily, 20% may be a good max number for gains, but if you are running it every 5 minutes, it could be as low as a few percents.
* `LOSS_MAX` - Same as above, but for losses. This one is negative
* `GREEN_HUE` - The type of green used when you're up. This can be changed to any color. see the Phillips Hue documentation for other color values
* `RED_HUE` - same as above. This is the hue used when you're down

## Troubleshooting
Make sure the values in the config file do not have any whitespace between the `=`. This will cause them to be parsed incorrectly

The first time you run this script in delta mode, or if you have deleted the generated `crypto_delta.dat` file, the lamp will always be green on the first run. This is because without the file it treats your balance at $0. Subsequent runs will be correct.

If running in delta mode, but switching between data sources, the light will probably flash. Currently a single `crypto_delta.dat` file is used to keep track of previous amount regardless of where the data is coming from. So if it was tracking the market cap BTC and suddenly is tracking your portfolio, it's going to think you lost A LOT of money. Delete the `crypto_delta.dat` file if you want to switch sources.

Do not modify the `crypto_delta.dat` file. This could cause the script to crash. If you suspect that file has become corrupted, just delete it and run the script again.

Brightness is based on your `GAINS_MAX` and `LOSS_MAX` values. Adjust these params based on how often you run the script, and how much money expect to lose or make. Any gains or losses over these will trigger maximum brightness plus an annoying flashing effect. If you want to disable the flash, change the `ALERT_MULTI_BLINK` variable in the script to `"none"`.




