# crypto_lamp
A python script for smart lightbulbs that shows how badly you're losing money in crypto. Glows green when you're up, red when you're down.

The script can be set to track either your portfolio (using Blockfolio) or the value of an individual coin

## NOTE: Blockfolio recently changed their APIs so blockfolio tracking does not currently work. I will look into fixing this soon. If anyone sees a fix feel free to open a PR. Tracking an individual coin still works. For instance, to track Bitcoin in 24 hour mode you would run `python am_i_broke.py --ticker bitcoin`

## You will need:
* Phillips Hue Color Bulb + a Hue Bridge
* The Blockfolio app (free, iOS/Android) if tracking portfolio
* A lamp
* A computer capable of running Python. A raspberry pi would work fine
* A CoinMarketCap API key (free) if tracking individual coins

## Setup

#### Lightbulb setup
* Set up your Hue bridge + bulb. Make sure it's plugged in
* Find the IP of your Hue bridge and add it to the `crypto_lamp.config` file under `hue_bridge_ip`
* Follow the instructions at [Hue API v2 Getting Started](https://developers.meethue.com/develop/hue-api-v2/getting-started/) to obtain a user token (application key)
* Add the application key to `crypto_lamp.config` under `hue_user_token`
* To find your light ID, make a GET request to `https://<bridge ip address>/clip/v2/resource/light` with your application key in the header:
  ```
  GET /clip/v2/resource/light HTTP/1.1
  hue-application-key: your_application_key
  ```
* In the response, look for the light you want to use and find its `rid` value for the `service` with `rtype` of `light`. This should be a UUID. **Note**: This is NOT the light ID of the bulb. The array of services is nested inside of the device object.

```
{
    "id": "{Ignore this}",
    "metadata": {
        "name": "Your Light Name",
        "archetype": "sultan_bulb"
        },
    "services": [
        ...
                    {
                        "rid": "79dec3ce-6873-46ed-0bb9-f08f1eb635e9",
                        "rtype": "light"
                    },
        ...
                ]
}
```
* Add this light ID to `crypto_lamp.config` under `hue_light_id`

#### CoinMarketCap API setup (for tracking individual coins)
* Go to [CoinMarketCap](https://coinmarketcap.com/api/) and sign up for a free API key
* After signing up, go to your dashboard and copy your API key
* Add this API key to `crypto_lamp.config` under `cmc_api_key`

#### Blockfolio setup (if tracking portfolio)
* Download the Blockfolio app
* Update your portfolio
* Go to settings and find your user token at the bottom of the screen. Copy it and add it to `crypto_lamp.config` under `blockfolio_token`

#### Ticker setup (if tracking individual coin)
To track a coin, the script uses Coin Market Cap's [API](https://coinmarketcap.com/api/). You'll need to use the coin's symbol (like BTC, ETH, etc.) as a parameter for the script.

## Running the script
You will need a machine capable of running Python. If you do not have python installed, look up how to install it for your OS.

To run the script, navigate to the root folder of this project in your terminal and enter `python am_i_broke.py`.

There are two data sources you can run and two ways to calculate gains. By default, the script will use the 24 hour percentage change of your blockfolio account

#### Tracking an individual coin
Using the symbol of the coin you want to track, run `python am_i_broke.py --ticker {coin symbol}`. For example, to track Bitcoin: `python am_i_broke.py --ticker BTC`.

#### Using Blockfolio Data (NOTE: This is currently broken. See comment at the top of the Readme)
This is how you track your portfolio. This is the default setting and does not require an extra command line argument.

#### Delta Mode
This calculates the percent delta between each time your run the script. The first time you run the script in this mode will always treat the percent change as 0 since there was no previous data. The previous balance is stored in a `crypto_delta.dat` file. If you modify this file the script may not run properly. Deleting the file will remove previous data. add the `-d` argument to the script to run in delta mode. This can be used when tracking both portfolio or an individual coin, i.e. `python am_i_broke.py -d --ticker raiblocks`. If switching from portfolio to ticker it is probably a good idea to delete `crypto_delta.dat`.

#### 24 Hour Mode
This uses the 24hr percent change on your Blockfolio portfolio (number at the top right) or the 24hr change Coin Market Cap returns from a coin depending on which you are using. This is the default and does not require additional command line arguments.

## Scheduling
If you are running the script from a Linux device or Mac, use `cron` to schedule the script. Not sure the best way on Windows, but I'm sure there's plenty

## Adjust parameters
There are a few parameters in the script you can tweak. Edit `am_i_broke.py` to change them. 

* `GAINS_MAX` - What percent gains should make the light shine brightest. It will increase from brightness from 0% to whatever this value is. If it goes pass this value it will start flashing. You should tweak this based on how often you are running the script. For example if you are running it daily, 20% may be a good max number for gains, but if you are running it every 5 minutes, it could be as low as a few percents.
* `LOSS_MAX` - Same as above, but for losses. This one is negative

## Troubleshooting
Make sure the values in the config file do not have any whitespace between the `=`. This will cause them to be parsed incorrectly

The first time you run this script in delta mode, or if you have deleted the generated `crypto_delta.dat` file, the lamp will always be green on the first run. This is because without the file it treats your balance at $0. Subsequent runs will be correct.

If running in delta mode, but switching between data sources, the light will probably flash. Currently a single `crypto_delta.dat` file is used to keep track of previous amount regardless of where the data is coming from. So if it was tracking the market cap BTC and suddenly is tracking your portfolio, it's going to think you lost A LOT of money. Delete the `crypto_delta.dat` file if you want to switch sources.

Do not modify the `crypto_delta.dat` file. This could cause the script to crash. If you suspect that file has become corrupted, just delete it and run the script again.

Brightness is based on your `GAINS_MAX` and `LOSS_MAX` values. Adjust these params based on how often you run the script, and how much money expect to lose or make. Any gains or losses over these will trigger maximum brightness plus an annoying flashing effect.




