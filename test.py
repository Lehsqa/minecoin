import requests

from blockchain_users.camille import private_key as camille_private_key
from blockchain_users.coinbase import private_key as coinbase_private_key
from blockchain_users.bertrand import private_key as bertrand_private_key
from blockchain_users.miner import private_key as miner_private_key
from common.initialize_blockchain import initialize_blockchain
from common.io_blockchain import get_blockchain_from_memory
from common.io_mem_pool import store_transactions_in_memory
from common.io_users import get_user
from common.transaction import Transaction
from common.transaction_input import TransactionInput
from common.transaction_output import TransactionOutput
from node.new_block_creation import ProofOfWork
from wallet.wallet import Owner, Wallet

coinbase = Owner(private_key=coinbase_private_key)
camille = Owner(private_key=camille_private_key)
bertrand = Owner(private_key=bertrand_private_key)
miner = Owner(private_key=miner_private_key)


def create_good_transactions():
    utxo_0 = TransactionInput(transaction_hash="dd78c71eff7f13b73672e707230f1bd35133377eb0a011214b2d3e4c6be11916",
                              output_index=1)
    utxo_0_1 = TransactionInput(transaction_hash="45260cd90229f697153ab3073e70fa3c32104bb78585c86dd197d99eb70aeaef",
                                output_index=1)
    utxo_0_2 = TransactionInput(transaction_hash="3c9b916f618baeb2508c9bb92081c0bfd1804c6e02fa3e10cc3327b0fac9b62b",
                                output_index=1)
    output_0 = TransactionOutput(public_key_hash=coinbase.public_key_hash, amount=987000)
    output_0_1 = TransactionOutput(public_key_hash=bertrand.public_key_hash, amount=1000)
    transaction_1 = Transaction(inputs=[utxo_0], outputs=[output_0, output_0_1])
    transaction_1.sign(coinbase)
    transactions = [transaction_1]
    transactions_str = [transaction.transaction_data for transaction in transactions]
    store_transactions_in_memory(transactions_str)


# create_good_transactions()
# pow = ProofOfWork()
# pow.create_new_block()
# pow.broadcast()

# print(requests.get("http://127.0.0.1:5000/create_transaction",
#                    params={'sender_name': 'bertrand', 'receiver_name': 'camille', 'amount': '2000'}))
