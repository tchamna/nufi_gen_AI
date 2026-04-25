import sys

from nufi_windows_keyboard.app import main


if __name__ == "__main__":
    raise SystemExit(main(["--customizable", *sys.argv[1:]]))
