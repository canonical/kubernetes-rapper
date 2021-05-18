Kubernetes (w)Rapper
=================

A wrapper with some flow!

## A Python Wrapper for your Kubernetes Operators!

Talk to the kubernetes api in a simpler way in your kubernetes operators written in python.

## How to use

Initialize your kubernetes wrapper class with the default namespace you want to use.

```python
from kubernetes_wrapper import Kubernetes

[..]

self.kubernetes = Kubernetes("my-namespace")
```

Apply your manifests just like you would do with `kubectl`:

```python
self.kubernetes.apply(Path("my-manifest.yaml").read_text())
```

Delete your manifests the same way:
```python
self.kubernetes.delete(Path("my-manifest.yaml").read_text())
```
