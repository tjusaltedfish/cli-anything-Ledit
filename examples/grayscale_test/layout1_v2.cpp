#include <stdio.h>
#include "ldata.h"

#define TOTAL_SIZE_MM 15.0
#define NUM_DOSE_LEVELS 256

static LLayer EnsureLayer(LFile file, const char* name) {
    LLayer layer = LLayer_Find(file, name);
    if (!layer) {
        LLayer_New(file, LLayer_GetList(file), name);
        layer = LLayer_Find(file, name);
    }
    return layer;
}

static void WriteReceipt(const char* status, int shapes) {
    FILE* f = fopen("C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\layout1_v2_receipt.txt", "w");
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

// ??1: 256?????
// ??: 16? x 16? = 256?????
// ?????0.9375mm x 0.9375mm
// ???0/255?255/255????
static int GenerateDoseCalibration256(LCell cell, LFile file) {
    int count = 0;
    double margin = 1.0;
    double usable = TOTAL_SIZE_MM - 2 * margin;
    int grid = 16;  // 16x16 = 256
    double cell_size = usable / grid;  // ?0.875mm
    double gap = 0.02;  // 20?m??????
    
    for (int row = 0; row < grid; row++) {
        for (int col = 0; col < grid; col++) {
            int dose_index = row * grid + col;  // 0-255
            double dose_percent = dose_index * 100.0 / 255.0;
            
            // ?????????????
            char layerName[32];
            sprintf(layerName, "Dose%03d", dose_index);  // Dose000 ? Dose255
            
            LLayer layer = EnsureLayer(file, layerName);
            if (!layer) continue;
            
            double x = margin + col * cell_size + gap/2;
            double y = margin + row * cell_size + gap/2;
            
            LBox_New(cell, layer, 
                LFile_DispUtoIntU(file, x), 
                LFile_DispUtoIntU(file, y), 
                LFile_DispUtoIntU(file, x + cell_size - gap), 
                LFile_DispUtoIntU(file, y + cell_size - gap));
            count++;
        }
    }
    
    return count;
}

extern "C" void DoseCalibration256(void) {
    WriteReceipt("started", 0);
    int quiet = LUpi_InQuietMode();
    LUpi_SetQuietMode(1);
    
    LFile file = LFile_New(NULL, "DoseCalibration256");
    LCell cell = LCell_New(file, "TOP");
    if (!file || !cell) {
        WriteReceipt("error", 0);
        LUpi_SetQuietMode(quiet);
        return;
    }
    LCell_MakeVisible(cell);
    
    int totalShapes = 0;
    totalShapes += DrawAlignmentMarks(cell, file);
    totalShapes += GenerateDoseCalibration256(cell, file);
    
    LFile_SaveAs(file, "C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\Layout1_DoseCalibration256", LTdbFile);
    LDisplay_Refresh();
    WriteReceipt("ok", totalShapes);
    LUpi_SetQuietMode(quiet);
}

extern "C" int UPI_Entry_Point(void) {
    LMacro_Register("Dose Calibration 256", "DoseCalibration256");
    return 1;
}
