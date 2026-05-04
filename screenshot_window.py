"""
Take a screenshot of a specific window by title.
Requires: pip install pywin32 pillow
"""

import ctypes
from ctypes import wintypes
import sys

try:
    import win32gui
    import win32ui
    import win32con
    from PIL import Image
except ImportError:
    print("Required packages not installed. Run:")
    print("  pip install pywin32 pillow")
    sys.exit(1)


def list_windows():
    """List all visible windows with titles."""
    windows = []

    def enum_callback(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                results.append((hwnd, title))
        return True

    win32gui.EnumWindows(enum_callback, windows)
    return windows


def screenshot_window(hwnd, output_path="screenshot.png"):
    """Take a screenshot of a specific window."""
    # Get window dimensions
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top

    if width <= 0 or height <= 0:
        print(f"Invalid window dimensions: {width}x{height}")
        return False

    # Get window device context
    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()

    # Create bitmap
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
    save_dc.SelectObject(bitmap)

    # Copy window content to bitmap
    # Use PrintWindow for better results with some windows
    result = ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)

    if result == 0:
        # Fallback to BitBlt
        save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)

    # Convert to PIL Image
    bmp_info = bitmap.GetInfo()
    bmp_str = bitmap.GetBitmapBits(True)

    img = Image.frombuffer(
        'RGB',
        (bmp_info['bmWidth'], bmp_info['bmHeight']),
        bmp_str, 'raw', 'BGRX', 0, 1
    )

    # Save
    img.save(output_path)
    print(f"Screenshot saved to: {output_path}")

    # Cleanup
    win32gui.DeleteObject(bitmap.GetHandle())
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)

    return True


def find_window_by_title(search_term):
    """Find windows matching a search term."""
    windows = list_windows()
    matches = [(hwnd, title) for hwnd, title in windows
               if search_term.lower() in title.lower()]
    return matches


def main():
    if len(sys.argv) > 1:
        # Search term provided
        search_term = " ".join(sys.argv[1:])
        matches = find_window_by_title(search_term)

        if not matches:
            print(f"No windows found matching: {search_term}")
            print("\nAvailable windows:")
            for hwnd, title in list_windows()[:20]:
                print(f"  {title[:60]}")
            return

        if len(matches) == 1:
            hwnd, title = matches[0]
            print(f"Found window: {title}")
            screenshot_window(hwnd, "screenshot.png")
        else:
            print(f"Multiple matches for '{search_term}':")
            for i, (hwnd, title) in enumerate(matches):
                print(f"  {i+1}. {title[:60]}")
            choice = input("Enter number (or press Enter for first): ").strip()
            idx = int(choice) - 1 if choice else 0
            hwnd, title = matches[idx]
            screenshot_window(hwnd, "screenshot.png")
    else:
        # List all windows
        print("Available windows:\n")
        windows = list_windows()
        for i, (hwnd, title) in enumerate(windows[:30]):
            print(f"  {i+1:2}. {title[:70]}")

        print("\nUsage: python screenshot_window.py <window title search>")
        print("Example: python screenshot_window.py python")
        print("         python screenshot_window.py reter")


if __name__ == "__main__":
    main()
