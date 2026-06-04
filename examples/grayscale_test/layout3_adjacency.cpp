#include <stdio.h>
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
    FILE* f = fopen("C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\layout3_receipt.txt", "w");
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

// ??3: ??????
// ??: 
// ????: 50%???? + 4????(10%, 30%, 70%, 90%)
// ????: 21????? (0%?100%)
// ?????2mm x 2mm?????
static int GenerateAdjacencyTest(LCell cell, LFile file) {
    int count = 0;
    double margin = 1.5;
    double usable = TOTAL_SIZE_MM - 2 * margin;
    
    // === ????: ?????? ===
    double upper_height = usable * 0.6;  // ?????60%
    double bg_x1 = margin;
    double bg_y1 = margin + usable * 0.35;  // ?35%????
    double bg_x2 = TOTAL_SIZE_MM - margin;
    double bg_y2 = bg_y1 + upper_height;
    
    // ???? (50% ??)
    LLayer bg_layer = EnsureLayer(file, "Dose050");
    if (bg_layer) {
        LBox_New(cell, bg_layer, 
            LFile_DispUtoIntU(file, bg_x1), 
            LFile_DispUtoIntU(file, bg_y1), 
            LFile_DispUtoIntU(file, bg_x2), 
            LFile_DispUtoIntU(file, bg_y2));
        count++;
    }
    
    // ??? (?????????)
    int test_doses[] = {10, 30, 70, 90};
    double test_size = 2.5;  // ?????2.5mm
    double test_gap = 0.0;   // ??????
    double total_test_width = 4 * test_size + 3 * test_gap;
    double test_x_start = margin + (usable - total_test_width) / 2;
    double test_y_start = bg_y1 + (upper_height - test_size) / 2;
    
    for (int i = 0; i < 4; i++) {
        char layerName[32];
        sprintf(layerName, "Dose%03d", test_doses[i]);
        LLayer layer = EnsureLayer(file, layerName);
        if (!layer) continue;
        
        double x = test_x_start + i * (test_size + test_gap);
        LBox_New(cell, layer, 
            LFile_DispUtoIntU(file, x), 
            LFile_DispUtoIntU(file, test_y_start), 
            LFile_DispUtoIntU(file, x + test_size), 
            LFile_DispUtoIntU(file, test_y_start + test_size));
        count++;
    }
    
    // === ????: ?????? ===
    double lower_height = usable * 0.25;  // ?????25%
    double step_y_start = margin;
    double step_width = usable / 21;  // 21??? (0%, 5%, 10%, ..., 100%)
    
    for (int i = 0; i <= 20; i++) {
        int dose = i * 5;
        char layerName[32];
        sprintf(layerName, "Dose%03d", dose);
        LLayer layer = EnsureLayer(file, layerName);
        if (!layer) continue;
        
        double x = margin + i * step_width;
        LBox_New(cell, layer, 
            LFile_DispUtoIntU(file, x), 
            LFile_DispUtoIntU(file, step_y_start), 
            LFile_DispUtoIntU(file, x + step_width - 0.01), 
            LFile_DispUtoIntU(file, step_y_start + lower_height));
        count++;
    }
    
    return count;
}

extern "C" void AdjacencyTestMask(void) {
    WriteReceipt("started", 0);
    int quiet = LUpi_InQuietMode();
    LUpi_SetQuietMode(1);
    
    LFile file = LFile_New(NULL, "AdjacencyTest");
    LCell cell = LCell_New(file, "TOP");
    if (!file || !cell) {
        WriteReceipt("error", 0);
        LUpi_SetQuietMode(quiet);
        return;
    }
    LCell_MakeVisible(cell);
    
    int totalShapes = 0;
    totalShapes += DrawAlignmentMarks(cell, file);
    totalShapes += GenerateAdjacencyTest(cell, file);
    
    LFile_SaveAs(file, "C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\Layout3_Adjacency", LTdbFile);
    LDisplay_Refresh();
    WriteReceipt("ok", totalShapes);
    LUpi_SetQuietMode(quiet);
}

extern "C" int UPI_Entry_Point(void) {
    LMacro_Register("Adjacency Test Mask", "AdjacencyTestMask");
    return 1;
}
