from flask import Flask, request, jsonify

from common.initialize_blockchain import initialize_blockchain
from common.io_blockchain import get_blockchain_from_memory
from common.io_mem_pool import store_transactions_in_memory
from common.transaction_input import TransactionInput
from common.transaction_output import TransactionOutput
from common.transaction import Transaction
from node.new_block_creation import ProofOfWork
from node.new_block_validation import NewBlock, NewBlockException
from node.transaction_validation import Transaction as TransactionValidation
from node.transaction_validation import TransactionException

from blockchain_users.camille import private_key as camille_private_key
from blockchain_users.coinbase import private_key as coinbase_private_key
from blockchain_users.bertrand import private_key as bertrand_private_key
from wallet.wallet import Owner

from common.io_users import get_user

coinbase = Owner(private_key=coinbase_private_key)
camille = Owner(private_key=camille_private_key)
bertrand = Owner(private_key=bertrand_private_key)

app = Flask(__name__)
# initialize_blockchain()


@app.route("/block", methods=['POST'])
def validate_block():
    content = request.json
    blockchain_base = get_blockchain_from_memory()
    try:
        new_block = NewBlock(blockchain_base)
        new_block.receive(new_block=content["block"])
        new_block.validate()
        new_block.add()
    except (NewBlockException, TransactionException) as new_block_exception:
        return f'{new_block_exception}', 400
    return "Transaction success", 200


@app.route("/transactions", methods=['POST'])
def validate_transaction():
    content = request.json
    blockchain_base = get_blockchain_from_memory()
    try:
        transaction_validation = TransactionValidation(blockchain_base)
        transaction_validation.receive(transaction=content["transaction"])
        transaction_validation.validate()
        transaction_validation.validate_funds()
        transaction_validation.broadcast()
        transaction_validation.store()
    except TransactionException as transaction_exception:
        return f'{transaction_exception}', 400
    return "Transaction success", 200


@app.route("/block", methods=['GET'])
def get_blocks():
    blockchain_base = get_blockchain_from_memory()
    return jsonify(blockchain_base.to_dict)


@app.route("/utxo/<user>", methods=['GET'])
def get_user_utxos(user):
    blockchain_base = get_blockchain_from_memory()
    return jsonify(blockchain_base.get_user_utxos(user))


@app.route("/transactions/<transaction_hash>", methods=['GET'])
def get_transaction(transaction_hash):
    blockchain_base = get_blockchain_from_memory()
    return jsonify(blockchain_base.get_transaction(transaction_hash))


@app.route("/create_transaction", methods=['GET'])
def create_transaction():
    sender_name = request.args.get('sender_name')
    receiver_name = request.args.get('receiver_name')
    amount = int(request.args.get('amount'))

    if sender_name == "coinbase":
        sender = coinbase
    elif sender_name == "camille":
        sender = camille
    elif sender_name == "bertrand":
        sender = bertrand
    else:
        return "Error sender", 400

    sender_data = get_user(sender.public_key_hash)
    sender_balance = sender_data["balance"]
    sender_total_amount = sender_data["total_amount"]

    if sender_total_amount < amount:
        return "Error amount", 400

    if receiver_name == "camille":
        receiver_public_key_hash = camille.public_key_hash
    elif receiver_name == "bertrand":
        receiver_public_key_hash = bertrand.public_key_hash
    else:
        return "Error receiver", 400

    try:
        transaction = Transaction(inputs=[TransactionInput(transaction_hash=sb["transaction_hash"],
                                                           output_index=sb["output_index"]) for sb in sender_balance],
                                  outputs=[TransactionOutput(public_key_hash=sender.public_key_hash,
                                                             amount=sender_total_amount - amount),
                                           TransactionOutput(public_key_hash=receiver_public_key_hash,
                                                             amount=amount)])
        transaction.sign(sender)
        transactions = [transaction]
        transactions_str = [transaction.transaction_data for transaction in transactions]
        store_transactions_in_memory(transactions_str)

        pow = ProofOfWork()
        pow.create_new_block()
        pow.broadcast()
    except:
        return "Error transaction", 400
    return "Transaction success", 200
