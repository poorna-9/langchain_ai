from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import *
from .prompts import gptresults
from PyPDF2 import PdfReader

def extract_text_from_file(file):
    if file.name.endswith(".pdf"):
        reader=PdfReader(file)
        text = ""
        for page in reader.pages:
            text+=(page.extract_text() or "") + "\n"
        return text

    if file.name.endswith(".txt"):
        return file.read().decode("utf-8")

    return ""

@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def start_research_view(request):
    user=request.user
    query=request.POST.get("query") or request.GET.get("query")
    if not query:
        return Response(
            {"error": "Query is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    root_session=ResearchSession.objects.create(
        user=user,
        query=query,
        parent_session=None,
        status="running"
    )
    root_session.parent_session=root_session
    root_session.save(update_fields=["parent_session"])
    chat_context=[]
    files = request.FILES.getlist("files")
    for file in files:
        UploadedDocument.objects.create(
            session=root_session,
            file=file
        )
        extracted=extract_text_from_file(file)
        if extracted.strip():
            chat_context.append({
                "role": "system",
                "content": extracted
            })
    chat_context.append({
        "role": "user",
        "content": query
    })

    result=gptresults(chat_context)
    LLM.objects.create(
        session=root_session,
        parent_session=root_session,
        query=query,
        gptresponse=result["report"]
    )
    ResearchSummary.objects.create(
        session=root_session,
        summary=result["summary"]
    )
    ResearchReasoning.objects.create(
        session=root_session,
        reasoning_json=result["reasoning"],
        sources_json=result["sources"]
    )
    ResearchCost.objects.create(
        session=root_session,
        input_tokens=result["token_usage"]["input_tokens"],
        output_tokens=result["token_usage"]["output_tokens"],
        total_cost=result["cost"]
    )
    root_session.trace_id = result["trace_id"]
    root_session.status = "completed"
    root_session.save(update_fields=["trace_id", "status"])

    return Response(
        {
            "session_id": root_session.id,
            "parent_session_id": root_session.id,
            "report": result["report"]
        },
        status=status.HTTP_201_CREATED
    )

@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def continue_research_view(request, research_id):
    user = request.user
    query = request.POST.get("query") or request.data.get("query")

    if not query:
        return Response(
            {"error": "Query is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    root_session=get_object_or_404(
        ResearchSession,
        id=research_id,
        user=user,
        parent_session=research_id
    )

    session = ResearchSession.objects.create(
        user=user,
        query=query,
        parent_session=root_session,
        status="running"
    )

    chat_context = []
    previous_llm = LLM.objects.filter(
        parent_session=root_session
    ).order_by("created_at")

    for record in previous_llm:
        chat_context.append({
            "role": "user",
            "content": record.query
        })
        chat_context.append({
            "role": "assistant",
            "content": record.gptresponse
        })
    files=request.FILES.getlist("files")
    for file in files:
        UploadedDocument.objects.create(
            session=root_session,
            file=file
        )
        extracted = extract_text_from_file(file)
        if extracted.strip():
            chat_context.append({
                "role": "system",
                "content": extracted
            })

    chat_context.append({
        "role": "user",
        "content": query
    })

    result =gptresults(chat_context)
    LLM.objects.create(
        session=session,
        parent_session=root_session,
        query=query,
        gptresponse=result["report"]
    )
    ResearchSummary.objects.filter(session=root_session).delete()
    ResearchSummary.objects.create(
        session=root_session,
        summary=result["summary"]
    )
    ResearchReasoning.objects.filter(session=root_session).delete()
    ResearchReasoning.objects.create(
        session=root_session,
        reasoning_json=result["reasoning"],
        sources_json=result["sources"]
    )
    ResearchCost.objects.create(
        session=root_session,
        input_tokens=result["token_usage"]["input_tokens"],
        output_tokens=result["token_usage"]["output_tokens"],
        total_cost=result["cost"]
    )
    session.status = "completed"
    session.save(update_fields=["status"])
    return Response(
        {
            "session_id": session.id,
            "parent_session_id": root_session.id,
            "report": result["report"]
        },
        status=status.HTTP_201_CREATED
    )



@api_view(["GET"])
def researchhistoryview(request):
    user = request.user
    sessions = ResearchSession.objects.filter(
        user=user,
        parent_session__isnull=False,
        id=models.F("parent_session")
    ).order_by("-updated_at")
    data = []
    for session in sessions:
        summary = ResearchSummary.objects.filter(session=session).first()
        data.append({
            "research_id": session.id,
            "original_query": session.query,
            "summary": summary.summary if summary else None,
            "status": session.status
        })
    return Response(data)


@api_view(["GET"])
def researchdetailview(request, research_id):
    user = request.user
    root_session = get_object_or_404(
        ResearchSession,
        id=research_id,
        user=user,
        parent_session=research_id
    )
    last_llm = LLM.objects.filter(
        parent_session=root_session
    ).last()
    summary = ResearchSummary.objects.filter(session=root_session).first()
    reasoning = ResearchReasoning.objects.filter(session=root_session).first()
    costs = ResearchCost.objects.filter(session=root_session)

    return Response({
        "report": last_llm.gptresponse if last_llm else None,
        "summary": summary.summary if summary else None,
        "reasoning": reasoning.reasoning_json if reasoning else None,
        "sources": reasoning.sources_json if reasoning else [],
        "token_usage": {
            "input_tokens": sum(c.input_tokens for c in costs),
            "output_tokens": sum(c.output_tokens for c in costs)
        },
        "cost": sum(c.total_cost for c in costs),
        "trace_id": root_session.trace_id
    })


