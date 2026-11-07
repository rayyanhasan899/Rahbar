# RAHBAR: Setup and Cold Start

Windows laptop. Commands in `powershell` blocks go in PowerShell. Commands in `bash` blocks go in Ubuntu.

First list the installed distributions in PowerShell:
```powershell
wsl --list --verbose
```
Open the installed Ubuntu distribution by its exact name. This setup example uses
`Ubuntu-24.04`; Rayyan's existing environment is named `Ubuntu`, so use
`wsl -d Ubuntu` there. Do not replace a working distribution or project environment.
```powershell
wsl -d Ubuntu-24.04
```
A plain `wsl` may open Docker's internal Linux (prompt `-sh` and `#`, path `/mnt/host/c/...`). Nothing works there.

## Already-prepared Rayyan laptop

Use the existing environment rather than repeating initial installation. Start
Docker Desktop and Ollama, open `wsl -d Ubuntu`, then:

```bash
cd '/mnt/d/RAYYAN/ASSIGNMENTS/Software Construction and Development/Assignment2/rahbar-starter'
source .venv/rahbar-env.sh
minikube start
kubectl -n rahbar get pods
kubectl -n ingress-nginx port-forward service/ingress-nginx-controller 18080:80
```

Keep the forward open and visit http://localhost:18080. The prepared cluster has
a development-only localhost Ingress alias; fresh clusters below use rahbar.local.
If port18080 is already forwarded, use the existing forward. The known model
memory limitation can still produce safe fallbacks even with healthy API pods.
The following installation and `~/Rahbar` commands are for a fresh environment.

---

## Part 1: Initial setup (once)

### 1. Windows

```powershell
wsl --install -d Ubuntu-24.04
```
Install only if no suitable Ubuntu environment already exists. Restart Windows
if asked. Create the Linux username and password when prompted. Changing the
default distribution is optional; the explicit `wsl -d` command does not need it.

**Docker Desktop**
1. Install it with the WSL 2 backend.
2. Settings → Resources → **WSL Integration** → switch on **Ubuntu-24.04** → **Apply & restart**.
3. Close and reopen the Ubuntu terminal.

**Ollama**
```powershell
winget install Ollama.Ollama
setx OLLAMA_HOST 0.0.0.0
```
Quit Ollama from the tray icon (right-click → Quit), start it again from the Start menu, then:
```powershell
ollama pull nomic-embed-text
ollama pull llama3.2:3b
curl.exe http://localhost:11434/api/tags
netstat -ano | findstr 11434
```
`netstat` must show `0.0.0.0:11434 ... LISTENING`. Allow **Private networks only** if Windows Firewall asks.

**VS Code:** install it and the **WSL** and **Python** extensions.

### 2. Ubuntu tools

```bash
sudo apt update
sudo apt install -y make git curl python3.12-venv

cd /tmp
curl -fLO https://dl.k8s.io/release/v1.34.0/bin/linux/amd64/kubectl
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
curl -fLO https://storage.googleapis.com/minikube/releases/v1.37.0/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
rm kubectl minikube-linux-amd64

python3.12 --version && make --version && git --version
kubectl version --client && minikube version && docker version
```
`docker version` must print both **Client** and **Server**.

### 3. Code and Python environment

For a fresh WSL installation, prefer the Linux filesystem under `~` for better
performance and permissions. A venv failed under `/mnt/c` during one setup;
that is not a universal prohibition on Windows-mounted paths. Rayyan's existing
project on `D:` and its inspected `.venv/rahbar-env.sh` work and should be preserved.
```bash
cd ~
git clone https://github.com/rayyanhasan899/Rahbar.git
cd Rahbar
git checkout main
make install PY=python3.12
source .venv/bin/activate
make test
python scripts/check_submission.py
```
Expect `162 passed, 0 failures`.

### 4. Corpus
```bash
make fetch
python corpus/fetch.py --verify
```

### 5. Cluster

Docker Desktop and Ollama must be running first.
```bash
minikube start --driver=docker --cni=calico --memory=4096 --cpus=2 --kubernetes-version=v1.34.0
minikube addons enable metrics-server
minikube addons enable ingress
```
Wait for it to finish. The "Verifying ingress addon" step takes several minutes. Then:
```bash
kubectl -n ingress-nginx rollout status deployment/ingress-nginx-controller --timeout=240s
```

