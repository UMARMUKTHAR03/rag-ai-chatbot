import time
import json
import os
import sys

# Ensure server module is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server")))

from core.document_processor import DocumentChunk, split_text_into_chunks
from core.vector_database import SemanticVectorIndex

BENCHMARK_CORPUS = [
    {
        "id": "doc_quantum",
        "title": "quantum_computing_primer.pdf",
        "text": "Quantum computing harnesses principles of superposition and entanglement to execute complex calculations exponentially faster than classical Turing architectures. Qubits represent states between 0 and 1 simultaneously."
    },
    {
        "id": "doc_finance",
        "title": "q4_financial_statement.xlsx",
        "text": "In the fourth quarter of 2026, enterprise gross revenue reached $142.5 million, reflecting a year-over-year net expansion of 28.4%. Operating margins improved to 21.2%."
    },
    {
        "id": "doc_climate",
        "title": "renewable_energy_transition.docx",
        "text": "Photovoltaic solar generation capacity expanded by 41 gigawatts across coastal installations. Battery energy storage systems stabilized peak load demand fluctuations."
    },
    {
        "id": "doc_medical",
        "title": "clinical_trial_summary.pdf",
        "text": "The Phase III randomized double-blind clinical trial demonstrated an 89.2% efficacy rate with minimal adverse events reported among the treatment cohort."
    }
]

EVALUATION_QUERIES = [
    {"query": "superposition and entanglement in computing", "expected_source": "quantum_computing_primer.pdf"},
    {"query": "quarterly revenue growth and operating margins", "expected_source": "q4_financial_statement.xlsx"},
    {"query": "photovoltaic solar generation gigawatts", "expected_source": "renewable_energy_transition.docx"},
    {"query": "Phase III clinical trial efficacy rate", "expected_source": "clinical_trial_summary.pdf"},
]

def run_retrieval_benchmark():
    print("Initializing OmniMind AI Benchmark Vector Index...")
    index = SemanticVectorIndex(session_id="benchmark_eval_suite", provider="gemini")
    index.clear()

    # Index corpus
    for doc in BENCHMARK_CORPUS:
        chunk = DocumentChunk(doc["text"], {"source": doc["title"], "page": 1})
        index.add_chunks(doc["id"], doc["title"], [chunk])

    print(f"Indexed {index.count()} chunks. Running evaluation across queries...")

    hits_top1 = 0
    hits_top3 = 0
    reciprocal_ranks = []
    latencies = []

    results = []

    for item in EVALUATION_QUERIES:
        q = item["query"]
        expected = item["expected_source"]

        t0 = time.perf_counter()
        matches = index.search(query=q, top_k=3)
        lat = (time.perf_counter() - t0) * 1000
        latencies.append(lat)

        found_rank = None
        for r_idx, match in enumerate(matches):
            if match["metadata"]["source"] == expected:
                found_rank = r_idx + 1
                break

        if found_rank == 1:
            hits_top1 += 1
        if found_rank is not None and found_rank <= 3:
            hits_top3 += 1

        rr = (1.0 / found_rank) if found_rank else 0.0
        reciprocal_ranks.append(rr)

        results.append({
            "query": q,
            "expected_source": expected,
            "matched_source": matches[0]["metadata"]["source"] if matches else None,
            "rank": found_rank,
            "score": matches[0]["similarity_score"] if matches else 0.0,
            "latency_ms": round(lat, 2)
        })

    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
    recall_top1 = hits_top1 / len(EVALUATION_QUERIES)
    recall_top3 = hits_top3 / len(EVALUATION_QUERIES)
    avg_latency = sum(latencies) / len(latencies)

    report = {
        "status": "genuine_evaluated",
        "benchmark_name": "OmniMind AI Grounded Retrieval & Latency Benchmark",
        "corpus_documents": len(BENCHMARK_CORPUS),
        "total_test_queries": len(EVALUATION_QUERIES),
        "metrics": {
            "recall_at_1": round(recall_top1, 4),
            "recall_at_3": round(recall_top3, 4),
            "mean_reciprocal_rank_mrr": round(mrr, 4),
            "avg_retrieval_latency_ms": round(avg_latency, 2),
            "min_latency_ms": round(min(latencies), 2),
            "max_latency_ms": round(max(latencies), 2)
        },
        "query_results": results
    }

    os.makedirs("evaluations", exist_ok=True)
    with open("evaluations/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Benchmark Complete! Recall@1: {recall_top1*100:.1f}%, MRR: {mrr:.3f}, Avg Latency: {avg_latency:.2f}ms")
    index.clear()
    return report

if __name__ == "__main__":
    run_retrieval_benchmark()
