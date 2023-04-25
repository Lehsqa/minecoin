import pymongo
from wallet.wallet import Owner


def collections(db_client):
    return db_client["minecoin"]["users"]


def default_struct(public_key_hash: str) -> dict:
    return {
                "public_key_hash": public_key_hash,
                "balance": {},
                "total_amount": 0
            }


def get_user(public_key_hash: str):
    try:
        with pymongo.MongoClient("mongodb://localhost:27017/") as db_client:
            c = collections(db_client)
            return c.find_one({"public_key_hash": public_key_hash})
    except Exception as e:
        print(e)


def create_user(private_key: str = ""):
    usr = Owner(private_key=private_key)
    try:
        with pymongo.MongoClient("mongodb://localhost:27017/") as db_client:
            c = collections(db_client)
            c.insert_one(default_struct(usr.public_key_hash))
    except Exception as e:
        print(e)


def set_user(public_key_hash: str, field: str, data):
    try:
        with pymongo.MongoClient("mongodb://localhost:27017/") as db_client:
            c = collections(db_client)
            c.update_one({"public_key_hash": public_key_hash}, {"$set": {field: data}})
    except Exception as e:
        print(e)


def calculate_total_amount(public_key_hash: str):
    balance = get_user(public_key_hash)["balance"]
    total_amount = 0
    for i in balance:
        total_amount = total_amount + i["amount"]
    set_user(public_key_hash, "total_amount", total_amount)


# print(get_user('a037a093f0304f159fe1e49cfcfff769eaac7cda')["balance"][0]["transaction_hash"])
# print(get_user('7681c82af05a85f68a5810d967ee3a4087711867')["balance"])
# create_user()
# set_user("a037a093f0304f159fe1e49cfcfff769eaac7cda", "balance",
#          [{"transaction_hash": "59123576a84d19b36199ebf9dbe67b14fe8f9e331c7840c7157d46dd76c0d06c",
#            "output_index": 0,
#            "amount": 1000000}])
# calculate_total_amount("1ebcc7a0c357bdf3f2ffbfa327e7ff572a08c229")
