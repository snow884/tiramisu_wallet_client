import logging
import os
from enum import Enum

import requests
from requests.auth import HTTPBasicAuth

import time

BASE_URLS = {
    "testnet": "https://testnet.tarowallet.net/walletapp/",
    "mainnet": "https://mainnet.tarowallet.net/walletapp/",
}


class TiramisuClient:
    class Endpoints(Enum):
        # Balances
        BALANCES = "api/balances/"
        NFT_BALANCES = "api/balances-nft/"
        BALANCE_CREATE = "api/balance/create/"

        # Asset
        ASSET = "api/currencies/"
        ASSET_CREATE = "api/currency/create/"
        ASSET_DETAIL = "api/currencies/{id}"
        ASSET_MINT = "api/currencies/mint/"
        ASSET_MINT_NFT = "api/currencies/mint-nft/"

        # Transaction
        TRANSACTION = "api/transactions/"
        TRANSACTION_DETAIL = "api/transactions/{id}/"
        TRANSACTION_SEND_TAPROOT_ASSET = "api/transactions/send_taro/"
        TRANSACTION_SEND_BTC = "api/transactions/send_btc/"
        TRANSACTION_SEND_INTERNAL = "api/transactions/send_internal/"
        TRANSACTION_RECEIVE_TAPROOT = "api/transactions/receive_taro/"
        TRANSACTION_RECEIVE_BTC = "api/transactions/receive_btc/"

        # Listing
        LIST_ASSET = "api/list_asset/"
        LIST_NFT_ASSET = "api/list_nft_asset/"
        LISTING = "api/listings/"
        LISTINGS_NFTS = "api/listings_nfts/"
        LISTING_MY = "api/listings_my/"

        # Buy any sell
        BUY_TAPROOT_ASSET = "api/buy_taro_asset/"
        BUY_NFT_ASSET = "api/buy_nft_asset/"
        SELL_TAPROOT_ASSET = "api/sell_taro_asset/"

    def __init__(self, username: str, password: str, network: str = "testnet") -> None:
        self._check_network(network)
        self.base_url = BASE_URLS[network]
        self.auth = HTTPBasicAuth(username, password)
        self.btc_asset_id = self._get_btc_asset_id()

    def _get_btc_asset_id(self):
        assets = self.assets()
        assets_dict = {curr["acronym"]: curr for curr in assets}
        return assets_dict["SAT"]["id"]

    def _check_network(self, network):
        if network not in BASE_URLS:
            raise Exception(f"Unknown value '{network}' supplied for network argument.")
        if network == 'mainnet':
            raise Exception("Taproot Assets is only on testnet! Mainnet is not working yet.")

    @staticmethod
    def raise_with_text(res):
        try:
            res.raise_for_status()
        except requests.HTTPError as e:
            raise requests.HTTPError(f"{res.text}", response=res) from e

    def _make_request(self, method, endpoint, data=None, files=None):
        url = self.base_url + endpoint
        res = requests.request(method, url, data=data, auth=HTTPBasicAuth(self.auth.username, self.auth.password),
                               files=files)
        self.raise_with_text(res)
        return res.json()

    def balance_create(self, asset: str):
        """
        Create a new balance in the current user account

        Args:
            asset (str): Acronym of the asset to create 
            new balance for
        """
        return self._make_request("POST", self.Endpoints.BALANCE_CREATE, {"currency": asset})

    def get_btc_balance(self):
        """
        List all asset balances in the current user account
        """
        balances_dict = {bal["currency"]: bal for bal in self.balances()}
        return balances_dict[self.btc_asset_id]

    def balances(self):
        """
        List all asset balances in the current user account
        """
        return self._make_request("GET", self.Endpoints.BALANCES)

    def balances_nft(self):
        """
        List all NFT balances in the current user account
        """
        return self._make_request("GET", self.Endpoints.NFT_BALANCES)

    def asset_create(self, acronym: str, asset_id: str, file_path: str = None):
        files = None
        if file_path:
            with open(file_path, 'rb') as f:
                files = {"picture_orig": f.read()}

        data = {"acronym": acronym, "asset_id": asset_id}

        return self._make_request("POST", self.Endpoints.ASSET_CREATE, data=data, files=files)

    @staticmethod
    def _get_mime_type(file_path: str) -> str:
        extension = file_path.split(".")[-1].lower()
        mime_types = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
        }
        return mime_types.get(extension, "application/octet-stream")

    def assets_mint(self, acronym: str, name: str, description: str, supply: int, file_path: str):
        files = None
        if file_path:
            with open(file_path, 'rb') as f:
                files = {
                    'picture_orig': (
                        os.path.basename(file_path),
                        f.read(),
                        self._get_mime_type(file_path)
                    )
                }

        data = {
            "acronym": acronym,
            "name": name,
            "description": description,
            "supply": str(supply),
        }

        return self._make_request("POST", self.Endpoints.ASSET_MINT, data=data, files=files)

    def assets_mint_wait_finished(self, acronym: str, name: str, description: str, supply: int, file_path: str):

        asset = self.assets_mint(acronym, name, description, supply, file_path)
        asset = self.asset(asset['id'])
        minting_transaction = self.transactions_wait_status(transaction_id=asset['minting_transaction'],
                                                            status_wait_for='minted')

        return asset

    def assets_mint_nft(self, acronym: str, name: str, description: str, supply: int, file_path: str):
        files = None

        if file_path:
            with open(file_path, 'rb') as f:
                files = {
                    'picture_orig': (
                        os.path.basename(file_path),
                        f.read(),
                        self._get_mime_type(file_path)
                    )
                }

        data = {
            "acronym": acronym,
            "name": name,
            "description": description,
            "supply": supply
        }

        return self._make_request("POST", self.Endpoints.ASSET_MINT_NFT, data=data, files=files)

    def assets_mint_nft_wait_finished(self, acronym: str, name: str, description: str, supply: int, file_path: str):

        minting_transaction = self.assets_mint_nft(acronym, name, description, supply, file_path)
        minting_transaction = self.transactions_wait_status(transaction_id=minting_transaction["id"],
                                                            status_wait_for='minted')

        return minting_transaction

    def assets(self):
        return self._make_request("GET", self.Endpoints.ASSET)

    def asset(self, id):
        uri = self.Endpoints.ASSET_DETAIL.value.format(id=id)
        return self._make_request("GET", uri)

    def transactions_send_taproot_asset(self, invoice_outbound):
        return self._make_request("POST", self.Endpoints.TRANSACTION_SEND_TAPROOT_ASSET,
                                  {"invoice_outbound": invoice_outbound})

    def transactions_send_btc(self, invoice_outbound: str, amount: int):
        data = {
            "invoice_outbound": invoice_outbound,
            "amount": amount
        }
        return self._make_request("POST", self.Endpoints.TRANSACTION_SEND_BTC, data)

    def transactions_send_btc_wait_sent(self, invoice_outbound: str, amount: int):

        transaction_receive = self.transactions_send_btc(invoice_outbound, amount)
        transaction_receive = self.transactions_wait_status(transaction_id=transaction_receive["id"],
                                                            status_wait_for='outbound_invoice_paid')
        return transaction_receive

    def transactions_send_internal(self, destination_user: int, asset: int, amount: int, description: str):
        data = {
            "destination_user": destination_user,
            "currency": asset,
            "amount": amount,
            "description": description
        }

        return self._make_request("POST", self.Endpoints.TRANSACTION_SEND_INTERNAL, data)

    def transactions_send_internal_wait_sent(self, destination_user: int, asset: int, amount: int, description: str):

        transaction_receive = self.transactions_send_internal(destination_user, asset, amount, description)
        transaction_receive = self.transactions_wait_status(transaction_id=transaction_receive["id"],
                                                            status_wait_for='internal_finished')

        return transaction_receive

    def transactions_receive_taproot_asset(self, amount: int, asset: int, description: str):
        data = {
            "amount": amount,
            "currency": asset,
            "description": description
        }
        return self._make_request("POST", self.Endpoints.TRANSACTION_RECEIVE_TAPROOT, data)

    def transactions_wait_status(self, transaction_id: int, status_wait_for: str, timeout=1000, interval=5):
        """
        Wait for a transaction to reach a specified status.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                transaction_dict = self.transaction(transaction_id)
                status = transaction_dict['status']

                if status == status_wait_for:
                    return transaction_dict
                elif status == 'error':
                    raise Exception(f"Transaction error: {transaction_dict['status_description']}")
                time.sleep(interval)

                logging.info(f"Transaction status: {status}")

            except Exception as e:
                logging.error(f"Error checking transaction status: {e}")
                break

        raise TimeoutError("Max wait time for transaction status exceeded.")

    def transactions_receive_taproot_asset_get_invoice(self, amount: int, asset: int, description: str):

        transaction_receive = self.transactions_receive_taproot_asset(amount, asset, description)
        transaction_receive = self.transactions_wait_status(transaction_id=transaction_receive["id"],
                                                            status_wait_for='inbound_invoice_generated')

        return transaction_receive["invoice_inbound"]

    def transactions_receive_btc(self, amount: int, description: str):
        data = {
            "amount": amount,
            "description": description
        }
        return self._make_request("POST", self.Endpoints.TRANSACTION_RECEIVE_BTC, data)

    def transactions_receive_btc_get_invoice(self, amount: int, description: str):

        transaction_receive = self.transactions_receive_btc(amount, description)
        transaction_receive = self.transactions_wait_status(transaction_id=transaction_receive["id"],
                                                            status_wait_for='inbound_invoice_generated')

        return transaction_receive

    def transactions(self):
        return self._make_request("GET", self.Endpoints.TRANSACTION)

    def transaction(self, id):
        uri = self.Endpoints.TRANSACTION_DETAIL.value.format(id=id)
        return self._make_request("GET", uri)

    def list_asset(self, asset: int):
        data = {
            "currency": asset
        }
        return self._make_request("POST", self.Endpoints.LIST_ASSET, data)

    def list_nft_asset(self, asset: int, price_sat: int):
        data = {
            "currency": asset,
            "price_sat": price_sat
        }
        return self._make_request("POST", self.Endpoints.LIST_NFT_ASSET, data)

    def listings(self):
        return self._make_request("GET", self.Endpoints.LISTING)

    def listings_nfts(self):
        return self._make_request("GET", self.Endpoints.LISTINGS_NFTS)

    def listings_my(self):
        return self._make_request("GET", self.Endpoints.LISTING_MY)

    def buy_taproot_asset(self, asset: int, amount: int):
        data = {
            "currency": asset,
            "amount": amount
        }
        return self._make_request("POST", self.Endpoints.BUY_TAPROOT_ASSET, data)

    def buy_taproot_asset_asset_wait_finished(self, asset: int, amount: int):

        transaction_receive = self.buy_taproot_asset(asset, amount)
        transaction_receive = self.transactions_wait_status(transaction_id=transaction_receive["id"],
                                                            status_wait_for='exchange_finished')
        return transaction_receive

    def buy_nft_asset(self, asset: int, amount: int):
        data = {
            "currency": asset,
            "amount": amount
        }
        return self._make_request("POST", self.Endpoints.BUY_NFT_ASSET, data)

    def buy_nft_asset_wait_finished(self, asset: int, amount: int):

        transaction_receive = self.buy_nft_asset(asset, amount)
        transaction_receive = self.transactions_wait_status(transaction_id=transaction_receive["id"],
                                                            status_wait_for='exchange_finished')
        return transaction_receive

    def sell_taproot_asset_asset(self, asset: int):
        data = {"currency": asset}
        return self._make_request("POST", self.Endpoints.SELL_TAPROOT_ASSET, data)

    def sell_taproot_asset_asset_wait_finished(self, asset: int):

        transaction_receive = self.sell_taproot_asset_asset(asset)
        transaction_receive = self.transactions_wait_status(transaction_id=transaction_receive["id"],
                                                            status_wait_for='exchange_finished')
        return transaction_receive
