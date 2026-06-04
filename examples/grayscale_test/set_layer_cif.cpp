#include <stdio.h>
#include <string.h>
#include "ldata.h"

static void WriteReceipt(const char* status, const char* msg) {
    FILE* f = fopen("C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\set_layer_cif_receipt.txt", "w");
    if (f) {
        fprintf(f, "status=%s\nmessage=%s\n", status, msg);
        fclose(f);
    }
}

extern "C" void SetLayerCifNames(void) {
    WriteReceipt("started", "Opening file and setting CIF names...");
    
    // ????
    LFile file = LFile_Open("C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\Layout1_DoseCalibration64.tdb", LTdbFile);
    if (!file) {
        WriteReceipt("error", "Failed to open file");
        return;
    }
    
    // ????
    LCell cell = LCell_Find(file, "TOP");
    if (!cell) {
        WriteReceipt("error", "Failed to find TOP cell");
        return;
    }
    LCell_MakeVisible(cell);
    
    int count = 0;
    
    // ?? Alignment ?? CIF ??
    LLayer alignLayer = LLayer_Find(file, "Alignment");
    if (alignLayer) {
        LLayerParamEx1512 param;
        LLayer_GetParametersEx1512(alignLayer, &param);
        strcpy(param.CIFName, "AL");
        LLayer_SetParametersEx1512(alignLayer, &param);
        count++;
    }
    
    // ?? Dose00-Dose63 ?? CIF ??
    for (int i = 0; i < 64; i++) {
        char layerName[32];
        char cifName[32];
        sprintf(layerName, "Dose%02d", i);
        sprintf(cifName, "D%02d", i);
        
        LLayer layer = LLayer_Find(file, layerName);
        if (layer) {
            LLayerParamEx1512 param;
            LLayer_GetParametersEx1512(layer, &param);
            strcpy(param.CIFName, cifName);
            LLayer_SetParametersEx1512(layer, &param);
            count++;
        }
    }
    
    // ????
    LFile_Save(file);
    
    LDisplay_Refresh();
    
    char msg[256];
    sprintf(msg, "CIF names set for %d layers", count);
    WriteReceipt("ok", msg);
}

extern "C" int UPI_Entry_Point(void) {
    LMacro_Register("Set Layer CIF Names", "SetLayerCifNames");
    return 1;
}
