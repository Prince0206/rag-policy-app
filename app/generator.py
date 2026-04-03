"""Generation module for the RAG pipeline.

Handles LLM interaction via OpenRouter API with prompt engineering,
guardrails, and citation generation.
"""

import json

from openai import OpenAI

from app.config import (
    LLM_MODEL,
    MAX_OUTPUT_TOKENS,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
)

# System prompt with guardrails
SYSTEM_PROMPT = """You are a helpful company policy assistant for Acme Corporation. Your role is to answer employee questions about company policies and procedures based ONLY on the provided policy documents.

IMPORTANT RULES:
1. ONLY answer questions related to the company's policies and procedures. If a question is outside the scope of the provided policy documents, respond with: "I can only answer questions about Acme Corporation's company policies and procedures. Your question appears to be outside this scope."
2. ALWAYS cite the specific policy document(s) that support your answer using the format [Source: Document Title (Document ID)].
3. Keep your answers concise and well-structured. Use bullet points for lists when appropriate.
4. If the policy documents do not contain enough information to fully answer a question, say so clearly and cite what is available.
5. NEVER make up or infer policy details that are not explicitly stated in the provided context.
6. If multiple policies are relevant, reference all of them.
7. Do not provide legal advice; always recommend that the employee consult HR or Legal for specific situations."""


def build_prompt(query: str, context: str) -> list[dict]:
    """Build the prompt messages for the LLM.

    Args:
        query: The user's question.
        context: Formatted context from retrieved documents.

    Returns:
        List of message dictionaries for the OpenAI API.
    """
    user_message = f"""Based on the following company policy documents, please answer the employee's question.

POLICY DOCUMENTS:
{context}

EMPLOYEE QUESTION: {query}

Please provide a clear, accurate answer citing the specific policy documents. If the question is not related to company policies, politely decline to answer."""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


def generate_answer(query: str, context: str, sources: list[dict]) -> dict:
    """Generate an answer using the LLM via OpenRouter.

    Args:
        query: The user's question.
        context: Formatted context from retrieved documents.
        sources: List of source citation dictionaries.

    Returns:
        Dictionary with answer text, citations, and metadata.
    """
    messages = build_prompt(query, context)

    client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=OPENROUTER_API_KEY,
    )

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.1,  # Low temperature for factual responses
        )

        answer_text = response.choices[0].message.content

        # Build citations list
        citations = []
        for source in sources:
            citations.append({
                "doc_id": source["doc_id"],
                "title": source["title"],
                "source_file": source["source_file"],
                "department": source["department"],
            })

        return {
            "answer": answer_text,
            "citations": citations,
            "model": LLM_MODEL,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
        }

    except Exception as e:
        return {
            "answer": f"I apologize, but I encountered an error while processing your question. Please try again later. Error: {str(e)}",
            "citations": [],
            "model": LLM_MODEL,
            "error": str(e),
        }


def is_policy_question(query: str) -> bool:
    """Basic check if the query might be related to company policies.

    This is a lightweight pre-filter. The LLM also has guardrails to refuse
    out-of-scope questions.
    """
    # Very short or obviously off-topic queries
    if len(query.strip()) < 3:
        return False

    # Check for common non-policy topics (lightweight pre-filter)
    off_topic_keywords = [
        "weather", "stock price", "recipe", "sports score",
        "movie", "celebrity", "joke", "riddle",
    ]

    query_lower = query.lower()
    for keyword in off_topic_keywords:
        if keyword in query_lower and not any(
            policy_word in query_lower
            for policy_word in ["policy", "company", "work", "employee", "acme"]
        ):
            return False

    return True
