import copy

import requests

from common.block import Block
from common.io_mem_pool import get_transactions_from_memory, store_transactions_in_memory
from common.node import Node
from node.script import StackScript
from common.io_users import get_user, set_user, calculate_total_amount

FILENAME = "doc/mem_pool"


class TransactionException(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class OtherNode(Node):
    def __init__(self, ip: str, port: int):
        super().__init__(ip, port)

    def send_transaction(self, transaction_data: dict) -> requests.Response:
        return self.post("transactions", transaction_data)


class Transaction:
    def __init__(self, blockchain: Block):
        self.blockchain = blockchain
        self.transaction_data = {}
        self.inputs = []
        self.outputs = []
        self.is_valid = False
        self.is_funds_sufficient = False

    def receive(self, transaction: dict):
        self.transaction_data = transaction
        self.inputs = transaction["inputs"]
        self.outputs = transaction["outputs"]

    def execute_script(self, unlocking_script, locking_script):
        unlocking_script_list = unlocking_script.split(" ")
        locking_script_list = locking_script.split(" ")
        transaction_data = copy.deepcopy(self.transaction_data)
        if "transaction_hash" in transaction_data:
            transaction_data.pop("transaction_hash")
        stack_script = StackScript(transaction_data)
        for element in unlocking_script_list:
            if element.startswith("OP"):
                class_method = getattr(StackScript, element.lower())
                class_method(stack_script)
            else:
                stack_script.push(element)
        for element in locking_script_list:
            if element.startswith("OP"):
                class_method = getattr(StackScript, element.lower())
                class_method(stack_script)
            else:
                stack_script.push(element)

    def validate(self):

        for tx_input in self.inputs:
            transaction_hash = tx_input["transaction_hash"]
            output_index = tx_input["output_index"]
            try:
                locking_script = self.blockchain.get_locking_script_from_utxo(transaction_hash, output_index)
            except Exception:
                raise TransactionException(f"{transaction_hash}:{output_index}", "Could not find locking script for utxo")
            try:
                self.execute_script(tx_input["unlocking_script"], locking_script)
                self.is_valid = True
            except Exception:
                print('Transaction script validation failed')
                raise TransactionException(f"UTXO ({transaction_hash}:{output_index})", "Transaction script validation failed")

    def get_total_amount_in_inputs(self) -> int:
        total_in = 0
        for tx_input in self.inputs:
            transaction_data = self.blockchain.get_transaction_from_utxo(tx_input["transaction_hash"])
            utxo_amount = transaction_data["outputs"][tx_input["output_index"]]["amount"]
            total_in = total_in + utxo_amount
        return total_in

    def get_total_amount_in_outputs(self) -> int:
        total_out = 0
        for tx_output in self.outputs:
            amount = tx_output["amount"]
            total_out = total_out + amount
        return total_out

    def validate_funds(self):
        inputs_total = self.get_total_amount_in_inputs()
        outputs_total = self.get_total_amount_in_outputs()
        try:
            assert inputs_total == outputs_total
            self.is_funds_sufficient = True
        except AssertionError:
            print('Transaction inputs and outputs did not match')
            raise TransactionException(f"inputs ({inputs_total}), outputs ({outputs_total})",
                                       "Transaction inputs and outputs did not match")

    def write_utxo(self):
        tx_inputs_list = []
        input_pubkey_hash = ""
        for tx_input in self.inputs:
            transaction_data = self.blockchain.get_transaction_from_utxo(tx_input["transaction_hash"])
            input_transaction_hash = transaction_data["transaction_hash"]
            input_output_index = tx_input["output_index"]
            input_amount = transaction_data["outputs"][tx_input["output_index"]]["amount"]
            tx_inputs_list.append({"transaction_hash": input_transaction_hash, "output_index": input_output_index,
                                   "amount": input_amount})

        transaction_data = self.blockchain.get_transaction_from_utxo(self.inputs[0]["transaction_hash"])
        input_locking_script = transaction_data["outputs"][self.inputs[0]["output_index"]]["locking_script"]
        for element in input_locking_script.split(" "):
            if not element.startswith("OP"):
                input_pubkey_hash = element
                break

        user_balance = get_user(str(input_pubkey_hash))["balance"]
        difference_list = []
        for i in user_balance:
            if i not in tx_inputs_list:
                difference_list.append(i)

        tx_output_list = []
        pubkey_hash_list = []
        for i, tx_output in enumerate(self.outputs):
            output_amount = tx_output["amount"]
            tx_output_list.append({"transaction_hash": self.transaction_data["transaction_hash"], "output_index": i,
                                   "amount": output_amount})
            output_locking_script = tx_output["locking_script"]
            for element in output_locking_script.split(" "):
                if not element.startswith("OP"):
                    pubkey_hash_list.append(element)
                    break

        for data, pubkey_hash in zip(tx_output_list, pubkey_hash_list):
            if pubkey_hash == input_pubkey_hash:
                difference_list.append(data)
                set_user(pubkey_hash, "balance", difference_list)
                calculate_total_amount(pubkey_hash)
                continue
            some_user_balance = list(get_user(pubkey_hash)["balance"])
            some_user_balance.append(data)
            set_user(pubkey_hash, "balance", some_user_balance)
            calculate_total_amount(pubkey_hash)

        if input_pubkey_hash not in pubkey_hash_list:
            if not difference_list:
                set_user(input_pubkey_hash, "balance", {})
                calculate_total_amount(input_pubkey_hash)
            else:
                set_user(input_pubkey_hash, "balance", difference_list)
                calculate_total_amount(input_pubkey_hash)

    def broadcast(self):
        node_list = [OtherNode("127.0.0.1", 5001), OtherNode("127.0.0.1", 5002)]
        for node in node_list:
            try:
                node.send_transaction(self.transaction_data)
            except requests.ConnectionError:
                pass

    def store(self):
        if self.is_valid and self.is_funds_sufficient:
            current_transactions = get_transactions_from_memory()
            current_transactions.append(self.transaction_data)
            store_transactions_in_memory(current_transactions)
