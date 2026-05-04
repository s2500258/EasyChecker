from pathlib import Path

from PIL import Image


# Build a Windows .ico file for PyInstaller from the shared project logo.
# The executable file icon is separate from the runtime window/tray icon, so
# we generate a dedicated .ico asset from logo1.png during the Windows build flow.
def main() -> None:
    agent_dir = Path(__file__).resolve().parent
    project_root = agent_dir.parent
    source_path = project_root / "logo1.png"
    output_path = agent_dir / "logo1.ico"

    if not source_path.exists():
        raise FileNotFoundError(f"Logo file not found: {source_path}")

    image = Image.open(source_path)
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    image.save(
        output_path,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"Created icon: {output_path}")


if __name__ == "__main__":
    main()
