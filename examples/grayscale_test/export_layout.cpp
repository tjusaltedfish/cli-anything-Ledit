#include <stdio.h>
#include "ldata.h"

static void WriteReceipt(const char* status, const char* msg) {
    FILE* f = fopen("C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\export_receipt.txt", "w");
    if (f) {
        fprintf(f, "status=%s\nmessage=%s\n", status, msg);
        fclose(f);
    }
}

extern "C" void ExportLayout(void) {
    WriteReceipt("started", "Opening layout file...");
    
    // ??????????????
    LFile file = LFile_Open("C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\Layout1_DoseCalibration64.tdb", LTdbFile);
    if (!file) {
        WriteReceipt("error", "Failed to open layout file");
        return;
    }
    
    // ??????
    LCell cell = LCell_Find(file, "TOP");
    if (!cell) {
        WriteReceipt("error", "Failed to find TOP cell");
        return;
    }
    LCell_MakeVisible(cell);
    
    // ??? CIF ??
    WriteReceipt("progress", "Exporting to CIF format...");
    LStatus status1 = LFile_SaveAs(file, "C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\Layout1_DoseCalibration64", LCifFile);
    if (status1 == LStatusOK) {
        WriteReceipt("ok", "CIF exported successfully. Please manually export BMP from L-Edit: File -> Export -> Bitmap");
    } else {
        WriteReceipt("error", "CIF export failed");
    }
    
    LDisplay_Refresh();
}

extern "C" int UPI_Entry_Point(void) {
    LMacro_Register("Export Layout", "ExportLayout");
    return 1;
}
