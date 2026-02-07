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

# Sample test data — features reais do modelo de defasagem escolar Passos Mágicos
# 13 features conforme model_signature.json:
#   instituicao_2023, idade_2023, fase_2023, ian_2023, ida_2023, ieg_2023,
#   iaa_2023, ips_2023, ipp_2023, ipv_2023, media_indicadores, min_indicador, std_indicadores
SAMPLE_INSTANCES = [
    {
        # Perfil: aluno Fase 4, bom desempenho, baixo risco
        "instituicao_2023": "Inst_A",
        "idade_2023": 14.0,
        "fase_2023": "4",
        "ian_2023": 7.8,
        "ida_2023": 8.2,
        "ieg_2023": 7.5,
        "iaa_2023": 8.0,
        "ips_2023": 7.0,
        "ipp_2023": 6.5,
        "ipv_2023": 7.2,
        "media_indicadores": 7.46,
        "min_indicador": 6.5,
        "std_indicadores": 0.55,
    },
    {
        # Perfil: aluno Fase 2, desempenho fraco, alto risco
        "instituicao_2023": "Inst_B",
        "idade_2023": 11.0,
        "fase_2023": "2",
        "ian_2023": 4.2,
        "ida_2023": 3.8,
        "ieg_2023": 5.0,
        "iaa_2023": 4.5,
        "ips_2023": 3.5,
        "ipp_2023": 4.0,
        "ipv_2023": 3.2,
        "media_indicadores": 4.03,
        "min_indicador": 3.2,
        "std_indicadores": 0.60,
    },
    {
        # Perfil: aluno Fase 7, desempenho mediano, risco moderado
        "instituicao_2023": "Inst_A",
        "idade_2023": 16.0,
        "fase_2023": "7",
        "ian_2023": 6.0,
        "ida_2023": 5.5,
        "ieg_2023": 6.2,
        "iaa_2023": 5.8,
        "ips_2023": 6.5,
        "ipp_2023": 5.0,
        "ipv_2023": 6.8,
        "media_indicadores": 5.97,
        "min_indicador": 5.0,
        "std_indicadores": 0.62,
    },
    {
        # Perfil: aluno Fase 1, muito jovem, dados parciais (nulls)
        "instituicao_2023": "Inst_C",
        "idade_2023": 9.0,
        "fase_2023": "1",
        "ian_2023": 5.5,
        "ida_2023": None,
        "ieg_2023": 6.0,
        "iaa_2023": None,
        "ips_2023": 5.0,
        "ipp_2023": None,
        "ipv_2023": None,
        "media_indicadores": 5.5,
        "min_indicador": 5.0,
        "std_indicadores": 0.41,
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
