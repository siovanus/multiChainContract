OntCversion = '2.0.0'
"""
An Example of OEP-4
"""
from ontology.interop.System.Storage import GetContext, Get, Put, Delete
from ontology.interop.System.Runtime import Notify, CheckWitness, Serialize, Deserialize
from ontology.interop.System.Action import RegisterAction
from ontology.builtins import concat
from ontology.interop.Ontology.Runtime import Base58ToAddress
from ontology.interop.System.ExecutionEngine import GetExecutingScriptHash
from ontology.interop.Ontology.Native import Invoke

TransferEvent = RegisterAction("transfer", "from", "to", "amount")
ApprovalEvent = RegisterAction("approval", "owner", "spender", "amount")
LockEvent = RegisterAction("lock", "fee", "to_chain_id", "destination_contract", "address", "amount")
UnlockEvent = RegisterAction("unlock", "address", "amount")

ctx = GetContext()
CONTRACT_ADDRESS = GetExecutingScriptHash()
CROSS_CHAIN_CONTRACT_ADDRESS = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x09')

NAME = 'MyToken0'
SYMBOL = 'MYT0'
DECIMALS = 8
FACTOR = 100000000
OWNER = Base58ToAddress("AKQj23VWXpdRou1FCUX3g8XBcSxfBLiezp")
TOTAL_AMOUNT = 1000000000
BALANCE_PREFIX = bytearray(b'\x01')
APPROVE_PREFIX = b'\x02'
SUPPLY_KEY = 'TotalSupply'

def Main(operation, args):
    """
    :param operation:
    :param args:
    :return:
    """
    # 'init' has to be invokded first after deploying the contract to store the necessary and important info in the blockchain
    if operation == 'init':
        return init()
    if operation == 'name':
        return name()
    if operation == 'symbol':
        return symbol()
    if operation == 'decimals':
        return decimals()
    if operation == 'totalSupply':
        return totalSupply()
    if operation == 'balanceOf':
        if len(args) != 1:
            return False
        acct = args[0]
        return balanceOf(acct)
    if operation == 'transfer':
        if len(args) != 3:
            return False
        else:
            from_acct = args[0]
            to_acct = args[1]
            amount = args[2]
            return transfer(from_acct,to_acct,amount)
    if operation == 'transferMulti':
        return transferMulti(args)
    if operation == 'transferFrom':
        if len(args) != 4:
            return False
        spender = args[0]
        from_acct = args[1]
        to_acct = args[2]
        amount = args[3]
        return transferFrom(spender,from_acct,to_acct,amount)
    if operation == 'approve':
        if len(args) != 3:
            return False
        owner  = args[0]
        spender = args[1]
        amount = args[2]
        return approve(owner,spender,amount)
    if operation == 'allowance':
        if len(args) != 2:
            return False
        owner = args[0]
        spender = args[1]
        return allowance(owner,spender)
    if operation == 'lock':
        if len(args) != 5:
            return False
        fee = args[0]
        to_chain_id = args[1]
        destination_contract = args[2]
        address = args[3]
        amount = args[4]
        return lock(fee, to_chain_id, destination_contract, address, amount)
    if operation == 'unlock':
        if len(args) != 1:
            return False
        args = args[0]
        return unlock(args)
    raise Exception("method not supported")

def init():
    """
    initialize the contract, put some important info into the storage in the blockchain
    :return:
    """

    if len(OWNER) != 20:
        Notify(["Owner illegal!"])
        return False
    if Get(ctx,SUPPLY_KEY):
        Notify("Already initialized!")
        return False
    else:
        total = TOTAL_AMOUNT * FACTOR
        Put(ctx,SUPPLY_KEY,total)
        Put(ctx,concat(BALANCE_PREFIX,OWNER),total)
        # Notify(["transfer", "", Base58ToAddress(OWNER), total])
        # ownerBase58 = AddressToBase58(OWNER)
        TransferEvent("", OWNER, total)

        return True


def name():
    """
    :return: name of the token
    """
    return NAME


def symbol():
    """
    :return: symbol of the token
    """
    return SYMBOL


def decimals():
    """
    :return: the decimals of the token
    """
    return DECIMALS


def totalSupply():
    """
    :return: the total supply of the token
    """
    return Get(ctx, SUPPLY_KEY)


def balanceOf(account):
    """
    :param account:
    :return: the token balance of account
    """
    if len(account) != 20:
        raise Exception("address length error")
    return Get(ctx,concat(BALANCE_PREFIX,account))


def transfer(from_acct,to_acct,amount):
    """
    Transfer amount of tokens from from_acct to to_acct
    :param from_acct: the account from which the amount of tokens will be transferred
    :param to_acct: the account to which the amount of tokens will be transferred
    :param amount: the amount of the tokens to be transferred, >= 0
    :return: True means success, False or raising exception means failure.
    """
    if len(to_acct) != 20 or len(from_acct) != 20:
        raise Exception("address length error")
    if CheckWitness(from_acct) == False or amount < 0:
        return False
    assert(_transfer(from_acct, to_acct, amount))
    return True

