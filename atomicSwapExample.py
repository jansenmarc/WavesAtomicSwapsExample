import pywaves.crypto as crypto
import base58
import struct
import json
import hashlib
import time
import pywaves

# Config section, plase fill the variables with corresponding values
aliceAddress = ''
alicePrivateKey = ''
alicePublicKey = ''
bobsAddress = ''
bobsPrivateKey = ''
bobsPublicKey = ''
secret = ''
assetId = ''
node = ''

hashedSecret = hashlib.sha256(crypto.str2bytes(secret)).digest()
base58.b58encode(hashedSecret)
base58EncodedHashedSecret = base58.b58encode(crypto.str2bytes(hashedSecret))

# Method that sets the Atomic Swap smart contract for an account. IMPORTANT: remove the first case in production mode
def setSmartContract(privateKeyForScriptAccount, firstPublicKey, secondPublicKey, lockheight):
    smartContract = "match tx {\n" + \
        "case t : SetScriptTransaction => true\n" + \
        "case _ => \n" + \
            "let pubKeyUser1 = base58'" + firstPublicKey + "'\n" + \
            "let pubKeyUser2 = base58'" + secondPublicKey + "'\n" + \
            "let lockHeight = " + str(lockheight) + "\n" + \
            "let hashedSecret = tx.proofs[1]\n" + \
            "let preimage = tx.proofs[2]\n" + \
            "let hashPreimage = sha256(preimage)\n" + \
            "let secretMatches = hashPreimage == base58'" + base58EncodedHashedSecret + "'\n" + \
            "let signedByUser1 = sigVerify(tx.bodyBytes, tx.proofs[0], pubKeyUser1)\n" + \
            "let signedByUser2 = sigVerify(tx.bodyBytes, tx.proofs[0], pubKeyUser2)\n" + \
            "let afterTimelock = height > lockHeight\n" + \
            "(signedByUser2 && afterTimelock) || (signedByUser1 && secretMatches)\n" + \
    "}"
    account = pywaves.Address(privateKey = privateKeyForScriptAccount)
    tx = account.setScript(smartContract, txFee = 500000)

# Methods that creates a transaction that sends Waves
def createTransaction(recipient, publicKey, privateKey, amount, attachment='', txFee=100000):
    timestamp = int(time.time() * 1000)
    sData = b'\4' + \
            b'\2' + \
            base58.b58decode(publicKey) + \
            b'\0\0' + \
            struct.pack(">Q", timestamp) + \
            struct.pack(">Q", amount) + \
            struct.pack(">Q", txFee) + \
            base58.b58decode(recipient) + \
            struct.pack(">H", len(attachment)) + \
            crypto.str2bytes(attachment)
    signature = crypto.sign(privateKey, sData)
    data = {
        "type": 4,
        "version": 2,
        "senderPublicKey": publicKey,
        "recipient": recipient,
        "amount": amount,
        "fee": txFee,
        "timestamp": timestamp,
        "attachment": base58.b58encode(crypto.str2bytes(attachment)),
        "proofs": [
            signature
        ]
    }

    return data

# Methods that creates a transaction that sends asset with assetId
def createAssetTransaction(recipient, assetId, amount, publicKey, privateKey, attachment='', txFee=100000):
    timestamp = int(time.time() * 1000)
    sData = b'\4' + \
            b'\2' + \
            base58.b58decode(publicKey) + \
            b'\1' + base58.b58decode(assetId) + \
            b'\0' + \
            struct.pack(">Q", timestamp) + \
            struct.pack(">Q", amount) + \
            struct.pack(">Q", txFee) + \
            base58.b58decode(recipient) + \
            struct.pack(">H", len(attachment)) + \
            crypto.str2bytes(attachment)
    signature = crypto.sign(privateKey, sData)
    data = {
        "type": 4,
        "version": 2,
        "assetId": assetId,
        "senderPublicKey": publicKey,
        "recipient": recipient,
        "amount": amount,
        "fee": txFee,
        "timestamp": timestamp,
        "attachment": base58.b58encode(crypto.str2bytes(attachment)),
        "proofs": [
            signature
        ]
    }

    return data

pywaves.setNode(node, 'testnet')

# Alice creates a new transaction for Bob
aliceInitialTxForBob = createTransaction(bobsAddress, alicePublicKey, alicePrivateKey, 100, txFee=500000)
# add the hashed secret to the proofs on second position
aliceInitialTxForBob['proofs'].append(base58.b58encode(crypto.str2bytes(hashedSecret)))
# Alice secures her account by a Smart Contract implmenting the Atomic Swap protocol
setSmartContract(alicePrivateKey, alicePublicKey, bobsPublicKey, 385000)

# Bob creates a new transaction for Alice
bobsInitialTxForAlice = createAssetTransaction(aliceAddress, assetId, 100, bobsPublicKey, bobsPrivateKey, txFee=500000)
# take the hash of the secret and add it to the transaction also on the second position
bobsInitialTxForAlice['proofs'].append(aliceInitialTxForBob['proofs'][1])
# Bob secures his account by a Smart Contract implmenting the Atomic Swap protocol
setSmartContract(bobsPrivateKey, bobsPublicKey, alicePublicKey, 380000)


# wait before the tx is executed so that the script is really activated (tx is in the blockchain)
time.sleep(30)
# Alice executes Bobs transactions and by this reveals the secret to Bob
bobsInitialTxForAlice['proofs'].append(base58.b58encode(secret))
transferredTransactionByAlice = pywaves.wrapper('/assets/broadcast/transfer', json.dumps(bobsInitialTxForAlice))
print(json.dumps(transferredTransactionByAlice))

# Bobs executes Alice transaction and makes use of the formerly revealed secret
aliceInitialTxForBob['proofs'].append(transferredTransactionByAlice['proofs'][2])
transferredTransactionByBob = pywaves.wrapper('/assets/broadcast/transfer', json.dumps(aliceInitialTxForBob))
print(json.dumps(transferredTransactionByBob))
