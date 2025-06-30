### This is a utility function that generates a numbered code from a file.
### Author: Kody Kendall
### Date: 2025-05-25
"""
Usage:

numbered = get_numbered_code_from_file("page.html")
print(numbered)
"""


def get_numbered_code_from_file(file_path: str) -> str:
    numbered = [
        f"{i:05d}: {ln.rstrip()}"  # 5–6 digits = ≤ 999 999 lines
        for i, ln in enumerate(open(file_path), 1)
    ]
    return "\n".join(numbered)


# Example Usage:
# python agents/utils/get_numbered_code_from_file.py
if __name__ == "__main__":
    numbered = get_numbered_code_from_file("page.html")
    print(numbered)
