from dotenv import load_dotenv
import os, time
from bundle import Blocknative, getRawTransactionHash
from web3 import Web3
from blocknative.stream import Stream

w3 = Web3(Web3.HTTPProvider(os.environ.get("RPC_PROVIDER")))

##### build your own raw transaction hash ####
# data = "<SOME-DATA>"
# bundle = Bundle()
# tx = bundle.getMyRawTransaction(data, 500000, 50000000000)
# response = bundle.makeRpcCall("callRpc", [tx])
# print(response)

# use blocknative sdk to get raw transaction hash from mempool payload
load_dotenv()

API_KEY = os.environ.get("API_KEY")

monitor_address = "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45" #uniswap autorouter

global_filters = [{
    'status': 'pending'
}]

async def txn_handler(txn, unsubscribe):
  # print(txn)
  rawTxHash = getRawTransactionHash(txn)
  time.sleep(1)
  checkRawTxHash = w3.eth.get_raw_transaction(txn['hash']).hex()
  print(rawTxHash==checkRawTxHash)


if __name__ == '__main__': 
    stream = Stream(API_KEY, global_filters=global_filters)
    stream.subscribe_address(monitor_address, txn_handler)
    stream.connect()