#include <stdio.h>
#include <math.h>
#include "ldata.h"

#define TOTAL_SIZE_MM 15.0

// ============================================================
// ???????????????????
// ============================================================
// 1. ?????????????? [x1, y1, x2, y2]
// 2. ??????????? 0.2mm ???
// 3. ????????? [margin, margin] ? [TOTAL_SIZE_MM - margin, TOTAL_SIZE_MM - margin] ???
// 4. ??????????????????????
// ============================================================

static LLayer EnsureLayer(LFile file, const char* name) {
    LLayer layer = LLayer_Find(file, name);
    if (!layer) {
        LLayer_New(file, LLayer_GetList(file), name);
        layer = LLayer_Find(file, name);
    }
    return layer;
}

static void WriteReceipt(const char* status, int shapes) {
    FILE* f = fopen("C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\layout2_v4_receipt.txt", "w");
    if (f) {
        fprintf(f, "status=%s\nshapes=%d\n", status, shapes);
        fclose(f);
    }
}

static int DrawAlignmentMarks(LCell cell, LFile file) {
    LLayer alignLayer = EnsureLayer(file, "Alignment");
    if (!alignLayer) return 0;
    int count = 0;
    double mark_size = 0.5;
    double mark_width = 0.05;
    double offset = 0.5;
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

// ??2 v4: ??????????????????
// ??: 2?(32x32, 64x64) x 4?(20%, 40%, 60%, 80%)
// ??????????????
static int GenerateGridDoseMatrix(LCell cell, LFile file) {
    int count = 0;
    
    // ????
    double margin = 1.5;  // ??
    double gap = 0.3;     // ????
    int num_cols = 2;     // 2?
    int num_rows = 4;     // 4?
    
    // ???????
    int grids[] = {32, 64};
    int doses[] = {20, 40, 60, 80};
    
    // ??????
    double usable_width = TOTAL_SIZE_MM - 2 * margin;
    double usable_height = TOTAL_SIZE_MM - 2 * margin;
    
    // ????????????????????
    double region_width = (usable_width - (num_cols - 1) * gap) / num_cols;
    double region_height = (usable_height - (num_rows - 1) * gap) / num_rows;
    double region_size = fmin(region_width, region_height);  // ??????????
    
    // ??????????
    double grid_width = num_cols * region_size + (num_cols - 1) * gap;
    double grid_height = num_rows * region_size + (num_rows - 1) * gap;
    double x_origin = margin + (usable_width - grid_width) / 2;
    double y_origin = margin + (usable_height - grid_height) / 2;
    
    // ??????
    if (x_origin < margin || y_origin < margin || 
        x_origin + grid_width > TOTAL_SIZE_MM - margin || 
        y_origin + grid_height > TOTAL_SIZE_MM - margin) {
        WriteReceipt("error", 0);
        return 0;
    }
    
    // ????
    for (int col = 0; col < num_cols; col++) {
        for (int row = 0; row < num_rows; row++) {
            // ??????????
            double x1 = x_origin + col * (region_size + gap);
            double y1 = y_origin + row * (region_size + gap);
            double x2 = x1 + region_size;
            double y2 = y1 + region_size;
            
            // ???????
            double cx = (x1 + x2) / 2;
            double cy = (y1 + y2) / 2;
            double radius = region_size / 2 * 0.9;  // ?10%??
            
            // ????????
            double cell_size = region_size / grids[col];
            
            // ??
            char layerName[32];
            sprintf(layerName, "G%d_D%02d", grids[col], doses[row]);
            
            LLayer layer = EnsureLayer(file, layerName);
            if (!layer) continue;
            
            // ??????
            for (int r = 0; r < grids[col]; r++) {
                for (int c = 0; c < grids[col]; c++) {
                    double px = x1 + c * cell_size;
                    double py = y1 + r * cell_size;
                    double dx = (px + cell_size/2) - cx;
                    double dy = (py + cell_size/2) - cy;
                    double dist = sqrt(dx*dx + dy*dy);
                    
                    if (dist <= radius) {
                        LBox_New(cell, layer, 
                            LFile_DispUtoIntU(file, px), 
                            LFile_DispUtoIntU(file, py), 
                            LFile_DispUtoIntU(file, px + cell_size - 0.001), 
                            LFile_DispUtoIntU(file, py + cell_size - 0.001));
                        count++;
                    }
                }
            }
        }
    }
    
    return count;
}

extern "C" void GridDoseMatrix(void) {
    WriteReceipt("started", 0);
    int quiet = LUpi_InQuietMode();
    LUpi_SetQuietMode(1);
    
    LFile file = LFile_New(NULL, "GridDoseMatrix");
    LCell cell = LCell_New(file, "TOP");
    if (!file || !cell) {
        WriteReceipt("error", 0);
        LUpi_SetQuietMode(quiet);
        return;
    }
    LCell_MakeVisible(cell);
    
    int totalShapes = 0;
    totalShapes += DrawAlignmentMarks(cell, file);
    totalShapes += GenerateGridDoseMatrix(cell, file);
    
    LFile_SaveAs(file, "C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\Layout2_GridDoseMatrix", LTdbFile);
    LDisplay_Refresh();
    WriteReceipt("ok", totalShapes);
    LUpi_SetQuietMode(quiet);
}

extern "C" int UPI_Entry_Point(void) {
    LMacro_Register("Grid Dose Matrix", "GridDoseMatrix");
    return 1;
}
