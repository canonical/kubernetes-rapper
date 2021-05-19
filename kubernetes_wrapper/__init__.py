import logging
import yaml
import kubernetes

from .retry_wrapper import RetryWrapper
from inflection import underscore


class Kubernetes:
    def __init__(self, namespace):
        kubernetes.config.load_incluster_config()
        self.api_client = kubernetes.client.ApiClient
        self.namespace = namespace

    def apply(self, rawData, **kwargs):
        for obj in yaml.safe_load_all(rawData):
            self.apply_object(obj, **kwargs)

    def delete(self, rawData, **kwargs):
        for obj in yaml.safe_load_all(rawData):
            self.delete_object(obj, self.api_client, **kwargs)

    def apply_object(self, obj, client=None, **kwargs):
        k8s_api = self.find_k8s_api(obj, client)

        try:
            res = self.call_api(k8s_api, "create", obj, **kwargs)
            logging.info(f"K8s: {self.describe(obj)} CREATED")

        except kubernetes.client.rest.ApiException as apiEx:
            if apiEx.reason != "Conflict":
                raise
            try:
                # asking for forgiveness...
                res = self.call_api(k8s_api, "patch", obj, **kwargs)
                logging.info(
                    f"K8s: {self.describe(obj)} PATCHED -> uid={res.metadata.uid}"
                )
            except kubernetes.client.rest.ApiException as apiEx:
                if apiEx.reason != "Unprocessable Entity":
                    raise
                try:
                    # second attempt... delete the existing object and re-insert
                    logging.info(
                        f"K8s: replacing {self.describe(obj)} FAILED. Attempting \
                          deletion and recreation..."
                    )
                    res = self.call_api(k8s_api, "delete", obj, **kwargs)
                    logging.info(f"K8s: {self.describe(obj)}  DELETED...")
                    res = self.call_api(k8s_api, "create", obj, **kwargs)
                    logging.info(f"K8s: {self.describe(obj)} CREATED")
                except Exception as ex:
                    message = (
                        f"K8s: FAILURE updating {self.describe(obj)} Exception: {ex}"
                    )
                    logging.error(message)
                    raise RuntimeError(message)
        return res

    def delete_object(self, obj, client=None, **kwargs):
        k8s_api = self.find_k8s_api(obj, client)
        try:
            self.call_api(k8s_api, "delete", obj, **kwargs)
            logging.info(f"K8s: {self.describe(obj)}  DELETED")
            return True
        except kubernetes.client.rest.ApiException as apiEx:
            if apiEx.reason == "Not Found":
                logging.warning(f"K8s: {self.describe(obj)} does not exist (anymore).")
                return False
            else:
                message = (
                    f"K8s: deleting {self.describe(obj)} FAILED. Exception: {apiEx}"
                )
                logging.error(message)
                raise RuntimeError(message)

    def read_object(self, obj, client=None, **kwargs):
        k8s_api = self.find_k8s_api(obj, client)
        return self.call_api(k8s_api, "read", obj, **kwargs)

    def find_k8s_api(self, obj, client=None):
        grp, ver2, ver = obj["apiVersion"].partition("/")
        if ver == "":
            ver = grp
            grp = "core"

        grp = "".join(
            part.capitalize() for part in grp.rsplit(".k8s.io", 1)[0].split(".")
        )
        ver = ver.capitalize()

        k8s_api = f"{grp}{ver}Api"
        print(k8s_api)
        return RetryWrapper(getattr(kubernetes.client, k8s_api)(client), Exception)

    def call_api(self, k8s_api, action, obj, **args):
        kind = underscore(obj["kind"])
        call_name = f"{action}_{kind}"

        if hasattr(k8s_api, call_name):
            call = getattr(k8s_api, call_name)
        else:
            call_name = f"{action}_namespaced_{kind}"
            call = getattr(k8s_api, call_name)
            args["namespace"] = self.namespace
        if "create" not in call_name:
            args["name"] = obj["metadata"]["name"]
        if "delete" in call_name:
            from kubernetes.client.models.v1_delete_options import V1DeleteOptions

            obj = V1DeleteOptions()

        if action == "read":
            return call(**args)
        else:
            return call(body=obj, **args)

    def describe(self, obj):
        return f"{obj['kind']} '{obj['metadata']['name']}'"
