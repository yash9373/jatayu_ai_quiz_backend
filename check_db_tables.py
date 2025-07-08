import sqlite3
import os

# Check if database exists
if os.path.exists('recruitment.db'):
    print('Database file exists')
    print(f'Database file size: {os.path.getsize("recruitment.db")} bytes')
else:
    print('Database file does not exist')

conn = sqlite3.connect('recruitment.db')
cursor = conn.cursor()

print('\nAll tables in database:')
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
if tables:
    for table in tables:
        print(f'Table: {table[0]}')
else:
    print('No tables found in database')

# Check each possible table name
table_names = ['users', 'user', 'tests', 'test']
for table_name in table_names:
    try:
        cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
        count = cursor.fetchone()[0]
        print(f'\n{table_name} table exists with {count} records')
        
        if table_name in ['users', 'user']:
            cursor.execute(f'SELECT * FROM {table_name} LIMIT 5')
            rows = cursor.fetchall()
            print(f'Sample data from {table_name}:')
            for row in rows:
                print(row)
        elif table_name in ['tests', 'test']:
            cursor.execute(f'SELECT * FROM {table_name} LIMIT 5')
            rows = cursor.fetchall()
            print(f'Sample data from {table_name}:')
            for row in rows:
                print(row)
                
    except sqlite3.OperationalError as e:
        print(f'{table_name} table does not exist: {e}')

conn.close()
