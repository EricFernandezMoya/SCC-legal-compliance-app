import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

def create_db_server_connection():
    connection = None
    
    try:
        connection = mysql.connector.connect(
            host = os.getenv("MYSQL_HOST"),
            user = os.getenv("MYSQL_USER"),
            passwd = os.getenv("MYSQL_PW"), 
            database = os.getenv("MYSQL_DB")
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")

    return connection

def create_tables():

    connection = create_db_server_connection()

    try:
        db_cursor = connection.cursor()

        db_cursor.execute("CREATE TABLE categories (category_id INT AUTO_INCREMENT PRIMARY KEY, category_code VARCHAR(25) NOT NULL, category_name VARCHAR(255) NOT NULL);")
        db_cursor.execute("CREATE TABLE rules (rule_id INT AUTO_INCREMENT PRIMARY KEY, rule_name VARCHAR(255) NOT NULL, description TEXT, category_id INT NOT NULL, approved_by VARCHAR(255), approved_at DATETIME, FOREIGN KEY (category_id) REFERENCES categories(category_id));")
        db_cursor.execute("CREATE TABLE document_types (document_type_id INT AUTO_INCREMENT PRIMARY KEY, type_name VARCHAR(255) NOT NULL);")
        db_cursor.execute("CREATE TABLE documents (document_id INT AUTO_INCREMENT PRIMARY KEY, document_name VARCHAR(500) NOT NULL, jurisdiction VARCHAR(255), year INT, description TEXT, date_created DATETIME DEFAULT CURRENT_TIMESTAMP, date_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, document_type_id INT NOT NULL, FOREIGN KEY (document_type_id) REFERENCES document_types(document_type_id));")
        db_cursor.execute("CREATE TABLE document_versions (version_id INT AUTO_INCREMENT PRIMARY KEY, document_id INT NOT NULL, version_number VARCHAR(255), effective_from DATE, effective_to DATE, source_url VARCHAR(1000), file_path VARCHAR(255), notes TEXT, FOREIGN KEY (document_id) REFERENCES documents(document_id));")
        db_cursor.execute("CREATE TABLE rule_basis (rule_basis_id INT AUTO_INCREMENT PRIMARY KEY, rule_id INT NOT NULL, document_version_id INT NOT NULL, section_name VARCHAR(255), FOREIGN KEY (rule_id) REFERENCES rules(rule_id), FOREIGN KEY (document_version_id) REFERENCES document_versions(version_id));")
        db_cursor.execute("CREATE TABLE rules_snapshots (snapshot_id INT AUTO_INCREMENT PRIMARY KEY, label VARCHAR(255), approved_by VARCHAR(255), approved_at DATETIME DEFAULT CURRENT_TIMESTAMP, created_at DATETIME);")
        db_cursor.execute("CREATE TABLE contract_groups (group_id INT AUTO_INCREMENT PRIMARY KEY, group_name VARCHAR(255) NOT NULL, counterparty VARCHAR(255), contract_type VARCHAR(255), created_at DATETIME);")
        db_cursor.execute("CREATE TABLE contracts (contract_id INT AUTO_INCREMENT PRIMARY KEY, group_id INT NOT NULL, previous_version_id INT, contract_name VARCHAR(255), counterparty VARCHAR(255), version_number INT, file_path VARCHAR(255), uploaded_by VARCHAR(255), uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP, period_start DATE, period_end DATE, FOREIGN KEY (group_id) REFERENCES contract_groups(group_id), FOREIGN KEY (previous_version_id) REFERENCES contracts(contract_id));")
        db_cursor.execute("CREATE TABLE compliance_reports (report_id INT AUTO_INCREMENT PRIMARY KEY, contract_id INT NOT NULL, prior_report_id INT, snapshot_id INT NOT NULL, compliance_status VARCHAR(255), created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (contract_id) REFERENCES contracts(contract_id), FOREIGN KEY (prior_report_id) REFERENCES compliance_reports(report_id), FOREIGN KEY (snapshot_id) REFERENCES rules_snapshots(snapshot_id));")
        db_cursor.execute("CREATE TABLE risk_levels (risk_level_id INT AUTO_INCREMENT PRIMARY KEY, risk_name VARCHAR(255) NOT NULL, description TEXT);")
        db_cursor.execute("CREATE TABLE compliance_risks (risk_id INT AUTO_INCREMENT PRIMARY KEY, report_id INT NOT NULL, risk_level_id INT NOT NULL, rule_id INT NOT NULL, description TEXT, finding_text TEXT, FOREIGN KEY (report_id) REFERENCES compliance_reports(report_id), FOREIGN KEY (risk_level_id) REFERENCES risk_levels(risk_level_id), FOREIGN KEY (rule_id) REFERENCES rules(rule_id));")
        db_cursor.execute("CREATE TABLE snapshot_rules (rule_id INT NOT NULL, snapshot_id INT NOT NULL, PRIMARY KEY (rule_id, snapshot_id), FOREIGN KEY (rule_id) REFERENCES rules(rule_id), FOREIGN KEY (snapshot_id) REFERENCES rules_snapshots(snapshot_id));")
        db_cursor.execute("CREATE TABLE audit_logs (log_id INT AUTO_INCREMENT PRIMARY KEY, entity_type VARCHAR(255), entity_id INT, action VARCHAR(255), actor VARCHAR(255), timestamp_at DATETIME DEFAULT CURRENT_TIMESTAMP);")

        print("The tables has been created successfully")

        db_cursor.execute("SHOW TABLES")

        for x in db_cursor:
            print(x)

    except Error as err:
        print(f"Error: '{err}'")
    
create_tables()
