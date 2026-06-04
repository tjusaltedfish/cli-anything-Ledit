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
    FILE* f = fopen("C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\layout3_v3_receipt.txt", "w");
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

// ??3 v3: ?????????
// ??: 4?????????
// ??: ??????
// ??: ????
// ??: ????
// ??: ????
static int GenerateAdjacencyComprehensive(LCell cell, LFile file) {
    int count = 0;
    double margin = 1.5;
    double usable = TOTAL_SIZE_MM - 2 * margin;
    double half = usable / 2;
    double gap = 0.3;
    
    // ??: ?????? (5???????)
    {
        double x_start = margin;
        double y_start = margin + half + gap;
        double block_size = 1.2;
        double pair_gap = 0.1;
        
        int dose_pairs[][2] = {{10, 90}, {20, 80}, {30, 70}, {40, 60}, {50, 50}};
        
        for (int i = 0; i < 5; i++) {
            double x = x_start + i * (block_size * 2 + pair_gap + 0.2);
            
            // ??
            char layerName1[32];
            sprintf(layerName1, "Dose%03d", dose_pairs[i][0]);
            LLayer layer1 = EnsureLayer(file, layerName1);
            if (layer1) {
                LBox_New(cell, layer1, 
                    LFile_DispUtoIntU(file, x), 
                    LFile_DispUtoIntU(file, y_start), 
                    LFile_DispUtoIntU(file, x + block_size), 
                    LFile_DispUtoIntU(file, y_start + block_size));
                count++;
            }
            
            // ??
            char layerName2[32];
            sprintf(layerName2, "Dose%03d", dose_pairs[i][1]);
            LLayer layer2 = EnsureLayer(file, layerName2);
            if (layer2) {
                LBox_New(cell, layer2, 
                    LFile_DispUtoIntU(file, x + block_size + pair_gap), 
                    LFile_DispUtoIntU(file, y_start), 
                    LFile_DispUtoIntU(file, x + 2*block_size + pair_gap), 
                    LFile_DispUtoIntU(file, y_start + block_size));
                count++;
            }
        }
    }
    
    // ??: ???? (5?????)
    {
        double x_start = margin;
        double y_start = margin;
        double block_size = 1.2;
        
        double gaps[] = {0.0, 0.05, 0.1, 0.2, 0.5};
        
        for (int i = 0; i < 5; i++) {
            double x = x_start + i * (block_size * 2 + gaps[i] + 0.2);
            
            // ?? (20%)
            LLayer layer1 = EnsureLayer(file, "Dose020");
            if (layer1) {
                LBox_New(cell, layer1, 
                    LFile_DispUtoIntU(file, x), 
                    LFile_DispUtoIntU(file, y_start), 
                    LFile_DispUtoIntU(file, x + block_size), 
                    LFile_DispUtoIntU(file, y_start + block_size));
                count++;
            }
            
            // ?? (80%)
            LLayer layer2 = EnsureLayer(file, "Dose080");
            if (layer2) {
                LBox_New(cell, layer2, 
                    LFile_DispUtoIntU(file, x + block_size + gaps[i]), 
                    LFile_DispUtoIntU(file, y_start), 
                    LFile_DispUtoIntU(file, x + 2*block_size + gaps[i]), 
                    LFile_DispUtoIntU(file, y_start + block_size));
                count++;
            }
        }
    }
    
    // ??: ???? (?????????)
    {
        double x_start = margin + half + gap;
        double y_start = margin + half + gap;
        double block_size = 1.8;
        double pair_gap = 0.1;
        
        LLayer layer30 = EnsureLayer(file, "Dose030");
        LLayer layer70 = EnsureLayer(file, "Dose070");
        
        if (layer30 && layer70) {
            // ????
            LBox_New(cell, layer30, 
                LFile_DispUtoIntU(file, x_start), 
                LFile_DispUtoIntU(file, y_start), 
                LFile_DispUtoIntU(file, x_start + block_size), 
                LFile_DispUtoIntU(file, y_start + block_size));
            LBox_New(cell, layer70, 
                LFile_DispUtoIntU(file, x_start + block_size + pair_gap), 
                LFile_DispUtoIntU(file, y_start), 
                LFile_DispUtoIntU(file, x_start + 2*block_size + pair_gap), 
                LFile_DispUtoIntU(file, y_start + block_size));
            count += 2;
            
            // ????
            double y_offset = block_size + pair_gap + 0.3;
            LBox_New(cell, layer30, 
                LFile_DispUtoIntU(file, x_start), 
                LFile_DispUtoIntU(file, y_start + y_offset), 
                LFile_DispUtoIntU(file, x_start + block_size), 
                LFile_DispUtoIntU(file, y_start + y_offset + block_size));
            LBox_New(cell, layer70, 
                LFile_DispUtoIntU(file, x_start), 
                LFile_DispUtoIntU(file, y_start + y_offset + block_size + pair_gap), 
                LFile_DispUtoIntU(file, x_start + block_size), 
                LFile_DispUtoIntU(file, y_start + y_offset + 2*block_size + pair_gap));
            count += 2;
            
            // ?????
            double x_offset = block_size + pair_gap + 0.3;
            LBox_New(cell, layer30, 
                LFile_DispUtoIntU(file, x_start + x_offset), 
                LFile_DispUtoIntU(file, y_start), 
                LFile_DispUtoIntU(file, x_start + x_offset + block_size), 
                LFile_DispUtoIntU(file, y_start + block_size));
            LBox_New(cell, layer70, 
                LFile_DispUtoIntU(file, x_start + x_offset + block_size + pair_gap), 
                LFile_DispUtoIntU(file, y_start + block_size + pair_gap), 
                LFile_DispUtoIntU(file, x_start + x_offset + 2*block_size + pair_gap), 
                LFile_DispUtoIntU(file, y_start + 2*block_size + pair_gap));
            count += 2;
        }
    }
    
    // ??: ?????? (21?)
    {
        double x_start = margin + half + gap;
        double y_start = margin;
        double step_width = half / 21;
        double step_height = half * 0.8;
        
        for (int i = 0; i <= 20; i++) {
            int dose = i * 5;
            char layerName[32];
            sprintf(layerName, "Dose%03d", dose);
            LLayer layer = EnsureLayer(file, layerName);
            if (!layer) continue;
            
            double x = x_start + i * step_width;
            LBox_New(cell, layer, 
                LFile_DispUtoIntU(file, x), 
                LFile_DispUtoIntU(file, y_start), 
                LFile_DispUtoIntU(file, x + step_width - 0.01), 
                LFile_DispUtoIntU(file, y_start + step_height));
            count++;
        }
    }
    
    return count;
}

extern "C" void AdjacencyComprehensive(void) {
    WriteReceipt("started", 0);
    int quiet = LUpi_InQuietMode();
    LUpi_SetQuietMode(1);
    
    LFile file = LFile_New(NULL, "AdjacencyComprehensive");
    LCell cell = LCell_New(file, "TOP");
    if (!file || !cell) {
        WriteReceipt("error", 0);
        LUpi_SetQuietMode(quiet);
        return;
    }
    LCell_MakeVisible(cell);
    
    int totalShapes = 0;
    totalShapes += DrawAlignmentMarks(cell, file);
    totalShapes += GenerateAdjacencyComprehensive(cell, file);
    
    LFile_SaveAs(file, "C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\Layout3_AdjacencyComprehensive", LTdbFile);
    LDisplay_Refresh();
    WriteReceipt("ok", totalShapes);
    LUpi_SetQuietMode(quiet);
}

extern "C" int UPI_Entry_Point(void) {
    LMacro_Register("Adjacency Comprehensive", "AdjacencyComprehensive");
    return 1;
}
