#include <stdio.h>
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

static void WriteReceipt(const char* status, int shapes) {
    FILE* f = fopen("C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\layout2_v3_receipt.txt", "w");
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

// ??2 v3: ??????????????
// ?????????L-Edit??
// 2???(32x32, 64x64) x 4???(20%, 40%, 60%, 80%)
static int GenerateGridDoseMatrix(LCell cell, LFile file) {
    int count = 0;
    double margin = 1.5;
    double gap = 0.5;
    
    // ??????
    int grids[] = {32, 64};
    int num_grids = 2;
    
    // ????
    int doses[] = {20, 40, 60, 80};
    int num_doses = 4;
    
    // ??????
    double region_width = (TOTAL_SIZE_MM - 2*margin - (num_grids-1)*gap) / num_grids;
    double region_height = (TOTAL_SIZE_MM - 2*margin - (num_doses-1)*gap) / num_doses;
    double region_size = fmin(region_width, region_height) * 0.95;  // ?5%??
    
    // ??????
    double total_width = num_grids * region_size + (num_grids-1) * gap;
    double total_height = num_doses * region_size + (num_doses-1) * gap;
    double x_origin = margin + (TOTAL_SIZE_MM - 2*margin - total_width) / 2;
    double y_origin = margin + (TOTAL_SIZE_MM - 2*margin - total_height) / 2;
    
    for (int g = 0; g < num_grids; g++) {
        for (int d = 0; d < num_doses; d++) {
            double x_start = x_origin + g * (region_size + gap);
            double y_start = y_origin + d * (region_size + gap);
            double cx = x_start + region_size / 2;
            double cy = y_start + region_size / 2;
            double radius = region_size / 2 * 0.9;
            double cell_size = region_size / grids[g];
            
            // ???????????
            char layerName[32];
            sprintf(layerName, "G%d_D%02d", grids[g], doses[d]);
            
            LLayer layer = EnsureLayer(file, layerName);
            if (!layer) continue;
            
            // ??????
            for (int row = 0; row < grids[g]; row++) {
                for (int col = 0; col < grids[g]; col++) {
                    double px = x_start + col * cell_size;
                    double py = y_start + row * cell_size;
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
