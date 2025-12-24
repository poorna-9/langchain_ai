import uuid
from typing import List, Dict
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import PydanticOutputParser
from django.conf import settings

class ResearchOutput(BaseModel):
    report: str = Field(description="Final detailed research report")
    summary: str = Field(description="Concise research summary")
    reasoning: Dict = Field(description="Step-by-step reasoning")
    sources: List[str] = Field(description="List of sources used")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2,openai_api_key=settings.OPENAI_API_KEY)
parser = PydanticOutputParser(pydantic_object=ResearchOutput)
def convert_context(chat_context):
    messages = []
    for item in chat_context:
        if item["role"] == "system":
            messages.append(SystemMessage(content=item["content"]))
        elif item["role"] == "user":
            messages.append(HumanMessage(content=item["content"]))
        elif item["role"] == "assistant":
            messages.append(AIMessage(content=item["content"]))
    return messages

def gptresults(chat_context):
    messages = convert_context(chat_context)
    messages.insert(0, SystemMessage(content=f"""
You are a professional research assistant.
Produce a detailed report, summary, reasoning, and cite sources.
{parser.get_format_instructions()}
"""))
    response = llm.invoke(messages=messages)
    parsed = parser.parse(response.content)
    usage = getattr(response, "usage_metadata", {}) or {}
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    cost = round((input_tokens * 0.00000015) + (output_tokens * 0.0000006), 6)
    return {
        "report": parsed.report,
        "summary": parsed.summary,
        "reasoning": parsed.reasoning,
        "sources": parsed.sources,
        "token_usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
        "cost": cost,
        "trace_id": f"trace_{uuid.uuid4().hex[:10]}"
    }
