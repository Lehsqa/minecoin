
from datetime import datetime

from blockchain_users.coinbase import private_key
from common.block import Block, BlockHeader
from common.io_blockchain import store_blockchain_in_memory
from common.merkle_tree import get_merkle_root
from common.transaction import Transaction
from common.transaction_input import TransactionInput
from common.transaction_output import TransactionOutput
from wallet.wallet import Owner

coinbase = Owner(private_key=private_key)
genesis = Owner()


def initialize_blockchain():
    timestamp_0 = datetime.timestamp(datetime.fromisoformat('2022-08-28 14:35:23.111'))
    input_0 = TransactionInput(transaction_hash="abcd1234", output_index=0)
    output_0 = TransactionOutput(public_key_hash=coinbase.public_key_hash, amount=1000000)
    transaction_0 = Transaction([input_0], [output_0])
    transaction_0.sign(genesis)
    block_header_0 = BlockHeader(previous_block_hash="f"*64,
                                 timestamp=timestamp_0,
                                 noonce=1,
                                 merkle_root=get_merkle_root([transaction_0.transaction_data]))
    block_0 = Block(
        transactions=[transaction_0.transaction_data],
        block_header=block_header_0
    )
    store_blockchain_in_memory(block_0)
