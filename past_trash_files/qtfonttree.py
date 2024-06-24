from PySide2 import QtCore, QtWidgets, QtGui

database = QtGui.QFontDatabase()
fontTree = QtWidgets.QTreeWidget()
fontTree.setColumnCount(2)
fontTree.setHeaderLabels(" Font << Smooth Sizes")

for family in database.families():

    familyItem = QtWidgets.QTreeWidgetItem(fontTree)
    familyItem.setText(0, family)
    print(familyItem)

    for style in database.styles(family):
        styleItem = QtWidgets.QTreeWidgetItem(familyItem)
        styleItem.setText(0, style)

        sizes = 0
        for points in database.smoothSizes(family, style):
            sizes += str(int(points)) + " "

        styleItem.setText(1, sizes)