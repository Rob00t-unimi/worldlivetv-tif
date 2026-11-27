# -*- coding: utf-8 -*-
import json
import wltv_bridge


def main():
    print("=== 1. Init & Hotfix Check ===")
    wltv_bridge.init()
    print("Hotfix:", wltv_bridge.check_hotfix())

    print("\n=== 2. Fetch Remote Lists ===")
    lists = json.loads(wltv_bridge.get_remote_lists())
    print(f"Found {len(lists)} lists:")
    for item in lists[:5]:
        print(f"  - {item['id']}: {item['name']} -> {item['url']}")

    print("\n=== 3. Test Broadcasters ===")
    tests = [
        ("rai", "Rai 1"),
        ("mediaset", "Canale 5"),
        ("la7", "La7"),
        ("discovery", "Nove"),
    ]
    for bdc, ch in tests:
        res = json.loads(wltv_bridge.resolve_channel(bdc, ch))
        url = res.get("url", "")
        has_lic = bool(res.get("licenseKey"))
        err = res.get("error", "")
        print(f"  [{bdc} / {ch}]")
        if err:
            print(f"    ERROR: {err}")
        else:
            print(f"    URL: {url[:90]}{'...' if len(url) > 90 else ''}")
            print(f"    Type: {res.get('manifestType')} | Widevine License: {has_lic}")
            if has_lic:
                lic_url = res["licenseKey"].split("|")[0]
                print(f"    License URL: {lic_url[:80]}...")


if __name__ == "__main__":
    main()
