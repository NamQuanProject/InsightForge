import asyncio
import uuid

import httpx
from a2a.client import A2AClient
from a2a.types import Message, MessageSendParams, Part, Role, SendMessageRequest, Task, TextPart
from a2a.utils import get_artifact_text, get_message_text


def build_request(prompt: str, task_id: str | None = None, context_id: str | None = None) -> SendMessageRequest:
    return SendMessageRequest(
        id=str(uuid.uuid4()),
        params=MessageSendParams(
            message=Message(
                messageId=str(uuid.uuid4()),
                taskId=task_id,
                contextId=context_id,
                role=Role.user,
                parts=[Part(root=TextPart(text=prompt))],
            )
        ),
    )


def extract_text(result: Message | Task) -> str:
    if isinstance(result, Message):
        return get_message_text(result)

    artifact_text = "\n\n".join(
        text
        for text in (get_artifact_text(artifact) for artifact in result.artifacts or [])
        if text
    )
    if artifact_text:
        return artifact_text

    if result.status.message:
        return get_message_text(result.status.message)

    return ""


async def test_agent() -> None:
    async with httpx.AsyncClient(timeout=60.0, verify=False) as httpx_client:
        client = A2AClient(url="http://localhost:5000/", httpx_client=httpx_client)

        request = build_request("Can you provide me with some user information?")
        response = await client.send_message(request)
        result = response.root.result

        print("Agent response:")
        print(extract_text(result))


if __name__ == "__main__":
    asyncio.run(test_agent())
