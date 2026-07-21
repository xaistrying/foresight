import sys

from scripts.run_predict import main

if __name__ == "__main__":
    target_month = sys.argv[1]
    main("configs/config.yaml", target_month)
