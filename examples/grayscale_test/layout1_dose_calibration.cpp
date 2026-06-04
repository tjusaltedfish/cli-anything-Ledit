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
    FILE* f = fopen("C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\layout1_receipt.txt", "w");
    if (f) {
        fprintf(f, "status=%s\nshapes=%d\n", status, shapes);
        fclose(f);
    }
}

// ????
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
        // ???
        LBox_New(cell, alignLayer, LFile_DispUtoIntU(file, cx - mark_size/2), LFile_DispUtoIntU(file, cy - mark_width/2), LFile_DispUtoIntU(file, cx + mark_size/2), LFile_DispUtoIntU(file, cy + mark_width/2));
        count++;
        // ???
        LBox_New(cell, alignLayer, LFile_DispUtoIntU(file, cx - mark_width/2), LFile_DispUtoIntU(file, cy - mark_size/2), LFile_DispUtoIntU(file, cx + mark_width/2), LFile_DispUtoIntU(file, cy + mark_size/2));
        count++;
    }
    return count;
}

// ??1: ????
// ??: 20????????????????
// ?????0.6mm???10mm?????
static int GenerateDoseCalibration(LCell cell, LFile file) {
    int count = 0;
    double margin = 1.5;
    double strip_width = 0.6;  // ??????0.6mm
    double strip_height = 10.0; // ????10mm
    double gap = 0.05;  // ????50?m
    int doses[] = {5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100};
    int num_doses = 20;
    
    // ????????????
    double total_width = num_doses * strip_width + (num_doses - 1) * gap;
    double x_start = (TOTAL_SIZE_MM - total_width) / 2;
    double y_start = (TOTAL_SIZE_MM - strip_height) / 2;
    
    for (int i = 0; i < num_doses; i++) {
        char layerName[32];
        sprintf(layerName, "Dose%03d", doses[i]);
        LLayer layer = EnsureLayer(file, layerName);
        if (!layer) continue;
        
        double x = x_start + i * (strip_width + gap);
        LBox_New(cell, layer, 
            LFile_DispUtoIntU(file, x), 
            LFile_DispUtoIntU(file, y_start), 
            LFile_DispUtoIntU(file, x + strip_width), 
            LFile_DispUtoIntU(file, y_start + strip_height));
        count++;
    }
    
    return count;
}

extern "C" void DoseCalibrationMask(void) {
    WriteReceipt("started", 0);
    int quiet = LUpi_InQuietMode();
    LUpi_SetQuietMode(1);
    
    LFile file = LFile_New(NULL, "DoseCalibration");
    LCell cell = LCell_New(file, "TOP");
    if (!file || !cell) {
        WriteReceipt("error", 0);
        LUpi_SetQuietMode(quiet);
        return;
    }
    LCell_MakeVisible(cell);
    
    int totalShapes = 0;
    totalShapes += DrawAlignmentMarks(cell, file);
    totalShapes += GenerateDoseCalibration(cell, file);
    
    LFile_SaveAs(file, "C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\Layout1_DoseCalibration", LTdbFile);
    LDisplay_Refresh();
    WriteReceipt("ok", totalShapes);
    LUpi_SetQuietMode(quiet);
}

extern "C" int UPI_Entry_Point(void) {
    LMacro_Register("Dose Calibration Mask", "DoseCalibrationMask");
    return 1;
}
