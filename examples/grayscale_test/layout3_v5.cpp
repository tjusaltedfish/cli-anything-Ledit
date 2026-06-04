#include <stdio.h>
#include "ldata.h"

#define TOTAL_SIZE_MM 15.0

// ============================================================
// ???????????????????
// ============================================================
// 1. ?????????????? [x1, y1, x2, y2]
// 2. ??????????? 0.2mm ???
// 3. ??????????????????
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
    FILE* f = fopen("C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\layout3_v5_receipt.txt", "w");
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

// ??3 v5: ?????????
// ??: 2x2?????????????
// ??: ?????? (10% vs 90%)
// ??: ???? (0.1mm??)
// ??: ???? (????)
// ??: ???? (21?)
static int GenerateAdjacencyComprehensive(LCell cell, LFile file) {
    int count = 0;
    
    // ????
    double margin = 1.5;
    double usable = TOTAL_SIZE_MM - 2 * margin;  // 12.0
    double half = usable / 2;  // 6.0
    double gap = 0.3;  // ????
    
    // ????????????
    // ????: [margin, margin+half+gap] ? [margin+half, margin+usable]
    double region1_x1 = margin;
    double region1_y1 = margin + half + gap;
    double region1_x2 = margin + half;
    double region1_y2 = margin + usable;
    
    // ????: [margin, margin] ? [margin+half, margin+half]
    double region2_x1 = margin;
    double region2_y1 = margin;
    double region2_x2 = margin + half;
    double region2_y2 = margin + half;
    
    // ????: [margin+half+gap, margin+half+gap] ? [margin+usable, margin+usable]
    double region3_x1 = margin + half + gap;
    double region3_y1 = margin + half + gap;
    double region3_x2 = margin + usable;
    double region3_y2 = margin + usable;
    
    // ????: [margin+half+gap, margin] ? [margin+usable, margin+half]
    double region4_x1 = margin + half + gap;
    double region4_y1 = margin;
    double region4_x2 = margin + usable;
    double region4_y2 = margin + half;
    
    // ??????
    if (region1_x1 < margin || region1_y1 < margin || region1_x2 > TOTAL_SIZE_MM - margin || region1_y2 > TOTAL_SIZE_MM - margin ||
        region2_x1 < margin || region2_y1 < margin || region2_x2 > TOTAL_SIZE_MM - margin || region2_y2 > TOTAL_SIZE_MM - margin ||
        region3_x1 < margin || region3_y1 < margin || region3_x2 > TOTAL_SIZE_MM - margin || region3_y2 > TOTAL_SIZE_MM - margin ||
        region4_x1 < margin || region4_y1 < margin || region4_x2 > TOTAL_SIZE_MM - margin || region4_y2 > TOTAL_SIZE_MM - margin) {
        WriteReceipt("error", 0);
        return 0;
    }
    
    // ??1: ?????? (10% vs 90%)
    {
        double block_size = 2.0;
        double pair_gap = 0.1;
        double region_width = region1_x2 - region1_x1;  // 6.0
        double region_height = region1_y2 - region1_y1;  // 5.7
        
        // ???????????????
        double x_start = region1_x1 + (region_width - 2*block_size - pair_gap) / 2;
        double y_start = region1_y1 + (region_height - block_size) / 2;
        
        // ??????????
        if (x_start >= region1_x1 && x_start + 2*block_size + pair_gap <= region1_x2 &&
            y_start >= region1_y1 && y_start + block_size <= region1_y2) {
            // ?? (10%)
            LLayer layer1 = EnsureLayer(file, "Dose010");
            if (layer1) {
                LBox_New(cell, layer1, 
                    LFile_DispUtoIntU(file, x_start), 
                    LFile_DispUtoIntU(file, y_start), 
                    LFile_DispUtoIntU(file, x_start + block_size), 
                    LFile_DispUtoIntU(file, y_start + block_size));
                count++;
            }
            
            // ?? (90%)
            LLayer layer2 = EnsureLayer(file, "Dose090");
            if (layer2) {
                LBox_New(cell, layer2, 
                    LFile_DispUtoIntU(file, x_start + block_size + pair_gap), 
                    LFile_DispUtoIntU(file, y_start), 
                    LFile_DispUtoIntU(file, x_start + 2*block_size + pair_gap), 
                    LFile_DispUtoIntU(file, y_start + block_size));
                count++;
            }
        }
    }
    
    // ??2: ???? (0.1mm??)
    {
        double block_size = 2.0;
        double pair_gap = 0.1;
        double region_width = region2_x2 - region2_x1;  // 6.0
        double region_height = region2_y2 - region2_y1;  // 6.0
        
        // ???????????????
        double x_start = region2_x1 + (region_width - 2*block_size - pair_gap) / 2;
        double y_start = region2_y1 + (region_height - block_size) / 2;
        
        // ??????????
        if (x_start >= region2_x1 && x_start + 2*block_size + pair_gap <= region2_x2 &&
            y_start >= region2_y1 && y_start + block_size <= region2_y2) {
            // ?? (20%)
            LLayer layer1 = EnsureLayer(file, "Dose020");
            if (layer1) {
                LBox_New(cell, layer1, 
                    LFile_DispUtoIntU(file, x_start), 
                    LFile_DispUtoIntU(file, y_start), 
                    LFile_DispUtoIntU(file, x_start + block_size), 
                    LFile_DispUtoIntU(file, y_start + block_size));
                count++;
            }
            
            // ?? (80%)
            LLayer layer2 = EnsureLayer(file, "Dose080");
            if (layer2) {
                LBox_New(cell, layer2, 
                    LFile_DispUtoIntU(file, x_start + block_size + pair_gap), 
                    LFile_DispUtoIntU(file, y_start), 
                    LFile_DispUtoIntU(file, x_start + 2*block_size + pair_gap), 
                    LFile_DispUtoIntU(file, y_start + block_size));
                count++;
            }
        }
    }
    
    // ??3: ???? (????)
    {
        double block_size = 2.0;
        double pair_gap = 0.1;
        double region_width = region3_x2 - region3_x1;  // 5.7
        double region_height = region3_y2 - region3_y1;  // 5.7
        
        // ???????????????
        double x_start = region3_x1 + (region_width - 2*block_size - pair_gap) / 2;
        double y_start = region3_y1 + (region_height - block_size) / 2;
        
        // ??????????
        if (x_start >= region3_x1 && x_start + 2*block_size + pair_gap <= region3_x2 &&
            y_start >= region3_y1 && y_start + block_size <= region3_y2) {
            LLayer layer30 = EnsureLayer(file, "Dose030");
            LLayer layer70 = EnsureLayer(file, "Dose070");
            
            if (layer30 && layer70) {
                // ?? (30%)
                LBox_New(cell, layer30, 
                    LFile_DispUtoIntU(file, x_start), 
                    LFile_DispUtoIntU(file, y_start), 
                    LFile_DispUtoIntU(file, x_start + block_size), 
                    LFile_DispUtoIntU(file, y_start + block_size));
                count++;
                
                // ?? (70%)
                LBox_New(cell, layer70, 
                    LFile_DispUtoIntU(file, x_start + block_size + pair_gap), 
                    LFile_DispUtoIntU(file, y_start), 
                    LFile_DispUtoIntU(file, x_start + 2*block_size + pair_gap), 
                    LFile_DispUtoIntU(file, y_start + block_size));
                count++;
            }
        }
    }
    
    // ??4: ?????? (21?)
    {
        double region_width = region4_x2 - region4_x1;  // 5.7
        double region_height = region4_y2 - region4_y1;  // 6.0
        double step_width = region_width / 21;
        double step_height = region_height * 0.8;
        double y_start = region4_y1 + (region_height - step_height) / 2;
        
        for (int i = 0; i <= 20; i++) {
            int dose = i * 5;
            char layerName[32];
            sprintf(layerName, "Dose%03d", dose);
            LLayer layer = EnsureLayer(file, layerName);
            if (!layer) continue;
            
            double x = region4_x1 + i * step_width;
            
            // ??????????
            if (x >= region4_x1 && x + step_width - 0.01 <= region4_x2 &&
                y_start >= region4_y1 && y_start + step_height <= region4_y2) {
                LBox_New(cell, layer, 
                    LFile_DispUtoIntU(file, x), 
                    LFile_DispUtoIntU(file, y_start), 
                    LFile_DispUtoIntU(file, x + step_width - 0.01), 
                    LFile_DispUtoIntU(file, y_start + step_height));
                count++;
            }
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
