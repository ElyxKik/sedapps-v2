import urllib.request
import urllib.error
import json
import time

BASE_URL = "http://localhost:8000/v1"

def make_request(url, data=None, headers=None, method='GET'):
    if headers is None:
        headers = {}
    
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
        
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            return json.loads(res_body) if res_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        print(f"HTTP Error {e.code}: {err_body}")
        raise e

def test_flow():
    # 1. Login
    print("Logging in...")
    tokens = make_request(f"{BASE_URL}/auth/login", method='POST', data={
        "email": "demo@sedapps.cloud",
        "password": "demo1234"
    })
    token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Logged in successfully.")

    # 2. Create project
    print("Creating project...")
    project = make_request(f"{BASE_URL}/projects", method='POST', headers=headers, data={
        "name": "Mon Restaurant Premium",
        "sector": "Restaurant"
    })
    project_id = project["id"]
    print(f"Project created: {project_id}")

    # 3. Save Onboarding
    print("Saving onboarding (Premium, Multipage)...")
    onboarding_data = {
        "business_name": "Le Gourmet Premium",
        "sector": "Restauration",
        "brief": "Un restaurant gastronomique haut de gamme à Paris proposant une cuisine raffinée.",
        "stack": "multipage",
        "premium": True,
        "tagline": "L'excellence dans votre assiette",
        "description": "Cuisine gastronomique avec des produits frais, locaux et de saison.",
        "contact_email": "contact@legourmet.fr",
        "primary_color": "#D4AF37", # Gold
        "secondary_color": "#1A1A1A", # Dark charcoal
        "font_style": "Playfair Display",
        "pages": ["home", "menu", "about", "contact"]
    }
    make_request(f"{BASE_URL}/projects/{project_id}/onboarding", method='POST', headers=headers, data=onboarding_data)
    print("Onboarding saved.")

    # 4. Generate site
    print("Starting site generation...")
    job = make_request(f"{BASE_URL}/projects/{project_id}/generate", method='POST', headers=headers, data={"force": True, "locale": "fr"})
    job_id = job["id"]
    print(f"Site generation started. Job ID: {job_id}")

    # 5. Monitor status
    print("Polling job status...")
    while True:
        try:
            job_status = make_request(f"{BASE_URL}/jobs/{job_id}", headers=headers)
        except Exception as e:
            print(f"Error fetching job status: {e}")
            time.sleep(5)
            continue
            
        status = job_status["status"]
        print(f"Status: {status}")
        for agent in job_status.get("agents", []):
            print(f"  - Agent {agent['name']}: {agent['status']} ({agent['duration_ms']}ms) - warnings: {agent['warnings']}")
            if agent['status'] == 'failed' or (agent['output'] and 'error' in agent['output']):
                print(f"    Error/Output: {json.dumps(agent['output'], indent=2)}")
        
        if status in ["success", "degraded", "failed", "error"]:
            print(f"Job finished with status: {status}")
            if job_status.get("error"):
                print(f"Job error: {job_status['error']}")
            break
        time.sleep(5)

if __name__ == "__main__":
    test_flow()
