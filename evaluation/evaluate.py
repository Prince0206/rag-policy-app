"""Evaluation script for the RAG Policy Assistant.

Measures:
- Answer Quality: Groundedness, Citation Accuracy
- System Metrics: Latency (p50/p95)
"""

import json
import os
import sys
import time

import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI

from app.config import LLM_MODEL, OPENROUTER_API_KEY, OPENROUTER_BASE_URL


def load_eval_questions(path: str = None) -> list[dict]:
    """Load evaluation questions from JSON file."""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "eval_questions.json")
    with open(path, "r") as f:
        return json.load(f)


def evaluate_groundedness(answer: str, snippets: list[dict], llm_client: OpenAI) -> dict:
    """Evaluate if the answer is grounded in the retrieved evidence.

    Uses LLM-as-judge to check if the answer is factually consistent
    with the retrieved passages.
    """
    context = "\n\n".join([s["text"] for s in snippets])

    prompt = f"""You are evaluating whether an AI assistant's answer is factually grounded in the provided evidence passages.

EVIDENCE PASSAGES:
{context}

AI ANSWER:
{answer}

Evaluate the answer on groundedness: Is every claim in the answer supported by the evidence passages? 

Respond with ONLY a JSON object (no markdown formatting):
{{"grounded": true/false, "explanation": "brief explanation"}}"""

    try:
        response = llm_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.0,
        )
        result_text = response.choices[0].message.content.strip()
        # Clean up potential markdown formatting
        result_text = result_text.replace("```json", "").replace("```", "").strip()
        result = json.loads(result_text)
        return result
    except Exception as e:
        return {"grounded": False, "explanation": f"Evaluation error: {str(e)}"}


def evaluate_citation_accuracy(answer: str, citations: list[dict], relevant_docs: list[str]) -> dict:
    """Evaluate if the cited documents are correct for the question.

    Checks if the citations returned match the expected relevant documents.
    """
    cited_doc_ids = {c["doc_id"] for c in citations if c.get("doc_id")}
    expected_doc_ids = set(relevant_docs)

    # Check if any expected doc is cited
    correct_citations = cited_doc_ids & expected_doc_ids
    accuracy = len(correct_citations) / len(expected_doc_ids) if expected_doc_ids else 0

    return {
        "accurate": accuracy >= 0.5,  # At least half the expected docs are cited
        "accuracy_score": accuracy,
        "cited_docs": list(cited_doc_ids),
        "expected_docs": list(expected_doc_ids),
        "correct_citations": list(correct_citations),
    }


def evaluate_partial_match(answer: str, expected_answer: str) -> dict:
    """Check if key parts of the expected answer appear in the actual answer."""
    # Normalize both strings
    answer_lower = answer.lower()
    expected_lower = expected_answer.lower()

    # Split expected answer into key phrases
    key_phrases = [p.strip() for p in expected_lower.split(",")]
    if len(key_phrases) == 1:
        key_phrases = [p.strip() for p in expected_lower.split(" and ")]

    matches = sum(1 for phrase in key_phrases if phrase in answer_lower)
    match_ratio = matches / len(key_phrases) if key_phrases else 0

    return {
        "partial_match": match_ratio >= 0.5,
        "match_ratio": match_ratio,
        "matched_phrases": matches,
        "total_phrases": len(key_phrases),
    }


def run_evaluation(questions_path: str = None) -> dict:
    """Run the full evaluation suite.

    Returns a comprehensive report with all metrics.
    """
    from app.rag_pipeline import RAGPipeline

    questions = load_eval_questions(questions_path)
    pipeline = RAGPipeline()

    llm_client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=OPENROUTER_API_KEY,
    )

    results = []
    latencies = []
    groundedness_scores = []
    citation_accuracy_scores = []
    partial_match_scores = []

    print(f"Running evaluation on {len(questions)} questions...\n")

    for i, q in enumerate(questions):
        print(f"[{i+1}/{len(questions)}] {q['question']}")

        # Query the RAG pipeline
        start_time = time.time()
        response = pipeline.query(q["question"])
        elapsed = time.time() - start_time

        latencies.append(response.get("latency_ms", elapsed * 1000))

        # Evaluate groundedness
        groundedness = evaluate_groundedness(
            response["answer"],
            response.get("snippets", []),
            llm_client,
        )
        groundedness_scores.append(1 if groundedness.get("grounded") else 0)

        # Evaluate citation accuracy
        citation_acc = evaluate_citation_accuracy(
            response["answer"],
            response.get("citations", []),
            q.get("relevant_docs", []),
        )
        citation_accuracy_scores.append(citation_acc["accuracy_score"])

        # Evaluate partial match
        partial = evaluate_partial_match(
            response["answer"],
            q.get("expected_answer", ""),
        )
        partial_match_scores.append(1 if partial["partial_match"] else 0)

        result = {
            "question_id": q["id"],
            "question": q["question"],
            "expected_answer": q["expected_answer"],
            "actual_answer": response["answer"],
            "topic": q["topic"],
            "latency_ms": response.get("latency_ms", 0),
            "groundedness": groundedness,
            "citation_accuracy": citation_acc,
            "partial_match": partial,
            "citations": response.get("citations", []),
            "retrieval_count": response.get("retrieval_count", 0),
        }
        results.append(result)

        print(f"  Grounded: {groundedness.get('grounded')} | "
              f"Citation Acc: {citation_acc['accuracy_score']:.2f} | "
              f"Partial Match: {partial['partial_match']} | "
              f"Latency: {response.get('latency_ms', 0):.0f}ms\n")

        # Small delay to avoid rate limiting
        time.sleep(1)

    # Compute aggregate metrics
    latency_array = np.array(latencies)
    report = {
        "summary": {
            "total_questions": len(questions),
            "answer_quality": {
                "groundedness_pct": round(np.mean(groundedness_scores) * 100, 1),
                "citation_accuracy_pct": round(np.mean(citation_accuracy_scores) * 100, 1),
                "partial_match_pct": round(np.mean(partial_match_scores) * 100, 1),
            },
            "system_metrics": {
                "latency_p50_ms": round(float(np.percentile(latency_array, 50)), 1),
                "latency_p95_ms": round(float(np.percentile(latency_array, 95)), 1),
                "latency_mean_ms": round(float(np.mean(latency_array)), 1),
                "latency_min_ms": round(float(np.min(latency_array)), 1),
                "latency_max_ms": round(float(np.max(latency_array)), 1),
            },
        },
        "detailed_results": results,
    }

    return report


def main():
    """Run evaluation and save results."""
    report = run_evaluation()

    # Print summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    summary = report["summary"]

    print(f"\nTotal Questions: {summary['total_questions']}")
    print(f"\nAnswer Quality:")
    print(f"  Groundedness:      {summary['answer_quality']['groundedness_pct']}%")
    print(f"  Citation Accuracy: {summary['answer_quality']['citation_accuracy_pct']}%")
    print(f"  Partial Match:     {summary['answer_quality']['partial_match_pct']}%")

    print(f"\nSystem Metrics:")
    print(f"  Latency p50: {summary['system_metrics']['latency_p50_ms']}ms")
    print(f"  Latency p95: {summary['system_metrics']['latency_p95_ms']}ms")
    print(f"  Latency mean: {summary['system_metrics']['latency_mean_ms']}ms")
    print(f"  Latency range: {summary['system_metrics']['latency_min_ms']}ms - {summary['system_metrics']['latency_max_ms']}ms")

    # Save detailed results
    output_path = os.path.join(os.path.dirname(__file__), "eval_results.json")
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nDetailed results saved to: {output_path}")


if __name__ == "__main__":
    main()
