from .crypto_trading import main
import sys
import traceback

if __name__ == "__main__":
    try:
        print("[DEBUG] __main__ starting...")
        main()
        print("[DEBUG] main() returned normally")
    except KeyboardInterrupt:
        print("[DEBUG] Interrupted")
        pass
    except Exception as e:
        print(f"[FATAL] Exception: {e}")
        traceback.print_exc()
        sys.exit(1)
