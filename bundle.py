from dotenv import load_dotenv
import json, os, requests, rlp
from rlp.sedes import Binary, big_endian_int, binary, CountableList, BigEndianInt
from web3 import Web3
from eth_account import messages, Account

load_dotenv()

class Bundle:
    def __init__(self):
        self.url = os.environ.get("BLOCKNATIVE")
        self.privateKey = os.environ.get("PRIVATE_KEY")
        self.address = os.environ.get("EOA_ADDRESS")
        self.contractAddress = os.environ.get("CONTRACT_ADDRESS")
        self.provider = os.environ.get("RPC_PROVIDER")
        self.signature = None
        self.bundleData = None
        self.w3 = Web3(Web3.HTTPProvider(self.provider))

    def callRpc(self, txs):
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_callBundle",
            "params": [
                {
                    "txs": txs,
                    "blockNumber": hex(self.w3.eth.blockNumber),
                    "stateBlockNumber": "latest",
                }
            ]
        }
    
    def sendRpc(self, txs):
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_sendBundle",
            "params": [
                {
                    "txs": txs,
                    "blockNumber": hex(self.w3.eth.blockNumber),
                }
            ]
        }
    
    def getMyRawTransaction(self, data, gas, gasPrice):
        tx_payload = {
            'from': self.address,
            'to': self.contractAddress,
            'data': data,
            'nonce': self.w3.eth.get_transaction_count(self.address),
            'gas': gas,
            'gasPrice': gasPrice,
            'value': 0
        }
        return self.w3.eth.account.sign_transaction(tx_payload, self.privateKey).rawTransaction.hex()
    
    def buildSignature(self, request, txs):
        self.bundleData = getattr(self.__class__, request)(self, txs)
        body = json.dumps(self.bundleData)
        message = messages.encode_defunct(text=Web3.keccak(text=body).hex())
        self.signature = Account.from_key(self.privateKey).address + ':' + Account.sign_message(message, self.privateKey).signature.hex()

    def makeRpcCall(self, request, txs):
        self.buildSignature(request, txs)
        headers = {
            "Content-Type": "application/json",
            "x-auction-signature": self.signature
        }
        
        return requests.post(url=self.url, headers=headers, json=self.bundleData).json()
       


class Transaction(rlp.Serializable):
    fields = [
        ('nonce', big_endian_int),
        ('gasprice', big_endian_int),
        ('gas', big_endian_int),
        ('to', Binary.fixed_length(20, allow_empty=True)),
        ('value', big_endian_int),
        ('data', binary),
        ('v', big_endian_int),
        ('r', big_endian_int),
        ('s', big_endian_int),
    ]

    def __init__(self, nonce, gasprice, gas, to, value, data, v=0, r=0, s=0):
        super(Transaction, self).__init__(nonce, gasprice, gas, to, value, data, v, r, s)

class AccountAccesses(rlp.Serializable):
    fields = [
        ('account', Binary.fixed_length(20, allow_empty=True)),
        ('storage_keys', CountableList(BigEndianInt(32))),
    ]

class DynamicTransaction(rlp.Serializable):
    fields = [
        ('chain_id', big_endian_int),
        ('nonce', big_endian_int),
        ('max_priority_fee_per_gas', big_endian_int),
        ('max_fee_per_gas', big_endian_int),
        ('gas', big_endian_int),
        ('to', Binary.fixed_length(20, allow_empty=True)),
        ('value', big_endian_int),
        ('data', binary),
        ('access_list', CountableList(AccountAccesses)),
        ('v', big_endian_int),
        ('r', big_endian_int),
        ('s', big_endian_int),
    ]

    def __init__(self, nonce, maxPriorityFeePerGas, maxFeePerGas, gas, to, value, data, accessList, v, r, s):
        super(DynamicTransaction, self).__init__(1, nonce, maxPriorityFeePerGas, maxFeePerGas, gas, to, value, data, accessList, v, r, s) # 1 is the chainId


def getRawTransactionHash(txn):
  try:
    if txn['type'] == 2:
      dynamicTransaction = DynamicTransaction(
        txn['nonce'], 
        int(txn['maxPriorityFeePerGas']), 
        int(txn['maxFeePerGas']), 
        txn['gas'], 
        bytes.fromhex(txn['to'][2:]), 
        int(txn['value']), 
        bytes.fromhex(txn['input'][2:]),
        (),
        int(txn['v'], 16), 
        int(txn['r'], 16),
        int(txn['s'], 16)
      )
      return "0x02" + rlp.encode(dynamicTransaction).hex()
    else:
      transaction = Transaction(
        txn['nonce'],
        int(txn['gasPrice']), 
        txn['gas'], 
        bytes.fromhex(txn['to'][2:]), 
        int(txn['value']), 
        bytes.fromhex(txn['input'][2:]),
        int(txn['v'], 16), 
        int(txn['r'], 16),
        int(txn['s'], 16)
      )
      return "0x" + rlp.encode(transaction).hex()
  except:
    print("Failed to get raw tx hash")
