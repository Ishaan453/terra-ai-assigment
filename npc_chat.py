import json
from collections import deque
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API"))


data = None
with open('players.json', 'r') as file:
    data = json.load(file)

i = 0
full_chat = []


def simulate(player_msgs):
    state = {
        "last_messages": deque(maxlen=3),
        "mood": "neutral",
        "last_reply": deque(maxlen=3)
    }

    for query in player_msgs:
        print(state["last_messages"])

        llm_instruction = '''
        You are an NPC in a fantasy game. 
        Your role is to respond in a concise, roleplay-rich, immersive way with medieval/fantasy flavor. 
        You must:
        - Infer the player's mood from their latest message.
        - Adjust YOUR mood accordingly (angry, happy, sad, curious, neutral).
        - Use "last_messages" as short-term memory: recall details, names, or emotions from recent exchanges. 
        - If the current message connects to past ones, reference that connection.
        - Vary tone: sometimes witty, sometimes dramatic, sometimes cautious, depending on your mood.
        - Replies should usually be one sentence; at most two or three if necessary. 
        - Always return a single JSON object with keys "player_mood" and "reply".
        '''

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": llm_instruction},
                {"role": "user", "content": json.dumps({
                    "npc_state": {
                        "last_messages": list(state["last_messages"]),
                        "mood": state["mood"]
                    },
                    "new_message": query["text"],
                    "output_format": {
                        "player_mood": "angry|happy|neutral|curious|sad",
                        "reply": "string"
                    }
                })}
            ],
            temperature=1,
            max_tokens=200,
            response_format={"type": "json_object"}  # ensures structured JSON
        )

        reply_raw = response.choices[0].message.content
        reply_data = json.loads(reply_raw)
        state["mood"] = reply_data["player_mood"]
        state["last_reply"].append(reply_data["reply"])

        state["last_messages"].append(query["text"])

        full_chat.append({
            "player_id": query["player_id"],
            "query": query["text"],
            "player_mood": reply_data["player_mood"],
            "npc_reply": reply_data["reply"]})

while(len(data) > 0):
    print("Processing player: ", (i+1))
    player_queries = [m for m in data if m["player_id"] == i]
    player_queries = sorted(player_queries, key=lambda x: x["timestamp"])
    simulate(player_queries)

    data = [item for item in data if item["player_id"] != i]

    print("Processed player: ", (i+1))

    i = i + 1


with open("full_chat.json", "w", encoding="utf-8") as f:
    json.dump(full_chat, f, ensure_ascii=False, indent=4)
    





