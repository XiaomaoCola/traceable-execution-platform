"""
Example script demonstrating a ProofRun workflow.

This shows the complete flow:
1. Create a ticket
2. Upload artifacts (e.g., switch config)
3. Create a proof run to validate artifacts
4. View results
"""

import requests
import json
from pathlib import Path


API_BASE = "http://localhost:8000/api/v1"


def login(username: str, password: str) -> str:
    """Login and get access token."""
    response = requests.post(
        f"{API_BASE}/auth/login",
        json={"username": username, "password": password}
    )
    response.raise_for_status()
    return response.json()["access_token"]


def create_ticket(token: str, title: str, description: str, asset_id: int | None = None):
    """Create a new ticket."""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.post(
        f"{API_BASE}/tickets",
        headers=headers,
        json={
            "title": title,
            "description": description,
            "asset_id": asset_id
        }
    )
    response.raise_for_status()
    return response.json()


def create_run(token: str, ticket_id: int):
    """Create a proof run."""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.post(
        f"{API_BASE}/runs",
        headers=headers,
        json={
            "run_type": "proof",
            "ticket_id": ticket_id,
            "script_id": "proof.file_hash"
        }
    )
    response.raise_for_status()
    return response.json()


def upload_artifact(token: str, run_id: int, file_path: str, artifact_type: str = "config"):
    """Upload an artifact."""
    headers = {"Authorization": f"Bearer {token}"}

    with open(file_path, "rb") as f:
        files = {"file": f}
        params = {
            "run_id": run_id,
            "artifact_type": artifact_type,
            "description": f"Sample {artifact_type} file"
        }

        response = requests.post(
            f"{API_BASE}/artifacts",
            headers=headers,
            params=params,
            files=files
        )
        response.raise_for_status()
        return response.json()


def get_run_details(token: str, run_id: int):
    """Get run details."""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{API_BASE}/runs/{run_id}",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def main():
    """Run the example workflow."""
    print("🔐 Logging in...")
    token = login("employee", "employee123")
    print("✅ Logged in successfully")

    print("\n📝 Creating ticket...")
    ticket = create_ticket(
        token,
        title="Install and configure factory switch",
        description="Install new switch in Factory A and upload configuration",
        asset_id=3  # Factory Gateway
    )
    print(f"✅ Created ticket #{ticket['id']}: {ticket['title']}")

    print("\n🚀 Creating proof run...")
    run = create_run(token, ticket["id"])
    print(f"✅ Created run #{run['id']} (status: {run['status']})")

    print("\n📤 Uploading sample artifact...")
    # Create a sample config file
    sample_config = Path("sample_switch_config.txt")
    sample_config.write_text("""
# Sample Switch Configuration
hostname FactorySwitch-A
!
interface GigabitEthernet0/1
 description Uplink to Core
 switchport mode trunk
!
interface GigabitEthernet0/2
 description Factory Floor
 switchport access vlan 10
!
vlan 10
 name FACTORY_FLOOR
!
""")

    artifact = upload_artifact(
        token,
        run["id"],
        str(sample_config),
        "config"
    )
    print(f"✅ Uploaded artifact: {artifact['artifact']['filename']}")
    print(f"   SHA-256: {artifact['artifact']['sha256_hash']}")

    # Wait a moment for run to complete
    import time
    print("\n⏳ Waiting for run to complete...")
    time.sleep(2)

    print("\n📊 Fetching run details...")
    run_details = get_run_details(token, run["id"])
    print(f"✅ Run status: {run_details['status']}")
    print(f"   Result: {run_details['result_summary']}")

    if run_details.get('stdout_log'):
        print(f"\n📝 Validation output:")
        print(run_details['stdout_log'])

    # Cleanup
    sample_config.unlink()

    print("\n✅ Example workflow complete!")


if __name__ == "__main__":
    main()
