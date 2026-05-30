from flask import Flask, request, jsonify
import json

app = Flask('mock_openrouter')


@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    # Return a simplified OpenRouter-style response where the message content
    # contains a JSON string matching the recommender's expected output.
    example = {
        "Food": {
            "Morning": [{"name": "Oatmeal with berries", "reason": "Low glycemic index"}],
            "Afternoon": [{"name": "Grilled vegetables and quinoa", "reason": "Balanced macros"}],
            "Evening": [{"name": "Baked salmon and salad", "reason": "Lean protein"}]
        },
        "Drinks": [{"name": "Water", "reason": "Hydration"}],
        "Snacks": [{"name": "Almonds", "reason": "Healthy fats"}],
        "alternativeMessage": "Alternative food options are available.",
        "healthyTipsForToday": {"tip1": "Stay hydrated"}
    }

    content_str = json.dumps(example)

    resp = {
        "id": "mock-1",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content_str
                }
            }
        ]
    }
    return jsonify(resp), 200


if __name__ == '__main__':
    # Run on port 9000
    app.run(host='127.0.0.1', port=9000)
