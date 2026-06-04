#include <stdio.h>
#include "ldata.h"

extern "C" void ViewHome(void) {
    // ????????
    LCell cell = LCell_GetVisible();
    if (cell) {
        // ?????????
        LCell_MakeVisible(cell);
        LDisplay_Refresh();
    }
}

extern "C" int UPI_Entry_Point(void) {
    LMacro_Register("View Home", "ViewHome");
    return 1;
}
