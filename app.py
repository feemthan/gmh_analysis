import sys
from dataclasses import asdict
from pathlib import Path

from flask import Flask, jsonify, request

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.benchmark import _ensure_gaming_db  # noqa: E402
from src.pipeline import AnalyticsPipeline  # noqa: E402

app = Flask(__name__)


@app.route("/chat", methods=["POST"])
def chat() -> dict[str, str]:
    data = request.get_json()
    # response = run_pipeline(user_message)
    query = data.get("query", "")

    db_path = _ensure_gaming_db()

    pipeline = AnalyticsPipeline(db_path=db_path)

    result = pipeline.run(question=query)

    response = asdict(result)
    response = response["answer"]
    print(f"Received message: {query} \nResponse: {response}")
    return jsonify({"response": response})


if __name__ == "__main__":
    # trunk-ignore(bandit/B104)
    app.run(host="0.0.0.0", port=5000)
