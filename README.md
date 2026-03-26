# Rives Barebones Load Test

Load tests to send to rives barebones to test the Cartesi Rollups sdk.

## Instructions

Install the requirements

```shell
python3 -m venv .venv
. .venv/bin/activate
pip3 install -r requirements.txt
```

### Generate the Gameplays

Download `rivemu` program and `freedoom` cartridge

```shell
PLATFORM=linux
ARCH=amd64
wget https://github.com/rives-io/riv/releases/download/v0.3-rc16/rivemu-${PLATFORM}-${ARCH} -O rivemu
```

```shell
wget https://github.com/lynoferraz/rives-barebones-doom/raw/refs/heads/main/cartridges/freedoom.sqfs
```

Record short, medium and long gameplays:

```shell
gameplay_name=gameplay
gameplay_type=short
./rivemu -save-outhash=${gameplay_name}-${gameplay_type}.outhash -record=${gameplay_name}-${gameplay_type}.rivlog freedoom.sqfs
```

### Create an .env File

You should define some variables to allow to connect to the chain and send inputs. `PRIVATE_KEY` is a wallet used to fund `MNEMONIC` created wallets. Each user in the test will use a different `account_index` the `MNEMONIC` created account.

```shell
RPC_URL=
PRIVATE_KEY=
MNEMONIC=
INPUTBOX_ADDRESS=0x1b51e2992A2755Ba4D6F7094032DF91991a0Cfac
APP_ADDRESS=
GAMEPLAY_PREFIX=<gameplay_name>
```

### Start the Locust Load Tester

Run

```shell
ENV_FILE=.env locust --loglevel info --run-time 20m  --spawn-rate 0.016 --users 20 --tags medium
```

This will start a local web server on `http://0.0.0.0:8089`. Follow the instructions and start the test

Note: you can use the `--headless` option to start the test directly without the web server.

### Start the Locust Inspect Tester

To run the inspect probe test run (you will need the cartesi rollups node url):

```shell
ENV_FILE=.env locust -f locust_inspect.py --web-port 8090 --loglevel info --run-time 25m  --spawn-rate 0.5 --users 1 --tags medium
```

This will start a local web server on `http://0.0.0.0:8090`. Follow the instructions and start the test