def _transfer(_from, _to, _amount):
    fromKey = concat(BALANCE_PREFIX,_from)
    fromBalance = Get(ctx,fromKey)
    if _amount > fromBalance:
        return False
    if _amount == fromBalance:
        Delete(ctx,fromKey)
    else:
        Put(ctx,fromKey,fromBalance - _amount)
    toKey = concat(BALANCE_PREFIX,_to)
    toBalance = Get(ctx,toKey)
    Put(ctx,toKey,toBalance + _amount)

    # Notify(["transfer", AddressToBase58(from_acct), AddressToBase58(to_acct), amount])
    # TransferEvent(AddressToBase58(from_acct), AddressToBase58(to_acct), amount)
    TransferEvent(_from, _to, _amount)

    return True


def transferMulti(args):
    """
    :param args: the parameter is an array, containing element like [from, to, amount]
    :return: True means success, False or raising exception means failure.
    """
    for p in args:
        if len(p) != 3:
            # return False is wrong
            raise Exception("transferMulti params error.")
        if transfer(p[0], p[1], p[2]) == False:
            # return False is wrong since the previous transaction will be successful
            raise Exception("transferMulti failed.")
    return True


def approve(owner,spender,amount):
    """
    owner allow spender to spend amount of token from owner account
    Note here, the amount should be less than the balance of owner right now.
    :param owner:
    :param spender:
    :param amount: amount>=0
    :return: True means success, False or raising exception means failure.
    """
    if len(spender) != 20 or len(owner) != 20:
        raise Exception("address length error")
    if CheckWitness(owner) == False:
        return False
    if amount > balanceOf(owner) or amount < 0:
        return False

    key = concat(concat(APPROVE_PREFIX,owner),spender)
    Put(ctx, key, amount)

    # Notify(["approval", AddressToBase58(owner), AddressToBase58(spender), amount])
    # ApprovalEvent(AddressToBase58(owner), AddressToBase58(spender), amount)
    ApprovalEvent(owner, spender, amount)

    return True


def transferFrom(spender,from_acct,to_acct,amount):
    """
    spender spends amount of tokens on the behalf of from_acct, spender makes a transaction of amount of tokens
    from from_acct to to_acct
    :param spender:
    :param from_acct:
    :param to_acct:
    :param amount:
    :return:
    """
    if len(spender) != 20 or len(from_acct) != 20 or len(to_acct) != 20:
        raise Exception("address length error")
    if CheckWitness(spender) == False:
        return False

    fromKey = concat(BALANCE_PREFIX, from_acct)
    fromBalance = Get(ctx, fromKey)
    if amount > fromBalance or amount < 0:
        return False

    approveKey = concat(concat(APPROVE_PREFIX,from_acct),spender)
    approvedAmount = Get(ctx,approveKey)
    toKey = concat(BALANCE_PREFIX,to_acct)

    if amount > approvedAmount:
        return False
    elif amount == approvedAmount:
        Delete(ctx,approveKey)
        Put(ctx, fromKey, fromBalance - amount)
    else:
        Put(ctx,approveKey,approvedAmount - amount)
        Put(ctx, fromKey, fromBalance - amount)

    toBalance = Get(ctx, toKey)
    Put(ctx, toKey, toBalance + amount)

    # Notify(["transfer", AddressToBase58(from_acct), AddressToBase58(to_acct), amount])
    # TransferEvent(AddressToBase58(from_acct), AddressToBase58(to_acct), amount)
    TransferEvent(from_acct, to_acct, amount)

    return True


def allowance(owner,spender):
    """
    check how many token the spender is allowed to spend from owner account
    :param owner: token owner
    :param spender:  token spender
    :return: the allowed amount of tokens
    """
    key = concat(concat(APPROVE_PREFIX,owner),spender)
    return Get(ctx,key)
    
    
def lock(fee, to_chain_id, destination_contract, address, amount):
    """
    lock some amount of tokens of this contract, call cross chain method to release to_amount of tokens of another chain's contract
    :param fee: miner fee of this cross chain tx
    :param to_chain_id: chain id of destination chain
    :param address: address of caller
    :param to_amount: amount to lock
    :return:
    """
    if len(address) != 20:
        raise Exception("address length error")
    if CheckWitness(address) == False:
        raise Exception("address checkwitness failed.")
        
    # transfer asset
    res = transfer(address, CONTRACT_ADDRESS, amount)
    if not res:
        raise Exception("transfer failed.")
    
    # call cross chain contract
    input_map = {
        "address": address,
        "amount": amount
    }
    input_bytes = Serialize(input_map)
    
    param = state(fee, address, to_chain_id, destination_contract, "unlock", input_bytes)
    res = Invoke(0, CROSS_CHAIN_CONTRACT_ADDRESS, "createCrossChainTx", param)
    if not res:
        raise Exception("call cross chain contract failed.")  
        
    LockEvent(fee, to_chain_id, destination_contract, address, amount)
    return True
    
def unlock(args):
    """
    lock some amount of tokens of this contract, call cross chain method to release to_amount of tokens of another chain's contract
    :param fee: miner fee of this cross chain tx
    :param to_chain_id: chain id of destination chain
    :param address: address of caller
    :param to_amount: amount to lock
    :return:
    """
    if CheckWitness(CROSS_CHAIN_CONTRACT_ADDRESS) == False:
        raise Exception("cross chain contract address checkwitness failed.")
    
    input_map = Deserialize(args)
    address = input_map["address"]
    amount = input_map["amount"]
        
    # unlock asset
    res = _transfer(CONTRACT_ADDRESS, address, amount)
    if not res:
        raise Exception("transfer failed.")

    UnlockEvent(address, amount)    
    return True
