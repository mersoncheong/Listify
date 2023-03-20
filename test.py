import sqlalchemy

def generate_insert_table_statement(insertion):
        # ? Fetching table name and the rows/tuples body object from the request
        table_name = insertion["name"]
        body = insertion["body"]
        # valueTypes = insertion["valueTypes"]

        # ? Generating the default insert statement template
        statement = f"INSERT INTO {table_name}  "

        # ? Appending the entries with their corresponding columns
        column_names = "("
        column_values = "("
        for key, value in body.items():
            column_names += (key+",")
            # if valueTypes[key] == "TEXT" or valueTypes[key] == "TIME":
            #     column_values += (f"\'{value}\',")
            # else:
            column_values += (f"'{value}',")

        # ? Removing the last default comma
        column_names = column_names[:-1]+")"
        column_values = column_values[:-1]+")"

        # ? Combining it all into one statement and returning
        #! You may try to expand it to multiple tuple insertion in another method
        statement = statement + column_names+" VALUES "+ column_values+";"
        return sqlalchemy.text(statement)




data = {
        "name" : "registered",
        "body" : {
        "username": "username",
        "email": "email",
        "password": "password"
        }
    }

generate_insert_table_statement(data)


