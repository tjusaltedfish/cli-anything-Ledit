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
    FILE* f = fopen("C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\layout2_receipt.txt", "w");
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

// ??2: ???????
// ??: 3?(32x32, 48x48, 64x64) x 2?(8?, 16???)
// ????????????????
// ?????4mm??????5mm x 5mm
static int GenerateDiscretization(LCell cell, LFile file) {
    int count = 0;
    double margin = 1.5;
    double gap = 0.5;
    double region_size = 4.0;  // ????4mm x 4mm
    int grids[] = {32, 48, 64};
    int grays[] = {8, 16};
    
    // ??????
    double total_width = 3 * region_size + 2 * gap;
    double total_height = 2 * region_size + gap;
    double x_origin = (TOTAL_SIZE_MM - total_width) / 2;
    double y_origin = (TOTAL_SIZE_MM - total_height) / 2;
    
    for (int g = 0; g < 3; g++) {
        for (int h = 0; h < 2; h++) {
            double x_start = x_origin + g * (region_size + gap);
            double y_start = y_origin + h * (region_size + gap);
            double cx = x_start + region_size / 2;
            double cy = y_start + region_size / 2;
            double radius = region_size / 2 * 0.9;  // ??????10%??
            double cell_size = region_size / grids[g];
            
            char layerName[32];
            sprintf(layerName, "Grid%d_Gray%d", grids[g], grays[h]);
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
                    
                    // ???????????
                    if (dist <= radius) {
                        // ??????????????
                        // ????????
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

extern "C" void DiscretizationTestMask(void) {
    WriteReceipt("started", 0);
    int quiet = LUpi_InQuietMode();
    LUpi_SetQuietMode(1);
    
    LFile file = LFile_New(NULL, "DiscretizationTest");
    LCell cell = LCell_New(file, "TOP");
    if (!file || !cell) {
        WriteReceipt("error", 0);
        LUpi_SetQuietMode(quiet);
        return;
    }
    LCell_MakeVisible(cell);
    
    int totalShapes = 0;
    totalShapes += DrawAlignmentMarks(cell, file);
    totalShapes += GenerateDiscretization(cell, file);
    
    LFile_SaveAs(file, "C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\Layout2_Discretization", LTdbFile);
    LDisplay_Refresh();
    WriteReceipt("ok", totalShapes);
    LUpi_SetQuietMode(quiet);
}

extern "C" int UPI_Entry_Point(void) {
    LMacro_Register("Discretization Test Mask", "DiscretizationTestMask");
    return 1;
}
