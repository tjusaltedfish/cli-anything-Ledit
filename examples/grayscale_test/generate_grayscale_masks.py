#!/usr/bin/env python3
import math
from pathlib import Path

TOTAL_SIZE_MM = 15.0

def generate_upi_code():
    return r"""#include <stdio.h>
#include <math.h>
#include "ldata.h"

#define TOTAL_SIZE_MM 15.0

static LLayer EnsureLayer(LFile file, const char* name) {
    LLayer layer = LLayer_Find(file, name);
    if (!layer) {
        LLayer_New(file, LLayer_GetList(file), name);
        layer = LLayer_Find(file, name);
    }
    return layer;
}

static void WriteReceipt(const char* status, int shapes, const char* msg) {
    FILE* f = fopen("C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\receipt.txt", "w");
    if (f) {
        fprintf(f, "status=%s\nshapes=%d\nmessage=%s\n", status, shapes, msg);
        fclose(f);
    }
}

static int DrawAlignmentMarks(LCell cell, LFile file) {
    LLayer alignLayer = EnsureLayer(file, "Alignment");
    if (!alignLayer) return 0;
    int count = 0;
    double mark_size = 0.5;
    double mark_width = 0.05;
    double offset = 0.3;
    double positions[4][2] = {{offset, offset}, {TOTAL_SIZE_MM - offset, offset}, {offset, TOTAL_SIZE_MM - offset}, {TOTAL_SIZE_MM - offset, TOTAL_SIZE_MM - offset}};
    for (int i = 0; i < 4; i++) {
        double cx = positions[i][0];
        double cy = positions[i][1];
        LBox_New(cell, alignLayer, LFile_DispUtoIntU(file, cx - mark_size/2), LFile_DispUtoIntU(file, cy - mark_width/2), LFile_DispUtoIntU(file, cx + mark_size/2), LFile_DispUtoIntU(file, cy + mark_width/2));
        count++;
        LBox_New(cell, alignLayer, LFile_DispUtoIntU(file, cx - mark_width/2), LFile_DispUtoIntU(file, cy - mark_size/2), LFile_DispUtoIntU(file, cx + mark_width/2), LFile_DispUtoIntU(file, cy + mark_size/2));
        count++;
    }
    return count;
}

static int Generate_Layout1(LCell cell, LFile file) {
    int count = 0;
    double margin = 1.0;
    double usable_width = TOTAL_SIZE_MM - 2 * margin;
    double usable_height = TOTAL_SIZE_MM - 2 * margin;
    double strip_width = usable_width / 20;
    double strip_height = usable_height * 0.8;
    double y_start = margin + usable_height * 0.15;
    int doses[] = {5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100};
    for (int i = 0; i < 20; i++) {
        char layerName[32];
        sprintf(layerName, "Dose%03d", doses[i]);
        LLayer layer = EnsureLayer(file, layerName);
        if (!layer) continue;
        double x = margin + i * strip_width;
        LBox_New(cell, layer, LFile_DispUtoIntU(file, x), LFile_DispUtoIntU(file, y_start), LFile_DispUtoIntU(file, x + strip_width - 0.01), LFile_DispUtoIntU(file, y_start + strip_height));
        count++;
    }
    return count;
}

static int Generate_Layout2(LCell cell, LFile file) {
    int count = 0;
    double margin = 1.0;
    double gap = 0.5;
    double region_width = (TOTAL_SIZE_MM - 2*margin - 2*gap) / 3;
    double half_height = (region_width - 0.2) / 2;
    int grids[] = {32, 48, 64};
    int grays[] = {8, 16};
    for (int g = 0; g < 3; g++) {
        double x_start = margin + g * (region_width + gap);
        for (int h = 0; h < 2; h++) {
            double y_start = margin + h * (half_height + 0.2);
            double cx = x_start + region_width / 2;
            double cy = y_start + half_height / 2;
            double radius = region_width / 2 * 0.9;
            double cell_size = region_width / grids[g];
            char layerName[32];
            sprintf(layerName, "Grid%d_Gray%d", grids[g], grays[h]);
            LLayer layer = EnsureLayer(file, layerName);
            if (!layer) continue;
            for (int row = 0; row < grids[g]; row++) {
                for (int col = 0; col < grids[g]; col++) {
                    double px = x_start + col * cell_size;
                    double py = y_start + row * cell_size;
                    double dx = (px + cell_size/2) - cx;
                    double dy = (py + cell_size/2) - cy;
                    double dist = sqrt(dx*dx + dy*dy);
                    if (dist <= radius) {
                        LBox_New(cell, layer, LFile_DispUtoIntU(file, px), LFile_DispUtoIntU(file, py), LFile_DispUtoIntU(file, px + cell_size), LFile_DispUtoIntU(file, py + cell_size));
                        count++;
                    }
                }
            }
        }
    }
    return count;
}

static int Generate_Layout3(LCell cell, LFile file) {
    int count = 0;
    double margin = 1.0;
    double usable = TOTAL_SIZE_MM - 2*margin;
    double test_size = 2.0;
    double gap = 0.1;
    LLayer bg_layer = EnsureLayer(file, "Dose050");
    if (bg_layer) {
        LBox_New(cell, bg_layer, LFile_DispUtoIntU(file, margin), LFile_DispUtoIntU(file, margin), LFile_DispUtoIntU(file, TOTAL_SIZE_MM - margin), LFile_DispUtoIntU(file, TOTAL_SIZE_MM - margin));
        count++;
    }
    int test_doses[] = {10, 30, 70, 90};
    double start_x = margin + (usable - 4*test_size - 3*gap) / 2;
    double start_y = margin + (usable - test_size) / 2;
    for (int i = 0; i < 4; i++) {
        char layerName[32];
        sprintf(layerName, "Dose%03d", test_doses[i]);
        LLayer layer = EnsureLayer(file, layerName);
        if (!layer) continue;
        double x = start_x + i * (test_size + gap);
        LBox_New(cell, layer, LFile_DispUtoIntU(file, x), LFile_DispUtoIntU(file, start_y), LFile_DispUtoIntU(file, x + test_size), LFile_DispUtoIntU(file, start_y + test_size));
        count++;
    }
    double step_w = usable / 20;
    double step_h = 2.0;
    for (int i = 0; i <= 20; i++) {
        int dose = i * 5;
        char layerName[32];
        sprintf(layerName, "Dose%03d", dose);
        LLayer layer = EnsureLayer(file, layerName);
        if (!layer) continue;
        double x = margin + i * step_w;
        LBox_New(cell, layer, LFile_DispUtoIntU(file, x), LFile_DispUtoIntU(file, margin + 1.0), LFile_DispUtoIntU(file, x + step_w - 0.01), LFile_DispUtoIntU(file, margin + 1.0 + step_h));
        count++;
    }
    return count;
}

extern "C" void GrayscaleTestMasks(void) {
    WriteReceipt("started", 0, "Generating grayscale test masks...");
    int quiet = LUpi_InQuietMode();
    LUpi_SetQuietMode(1);
    LFile file = LFile_New(NULL, "GrayscaleTest");
    LCell cell = LCell_New(file, "TOP");
    if (!file || !cell) {
        WriteReceipt("error", 0, "Failed to create file or cell");
        LUpi_SetQuietMode(quiet);
        return;
    }
    LCell_MakeVisible(cell);
    int totalShapes = 0;
    totalShapes += DrawAlignmentMarks(cell, file);
    totalShapes += Generate_Layout1(cell, file);
    totalShapes += Generate_Layout2(cell, file);
    totalShapes += Generate_Layout3(cell, file);
    LFile_SaveAs(file, "C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\GrayscaleTest", LTdbFile);
    LDisplay_Refresh();
    char msg[256];
    sprintf(msg, "Completed: L1-L3, Total shapes: %d", totalShapes);
    WriteReceipt("ok", totalShapes, msg);
    LUpi_SetQuietMode(quiet);
}

extern "C" int UPI_Entry_Point(void) {
    LMacro_Register("Grayscale Test Masks", "GrayscaleTestMasks");
    return 1;
}
""";

def main():
    output_dir = Path(r"C:\Users\ASUS\Documents\L_edit\agent-harness\grayscale_test")
    output_dir.mkdir(exist_ok=True)
    print("=" * 60)
    print("Grayscale Lithography Test Mask Generator")
    print("=" * 60)
    upi_code = generate_upi_code()
    cpp_file = output_dir / "grayscale_test.cpp"
    cpp_file.write_text(upi_code, encoding="ascii")
    print(f"Saved: {cpp_file}")
    def_content = """LIBRARY grayscale_test
EXPORTS
    UPI_Entry_Point @1
    GrayscaleTestMasks @2
"""
    def_file = output_dir / "grayscale_test.def"
    def_file.write_text(def_content, encoding="ascii")
    print(f"Saved: {def_file}")
    print("\nLayout Design:")
    print("  Layout1: 20 dose strips (5%-100%)")
    print("  Layout2: 32x32, 48x48, 64x64 grid circle discretization")
    print("  Layout3: Adjacency test (50% bg + 10/30/70/90% blocks)")
    print("\nNext: Compile and execute")
    print("=" * 60)

if __name__ == "__main__":
    main()
