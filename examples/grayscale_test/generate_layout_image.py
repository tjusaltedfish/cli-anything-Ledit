import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

# ????
TOTAL_SIZE_MM = 15.0
DPI = 300  # ?????
MARGIN_MM = 1.5
REGION_GAP_MM = 0.3
GRID = 8  # 8x8 = 64???

# ????/mm
PIXELS_PER_MM = DPI / 25.4

# ????
img_width = int(TOTAL_SIZE_MM * PIXELS_PER_MM)
img_height = int(TOTAL_SIZE_MM * PIXELS_PER_MM)

# ????????
img = Image.new('RGB', (img_width, img_height), 'white')
draw = ImageDraw.Draw(img)

# ??????
usable = TOTAL_SIZE_MM - 2 * MARGIN_MM
region_size = (usable - (GRID - 1) * REGION_GAP_MM) / GRID

# ??????
block_sizes = [10.0/50, 10.0/60, 10.0/80, 10.0/100, 10.0/120]
repeats_per_size = 5

# ??????
grid_width = GRID * region_size + (GRID - 1) * REGION_GAP_MM
grid_height = GRID * region_size + (GRID - 1) * REGION_GAP_MM
x_origin = MARGIN_MM + (usable - grid_width) / 2
y_origin = MARGIN_MM + (usable - grid_height) / 2

# ????????
def dose_to_color(dose_index):
    """????????????"""
    gray = int(255 * dose_index / 63)
    return (gray, gray, gray)

# ??????
def draw_alignment_marks(draw):
    mark_size = 0.5
    mark_width = 0.05
    offset = 0.5
    positions = [
        (offset, offset),
        (TOTAL_SIZE_MM - offset, offset),
        (offset, TOTAL_SIZE_MM - offset),
        (TOTAL_SIZE_MM - offset, TOTAL_SIZE_MM - offset)
    ]
    
    for cx, cy in positions:
        # ???
        x1 = int((cx - mark_size/2) * PIXELS_PER_MM)
        y1 = int((cy - mark_width/2) * PIXELS_PER_MM)
        x2 = int((cx + mark_size/2) * PIXELS_PER_MM)
        y2 = int((cy + mark_width/2) * PIXELS_PER_MM)
        draw.rectangle([x1, y1, x2, y2], fill='black')
        
        # ???
        x1 = int((cx - mark_width/2) * PIXELS_PER_MM)
        y1 = int((cy - mark_size/2) * PIXELS_PER_MM)
        x2 = int((cx + mark_width/2) * PIXELS_PER_MM)
        y2 = int((cy + mark_size/2) * PIXELS_PER_MM)
        draw.rectangle([x1, y1, x2, y2], fill='black')

# ????
def draw_layout(draw):
    # ??????
    draw_alignment_marks(draw)
    
    # ??64?dose??
    for row in range(GRID):
        for col in range(GRID):
            dose_index = row * GRID + col
            
            # ??????
            region_x1 = x_origin + col * (region_size + REGION_GAP_MM)
            region_y1 = y_origin + row * (region_size + REGION_GAP_MM)
            region_x2 = region_x1 + region_size
            region_y2 = region_y1 + region_size
            
            # ??????????
            color = dose_to_color(dose_index)
            x1_px = int(region_x1 * PIXELS_PER_MM)
            y1_px = int(region_y1 * PIXELS_PER_MM)
            x2_px = int(region_x2 * PIXELS_PER_MM)
            y2_px = int(region_y2 * PIXELS_PER_MM)
            draw.rectangle([x1_px, y1_px, x2_px, y2_px], fill=color)
            
            # ????
            inner_margin = 0.02
            inner_width = region_size - 2 * inner_margin
            inner_height = region_size - 2 * inner_margin
            blocks_per_row = 5
            rows_needed = 5
            cell_width = inner_width / blocks_per_row
            cell_height = inner_height / rows_needed
            
            # ???????????
            block_color = 'white' if dose_index < 32 else 'black'
            
            block_index = 0
            for size_idx in range(5):
                block_size = block_sizes[size_idx]
                for rep in range(repeats_per_size):
                    r = block_index // blocks_per_row
                    c = block_index % blocks_per_row
                    
                    block_x1 = region_x1 + inner_margin + c * cell_width + (cell_width - block_size) / 2
                    block_y1 = region_y1 + inner_margin + r * cell_height + (cell_height - block_size) / 2
                    block_x2 = block_x1 + block_size
                    block_y2 = block_y1 + block_size
                    
                    # ????
                    x1_px = int(block_x1 * PIXELS_PER_MM)
                    y1_px = int(block_y1 * PIXELS_PER_MM)
                    x2_px = int(block_x2 * PIXELS_PER_MM)
                    y2_px = int(block_y2 * PIXELS_PER_MM)
                    draw.rectangle([x1_px, y1_px, x2_px, y2_px], fill=block_color)
                    
                    block_index += 1

# ????
draw_layout(draw)

# ????
try:
    font = ImageFont.truetype("arial.ttf", 20)
except:
    font = ImageFont.load_default()

draw.text((10, 10), "Layout1: Dose Calibration (64 levels)", fill='black', font=font)
draw.text((10, 40), f"Grid: {GRID}x{GRID}, Region size: {region_size:.2f}mm", fill='black', font=font)

# ????
output_dir = r"C:\Users\ASUS\Documents\L_edit\agent-harness\grayscale_test"
bmp_path = os.path.join(output_dir, "Layout1_DoseCalibration64.bmp")
png_path = os.path.join(output_dir, "Layout1_DoseCalibration64.png")

img.save(bmp_path, "BMP")
img.save(png_path, "PNG")

print(f"?????:")
print(f"  BMP: {bmp_path}")
print(f"  PNG: {png_path}")
print(f"????: {img_width} x {img_height} ??")
print(f"???: {DPI} DPI")
