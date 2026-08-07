from typing import Dict


def extract_basic_client_info(
        data: Dict[str, str]
) -> Dict[str, str | int]:
    info_block = data.get("obj", {})
    client_data = info_block.get("client", {})

    sub_id = client_data.get("subId")

    used_traffic = info_block.get("usedTraffic")
    total_traffic = client_data.get("totalGB")

    traffic_left = (total_traffic - used_traffic) if total_traffic > 0 else -1

    total_gb = client_data.get("totalGB") if client_data.get("totalGB") > 0 else -1

    created_at = client_data.get("createdAt")

    expiry_time = client_data.get("expiryTime")

    client_info = {
        "email": client_data.get("email"),
        "totalGB": total_gb,
        "trafficLeft": traffic_left,
        "subId": sub_id,
        "createdAt": created_at,
        "expiryTime": expiry_time
    }

    return client_info

