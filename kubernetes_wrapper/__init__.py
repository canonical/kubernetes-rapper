from .retry_wrapper import RetryWrapper
from .k8s_client_wrapper import KubernetesClientWrapper


class Kubernetes(RetryWrapper):
    def __init__(self, namespace):
        super().__init__(KubernetesClientWrapper(namespace), Exception)
        # TODO we could be a bit more specific with the exceptions where we
        # retry
