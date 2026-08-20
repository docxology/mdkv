from pathlib import Path

from mdkv.errors import ValidationError
from mdkv.io import load_mdkv
from mdkv.validate import validate_document


def main() -> None:
    path = Path("example.mdkv")
    try:
        doc = load_mdkv(path)
        validate_document(doc)
        print("OK")
    except (FileNotFoundError, ValidationError) as e:
        print(f"Validation failed: {e}")


if __name__ == "__main__":
    main()