### 6. Build and load images
```bash
TAG=$(git rev-parse HEAD)
make images TAG="$TAG"
```

### 7. Deploy

Use the IPv4 from this command. Do **not** use `host.minikube.internal`; it points to the wrong machine.
```bash
minikube ssh "getent ahostsv4 host.docker.internal"
minikube ssh "curl -s -o /dev/null -w '%{http_code}\n' http://host.docker.internal:11434/api/tags"
```
Expect an IP (so far `192.168.65.254`) and `200`. Then:
```bash
MODEL_IP=192.168.65.254   # the IP printed above
python scripts/deploy_local.py --tag "$TAG" \
  --provider-cidr "$MODEL_IP/32" --ollama "http://$MODEL_IP:11434"
```
It stops silently at `job.batch/indexer-... created` for about 7 to 30 minutes while indexing. Leave it alone. Progress, from a second terminal:
```bash
kubectl -n rahbar get pods,jobs
```

### 8. Verify
```bash
kubectl -n rahbar get pods,jobs,hpa
kubectl -n rahbar get endpoints api
```
Expect 3 `api` pods at `1/1`, the indexer Job `Complete`, an HPA number (not `<unknown>`), and 3 endpoint IPs.

Second terminal (leave it open):
```bash
kubectl -n ingress-nginx port-forward service/ingress-nginx-controller 18080:80
```
First terminal:
```bash
curl -H 'Host: rahbar.local' http://127.0.0.1:18080/api/version
curl -H 'Host: rahbar.local' -H 'Content-Type: application/json' \
  -d '{"question":"What is the maximum duration of a BS degree?"}' \
  http://127.0.0.1:18080/api/ask
curl -H 'Host: rahbar.local' -H 'Content-Type: application/json' \
  -d '{"question":"What are the hostel rules?"}' \
  http://127.0.0.1:18080/api/ask
```
- Question 1: `provider: ollama`, `answered_from_context: true`, a citation.
- Question 2: `answered_from_context: false`, no citations.

### 9. Browser (one-time Windows change)

1. Start Menu → Notepad → right-click → **Run as administrator**.
2. Open `C:\Windows\System32\drivers\etc\hosts` (file filter: All files).
3. Add the line `127.0.0.1 rahbar.local` and save.
4. Open **http://rahbar.local:18080** (the port-forward must be running).

### 10. VS Code
```bash
cd ~/Rahbar
code -n .
```
The bottom-left corner must say **WSL: Ubuntu-24.04**.

---

## Part 2: Cold start (after a reboot)

1. **Windows:** start Docker Desktop and wait for *Engine running*.
2. **Windows:** make sure Ollama is running.
   ```powershell
   curl.exe http://localhost:11434/api/tags
   ```
