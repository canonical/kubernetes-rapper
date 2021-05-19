import yaml
from unittest.mock import patch
from unittest import TestCase
import kubernetes
from kubernetes_wrapper import Kubernetes

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
        # TODO figure out how to test this method with RetryWrapper
        self.kubernetes.find_k8s_api(LOADED_TEST_RESOURCE)
        assert True

    @patch("kubernetes.client.api.AppsV1Api.create_namespaced_deployment")
    def test_apply_object(self, mock_create):
        self.kubernetes.apply_object(LOADED_TEST_RESOURCE)
        mock_create.assert_called_once()

    @patch("kubernetes.client.api.AppsV1Api.patch_namespaced_deployment")
    @patch("kubernetes.client.api.AppsV1Api.create_namespaced_deployment")
    def test_apply_object_patch(self, mock_create, mock_patch):
        mock_create.side_effect = kubernetes.client.rest.ApiException(reason="Conflict")
        self.kubernetes.apply_object(LOADED_TEST_RESOURCE)
        mock_create.assert_called_once()
        mock_patch.assert_called_once()

    @patch("kubernetes.client.api.AppsV1Api.delete_namespaced_deployment")
    @patch("kubernetes.client.api.AppsV1Api.patch_namespaced_deployment")
    @patch("kubernetes.client.api.AppsV1Api.create_namespaced_deployment")
    def test_apply_object_delete_create(self, mock_create, mock_patch, mock_delete):
        class ApiException:
            times_called = 0

            def api_exception(**kwargs):
                ApiException.times_called += 1
                if ApiException.times_called == 2:
                    return
                else:
                    raise kubernetes.client.rest.ApiException(reason="Conflict")

        api_exception_class = ApiException
        mock_create.side_effect = api_exception_class.api_exception
        mock_patch.side_effect = kubernetes.client.rest.ApiException(
            reason="Unprocessable Entity"
        )
        self.kubernetes.apply_object(LOADED_TEST_RESOURCE)
        mock_create.assert_called()
        mock_patch.assert_called_once()
        mock_delete.assert_called_once()

    @patch("kubernetes.client.api.AppsV1Api.create_namespaced_deployment")
    def test_apply_object_exception(self, mock_create):
        mock_create.side_effect = kubernetes.client.rest.ApiException(reason="")
        with self.assertRaises(kubernetes.client.rest.ApiException):
            self.kubernetes.apply_object(LOADED_TEST_RESOURCE)
        mock_create.assert_called_once()

    @patch("kubernetes.client.api.AppsV1Api.delete_namespaced_deployment")
    def test_delete_object(self, mock_delete):
        self.kubernetes.delete_object(LOADED_TEST_RESOURCE)
        mock_delete.assert_called_once()

    @patch("kubernetes.client.api.AppsV1Api.delete_namespaced_deployment")
    def test_delete_object_not_found(self, mock_delete):
        mock_delete.side_effect = kubernetes.client.rest.ApiException(
            reason="Not Found"
        )
        self.kubernetes.delete_object(LOADED_TEST_RESOURCE)
        mock_delete.assert_called_once()

    @patch("kubernetes.client.api.AppsV1Api.delete_namespaced_deployment")
    def test_delete_object_exception(self, mock_delete):
        mock_delete.side_effect = kubernetes.client.rest.ApiException(reason="")
        with self.assertRaises(RuntimeError):
            self.kubernetes.delete_object(LOADED_TEST_RESOURCE)
        mock_delete.assert_called_once()

    @patch("kubernetes.client.api.AppsV1Api.read_namespaced_deployment")
    def test_read_object(self, mock_read):
        self.kubernetes.read_object(LOADED_TEST_RESOURCE)
        mock_read.assert_called_once()
