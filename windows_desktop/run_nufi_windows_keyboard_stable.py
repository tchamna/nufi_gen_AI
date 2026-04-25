import sys

from nufi_windows_keyboard.app import main


if __name__ == "__main__":
    raise SystemExit(main(["--stable-transform", *sys.argv[1:]]))
