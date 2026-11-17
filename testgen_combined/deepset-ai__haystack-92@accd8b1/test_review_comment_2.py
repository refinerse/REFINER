import pytest

from haystack.finder import Finder


class _Doc:
    def __init__(self, *, _id, meta):
        self.id = _id
        self.meta = meta
        self.text = "dummy"


class _FakeDocumentStore:
    """
    Exposes BOTH APIs used by before/after code:
    - get_all_docs_in_index (before)
    - get_all_documents_in_index (after)
    """

    def __init__(self, questions):
        self._questions = questions

    def get_all_docs_in_index(self, index, filters=None):
        return list(self._questions)

    def get_all_documents_in_index(self, index, filters=None):
        return list(self._questions)


class _FakeRetriever:
    def __init__(self, questions):
        self.document_store = _FakeDocumentStore(questions)
        self.embedding_model = None

    def retrieve(self, question, top_k=10, index=None, filters=None, candidate_doc_ids=None):
        # Always return the correct doc so correct_retrievals == number_of_questions.
        return [_Doc(_id="es_doc_1", meta={"doc_id": "gold_doc_1"})]


class _FakeReader:
    """
    Simulates a FARM-like reader behavior where top_k_per_candidate influences how many
    answers exist "per document". The "gold" answer is only present when
    top_k_per_candidate > 1. This makes it observable if Finder.eval() incorrectly forces
    top_k_per_candidate = 1 (before code).

    Important for matching the *after* implementation:
    - For unanswerable questions, Finder.eval() only counts correct_no_answers_topk if it
      sees answer["answer"] is None among the returned answers.
      To keep the test deterministic, we only use answerable questions (avoid depending on
      presence/position of a None answer).
    """

    def __init__(self):
        self.top_k_per_candidate = 5
        self.return_no_answers = False

    def predict(self, question, documents, top_k):
        doc_id = documents[0].id

        # If forced down to 1, we "miss" the gold answer (simulate candidate truncation bug)
        if self.top_k_per_candidate == 1:
            answers = [
                {
                    "answer": "wrong",
                    "document_id": doc_id,
                    "offset_start_in_doc": 0,
                    "offset_end_in_doc": 1,
                }
            ]
        else:
            # Gold answer exists, but only at rank 2
            answers = [
                {
                    "answer": "wrong",
                    "document_id": doc_id,
                    "offset_start_in_doc": 0,
                    "offset_end_in_doc": 1,
                },
                {
                    "answer": "gold",
                    "document_id": doc_id,
                    # Gold span in eval is (answer_start, answer_start + len(text) + 1) => (10, 15)
                    "offset_start_in_doc": 10,
                    "offset_end_in_doc": 15,
                },
            ]

        # Return only what top_k asks for (mimics real reader behavior)
        return {"answers": answers[:top_k]}


def test_eval_does_not_force_top_k_per_candidate_and_reports_topk_metrics():
    # Use ONLY answerable questions to avoid the after-code's separate no-answer metrics path.
    questions = [
        {
            "_source": {
                "question": "Q1 answerable",
                "doc_id": "gold_doc_1",
                "answers": [{"text": "gold", "answer_start": 10}],
            }
        },
        {
            "_source": {
                "question": "Q2 answerable",
                "doc_id": "gold_doc_1",
                "answers": [{"text": "gold", "answer_start": 10}],
            }
        },
    ]

    finder = Finder(reader=_FakeReader(), retriever=_FakeRetriever(questions))

    results = finder.eval(top_k_retriever=1, top_k_reader=2)

    # After fix: eval exposes top-k reader metrics.
    # Before fix: different keys ("reader_recall"/"reader_map"/...) and no "reader_top_k_accuracy".
    assert "reader_top_k_accuracy" in results, (
        "Finder.eval() should return the new reader top-k metrics (e.g., 'reader_top_k_accuracy'); "
        "older eval() returned 'reader_recall'/'reader_map' instead."
    )

    # Gold answer is only present when top_k_per_candidate is not forcibly set to 1.
    # After fix: top_k_per_candidate is not modified, so gold at rank 2 is found => accuracy 1.0.
    assert results["reader_top_k_accuracy"] == pytest.approx(1.0), (
        "With top_k_reader=2 and the gold answer at rank 2, eval() should yield perfect "
        "top-k accuracy when it does not force reader.top_k_per_candidate=1."
    )
    assert results["reader_top1_accuracy"] == pytest.approx(0.0), (
        "Since the gold answer is at rank 2, top-1 accuracy should be 0.0."
    )