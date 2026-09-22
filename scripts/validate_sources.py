from fetch_exhibitions import MUSEUMS, fetch, discover

def main():
    failures = []
    print("Museum source validation")
    print("=" * 72)

    for mid, name, url in MUSEUMS:
        try:
            soup, final_url = fetch(url)
            items = discover(soup, final_url, mid, name)
            status = "OK" if items else "WARN"
            print(f"[{status}] {name}: {len(items)} dated exhibition records")
            print(f"       {final_url}")
            if not items:
                failures.append((mid, name, "no dated exhibition records discovered"))
        except Exception as exc:
            print(f"[FAIL] {name}: {exc}")
            failures.append((mid, name, str(exc)))

    print("=" * 72)
    print(f"Checked: {len(MUSEUMS)} museums")
    print(f"Problems: {len(failures)}")

    if failures:
        print("\nProblems requiring adapter/source review:")
        for mid, name, reason in failures:
            print(f"- {mid} | {name} | {reason}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
