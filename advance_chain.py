#!/usr/bin/env python3
"""
Script to advance the Ethereum chain by sending transactions
Using prefunded test accounts from the genesis configuration
"""

from web3 import Web3
from eth_account import Account
import time
import random

# Local Ethereum node configuration
ETH_RPC = "http://127.0.0.1:61804"  # Port from kurtosis enclave inspect
CHAIN_ID = 3151908  # Default network ID from ethereum-package

# Prefunded test accounts from genesis_constants.star
# These accounts have ETH from genesis
accounts = [
    {
        "address": "0x8943545177806ED17B9F23F0a21ee5948eCaa776",
        "private_key": "0xbcdf20249abf0ed6d944c0288fad489e33f66b3960d9e6229c1cd214ed3bbe31"
    },
    {
        "address": "0xE25583099BA105D9ec0A67f5Ae86D90e50036425",
        "private_key": "0x39725efee3fb28614de3bacaffe4cc4bd8c436257e2c8bb887c4b5c4be45e76d"
    },
    {
        "address": "0x614561D2d143621E126e87831AEF287678B442b8",
        "private_key": "0x53321db7c1e331d93a11a41d16f004d7ff63972ec8ec7c25db329728ceeb1710"
    },
    {
        "address": "0xf93Ee4Cf8c6c40b329b0c0626F28333c132CF241",
        "private_key": "0xab63b23eb7941c1251757e24b3d2350d2bc05c3c388d06f8fe6feafefb1e8c70"
    },
    {
        "address": "0x802dCbE1B1A97554B4F50DB5119E37E8e7336417",
        "private_key": "0x5d2344259f42259f82d2c140aa66102ba89b57b4883ee441a8b312622bd42491"
    },
    {
        "address": "0xAe95d8DA9244C37CaC0a3e16BA966a8e852Bb6D6",
        "private_key": "0x27515f805127bebad2fb9b183508bdacb8c763da16f54e0678b16e8f28ef3fff"
    },
    {
        "address": "0x2c57d1CFC6d5f8E4182a56b4cf75421472eBAEa4",
        "private_key": "0x7ff1a4c1d57e5e784d327c4c7651e952350bc271f156afb3d00d20f5ef924856"
    },
    {
        "address": "0x741bFE4802cE1C4b5b00F9Df2F5f179A1C89171A",
        "private_key": "0x3a91003acaf4c21b3953d94fa4a6db694fa69e5242b2e37be05dd82761058899"
    }
]

def send_transaction(w3, sender_account, recipient, amount_wei, nonce):
    """Send a single transaction"""
    gas_price = w3.eth.gas_price
    
    transaction = {
        'to': recipient,
        'value': amount_wei,
        'gas': 21000,  # Standard ETH transfer gas
        'gasPrice': gas_price,
        'nonce': nonce,
        'chainId': CHAIN_ID
    }
    
    # Sign and send transaction
    signed_tx = sender_account.sign_transaction(transaction)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    return tx_hash

def main():
    # Connect to Ethereum node
    w3 = Web3(Web3.HTTPProvider(ETH_RPC))
    
    # Check connection
    if not w3.is_connected():
        print(f"❌ Failed to connect to Ethereum node at {ETH_RPC}")
        print("Make sure the node is running. Check with: kurtosis enclave inspect whispering-pond")
        return
    
    print(f"✅ Connected to Ethereum (chain {CHAIN_ID})")
    print(f"📊 Current block: {w3.eth.block_number}")
    print(f"⛽ Gas price: {w3.from_wei(w3.eth.gas_price, 'gwei')} gwei\n")
    
    # Check all account balances
    print("Account balances:")
    for i, acc in enumerate(accounts):
        balance = w3.eth.get_balance(acc["address"])
        print(f"  Account {i+1}: {acc['address'][:10]}... = {w3.from_wei(balance, 'ether'):.4f} ETH")
    print()
    
    # Parameters for chain advancement
    num_transactions = 5  # Number of transactions to send
    amount_per_tx = w3.to_wei(0.001, 'ether')  # Small amount per transaction
    
    print(f"📤 Sending {num_transactions} transactions to advance the chain...")
    print("=" * 60)
    
    tx_hashes = []
    start_block = w3.eth.block_number
    
    # Send transactions in a round-robin fashion between accounts
    for i in range(num_transactions):
        # Pick sender and recipient
        sender_idx = i % len(accounts)
        recipient_idx = (i + 1) % len(accounts)
        
        sender = accounts[sender_idx]
        recipient = accounts[recipient_idx]["address"]
        
        # Create account object
        sender_account = Account.from_key(sender["private_key"])
        
        # Get nonce
        nonce = w3.eth.get_transaction_count(sender["address"])
        
        try:
            # Send transaction
            tx_hash = send_transaction(w3, sender_account, recipient, amount_per_tx, nonce)
            tx_hashes.append(tx_hash)
            
            print(f"  Tx {i+1:2d}: {sender['address'][:8]}... → {recipient[:8]}... | Hash: {tx_hash.hex()[:16]}...")
            
            # Small delay between transactions
            if i < num_transactions - 1:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"  ❌ Tx {i+1} failed: {str(e)}")
    
    print("=" * 60)
    print(f"\n⏳ Waiting for transactions to be mined...")
    
    # Wait for confirmations
    confirmed = 0
    failed = 0
    
    for i, tx_hash in enumerate(tx_hashes):
        try:
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
            if receipt['status'] == 1:
                confirmed += 1
                print(f"  ✓ Tx {i+1} confirmed in block {receipt['blockNumber']}")
            else:
                failed += 1
                print(f"  ✗ Tx {i+1} failed")
        except Exception as e:
            print(f"  ⚠️  Tx {i+1} timeout or error: {str(e)}")
            failed += 1
    
    # Final statistics
    end_block = w3.eth.block_number
    blocks_advanced = end_block - start_block
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print(f"  • Transactions sent: {len(tx_hashes)}")
    print(f"  • Confirmed: {confirmed}")
    print(f"  • Failed: {failed}")
    print(f"  • Starting block: {start_block}")
    print(f"  • Ending block: {end_block}")
    print(f"  • Blocks advanced: {blocks_advanced}")
    print("=" * 60)
    
    # Show final balances for first 3 accounts
    print("\nFinal balances (first 3 accounts):")
    for i in range(min(3, len(accounts))):
        acc = accounts[i]
        balance = w3.eth.get_balance(acc["address"])
        print(f"  {acc['address']}: {w3.from_wei(balance, 'ether'):.6f} ETH")

if __name__ == "__main__":
    main()