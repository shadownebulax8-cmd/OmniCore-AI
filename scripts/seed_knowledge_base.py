"""
Run once after `docker compose up` to seed the knowledge base with sample
FAQ content, so /support/ask has something real to retrieve.

    docker compose exec app python main.py seed-kb
"""
from memory.vector_store import KnowledgeBaseStore

SAMPLE_FAQS = [
    ("What are your support hours?", "Our support team is available Monday to Friday, 9am to 6pm UTC."),
    ("How do I reset my password?", "Go to Settings > Security > Reset Password and follow the emailed link."),
    ("Do you offer refunds?", "Yes - full refunds within 14 days of purchase, no questions asked."),
    ("How do I upgrade my plan?", "Go to Settings > Billing > Change Plan and select your new tier."),
    ("How do I cancel my subscription?", "Go to Settings > Billing > Cancel Subscription. Access continues until the end of the paid period."),
]


def main():
    store = KnowledgeBaseStore()
    for question, answer in SAMPLE_FAQS:
        store.add_document(f"Q: {question}\nA: {answer}", metadata={"source": "seed_faq"})
    print(f"Seeded {len(SAMPLE_FAQS)} FAQ entries into the knowledge base.")


if __name__ == "__main__":
    main()
