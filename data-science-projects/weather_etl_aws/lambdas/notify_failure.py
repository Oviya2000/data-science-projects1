"""Publish a failure summary to SNS so on-call sees it in Slack/email."""
import json
import os


def handler(event, context=None):
    subject = f"[weather-etl] pipeline failure — {os.getenv('ENVIRONMENT','?')}"
    body = json.dumps({
        "run_id": event.get("run_id"),
        "error":  event.get("error"),
    }, indent=2)

    topic = os.getenv("TOPIC_ARN")
    if topic:
        import boto3
        boto3.client("sns").publish(TopicArn=topic, Subject=subject, Message=body)
    else:
        print(subject); print(body)

    return {"notified": bool(topic)}
