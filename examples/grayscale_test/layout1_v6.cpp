#include <stdio.h>
#include "ldata.h"

#define TOTAL_SIZE_MM 15.0
#define NUM_DOSE_LEVELS 64

// ============================================================
// ???????????????????
// ============================================================
// 1. ?????????????? [x1, y1, x2, y2]
// 2. ??????????? 0.1mm ???
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
    FILE* f = fopen("C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\layout1_v6_receipt.txt", "w");
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

// ??1 v6: 64????????????????????
// ?????
// - 64?dose???8??8???
// - ???????1.2mm?1.2mm
// - ???????5???????10mm/20, 30, 40, 50, 60?
// - ??????2???10???
// - ???????????
static int GenerateDoseCalibration(LCell cell, LFile file) {
    int count = 0;
    
    // ????
    double margin = 1.5;
    double usable = TOTAL_SIZE_MM - 2 * margin;  // 12.0
    double gap = 0.1;  // ????
    int grid = 8;  // 8?8 = 64???
    
    // ??????
    double region_size = (usable - (grid - 1) * gap) / grid;  // ?1.4125mm
    
    // ???????10mm??20?30?40?50?60?
    double block_sizes[] = {10.0/20, 10.0/30, 10.0/40, 10.0/50, 10.0/60};  // 0.5, 0.333, 0.25, 0.2, 0.167mm
    int num_block_sizes = 5;
    int repeats_per_size = 2;  // ??????2?
    
    // ??????
    double grid_width = grid * region_size + (grid - 1) * gap;
    double grid_height = grid * region_size + (grid - 1) * gap;
    double x_origin = margin + (usable - grid_width) / 2;
    double y_origin = margin + (usable - grid_height) / 2;
    
    // ??????
    if (x_origin < margin || y_origin < margin || 
        x_origin + grid_width > TOTAL_SIZE_MM - margin || 
        y_origin + grid_height > TOTAL_SIZE_MM - margin) {
        WriteReceipt("error", 0);
        return 0;
    }
    
    // ??64?dose??
    for (int row = 0; row < grid; row++) {
        for (int col = 0; col < grid; col++) {
            int dose_index = row * grid + col;  // 0-63
            
            // ??????
            double region_x1 = x_origin + col * (region_size + gap);
            double region_y1 = y_origin + row * (region_size + gap);
            double region_x2 = region_x1 + region_size;
            double region_y2 = region_y1 + region_size;
            
            // ????
            char layerName[32];
            sprintf(layerName, "Dose%02d", dose_index);
            LLayer layer = EnsureLayer(file, layerName);
            if (!layer) continue;
            
            // ?????????????
            // ????????????2?
            int blocks_per_row = 5;  // ??5????5????
            int total_blocks = num_block_sizes * repeats_per_size;  // 10???
            int rows_needed = (total_blocks + blocks_per_row - 1) / blocks_per_row;  // 2?
            
            // ?????????????
            double inner_margin = 0.05;  // ?????
            double inner_width = region_size - 2 * inner_margin;
            double inner_height = region_size - 2 * inner_margin;
            
            // ??????
            double block_gap = 0.02;  // ????20?m
            
            // ?????????????
            double max_block_width = (inner_width - (blocks_per_row - 1) * block_gap) / blocks_per_row;
            double max_block_height = (inner_height - (rows_needed - 1) * block_gap) / rows_needed;
            
            // ????
            int block_index = 0;
            for (int r = 0; r < rows_needed && block_index < total_blocks; r++) {
                for (int c = 0; c < blocks_per_row && block_index < total_blocks; c++) {
                    // ??????
                    int size_index = block_index % num_block_sizes;
                    double block_size = block_sizes[size_index];
                    
                    // ????????????
                    double block_x1 = region_x1 + inner_margin + c * (max_block_width + block_gap) + (max_block_width - block_size) / 2;
                    double block_y1 = region_y1 + inner_margin + r * (max_block_height + block_gap) + (max_block_height - block_size) / 2;
                    double block_x2 = block_x1 + block_size;
                    double block_y2 = block_y1 + block_size;
                    
                    // ??????????
                    if (block_x1 >= region_x1 && block_x2 <= region_x2 &&
                        block_y1 >= region_y1 && block_y2 <= region_y2) {
                        LBox_New(cell, layer, 
                            LFile_DispUtoIntU(file, block_x1), 
                            LFile_DispUtoIntU(file, block_y1), 
                            LFile_DispUtoIntU(file, block_x2), 
                            LFile_DispUtoIntU(file, block_y2));
                        count++;
                    }
                    
                    block_index++;
                }
            }
        }
    }
    
    return count;
}

extern "C" void DoseCalibration64(void) {
    WriteReceipt("started", 0);
    int quiet = LUpi_InQuietMode();
    LUpi_SetQuietMode(1);
    
    LFile file = LFile_New(NULL, "DoseCalibration64");
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
    
    LFile_SaveAs(file, "C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\Layout1_DoseCalibration64", LTdbFile);
    LDisplay_Refresh();
    WriteReceipt("ok", totalShapes);
    LUpi_SetQuietMode(quiet);
}

extern "C" int UPI_Entry_Point(void) {
    LMacro_Register("Dose Calibration 64", "DoseCalibration64");
    return 1;
}
