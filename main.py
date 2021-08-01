from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QFileDialog
from PyQt5 import QtWidgets
from pynput.mouse import Controller, Button
import sys, keyboard, pickle, os, sqlite3, gui, time
from shutil import copyfile

mouse = Controller()

try:
    loading = pickle.load(open('key.dat', 'rb'))
except:
    pickle.dump('F8', open('key.dat', 'wb'))


class Execution:
    def execute_macro(self):
        conn = sqlite3.connect('data.db')
        c = conn.cursor()

        c.execute("SELECT * FROM macros")
        row_amount = len(c.fetchall())

        conn.commit()
        c.execute("SELECT * FROM macros")
        for i in c.fetchall():
            click = i[0]
            x_mouse_position = i[1]
            y_mouse_position = i[2]
            delay = i[3]
            repeat = i[4]
            mouse.position = x_mouse_position, y_mouse_position
            mouse.click(Button.left, repeat)
            time.sleep(delay)

        conn.commit()
        conn.close()


class MainWindow(QMainWindow, Execution):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = gui.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setFixedSize(632, 605)
        self.ui.toolBar.close()
        self.row_num = 0
        self.ui.delay_input.setText('1')
        self.ui.repeat_count.setText('1')
        self.delete_database()
        self.load_file = False
        self.save_file = False
        self.updatable_location = ''
        self.loading_location = ''
        self.saving_location = ''
        self.setWindowTitle('Auto Mouse & Keyboard Clicker')
        # get the position from pickle

        get_position_key = pickle.load(open('key.dat', 'rb'))
        # Hotkeys
        try:
            keyboard.add_hotkey(get_position_key, lambda: self.show_coordinates())
        except ValueError:
            os.remove('key.dat')
            error_dialog = QtWidgets.QErrorMessage()
            error_dialog.showMessage('Value Error. The "Get Mouse Position" and "Execute Script" keys has been reset.')
            error_dialog.setWindowTitle('Error')
            app.exec_()
            pickle.dump('F8', open('key.dat', 'wb'))

        keyboard.add_hotkey(get_position_key, lambda: self.show_coordinates())

        # Connections

        self.ui.apply_position_shortcut.clicked.connect(lambda: self.assign_mouse_position_shortcut())
        self.ui.add_button.clicked.connect(lambda: self.add_item_table())
        self.ui.save_button.clicked.connect(lambda: self.save())
        self.ui.load_button.clicked.connect(lambda: self.load())
        self.ui.delete_button.setDisabled(True)
        self.ui.delete_all_button.clicked.connect(lambda: self.reset_table())
        self.ui.apply_execution_shortcut.clicked.connect(lambda: self.execute_macro())
        self.ui.save_button.clicked.connect(lambda: self.update())

    # Default is F8.
    # Assigning the new key to get mouse position shortcut
    def assign_mouse_position_shortcut(self):
        os.remove('key.dat')
        shortcut_input = self.ui.get_mouse_position_shortcut.text()
        pickle.dump(str(shortcut_input), open('key.dat', 'wb'))

    # input the coordinates to X-Coordinate and Y-Coordinate inputs
    def show_coordinates(self):
        position = mouse.position
        x_coordinate = position[0]
        y_coordinate = position[1]
        # show the coordinates
        self.ui.x_coordinate_input.setText(str(x_coordinate))
        self.ui.y_coordinate_input.setText(str(y_coordinate))

    def add_item_table(self):
        # Additions to the table - maximum number of additions: 9
        i = 0
        column = 0
        while i < 9:
            text = self.ui.macro_table.item(i, column)
            if text is not None and text.text() != '':
                i = i + 1
            else:
                self.row_num = i
                i = i + 10

        # Setting new data to the table
        self.ui.macro_table.setItem(self.row_num, 0, QTableWidgetItem(self.ui.combo_box.currentText()))
        self.ui.macro_table.setItem(self.row_num, 1, QTableWidgetItem(self.ui.x_coordinate_input.text()))
        self.ui.macro_table.setItem(self.row_num, 2, QTableWidgetItem(self.ui.y_coordinate_input.text()))
        self.ui.macro_table.setItem(self.row_num, 3, QTableWidgetItem(self.ui.delay_input.text()))
        self.ui.macro_table.setItem(self.row_num, 4, QTableWidgetItem(self.ui.repeat_count.text()))

        # Setting the data to the database
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute("INSERT INTO macros VALUES(?,?,?,?,?)", (
            self.ui.combo_box.currentText(), self.ui.x_coordinate_input.text(), self.ui.y_coordinate_input.text(),
            self.ui.delay_input.text(), self.ui.repeat_count.text()))
        conn.commit()
        conn.close()

    def delete_database(self):
        # Deleting database every time program opens
        conn = sqlite3.connect('data.db')
        conn.close()
        os.remove('data.db')
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute("""
            CREATE TABLE macros(
            click text,
            xposition integer,
            yposition integer,
            delay integer,
            repeat integer
            )            
        """)
        conn.commit()
        conn.close()

    # Save As the Database
    def save(self):
        option = QFileDialog.Options()
        new_location = QFileDialog.getSaveFileName(widget, 'Save As...', 'macro', "All Files (*)", options=option)
        self.saving_location = new_location[0]
        if self.saving_location != '':
            self.save_file = True
            self.ui.save_button.setDisabled(True)
            old_location = os.path.dirname(os.path.realpath(__file__)) + '\data.db'
            copyfile(old_location, new_location[0])
            if ".db" not in new_location[0]:
                os.rename(new_location[0], new_location[0] + '.db')
                self.updatable_location = new_location[0] + '.db'
            else:
                self.updatable_location = new_location[0]

    # Load the database
    def load(self):
        # open file dialog
        option = QFileDialog.Options()
        location = QFileDialog.getOpenFileName(widget, 'Load', '', 'All Files(*)', options=option)
        # if a file is loaded, self.load_file = True, thus activating the load database function
        self.loading_location = location[0]
        if self.loading_location != '':
            self.load_file = True
            self.updatable_location = self.loading_location
            self.load_database()
    # for the save button - saves the changes made to the file
    def update(self):
        conn = sqlite3.connect('data.db')
        conn2 = sqlite3.connect(self.updatable_location)
        c = conn.cursor()
        d = conn2.cursor()
        c.execute("SELECT * FROM macros")
        output = c.fetchall()
        conn.close()
        d.execute("DELETE FROM macros")
        conn2.commit()
        for row in output:
            print(row)
            d.execute("INSERT INTO macros VALUES(?,?,?,?,?)", (row[0],row[1],row[2],row[3],row[4]))
        conn2.commit()
        d.execute("SELECT * FROM macros")
        print(d.fetchall())

        conn2.commit()
        conn2.close()

    def load_database(self):
        conn = sqlite3.connect(self.loading_location)
        c = conn.cursor()

        total_loaded = 0

        # Getting the number of rows from the table macros in order to determine how many times to run the for loop
        c.execute("SELECT * FROM macros")
        rows = len(c.fetchall())

        for i in range(rows):
            c.execute("SELECT * FROM macros")
            self.ui.macro_table.setItem(i, 0, QTableWidgetItem(c.fetchall()[i][0]))
            c.execute("SELECT * FROM macros")
            self.ui.macro_table.setItem(i, 1, QTableWidgetItem(str(c.fetchall()[i][1])))
            c.execute("SELECT * FROM macros")
            self.ui.macro_table.setItem(i, 2, QTableWidgetItem(str(c.fetchall()[i][2])))
            c.execute("SELECT * FROM macros")
            self.ui.macro_table.setItem(i, 3, QTableWidgetItem(str(c.fetchall()[i][3])))
            c.execute("SELECT * FROM macros")
            self.ui.macro_table.setItem(i, 4, QTableWidgetItem(str(c.fetchall()[i][4])))
            total_loaded += 1

        conn.commit()
        conn.close()

        conn = sqlite3.connect('data.db')
        d = conn.cursor()
        i = 0
        for i in range(total_loaded):
            d.execute("INSERT INTO macros VALUES(?,?,?,?,?)", (
                self.ui.macro_table.item(i, 0).text(), self.ui.macro_table.item(i, 1).text(),
                self.ui.macro_table.item(i, 2).text(), self.ui.macro_table.item(i, 3).text(),
                self.ui.macro_table.item(i, 4).text()))
        conn.commit()
        conn.close()

    # TEST METHOD - TO BE DELETED
    def get_database(self):
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute("SELECT * FROM macros")
        for i in c.fetchall():
            print(i[0])
        conn.commit()
        conn.close()
        self.execute_macro()

    def delete_item_from_table(self):
        pass

    # Deletes everything from the database and the table
    def reset_table(self):
        # Deleting and creating a new database
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute("DELETE FROM macros")
        conn.commit()
        conn.close()

        # Deleting items from the table
        i = 0
        while i < 9:
            self.ui.macro_table.setItem(i, 0, QTableWidgetItem(''))
            self.ui.macro_table.setItem(i, 1, QTableWidgetItem(''))
            self.ui.macro_table.setItem(i, 2, QTableWidgetItem(''))
            self.ui.macro_table.setItem(i, 3, QTableWidgetItem(''))
            self.ui.macro_table.setItem(i, 4, QTableWidgetItem(''))
            i = i + 1


if __name__ == '__main__':
    app = QApplication(sys.argv)

    widget = MainWindow()
    widget.show()

    sys.exit(app.exec_())
