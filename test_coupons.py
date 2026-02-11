import requests
import json

def test_coupons():
    url = "http://127.0.0.1:5000/api/coupons"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            coupons = response.json()
            print(f"✅ Received {len(coupons)} coupons.")
            for c in coupons:
                print(f"\n--- {c['name']} (Total Odds: {c['total_odds']}) ---")
                used_match_ids = set()
                for m in c['matches']:
                    m_id = m['id']
                    if m_id in used_match_ids:
                        print(f"❌ ERROR: Duplicate match ID {m_id} in coupon!")
                    used_match_ids.add(m_id)
                    print(f"🔹 {m['home']} vs {m['away']} | Pick: {m['coupon_pick']} (%{m['coupon_prob']})")
        else:
            print(f"❌ API Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_coupons()
