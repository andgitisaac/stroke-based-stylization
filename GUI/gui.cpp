#include "gui.h"
#include "ui_gui.h"

GUI::GUI(QWidget *parent) :
    QDialog(parent),
    ui(new Ui::GUI)
{
    ui->setupUi(this);
}

GUI::~GUI()
{
    delete ui;
}
