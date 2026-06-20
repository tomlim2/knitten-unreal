#!/usr/bin/env python3
"""Generate sprite sheets from image sequence folders.

Batch-converts folders of image sequences (PNG/JPG/WebP) into sprite sheet
textures suitable for UE flipbooks.

Usage:
    python generate_spritesheet.py --input <path> [--output <path>] [options]

Requires: PIL (Pillow)
"""

import os
import sys
import argparse
from pathlib import Path

from PIL import Image


def calculate_sheet_size(frame_size, max_sheet_size=(1024, 1024)):
    """Calculate sprite sheet dimensions that fit the most frames."""
    frame_width, frame_height = frame_size
    max_width, max_height = max_sheet_size

    max_cols = max_width // frame_width
    max_rows = max_height // frame_height

    sheet_width = max_cols * frame_width
    sheet_height = max_rows * frame_height

    return (sheet_width, sheet_height)


def generate_sprite_sheet(folder_path, output_filename, frame_size=(260, 145),
                          fps_reduction=2, max_sheet_size=(1024, 1024)):
    """Generate a single sprite sheet from a folder of images.

    Images are center-cropped to the target aspect ratio and resized with LANCZOS.
    """
    try:
        png_files = [f for f in os.listdir(folder_path)
                     if f.lower().endswith(('.png', '.jpg', '.webp'))]
    except FileNotFoundError:
        print(f"Error: Folder '{folder_path}' not found")
        return False

    png_files.sort()

    if not png_files:
        print(f"No image files found in {folder_path}")
        return False

    png_files = png_files[::fps_reduction]
    sheet_size = calculate_sheet_size(frame_size, max_sheet_size)

    cols = sheet_size[0] // frame_size[0]
    rows = sheet_size[1] // frame_size[1]
    max_frames = cols * rows

    total_frames = min(len(png_files), max_frames)
    png_files = png_files[:total_frames]

    sprite_sheet = Image.new('RGBA', sheet_size, (0, 0, 0, 0))

    for i, png_file in enumerate(png_files):
        img = Image.open(os.path.join(folder_path, png_file))
        img_width, img_height = img.size
        target_width, target_height = frame_size
        target_ratio = target_width / target_height
        img_ratio = img_width / img_height

        if img_ratio > target_ratio:
            new_width = int(img_height * target_ratio)
            left = (img_width - new_width) // 2
            crop_box = (left, 0, left + new_width, img_height)
        else:
            new_height = int(img_width / target_ratio)
            top = (img_height - new_height) // 2
            crop_box = (0, top, img_width, top + new_height)

        img = img.crop(crop_box).resize(frame_size, Image.LANCZOS)

        row = i // cols
        col = i % cols
        x = col * frame_size[0]
        y = row * frame_size[1]

        sprite_sheet.paste(img, (x, y), img if img.mode == 'RGBA' else None)

    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    sprite_sheet.save(output_filename)
    print(f"Generated: {output_filename} ({total_frames} frames, sheet: {sheet_size})")
    return True


def main():
    parser = argparse.ArgumentParser(description='Generate sprite sheets from image folders')
    parser.add_argument('--input', required=True, help='Input directory containing sequence folders')
    parser.add_argument('--output', default=None, help='Output directory (default: .agent-local/private/unreal/spritesheet-generate/)')
    parser.add_argument('--frame_width', type=int, default=80, help='Frame width in pixels (default: 80)')
    parser.add_argument('--frame_height', type=int, default=80, help='Frame height in pixels (default: 80)')
    parser.add_argument('--fps_reduction', type=int, default=1, help='Sample every Nth frame (default: 1)')
    parser.add_argument('--use_png_subfolder', type=lambda x: x.lower() == 'true', default=True,
                        help='Look for images in png/ subfolder (default: True)')
    parser.add_argument('--max_width', type=int, default=1024, help='Max sheet width (default: 1024)')
    parser.add_argument('--max_height', type=int, default=1024, help='Max sheet height (default: 1024)')
    args = parser.parse_args()

    input_dir = os.path.abspath(args.input)
    if args.output:
        output_dir = os.path.abspath(args.output)
    else:
        output_dir = os.path.join(str(Path.home()), '.agent-local', 'private', 'unreal', 'spritesheet-generate')

    frame_size = (args.frame_width, args.frame_height)
    max_sheet_size = (args.max_width, args.max_height)

    if not os.path.isdir(input_dir):
        print(f"Error: Input directory not found: {input_dir}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    folders = [f for f in os.listdir(input_dir)
               if os.path.isdir(os.path.join(input_dir, f))]

    if not folders:
        print(f"No subfolders found in {input_dir}")
        sys.exit(1)

    print(f"Processing {len(folders)} folder(s)...")
    success_count = 0

    for folder in sorted(folders):
        folder_path = os.path.join(input_dir, folder)
        if args.use_png_subfolder:
            folder_path = os.path.join(folder_path, 'png')

        if not os.path.exists(folder_path):
            subfolder_hint = " (no 'png' subfolder)" if args.use_png_subfolder else ""
            print(f"Skipping {folder}{subfolder_hint}")
            continue

        img_files = [f for f in os.listdir(folder_path)
                     if f.lower().endswith(('.png', '.jpg', '.webp'))]

        sheet_size = calculate_sheet_size(frame_size, max_sheet_size)
        max_cols = sheet_size[0] // frame_size[0]
        max_rows = sheet_size[1] // frame_size[1]
        max_frames = max_cols * max_rows
        frame_count = min(len(img_files), max_frames)

        output_file = os.path.join(output_dir, f"{folder}_{frame_count}.png")

        if generate_sprite_sheet(
            folder_path=folder_path,
            output_filename=output_file,
            frame_size=frame_size,
            fps_reduction=args.fps_reduction,
            max_sheet_size=max_sheet_size
        ):
            success_count += 1

    print(f"\nDone: {success_count}/{len(folders)} sprite sheets generated")
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    main()
