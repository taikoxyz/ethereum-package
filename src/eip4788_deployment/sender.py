"""
this script deploys the contract used by eip4788. It has been presigned and the contract uses a deterministic deployment.
"""

from web3 import Web3
import os
import time
import logging
from decimal import Decimal

VALUE_TO_SEND = 0x9184

logging.basicConfig(filename="/tmp/sender.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)


def eip4788_deployment():
    # this is the 5th prefunded address
    sender = os.getenv("SENDER_PRIVATE_KEY", "bcdf20249abf0ed6d944c0288fad489e33f66b3960d9e6229c1cd214ed3bbe31")
    # this is the 4788 presigned contract deployer
    receiver = "0x0B799C86a49DEeb90402691F1041aa3AF2d3C875"
    signed_4788_deployment_tx = os.getenv("SIGNED_4788_DEPLOYMENT_TX", "f8838085e8d4a510008303d0908080b86a60618060095f395ff33373fffffffffffffffffffffffffffffffffffffffe14604d57602036146024575f5ffd5b5f35801560495762001fff810690815414603c575f5ffd5b62001fff01545f5260205ff35b5f5ffd5b62001fff42064281555f359062001fff0155001b820539851b9b6eb1f0")
    el_uri = os.getenv("EL_RPC_URI", 'http://0.0.0.0:32002')
    logging.info(f"Starting EIP4788 deployment process...")
    logging.info(f"Using sender {sender} receiver {receiver} and el_uri {el_uri}")

    try:
        w3 = Web3(Web3.HTTPProvider(el_uri))
        logging.info(f"Connected to Web3 provider at {el_uri}")
        
        # sleep for 10s before checking again
        time.sleep(10)

        # Check if the chain has started before submitting transactions
        block = w3.eth.get_block('latest')
        logging.info(f"Latest block number: {block.number}")
        
        if block.number > 1:
            logging.info("Chain has started, proceeding with Funding")
            # Import sender account
            sender_account = w3.eth.account.from_key(sender)
            logging.info(f"Sender account address: {sender_account.address}")
            
            # Check sender balance
            sender_balance = w3.eth.get_balance(sender_account.address)
            logging.info(f"Sender balance: {w3.from_wei(sender_balance, 'ether')} ETH")

            # Prepare funding transaction
            logging.info("Preparing funding tx")
            transaction = {
                "from": sender_account.address,
                "to": receiver,
                "value": w3.to_wei(Decimal('1000.0'), 'ether'),  # Sending 1000 Ether
                "gasPrice": w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(sender_account.address)
            }

            # Estimate gas
            logging.info("Estimating gas")
            estimated_gas = w3.eth.estimate_gas(transaction)
            logging.info(f"Estimated gas: {estimated_gas}")

            # Set gas value
            transaction["gas"] = estimated_gas

            # Sign and send transaction
            logging.info(f"Sending funding transaction: {transaction}")
            signed_txn = w3.eth.account.sign_transaction(transaction, sender)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            logging.info(f"Funding transaction sent with hash: {tx_hash.hex()}")

            time.sleep(10)
            # Wait for the transaction to be mined
            funding_tx = w3.eth.get_transaction(tx_hash)
            logging.info(f"Funding Txhash: {tx_hash.hex()}")
            logging.info(f"Genesis funder Balance after funding: {w3.from_wei(w3.eth.get_balance(sender_account.address), 'ether')} ETH")
            logging.info(f"4788 deployer Balance after funding: {w3.from_wei(w3.eth.get_balance(receiver), 'ether')} ETH")

            if funding_tx["from"] == sender_account.address:
                logging.info("Funding tx mined successfully")
                logging.info("Deploying signed tx")
                # Prepare deployment transaction
                deployment_tx_hash = w3.eth.send_raw_transaction(signed_4788_deployment_tx)
                logging.info(f"Deployment transaction sent with hash: {deployment_tx_hash.hex()}")

                # Sleep before checking
                time.sleep(10)
                deployment_tx = w3.eth.get_transaction(deployment_tx_hash)
                logging.info(f"Deployment Txhash: {deployment_tx.hash.hex()}")

                # Sleep before checking
                time.sleep(10)

                logging.info(f"4788 deployer Balance after deployment: {w3.from_wei(w3.eth.get_balance(receiver), 'ether')} ETH")
                assert deployment_tx["from"] == receiver

                # Check if contract has been deployed
                eip4788_code = w3.eth.get_code('0x000F3df6D732807Ef1319fB7B8bB8522d0Beac02')
                if eip4788_code != b"":
                    logging.info(f"Contract deployed successfully: {eip4788_code.hex()}")
                    logging.info("Deployment tx mined successfully")
                    return True
                else:
                    logging.error("Contract deployment failed - no code at expected address")
                    return False
            else:
                logging.error("Funding failed - transaction sender mismatch")
                return False
        else:
            logging.info(f"Chain has not started yet - block number: {block.number}")
            return False
    except Exception as e:
        logging.error(f"Exception during deployment: {str(e)}")
        logging.error(f"Exception type: {type(e).__name__}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return False
        logging.info("Funding failed, restarting script")
        return False
    else:
      logging.info("Chain has not started, restarting script")
      return False

def run_till_deployed():
    deployment_status = False
    attempt = 1
    # while deployment_status is False:
    try:
        logging.info(f"Starting deployment attempt #{attempt}")
        deployment_status = eip4788_deployment()
        if deployment_status:
            logging.info(f"Deployment successful on attempt #{attempt}")
        else:
            logging.info(f"Deployment failed on attempt #{attempt}, retrying in 30 seconds...")
            time.sleep(30)
            attempt += 1
    except Exception as e:
        logging.error(f"Attempt #{attempt} failed with exception: {e}")
        logging.error("restarting deployment as previous one failed")
        time.sleep(30)
        attempt += 1



if __name__ == "__main__":
    run_till_deployed()
    logging.info("Deployment complete, exiting script")