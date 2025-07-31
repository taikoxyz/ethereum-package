PYTHON_IMAGE = "python:3.11-alpine"
EIP4788_DEPLOYMENT_SERVICE_NAME = "eip4788-contract-deployment"
EIP4788_CONTRACT_ADDRESS = "0x000F3df6D732807Ef1319fB7B8bB8522d0Beac02"


def deploy_eip4788_contract_in_background(plan, sender_key, el_uri):
    sender_script = plan.upload_files("./sender.py")

    plan.add_service(
        name=EIP4788_DEPLOYMENT_SERVICE_NAME,
        config=ServiceConfig(
            image=PYTHON_IMAGE,
            files={"/tmp": sender_script},
            cmd=["/bin/sh", "-c", "touch /tmp/sender.log && tail -f /tmp/sender.log"],
            env_vars={
                "SENDER_PRIVATE_KEY": sender_key,
                "EL_RPC_URI": el_uri,
            },
        ),
    )

    plan.exec(
        service_name=EIP4788_DEPLOYMENT_SERVICE_NAME,
        recipe=ExecRecipe(["pip", "install", "web3"]),
    )

    # Start the deployment script in background
    plan.exec(
        service_name=EIP4788_DEPLOYMENT_SERVICE_NAME,
        recipe=ExecRecipe(
            ["/bin/sh", "-c", "python /tmp/sender.py &"]
        ),
    )
    
    # Wait a moment and then show the logs
    plan.exec(
        service_name=EIP4788_DEPLOYMENT_SERVICE_NAME,
        recipe=ExecRecipe(
            ["/bin/sh", "-c", "sleep 30 && echo '=== EIP4788 Deployment Logs ===' && cat /tmp/sender.log && echo '=== End of Logs ==='"]
        ),
    )