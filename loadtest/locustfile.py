"""
Load Testing with Locust.
Phase 8: Reliability Testing.

Run with:
    locust -f loadtest/locustfile.py --host http://localhost:8000 --users 10 --spawn-rate 2 --run-time 60s
"""

import json
import os
import random
from locust import HttpUser, task, between

# Sample test data (realistic feature values)
SAMPLE_INSTANCES = [
    {
        "turnover": 0.15,
        "headcount": 150,
        "nota_exame": 7.5,
        "idade_empresa": 5,
        "idade": 16,
        "horas_treinamento": 40,
        "participou_projeto": 1,
        "numero_avaliacoes": 4,
        "promocoes_ultimos_3_anos": 1,
        "nivel_senioridade": 2,
        "nivel_escolaridade": 3,
        "area_atuacao": 1,
        "percentual_meta_batida": 85.0,
    },
    {
        "turnover": 0.25,
        "headcount": 80,
        "nota_exame": 5.0,
        "idade_empresa": 3,
        "idade": 14,
        "horas_treinamento": 20,
        "participou_projeto": 0,
        "numero_avaliacoes": 2,
        "promocoes_ultimos_3_anos": 0,
        "nivel_senioridade": 1,
        "nivel_escolaridade": 2,
        "area_atuacao": 2,
        "percentual_meta_batida": 60.0,
    },
    {
        "turnover": 0.10,
        "headcount": 300,
        "nota_exame": 8.5,
        "idade_empresa": 10,
        "idade": 17,
        "horas_treinamento": 60,
        "participou_projeto": 1,
        "numero_avaliacoes": 6,
        "promocoes_ultimos_3_anos": 2,
        "nivel_senioridade": 3,
        "nivel_escolaridade": 4,
        "area_atuacao": 1,
        "percentual_meta_batida": 95.0,
    },
]

# API Key for authentication (set via environment variable)
API_KEY = os.getenv("LOAD_TEST_API_KEY", "")


class DefasagemAPIUser(HttpUser):
    """
    Simulated user for load testing the Defasagem Risk API.
    """
    
    # Wait time between requests (1-3 seconds)
    wait_time = between(1, 3)
    
    def on_start(self):
        """Set up headers for authenticated requests."""
        self.headers = {"Content-Type": "application/json"}
        if API_KEY:
            self.headers["X-API-Key"] = API_KEY
    
    @task(1)
    def health_check(self):
        """Test health endpoint (lightweight, no auth)."""
        self.client.get("/health", name="/health")
    
    @task(1)
    def readiness_check(self):
        """Test readiness endpoint."""
        self.client.get("/ready", name="/ready")
    
    @task(1)
    def get_metadata(self):
        """Test metadata endpoint."""
        self.client.get("/metadata", headers=self.headers, name="/metadata")
    
    @task(1)
    def get_metrics(self):
        """Test metrics endpoint."""
        self.client.get("/metrics", headers=self.headers, name="/metrics")
    
    @task(10)
    def predict_single(self):
        """Test single instance prediction (most common use case)."""
        instance = random.choice(SAMPLE_INSTANCES)
        payload = {"instances": [instance]}
        
        with self.client.post(
            "/predict",
            json=payload,
            headers=self.headers,
            name="/predict [single]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "predictions" in data and len(data["predictions"]) == 1:
                    response.success()
                else:
                    response.failure("Invalid response structure")
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(3)
    def predict_batch_small(self):
        """Test small batch prediction (5 instances)."""
        instances = random.choices(SAMPLE_INSTANCES, k=5)
        payload = {"instances": instances}
        
        with self.client.post(
            "/predict",
            json=payload,
            headers=self.headers,
            name="/predict [batch-5]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if len(data.get("predictions", [])) == 5:
                    response.success()
                else:
                    response.failure("Wrong prediction count")
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(1)
    def predict_batch_medium(self):
        """Test medium batch prediction (20 instances)."""
        instances = random.choices(SAMPLE_INSTANCES, k=20)
        payload = {"instances": instances}
        
        with self.client.post(
            "/predict",
            json=payload,
            headers=self.headers,
            name="/predict [batch-20]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")


class HighLoadUser(HttpUser):
    """
    User for stress testing - rapid fire predictions.
    Use with caution - may trigger rate limits.
    """
    
    wait_time = between(0.1, 0.5)
    weight = 1  # Lower weight than main user
    
    def on_start(self):
        self.headers = {"Content-Type": "application/json"}
        if API_KEY:
            self.headers["X-API-Key"] = API_KEY
    
    @task
    def rapid_predict(self):
        """Rapid single predictions for stress testing."""
        instance = random.choice(SAMPLE_INSTANCES)
        payload = {"instances": [instance]}
        
        self.client.post(
            "/predict",
            json=payload,
            headers=self.headers,
            name="/predict [stress]",
        )
