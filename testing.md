# Rives Barebones Tests

## Setup

Get the compose files:

```shell
wget https://raw.githubusercontent.com/Mugen-Builders/node-test-environment/refs/heads/main/docker-compose.yaml
wget https://raw.githubusercontent.com/Mugen-Builders/node-test-environment/refs/heads/main/docker-compose-devnet.yaml
```

Set the alias

```shell
alias node-compose="docker compose -f docker-compose.yaml -f docker-compose-devnet.yaml -f docker-compose-load-test.yaml"
```

Create env files to be used with the load tester

```shell
MNEMONIC=<mnemonic to create accounts to send inputs>
PRIVATE_KEY=<key of the account to fund inputs>
APP_ADDRESS=<address of the deployed app>
```

## Testing

### Test 10.2 Starvation

```shell
node-compose -f testing/docker-compose-test-10.2.yaml up
```
