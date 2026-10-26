from pathlib import Path

from mdkv.core.errors import ValidationError
from mdkv.core.validate import validate_document
from mdkv.storage import load_mdkv


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
