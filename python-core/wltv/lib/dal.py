import sqlite3
import os
import xbmc  # Import xbmc if you are in a Kodi addon

class DAL:
    """
    Data Access Layer class for managing SQLite database interactions.
    """
    def __init__(self, db_path=None, addon_id=None, db_file_name=None):
        """
        Initializes the DAL object. Supports two ways to specify the database:
        1. Provide 'db_path' directly (full path to the database file).
        2. Provide 'addon_id' and 'db_file_name' to construct the path within Kodi's addon data directory.

        Args:
            db_path (str, optional): The full path to the database file. Defaults to None.
            addon_id (str, optional): The ID of the Kodi addon. Required if 'db_path' is None. Defaults to None.
            db_file_name (str, optional): The name of the database file. Required if 'db_path' is None. Defaults to None.
        """
        self.db_file = None
        self.conn = None

        if db_path:
            self.db_file = db_path
        elif addon_id and db_file_name:
            self.addon_id = addon_id
            self.addon_path = xbmc.translatePath(os.path.join('special://userdata/addon_data/', self.addon_id))
            if not os.path.exists(self.addon_path):
                os.makedirs(self.addon_path)
            self.db_file = os.path.join(self.addon_path, db_file_name)
        else:
            raise ValueError("Either 'db_path' or both 'addon_id' and 'db_file_name' must be provided.")

    def connect(self):
        """
        Connects to the SQLite database.

        Returns:
            bool: True if the connection was successful, False otherwise.
        """
        try:
            self.conn = sqlite3.connect(self.db_file)
            return True
        except sqlite3.Error as e:
            print(f"Error connecting to the database at '{self.db_file}': {e}")
            self.conn = None
            return False

    def close(self):
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()
            self.conn = None

    def delete(self, table_name, condition=None):
        """
        Deletes records from a table.

        Args:
            table_name (str): The name of the table.
            condition (str, optional): The WHERE clause for the DELETE statement. Defaults to None.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        cursor = self.conn.cursor()
        sql = f"DELETE FROM {table_name}"
        if condition:
            sql += f" WHERE {condition}"
        try:
            cursor.execute(sql)
            self.conn.commit()
            print(f"Records deleted from table '{table_name}'.")
            if condition:
                print(f"Condition: {condition}")
            return True
        except sqlite3.Error as e:
            print(f"Error deleting from table '{table_name}': {e}")
            return False

    def update(self, table_name, set_values, condition=None):
        """
        Updates records in a table.

        Args:
            table_name (str): The name of the table.
            set_values (str): The SET clause for the UPDATE statement (e.g., "column1 = 'new_value', column2 = 123").
            condition (str, optional): The WHERE clause for the UPDATE statement. Defaults to None.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        cursor = self.conn.cursor()
        sql = f"UPDATE {table_name} SET {set_values}"
        if condition:
            sql += f" WHERE {condition}"
        try:
            cursor.execute(sql)
            self.conn.commit()
            print(f"Records updated in table '{table_name}'.")
            print(f"Setting: {set_values}")
            if condition:
                print(f"Condition: {condition}")
            return True
        except sqlite3.Error as e:
            print(f"Error updating table '{table_name}': {e}")
            return False

    def select(self, table_name, columns='*', condition=None, order_by=None, limit=None):
        """
        Executes a SELECT query and returns the results.

        Args:
            table_name (str): The name of the table.
            columns (str, optional): The columns to select (e.g., 'id, name'). Defaults to '*'.
            condition (str, optional): The WHERE clause for the SELECT statement. Defaults to None.
            order_by (str, optional): The ORDER BY clause for the SELECT statement. Defaults to None.
            limit (int, optional): The LIMIT clause for the SELECT statement. Defaults to None.

        Returns:
            list: A list of tuples representing the fetched rows, or None if an error occurred.
        """
        cursor = self.conn.cursor()
        sql = f"SELECT {columns} FROM {table_name}"
        if condition:
            sql += f" WHERE {condition}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit:
            sql += f" LIMIT {limit}"

        try:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return rows
        except sqlite3.Error as e:
            print(f"Error selecting from table '{table_name}': {e}")
            return None

# deleted = db.delete('my_table', condition="name = 'item_to_delete'")
# if deleted:
#     print("Items deleted successfully.")

# # Example of update
# updated = db.update('my_table', "value = value + 1", condition="id = 1")
# if updated:
#     print("Items updated successfully.")

# # Example of fetch after operations
# updated_data = db.fetch('my_table')
# if updated_data is not None:
#     print("\nData after delete and update operations:")
#     for row in updated_data:
#     print(row)