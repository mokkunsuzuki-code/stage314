from flask import Flask, request, jsonify
from sigstore_verify import verify_sigstore
from datetime import datetime
import hashlib
import json
import uuid

app = Flask(__name__)
STORE = {}

def calculate_trust(url, manifest):
    claims = manifest.get("claims", {})

    sigstore_result = verify_sigstore(
        "artifact.txt",
        "artifact.bundle",
        "cosign.pub"
    )

    breakdown = {
        "integrity": 1.0 if claims.get("integrity") else 0.0,
        "execution": 1.0 if claims.get("execution") and claims.get("workflow") == "github-actions" else 0.0,
        "identity": 1.0 if claims.get("identity") else 0.0,
        "time": 1.0 if claims.get("timestamp") else 0.0,
        "sigstore": 1.0 if sigstore_result["ok"] else 0.0
    }

    trust_score = round(sum(breakdown.values()) / len(breakdown), 2)

    if trust_score >= 0.85:
        decision = "accept"
        reason = "All major trust conditions are satisfied, including real Sigstore verification."
    elif trust_score >= 0.45:
        decision = "pending"
        reason = "Some trust conditions are incomplete."
    else:
        decision = "reject"
        reason = "Trust score is too low. Fail-closed."

    result_id = str(uuid.uuid4())[:8]

    manifest_sha256 = hashlib.sha256(
        json.dumps(manifest, sort_keys=True).encode("utf-8")
    ).hexdigest()

    result = {
        "id": result_id,
        "stage": 311,
        "url": url,
        "decision": decision,
        "trust_score": trust_score,
        "breakdown": breakdown,
        "reason": reason,
        "sigstore_verification": {
            "verified": sigstore_result["ok"],
            "stdout": sigstore_result["stdout"],
            "stderr": sigstore_result["stderr"],
            "artifact": "artifact.txt",
            "bundle": "artifact.bundle",
            "public_key": "cosign.pub"
        },
        "evidence": {
            "created_at": datetime.utcnow().isoformat() + "Z",
            "manifest_sha256": manifest_sha256
        },
        "share": {
            "trust_url": f"http://127.0.0.1:3110/trust/{result_id}",
            "api_url": f"http://127.0.0.1:3110/api/trust/{result_id}"
        }
    }

    STORE[result_id] = result
    return result

@app.route("/")
def index():
    return """
<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>Stage311 REMEDA Sigstore Verification</title>
<style>
body{font-family:system-ui;background:#0f172a;color:#e5e7eb;padding:30px}
textarea,input{width:100%;padding:10px;background:#020617;color:#fff;border:1px solid #475569;border-radius:8px}
button{padding:12px 18px;background:#38bdf8;border:0;border-radius:8px;font-weight:bold}
.card{background:#111827;border:1px solid #334155;border-radius:14px;padding:20px;margin:20px 0}
</style>
</head>
<body>
<h1>Stage311 REMEDA Sigstore Real Verification</h1>
<p>sigstore:true の自己申告ではなく、cosign verify-blob による実検証をTrust Scoreに反映します。</p>

<div class="card">
<form method="post" action="/verify">
<p>URL</p>
<input name="url" value="https://example.com">

<p>Manifest JSON</p>
<textarea name="manifest" rows="10">{
  "claims": {
    "execution": true,
    "identity": true,
    "integrity": true,
    "timestamp": true,
    "workflow": "github-actions",
    "policy_version": "v1"
  }
}</textarea>
<br><br>
<button type="submit">Sigstore実検証つきTrust Scoreを作成する</button>
</form>
</div>
</body>
</html>
"""

@app.route("/verify", methods=["POST"])
def verify():
    url = request.form.get("url", "")
    manifest = json.loads(request.form.get("manifest", "{}"))
    result = calculate_trust(url, manifest)

    return f"""
<!doctype html>
<html lang="ja">
<head><meta charset="utf-8"><title>Stage311 Result</title></head>
<body style="font-family:system-ui;background:#0f172a;color:#e5e7eb;padding:30px">
<h1>Stage311 Result</h1>
<h2>Decision: {result["decision"].upper()}</h2>
<h2>Trust Score: {result["trust_score"]}</h2>
<h2>Sigstore Verified: {result["sigstore_verification"]["verified"]}</h2>

<p>Public Trust URL:</p>
<p><a style="color:#38bdf8" href="/trust/{result["id"]}">http://127.0.0.1:3110/trust/{result["id"]}</a></p>

<p>JSON API:</p>
<p><a style="color:#38bdf8" href="/api/trust/{result["id"]}">http://127.0.0.1:3110/api/trust/{result["id"]}</a></p>

<pre>{json.dumps(result, ensure_ascii=False, indent=2)}</pre>
<p><a style="color:#38bdf8" href="/">戻る</a></p>
</body>
</html>
"""

@app.route("/trust/<rid>")
def trust(rid):
    result = STORE.get(rid)
    if not result:
        return "not found", 404

    return f"""
<!doctype html>
<html lang="ja">
<head><meta charset="utf-8"><title>Trust {rid}</title></head>
<body style="font-family:system-ui;background:#0f172a;color:#e5e7eb;padding:30px">
<h1>Public Trust URL</h1>
<h2>Decision: {result["decision"].upper()}</h2>
<h2>Trust Score: {result["trust_score"]}</h2>
<h2>Sigstore Verified: {result["sigstore_verification"]["verified"]}</h2>
<pre>{json.dumps(result, ensure_ascii=False, indent=2)}</pre>
</body>
</html>
"""

@app.route("/api/verify", methods=["POST"])
def api_verify():
    data = request.get_json(force=True)
    result = calculate_trust(data.get("url", ""), data.get("manifest", {}))
    return jsonify(result)

@app.route("/api/trust/<rid>")
def api_trust(rid):
    result = STORE.get(rid)
    if not result:
        return jsonify({"error": "not_found"}), 404
    return jsonify(result)

@app.route("/api/health")
def health():
    return jsonify({
        "ok": True,
        "stage": 311,
        "service": "remeda-sigstore-real-verification"
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3110, debug=True)
