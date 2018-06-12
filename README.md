# WavesAtomicSwapsExample
The Waves Platform will add Smart Contracts (SC) to mainnet in July 2018. While this is a long awaited feature, the
community discusses different use cases that could be implemented on top of SC. One of the most important
use cases are Atomic Swaps (AS). While there is a lot of enthusiasm about AS in the community, very few people dived
into how AS will work. This repository targets an easy to understand example for an AS on the Waves Platform. In order
to keep it simple, the AS swaps Waves against a defined asset. Usually, one of the assets that are swapped would be an
asset on a different blockchain, but the swap protocol could also be performed on one chain, e.g., both assets are
on the Waves blockchain, in order to keep the example easy.

## General description of the protocol
Imagine Alice and Bob want to exchange a certain asset. In order for being on the safe side, in the sense that neither
Alice nor Bob can take an advantage of one another, both can make use of the following protocol in order to ensure that
the swap of the asset it atomic, in the sense that either both transfers happen or none of the transfers:
- Alice generates a secret s and a corresponding hash(s)
- Alice protects her account with a contract that checks:
  - either if blockheight is > timelock (height when the contract was activated + n) and
  the tx is signed by Alice (timelock)
  - tx is signed by Bob and s is included in the tx so that hash(s) is valid for
  the hashlock.
- Alice sends a signed tx with coinA to Bob, including hash(s).
- Bob secures his account by a contract that checks:
  - either if blockheight > timelock (height when the contract was activated + m, with m < n) and
  signed by Bob
  - if tx is signed by alice and s is included so that it is valid for the hashlock
- Bob sends a signed tx with coinB to Alice, including hash(s).
- If Alice executes a transaction that fullfills Bobs contract, she reveals the secret to Bob which allows him to
to execute the first transaction.

If either Bob or Alice do not send transactions that fullfill the corresponding contracts, both will be able to
transfer the funds back to their accounts after the timelock passed. Actually, the described protocol for AS is a
combination of hash- and timelocks. Therefore, this example could also be helpful for understanding those two usecases.

## Implementation of the SC
Both Alice and Bob deploy the same smart contract with slightly different parameters, especially for the keys that are
allowed to sign a transaction and the timelock. The RIDE based contract for the above described protocol may look like
this:

```python
match tx {
    case t : SetScriptTransaction => true
    case _ =>
        let pubKeyUser1 = base58'$firstPublicKey'
        let pubKeyUser2 = base58'$secondPublicKey'
        let lockHeight = " + str($lockheight)
        let hashedSecret = tx.proofs[1]
        let preimage = tx.proofs[2]
        let hashPreimage = sha256(preimage)
        let secretMatches = hashPreimage == base58'$base58EncodedHashedSecret'
        let signedByUser1 = sigVerify(tx.bodyBytes, tx.proofs[0], pubKeyUser1)
        let signedByUser2 = sigVerify(tx.bodyBytes, tx.proofs[0], pubKeyUser2)
        let afterTimelock = height > lockHeight
        (signedByUser2 && afterTimelock) || (signedByUser1 && secretMatches)
}
```

## Implementation of the protocol in python

## Next steps
