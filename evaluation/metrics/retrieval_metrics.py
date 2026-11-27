from math import log2


def precision_at_k(retrieved_ids, relevant_ids, k):
    if k <= 0:
        raise ValueError("k must be > 0")
    retrieved = list(retrieved_ids)[:k]
    relevant = set(relevant_ids)
    if not retrieved:
        return 0.0
    return sum(x in relevant for x in retrieved) / k


def recall_at_k(retrieved_ids, relevant_ids, k):
    if k <= 0:
        raise ValueError("k must be > 0")
    relevant = set(relevant_ids)
    if not relevant:
        raise ValueError("relevant_ids cannot be empty")
    return len(set(list(retrieved_ids)[:k]) & relevant) / len(relevant)


def reciprocal_rank(retrieved_ids, relevant_ids):
    relevant = set(relevant_ids)
    for rank, item in enumerate(retrieved_ids, start=1):
        if item in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(ranked_ids, relevance_by_id, k):
    if k <= 0:
        raise ValueError("k must be > 0")
    ranked = list(ranked_ids)[:k]

    def dcg(items):
        return sum(
            (2 ** max(0, float(relevance_by_id.get(item, 0))) - 1)
            / log2(position + 1)
            for position, item in enumerate(items, start=1)
        )

    ideal = sorted(relevance_by_id, key=lambda x: relevance_by_id[x], reverse=True)[:k]
    ideal_dcg = dcg(ideal)
    return dcg(ranked) / ideal_dcg if ideal_dcg else 0.0
