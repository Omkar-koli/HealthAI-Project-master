# Kubernetes manifests (Milestone 5)

Cluster: GKE Autopilot `healthai-cluster` (us-central1). Public entry: `https://app.healthai-g6-uh.com`.

```
Internet -> global HTTPS load balancer (static IP healthai-lb-ip, managed certificate, http->https redirect)
         -> Ingress -> Service "frontend" -> frontend pods (Streamlit, 2+)
                                                   |  http://backend:8000 (cluster-internal)
                                                   v
                       Service "backend" -> backend pods (FastAPI + model, 2-4, autoscaled)
                                                   |
                                  Cloud SQL (private IP)  +  Cloud Storage bucket  +  Secret Manager
```

| File | What it is |
|---|---|
| `00-serviceaccount.yaml` | Pod identity (Workload Identity, no key files) |
| `10-`/`11-` backend | Deployment (2 replicas, startup/liveness/readiness probes) and internal Service |
| `20-`/`21-` frontend | Deployment (2 replicas) and Service exposed through the Ingress |
| `22-backendconfig.yaml` | Load balancer timeout, cookie affinity, health check |
| `30-managed-certificate.yaml` | Google-managed TLS certificate |
| `31-frontendconfig.yaml` | http -> https redirect |
| `32-ingress.yaml` | The Ingress |
| `40-hpa.yaml` | Backend autoscaler: CPU 50%, 2 to 4 replicas |
| `50-pdb.yaml` | PodDisruptionBudgets: at least 1 pod always available |
| `loadtest/loadtest-job.yaml` | Optional traffic generator for the autoscaling demo |

## Probe design

- **Liveness `/healthz`**: the process is up. It checks no dependency, so a database outage never restarts healthy pods.
- **Readiness `/readyz`**: also runs `SELECT 1` against Cloud SQL. Failing it removes the pod from the load balancer but does not restart it.
- **Startup `/healthz`**: allows up to 4 minutes for imports and model warm-up before the other probes start.

## Deploy and verify

```
kubectl apply -f k8s/
kubectl get pods -o wide
kubectl get managedcertificate healthai-cert      # Status becomes Active (15-60 min after DNS is correct)
kubectl get ingress healthai-ingress
kubectl get hpa,pdb
```

## Tests

Self-healing: `kubectl get pods`, then `kubectl delete pod <one backend pod>`, then `kubectl get pods -w`.

Autoscaling: `kubectl apply -f k8s/loadtest/loadtest-job.yaml`, then `kubectl get hpa -w`, then `kubectl describe hpa backend`.

## Clean up after the load test

The load test creates studies named `loadtest` and image files `uploads/loadtest_*.png`.

```
kubectl exec deploy/backend -- python -c "from backend.database.database import SessionLocal; from sqlalchemy import text; db=SessionLocal(); n=db.execute(text('DELETE FROM studies WHERE patient_name = :n'), {'n': 'loadtest'}).rowcount; db.commit(); print('deleted rows:', n)"
kubectl exec deploy/backend -- python -c "from google.cloud import storage; b=storage.Client().bucket('healthai-uploads-508921'); n=[x.delete() for x in b.list_blobs(prefix='uploads/loadtest_')]; print('deleted objects:', len(n))"
```

## Tear down (stops the billing)

```
kubectl delete -f k8s/
gcloud container clusters delete healthai-cluster --region=us-central1
```
