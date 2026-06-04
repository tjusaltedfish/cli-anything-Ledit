#include <stdio.h>
#include "ldata.h"

extern "C" void OpenAllLayouts(void) {
    // ????1
    LFile file1 = LFile_Open("C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\Layout1_DoseCalibration", LTdbFile);
    if (file1) {
        // ???????????
        LCell cell1 = LCell_Find(file1, "TOP");
        if (cell1) LCell_MakeVisible(cell1);
    }
    
    // ????2
    LFile file2 = LFile_Open("C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\Layout2_Discretization", LTdbFile);
    if (file2) {
        LCell cell2 = LCell_Find(file2, "TOP");
        if (cell2) LCell_MakeVisible(cell2);
    }
    
    // ????3
    LFile file3 = LFile_Open("C:\\Users\\ASUS\\Documents\\L_edit\\agent-harness\\grayscale_test\\Layout3_Adjacency", LTdbFile);
    if (file3) {
        LCell cell3 = LCell_Find(file3, "TOP");
        if (cell3) LCell_MakeVisible(cell3);
    }
    
    LDisplay_Refresh();
}

extern "C" int UPI_Entry_Point(void) {
    LMacro_Register("Open All Layouts", "OpenAllLayouts");
    return 1;
}