3. **PowerShell:** open the installed Ubuntu distro by name (for example,
   `wsl -d Ubuntu-24.04`; Rayyan's existing one is `wsl -d Ubuntu`).
4. **Ubuntu:**
   ```bash
   cd ~/Rahbar
   source .venv/bin/activate
   minikube start
   kubectl -n rahbar get pods -w
   ```
   Press Ctrl+C when all pods are `Running` and `1/1`. API pods stay `0/1` for a while first.
5. **Second Ubuntu terminal:**
   ```bash
   kubectl -n ingress-nginx port-forward service/ingress-nginx-controller 18080:80
   ```
6. **Test:**
   ```bash
   curl -H 'Host: rahbar.local' http://127.0.0.1:18080/api/version
   ```
7. **Browser:** http://rahbar.local:18080

Do not redeploy or reindex. Do not run `make cluster` again.

**Shut down:** Ctrl+C the port-forward, then `minikube stop`. Quit Ollama from the tray to free memory.

---

## Fixes for problems already hit

| Problem | Fix |
|---|---|
| `python3.12`, `make` or `git` "not found", `-sh` prompt | `exit`, then `wsl -d Ubuntu-24.04` |
| `OLLAMA_HOST=0.0.0.0 ollama serve` fails in PowerShell | Use `setx OLLAMA_HOST 0.0.0.0`, then restart Ollama |
| `ensurepip ... exit status 1` | The repo is on `/mnt/c`. Use `~/Rahbar` |
| `docker: command not found` / `minikube ... PROVIDER_DOCKER_VERSION_EXIT_1` | Docker Desktop WSL Integration off. Enable it, reopen Ubuntu |
| `localhost:8080 connection refused` from kubectl | Inspect `kubectl config current-context` and `minikube status`; a missing/wrong kubeconfig can cause this even when a cluster exists |
| Ingress step takes minutes | Normal. Check `kubectl get pods -A`; the controller goes `ContainerCreating` then `Running` |
| `curl` from minikube to Ollama fails (exit 7) with `host.minikube.internal` | Use the IPv4 from `host.docker.internal` (step 7) |
| Deploy script silent after `indexer-... created` | Normal. Indexing takes 7 to 30 minutes |
| `bind: address already in use` on 18080 | A port-forward is already running in another terminal. Leave it |
| Browser shows 404 or can't connect | Missing `rahbar.local` hosts line, or port-forward not running |
| Pod not ready | `kubectl -n rahbar describe pod <name>`, then `kubectl -n rahbar logs <name>` |
| `<unknown>` in HPA | Wait about a minute for metrics-server |
| Fallback answers instead of real ones | Known memory limit of this laptop. Quit other programs |
| Indexer exit 137 | SIGKILL, not proof of OOM. Inspect the terminated container's reason/exit code with `kubectl -n rahbar describe pod <name>` and events; confirm `OOMKilled` before diagnosing a memory limit. `kubectl top` only samples running usage |

---

## Demo reference (likely questions)

**The demo from the assignment ("done" definition)**
```bash
# cited answer
curl -H 'Host: rahbar.local' -H 'Content-Type: application/json' \
  -d '{"question":"What is the maximum duration of a BS degree?"}' http://127.0.0.1:18080/api/ask
# declines an uncovered topic
curl -H 'Host: rahbar.local' -H 'Content-Type: application/json' \
  -d '{"question":"What are the hostel rules?"}' http://127.0.0.1:18080/api/ask
# delete a pod, service keeps answering
kubectl -n rahbar get pods
kubectl -n rahbar delete pod <one-api-pod>
curl -H 'Host: rahbar.local' http://127.0.0.1:18080/api/version
kubectl -n rahbar get pods
```

**Other commands the assignment asks you to show**
```bash
kubectl -n rahbar create job --from=cronjob/reindex manual-reindex-1   # reindex, no redeploy
kubectl -n rahbar top pods                                              # resource numbers
kubectl -n rahbar get hpa                                               # autoscaler
kubectl -n rahbar get endpoints api                                     # 3 IPs
kubectl -n rahbar rollout status deployment/api
kubectl -n rahbar rollout undo deployment/api
git show --stat <sha>                                                   # "what is running": revision from /api/version
```
Evaluation (overwrites the committed `eval/results.json`; run only on purpose):
```bash
python eval/run_eval.py --api http://127.0.0.1:18080 --host rahbar.local
```

**Why questions**
- **Why is indexing a Job and not done at API startup?** Three API replicas would write one Chroma volume at the same time, every restart would reindex, readiness would be wrong, and reindexing would need a redeploy.
- **Why a StatefulSet for Chroma?** It needs a stable volume. The StatefulSet's `volumeClaimTemplates` gives it one.
- **Why Calico?** The default minikube network plugin accepts NetworkPolicy manifests and silently ignores them.
- **Readiness vs liveness?** `/healthz` (liveness) touches no dependency, so a slow dependency cannot cause a restart storm. `/readyz` checks Chroma, a non-empty collection, and Redis. Failure removes the pod from the Service without restarting it.
- **What does the embedding pin do?** `EMBED_MODEL` is read by the indexer and the API. The indexer writes the model name and dimension into the collection. If the API's value differs, it refuses to become ready and logs the conflict.
- **Why images tagged with the commit SHA?** `/api/version` returns the commit, so "what is running" has a one-word answer. `:latest` is never deployed.
- **Why deny-by-default NetworkPolicy?** Only the needed paths are allowed. The UI pod cannot reach Chroma. The only outside address the API may reach is the single model host (`/32`).
- **Why does the answer decline when the best chunk scored 0.669, above the 0.65 floor?** Retrieval alone did not refuse. A later step declined, and the log line for that `request_id` shows which. Check `kubectl -n rahbar logs deploy/api` before the demo so you can say which.
