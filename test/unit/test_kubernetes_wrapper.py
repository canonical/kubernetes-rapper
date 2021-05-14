import yaml
from unittest.mock import patch
from unittest import TestCase
import kubernetes
from kubernetes_wrapper import Kubernetes
from kubernetes_wrapper.retry_wrapper import RetryWrapper

TEST_RESOURCE = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.7.9
        ports:
        - containerPort: 80
"""

LOADED_TEST_RESOURCE = yaml.safe_load(TEST_RESOURCE)


class KubernetesTestCase(TestCase):
    @patch("kubernetes.config.load_incluster_config")
    def setUp(self, config_mock):
        self.kubernetes = Kubernetes("test-namespace")

    def test_describe(self):
        result = self.kubernetes.describe(LOADED_TEST_RESOURCE)
        assert result == "Deployment 'nginx-deployment'"

    def test_find_k8s_api(self):
        result = self.kubernetes.find_k8s_api(LOADED_TEST_RESOURCE, None)
        assert True
