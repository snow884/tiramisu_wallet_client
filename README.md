# Tiramisu wallet API client

This is a Python client for tiramisu wallet API that allows for programmatic trading, minting, sending and receiving of Taproot Assets.

## Installation

Tiramisu wallet client is available as a package on PYPI and can be installed with pip:
```
pip install tiramisu_wallet_client
```

## Usage

The code below demonstrates how to perform disfferent actions using tiramisu wallet.

```
from tiramisu_client import TiramisuClient
import random

# Please go to https://testnet.tarowallet.net/walletapp/ 
# and create an account then populate your credentials 
USER_NAME="FILL_THIS_OUT"
PASSWORD="FILL_THIS_OUT"

print("Create client object")
client = TiramisuClient(username=USER_NAME,password=PASSWORD)

print("List all wallet balances")
print( client.balances() )

print("List all balances of NFTs in the wallet")
print( client.balances_nft() )

print("Get the BTC balance in wallet:")
print( client.get_btc_balance() )

print("List assets available")
assets=client.assets()
print( assets )

print("Get first asset and print it")
asset=client.asset(4)
print( asset )

print("List wallet transactions")
print( client.transactions() )

print("List all currency asset listings on exchange")
listings = client.listings()
print( listings )

print(f"Buy asset '{listings[4]['currency']}'")
print( client.buy_taproot_asset_asset_wait_finished(asset=listings[4]['currency'], amount=1) )

print("Balances after purchase:")
print( client.balances() )

print("List all NFT asset listings on exchange")
listings_nfts = client.listings_nfts()
print( listings_nfts )

print("Show all listings made from the current wallet")
print( client.listings_my() )

print("transactions_receive_btc")
transaction_inbound_btc = client.transactions_receive_btc_get_invoice(amount=10000, description='test BTC deposit')

print(f"send BTC to this address to top-up your BTC balance: {transaction_inbound_btc['invoice_inbound']}")

invoice_inbound_taproot_asset = client.transactions_receive_taproot_asset(amount=1, asset=asset['id'], description=f"receive asset {asset['id']}")

print(f"send Taproot asset {asset['name']} with ID {asset['id']} to this address to top-up your TAP balance: {invoice_inbound_taproot_asset}")

tn = random.randint(1, 1000)

print("Minting a new currency and waiting for minting to finish.")

new_asset = client.assets_mint_wait_finished(acronym=f'TC{tn}', name=f'Testasset{tn}', description=f'Test asset {tn}', supply=1234, file_path='test_image.jpg')

print("Newly created asset")
print(new_asset)

print("Listing the currency on an exchange...")
client.list_asset(asset=new_asset['id'])

print("Show all listings made from the current wallet")
print( client.listings_my() )


```

## Taproot Assets 

[Taproot assets](https://docs.lightning.engineering/the-lightning-network/taproot-assets) is a protocol operating on Bitcoin Blockchain and the Bitcoin lightning network. Taproot assets protocol (TAP) represents alternative crypto currencies and non-fungible tokens (NFTs) allowing for minting, sending and receiving of these assets. Taproot assets protocol is being developed by the company lightning labs.

## Tiramisu wallet

[Tiramisu wallet](https://testnet.tarowallet.net/walletapp/) is a GUI that allows for simple access to Taproot assets protocol. To see the full documentation for the API visit our [swagger documents](https://testnet.tarowallet.net/walletapp/swagger-ui/).