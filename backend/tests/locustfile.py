from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        # In a real test, replace with a valid token
        self.token = 'testtoken'

    @task(1)
    def get_recommendations(self):
        self.client.post('/api/recommendations/get', headers={'Authorization': f'Bearer {self.token}'})

    @task(2)
    def get_health_info(self):
        self.client.get('/api/patient/health-information', headers={'Authorization': f'Bearer {self.token}'})
