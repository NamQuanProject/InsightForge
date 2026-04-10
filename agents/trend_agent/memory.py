import os
import json
from datetime import datetime
from typing import List, Dict
from typing import List, Dict
from openai import OpenAI
import numpy as np



class AgentMemory:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.base_path = os.path.join("agent_memory", agent_name)

        self.skills_file = os.path.join(self.base_path, "skills.md")
        self.experiments_path = os.path.join(self.base_path, "experiments")

        os.makedirs(self.experiments_path, exist_ok=True)

        if not os.path.exists(self.skills_file):
            with open(self.skills_file, "w") as f:
                f.write("# Skills\n\n")

        # 🔥 Embedding model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.embed_model = "text-embedding-3-small"
        os.makedirs(self.experiments_path, exist_ok=True)
        if not os.path.exists(self.skills_file):
            with open(self.skills_file, "w") as f:
                f.write("# Skills\n\n")


    def create_embedding(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model=self.embed_model,
            input=text
        )
        return response.data[0].embedding

    def cosine_similarity(self, a, b):
        a = np.array(a)
        b = np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    # =========================
    # SKILLS
    # =========================
    def get_skills(self) -> str:
        with open(self.skills_file, "r") as f:
            return f.read()

    def add_skill(self, skill_text: str):
        with open(self.skills_file, "a") as f:
            f.write(f"- {skill_text}\n")

    # =========================
    # EXPERIMENTS
    # =========================
    def save_experiment(
        self,
        query: str,
        response: str,
        tools_used: List[str] = None,
        notes: str = ""
    ):
        embedding = self.create_embedding(query)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(self.experiments_path, f"{timestamp}.json")

        data = {
            "query": query,
            "response": response,
            "tools_used": tools_used or [],
            "notes": notes,
            "embedding": embedding,
            "timestamp": timestamp
        }

        with open(file_path, "w") as f:
            json.dump(data, f)

    def get_recent_experiments(self, k: int = 3) -> List[Dict]:
        files = sorted(os.listdir(self.experiments_path))[-k:]
        results = []

        for f_name in files:
            path = os.path.join(self.experiments_path, f_name)
            try:
                with open(path, "r") as f:
                    results.append(json.load(f))
            except:
                continue

        return results
    
    def retrieve_similar_experiments(self, query: str, k: int = 5):
        query_emb = self.create_embedding(query)

        scored = []

        for file in os.listdir(self.experiments_path):
            path = os.path.join(self.experiments_path, file)

            try:
                with open(path, "r") as f:
                    data = json.load(f)

                sim = self.cosine_similarity(query_emb, data["embedding"])
                scored.append((sim, data))

            except:
                continue

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:k]   # 🔥 return (sim, data)

    # =========================
    # FORMAT FOR PROMPT
    # =========================
    
    # =========================
    # MEMORY CONTEXT
    # =========================
    def build_memory_context(self, query: str) -> str:
        skills = self.get_skills()
        similar_experiments = self.retrieve_similar_experiments(query)



        exp_text = ""
        for exp in similar_experiments:
            exp_text += f"""
            - Query: {exp['query']}
            - Tools: {exp.get('tools_used', [])}
            - Result: {exp['response'][:150]}
            """
        return exp_text