import os

import boto3
from botocore.exceptions import ClientError

# Initialize the Boto3 clients
sns = boto3.client("sns")
ec2 = boto3.client("ec2")

TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]


def lambda_handler(event, context):
    print(f"Received event: {event}")

    # 1. Extract details about the state change from the event
    detail = event.get("detail", {})
    instance_id = detail.get("instance-id", "unknown")
    state = detail.get("state", "unknown")
    region = event.get("region", "unknown")
    event_time = event.get("time", "unknown")

    # Look up extra details (the event itself has no name or type)
    name = "N/A"
    instance_type = "N/A"
    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response["Reservations"][0]["Instances"][0]
        instance_type = instance.get("InstanceType", "N/A")
        for tag in instance.get("Tags", []):
            if tag["Key"] == "Name":
                name = tag["Value"]
    except (ClientError, IndexError) as err:
        print(f"Could not describe {instance_id}: {err}")

    # 2. Send an SNS notification with the details
    subject = f"EC2 instance {instance_id} is now {state}"
    message = (
        "EC2 instance state change detected\n"
        "----------------------------------\n"
        f"Instance ID   : {instance_id}\n"
        f"Name          : {name}\n"
        f"Instance type : {instance_type}\n"
        f"New state     : {state}\n"
        f"Region        : {region}\n"
        f"Event time    : {event_time}\n"
    )

    response = sns.publish(TopicArn=TOPIC_ARN, Subject=subject, Message=message)
    print(f"Notification sent for {instance_id} ({state}). MessageId: {response['MessageId']}")

    return {"instance_id": instance_id, "state": state, "message_id": response["MessageId"]}