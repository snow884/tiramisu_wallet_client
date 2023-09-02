
import requests
from requests.auth import HTTPBasicAuth

import time 

class TiramisuClient():
    
    def __init__(self, username:str, password:str, network:str="testnet") -> None:
        if network=='testnet':
            self.base_url = "https://testnet.tarowallet.net/walletapp/"
        elif network=='mainnet':
            raise Exception("Taproot Assets in only on testnet ! Mainnet is not working yet.")
            self.base_url = "https://mainnet.tarowallet.net/walletapp/"
        else:    
            raise Exception(f"Unknown value '{network}' supplies for network argument.")
        
        self.username = username
        self.password = password
    
        assets = self.assets()
        
        assets_dict = {curr["acronym"]:curr for curr in assets} 
        self.btc_asset_id = assets_dict["SAT"]["id"]
    
    def raise_with_text(self, res:dict):
        
        try: 
            res.raise_for_status()
        except Exception as e:
            raise Exception(res.text) from e
    
    def balance_create(self, asset: str):
        """
        Create a new balance in the current user account

        Args:
            asset (str): Acronym of the asset to create 
            new balance for
        """
        
        url = "api/balance/create/"
        
        res = requests.post(self.base_url + url, data={"currency": asset}, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
    def get_btc_balance(self):
        """
        List all asset balances in the current user account
        """
        
        balances = self.balances()
        
        balances_dict = {bal["currency"]: bal for bal in balances}
        
        return balances_dict[self.btc_asset_id]
        
    def balances(self):
        """
        List all asset balances in the current user account
        """
        url = "api/balances/"
        
        res = requests.get(self.base_url + url, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
        return res.json()
        
    def balances_nft(self):
        """
        List all NFT balances in the current user account
        """
        
        url = "api/balances-nft/"
        
        res = requests.get(self.base_url + url, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
        return res.json()
    
    def asset_create(self, acronym:str, asset_id:str, file_path:str=None):
        url = "api/currency/create/"
        
        if file_path:
            with open(file_path,'rb') as f:
                picture_orig = f.read()
        else:
            picture_orig = None
        
        res = requests.post(self.base_url + url, data={"acronym": acronym, "asset_id":asset_id}, files={"picture_orig":picture_orig }, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
        return res.json()
        
    def assets_mint(self, acronym:str, name:str, description:str, supply:int, file_path:str):
        url = "api/currencies/mint/"
        
        if file_path:
            with open(file_path,'rb') as f:
                picture_orig = f.read()
        else:
            picture_orig = None
        
        data = {
                "acronym": acronym, 
                "name":name, 
                "description":description, 
                "supply":str(supply), 
            }
        
        files = {'picture_orig': ('test_image.jpg', picture_orig,'image/' + file_path.split(".")[0])}
        
        res = requests.post(self.base_url + url, data=data,files=files, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
        return res.json()

    def assets_mint_wait_finished(self, acronym:str, name:str, description:str, supply:int, file_path:str):
        
        asset = self.assets_mint(acronym, name, description, supply, file_path)
        asset = self.asset(asset['id'])
        minting_transaction = self.transactions_wait_status(transaction_id=asset['minting_transaction'], status_wait_for='minted')
        
        return asset

    def assets_mint_nft(self, name:str, description:str, file_path:str):
        url = "api/currencies/mint-nft/"
        
        if file_path:
            with open(file_path,'rb') as f:
                picture_orig = f.read()
        else:
            picture_orig = None
        
        data = {
                "name":name, 
                "description":description, 
            }
        
        files = {'picture_orig': ('test_image.jpg', picture_orig,'image/' + file_path.split(".")[0])}
        
        res = requests.post(self.base_url + url, data=data,files=files, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
        return res.json()

    def assets_mint_nft_wait_finished(self, acronym:str, name:str, description:str, supply:int, file_path:str):
        
        minting_transaction = self.assets_mint_nft(acronym, name, description, supply, file_path)
        minting_transaction = self.transactions_wait_status(transaction_id=minting_transaction["id"], status_wait_for='minted')
        
        return minting_transaction

    def assets(self):
        url = "api/currencies/"
    
        res = requests.get(self.base_url + url, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
        return res.json()

    def asset(self, id):
        url = f"api/currencies/{id}"
    
        res = requests.get(self.base_url + url, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
        return res.json()
    
    def transactions_send_taproot_asset(self, invoice_outbound):
        url = "api/transactions/send_taro/"

        res = requests.post(self.base_url + url,data={"invoice_outbound":invoice_outbound}, auth=HTTPBasicAuth(self.username, self.password ))
    
        self.raise_with_text(res)
        
        return res.json()
    
    def transactions_send_btc(self, invoice_outbound:str, amount:int):
        url = "api/transactions/send_btc/"
        
        res = requests.post(self.base_url + url,data={"invoice_outbound":invoice_outbound, "amount":amount}, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
        return res.json()
    
    def transactions_send_btc_wait_sent(self, invoice_outbound:str, amount:int):
        
        transaction_receive = self.transactions_send_btc(invoice_outbound, amount)
        transaction_receive = self.transactions_wait_status(transaction_id=transaction_receive["id"], status_wait_for='outbound_invoice_paid')
        
        return transaction_receive
    
    def transactions_send_internal(self,destination_user:int,asset:int,amount:int,description:str):
        url = "api/transactions/send_internal/"
        
        res = requests.post(self.base_url + url,data={"destination_user":destination_user, "currency":asset, "amount":amount, "description":description}, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
        return res.json()

    def transactions_send_internal_wait_sent(self,destination_user:int,asset:int,amount:int,description:str):
        
        transaction_receive = self.transactions_send_internal(destination_user,asset,amount,description)
        transaction_receive = self.transactions_wait_status(transaction_id=transaction_receive["id"], status_wait_for='internal_finished')
        
        return transaction_receive
        
    def transactions_receive_taproot_asset(self, amount:int, asset: int, description: str):
        
        url = "api/transactions/receive_taro/"
        
        res = requests.post(self.base_url + url, data={"amount":amount, "currency":asset, "description":description}, auth=HTTPBasicAuth(self.username, self.password ))

        self.raise_with_text(res)
        
        return res.json()
    
    def transactions_wait_status(self, transaction_id:int, status_wait_for:str):
        
        for _ in range(0,1000):
            
            transaction_dict = self.transaction(transaction_id)
            
            status = transaction_dict['status']

            if status==status_wait_for:
                return transaction_dict
            elif status=='error':
                raise Exception(f"Transaction error: {transaction_dict['status_description']}")

            print(f"Transaction status: {status}")

            time.sleep(1)
        
        raise Exception(f"Max number of retries exceeded!")
        
    def transactions_receive_taproot_asset_get_invoice(self, amount:int, asset: int, description: str):
        
        transaction_receive = self.transactions_receive_taproot_asset(amount, asset, description)
        transaction_receive = self.transactions_wait_status(transaction_id=transaction_receive["id"], status_wait_for='inbound_invoice_generated')
        
        return (transaction_receive["invoice_inbound"])
        
    def transactions_receive_btc(self, amount:int, description: str):
        url = "api/transactions/receive_btc/"
        
        res = requests.post(self.base_url + url,data={"amount":amount, "description":description}, auth=HTTPBasicAuth(self.username, self.password ))

        self.raise_with_text(res)
        
        return res.json()

    def transactions_receive_btc_get_invoice(self, amount:int, description: str):
        
        transaction_receive = self.transactions_receive_btc(amount, description)
        transaction_receive = self.transactions_wait_status(transaction_id=transaction_receive["id"], status_wait_for='inbound_invoice_generated')
        
        return (transaction_receive)

    def transactions(self):
        url = "api/transactions/"
        
        res = requests.get(self.base_url + url, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
        return res.json()
        
    def transaction(self, id):
        url = f"api/transactions/{id}"
    
        res = requests.get(self.base_url + url, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
        return res.json()
        
    def list_asset(self,asset:int):
        url = "api/list_asset/"
        
        res = requests.post(self.base_url + url, data={"currency":asset}, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
        return res.json()
        
    def list_nft_asset(self,asset:int,price_sat:int):
        url = "api/list_nft_asset/"
        
        res = requests.post(self.base_url + url, data={"currency":asset, "price_sat":price_sat}, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
        return res.json()
        
    def listings(self):
        url = "api/listings/"
        
        res = requests.get(self.base_url + url, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
        return res.json()
        
    def listings_nfts(self):
        url = "api/listings_nfts/"
        
        res = requests.get(self.base_url + url, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
        return res.json()
        
    def listings_my(self):
        url = "api/listings_my/"
        
        res = requests.get(self.base_url + url, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
        return res.json()
        
    def buy_taproot_asset_asset(self, asset:int, amount:int):
        url = "api/buy_taro_asset/"
    
        res = requests.post(self.base_url + url, data={"currency":asset, "amount":amount}, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
        return res.json()
    
    def buy_taproot_asset_asset_wait_finished(self, asset:int, amount:int):
        
        transaction_receive = self.buy_taproot_asset_asset(asset, amount)
        transaction_receive = self.transactions_wait_status(transaction_id=transaction_receive["id"], status_wait_for='exchange_finished')
        return transaction_receive
        
    def buy_nft_asset(self, asset:int):
        url = "api/buy_nft_asset/"
    
        res = requests.post(self.base_url + url, data={"currency":asset}, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
        return res.json()
    
    def buy_nft_asset_wait_finished(self, asset:int, amount:int):
        
        transaction_receive = self.buy_nft_asset(asset, amount)
        transaction_receive = self.transactions_wait_status(transaction_id=transaction_receive["id"], status_wait_for='exchange_finished')
        return transaction_receive
    
    def sell_taproot_asset_asset(self, asset:int):
        url = "api/sell_taro_asset/"

        res = requests.post(self.base_url + url, data={"currency":asset}, auth=HTTPBasicAuth(self.username, self.password ))
        
        self.raise_with_text(res)
        
        return res.json()

    def sell_taproot_asset_asset_wait_finished(self, asset:int):
        
        transaction_receive = self.sell_taproot_asset_asset(asset)
        transaction_receive = self.transactions_wait_status(transaction_id=transaction_receive["id"], status_wait_for='exchange_finished')
        return transaction_receive