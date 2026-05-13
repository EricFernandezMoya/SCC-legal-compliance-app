import mysql.connector
from mysql.connector import Error
from pathlib import Path
from dotenv import load_dotenv
import os

def create_db_server_connection():
    connection = None

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

    try:
        connection = mysql.connector.connect(
            host = os.getenv("MYSQL_HOST"),
            user = os.getenv("MYSQL_USER"),
            passwd = os.getenv("MYSQL_PW"),
            database = os.getenv("MYSQL_DB"),
            port = int(os.getenv("MYSQL_PORT", 3306))
        )
       
    except Error as err:
        print(f"Error: '{err}'")

    return connection

def create_tables():

    connection = create_db_server_connection()

    try:
        db_cursor = connection.cursor()

        db_cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS privileges (
                privilege_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE
            );
            '''
        )

        db_cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY, 
                user_name VARCHAR(100) NOT NULL UNIQUE, 
                full_name VARCHAR(255), 
                password VARCHAR(255) NOT NULL, 
                privilege INT NOT NULL,
                FOREIGN KEY (privilege) REFERENCES privileges(privilege_id)
            );
            '''
        )

        db_cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS categories (
                category_id INT AUTO_INCREMENT PRIMARY KEY, 
                category_code VARCHAR(25) NOT NULL UNIQUE, 
                category_name VARCHAR(255) NOT NULL UNIQUE
            );
            '''
        )
        
        db_cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS rules (
                rule_id INT AUTO_INCREMENT PRIMARY KEY, 
                rule_name VARCHAR(255) NOT NULL UNIQUE, 
                rule_code VARCHAR(255) NOT NULL UNIQUE, 
                description TEXT, 
                category INT NOT NULL, 
                approved_by INT NOT NULL, 
                approved_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
                rule_metadata JSON,
                FOREIGN KEY (category) REFERENCES categories(category_id),
                FOREIGN KEY (approved_by) REFERENCES users(user_id)
            );
            '''
        )
        
        db_cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS document_types (
                document_type_id INT AUTO_INCREMENT PRIMARY KEY,
                type_name VARCHAR(255) NOT NULL UNIQUE
            );
            '''
        )
        
        db_cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS documents (
                document_id INT AUTO_INCREMENT PRIMARY KEY, 
                document_name VARCHAR(500) NOT NULL UNIQUE, 
                jurisdiction VARCHAR(255), 
                year INT, 
                description TEXT, 
                date_created DATETIME DEFAULT CURRENT_TIMESTAMP, 
                date_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, 
                document_type INT NOT NULL, 
                FOREIGN KEY (document_type) REFERENCES document_types(document_type_id)
            );
            '''
        )
        
        db_cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS document_versions (
                version_id INT AUTO_INCREMENT PRIMARY KEY, 
                document INT NOT NULL, 
                version_number VARCHAR(255), 
                effective_from DATE, 
                effective_to DATE, 
                source_url VARCHAR(1000), 
                file_path VARCHAR(255), 
                notes TEXT, 
                FOREIGN KEY (document) REFERENCES documents(document_id)
            );
            '''
        )
        
        db_cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS rule_basis (
                rule_basis_id INT AUTO_INCREMENT PRIMARY KEY, 
                rule INT NOT NULL, 
                document_version INT NOT NULL, 
                section_name VARCHAR(255), 
                FOREIGN KEY (rule) REFERENCES rules(rule_id), 
                FOREIGN KEY (document_version) REFERENCES document_versions(version_id)
            );
            '''
        )
        
        db_cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS rules_snapshots (
                snapshot_id INT AUTO_INCREMENT PRIMARY KEY, 
                label VARCHAR(255) NOT NULL UNIQUE, 
                approved_by INT NOT NULL, 
                approved_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
                created_at DATETIME,
                FOREIGN KEY (approved_by) REFERENCES users(user_id)
            );
            '''
        )
        
        db_cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS contract_groups (
                group_id INT AUTO_INCREMENT PRIMARY KEY, 
                group_name VARCHAR(255) NOT NULL UNIQUE, 
                contact_details VARCHAR(255), 
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            '''
        )

        db_cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS contract_types (
                contract_type_id INT AUTO_INCREMENT PRIMARY KEY,
                type_name VARCHAR(255) NOT NULL UNIQUE
            );
            '''
        )
        
        db_cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS contracts (
                contract_id INT AUTO_INCREMENT PRIMARY KEY, 
                contract_group INT NOT NULL, 
                previous_version INT, 
                contract_name VARCHAR(255), 
                contract_type INT NOT NULL, 
                version_number INT, 
                file_path VARCHAR(255), 
                source_url VARCHAR(255),
                uploaded_by INT NOT NULL, 
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
                period_start DATE, 
                period_end DATE, 
                FOREIGN KEY (contract_group) REFERENCES contract_groups(group_id), 
                FOREIGN KEY (previous_version) REFERENCES contracts(contract_id),
                FOREIGN KEY (uploaded_by) REFERENCES users(user_id),
                FOREIGN KEY (contract_type) REFERENCES contract_types(contract_type_id)
            );
            '''
        )
        
        db_cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS compliance_reports (
                report_id INT AUTO_INCREMENT PRIMARY KEY,
                contract INT NOT NULL,
                prior_report INT,
                snapshot INT NOT NULL,
                compliance_status VARCHAR(255),
                failed_urls TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contract) REFERENCES contracts(contract_id),
                FOREIGN KEY (prior_report) REFERENCES compliance_reports(report_id),
                FOREIGN KEY (snapshot) REFERENCES rules_snapshots(snapshot_id)
            );
            '''
        )

        try:
            db_cursor.execute(
                "ALTER TABLE compliance_reports ADD COLUMN failed_urls TEXT"
            )
            connection.commit()
        except Exception:
            pass  # Column already exists

        db_cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS risk_levels (
                risk_level_id INT AUTO_INCREMENT PRIMARY KEY, 
                risk_name VARCHAR(255) NOT NULL, 
                description TEXT
            );
            '''
        )
        
        db_cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS compliance_risks (
                risk_id INT AUTO_INCREMENT PRIMARY KEY, 
                report INT NOT NULL, 
                risk_level INT NOT NULL, 
                rule INT NOT NULL, 
                description TEXT, 
                finding_text TEXT, 
                FOREIGN KEY (report) REFERENCES compliance_reports(report_id), 
                FOREIGN KEY (risk_level) REFERENCES risk_levels(risk_level_id), 
                FOREIGN KEY (rule) REFERENCES rules(rule_id)
            );
            '''
        )
        
        db_cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS snapshot_rules (
                rule INT NOT NULL, 
                snapshot INT NOT NULL, 
                PRIMARY KEY (rule, snapshot), 
                FOREIGN KEY (rule) REFERENCES rules(rule_id), 
                FOREIGN KEY (snapshot) REFERENCES rules_snapshots(snapshot_id)
            );
            '''
        )
        
        db_cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id INT AUTO_INCREMENT PRIMARY KEY, 
                entity_type VARCHAR(255), 
                entity_id INT, 
                action VARCHAR(255), 
                actor VARCHAR(255),
                timestamp_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                delta JSON
            );
            '''
        )
        
        
        createLegislationUpdateReviewsTable()

        db_cursor.execute("SHOW TABLES")

        for x in db_cursor:
            print(x)

    except Error as err:
        print(f"Error: '{err}'")

    finally:
        
        if connection.is_connected():
            db_cursor.close()
            connection.close()



def ensure_schema():
    connection = create_db_server_connection()
    try:
        db_cursor = connection.cursor()
        try:
            db_cursor.execute(
                "ALTER TABLE compliance_reports ADD COLUMN failed_urls TEXT"
            )
            connection.commit()
        except Exception:
            pass  # Column already exists
    except Error as err:
        print(f"Error: '{err}'")
    finally:
        if connection.is_connected():
            db_cursor.close()
            connection.close()



def executeQuery(sql, val):

    myresult = None

    try:

        connection = create_db_server_connection()
        db_cursor = connection.cursor()
        if val:
            db_cursor.execute(sql, val)
        else:
            db_cursor.execute(sql)
            
        myresult = db_cursor.fetchall()


        connection.commit()
    
    except Error as err:
        
        print(f"Error: '{err}'")
    
    finally:
        
        if connection.is_connected():
            db_cursor.close()
            connection.close()
    
    return myresult

#################################################################################
#                                                                               #
#                               PRIVILEGE TABLE                                 #
#                                                                               #
#################################################################################

def insertPrivilege(name):

    sql = "INSERT INTO privileges (name) VALUES (%s)"
    val = (name,)

    executeQuery(sql, val)

def selectPrivilegeByName(name):
    
    sql = "SELECT * FROM privileges WHERE name=%s"
    val = (name,)
    
    return executeQuery(sql, val)


def selectPrivileges():

    sql = "SELECT * FROM privileges"
    
    return executeQuery(sql, None)

#################################################################################
#                                                                               #
#                                  USER TABLE                                   #
#                                                                               #
#################################################################################

def selectUserByName(username):

    sql = "SELECT * FROM users WHERE user_name=%s"
    val = (username,)

    myresult = executeQuery(sql, val)

    return myresult

def selectUserForPage():

    sql = "SELECT user_id, user_name, full_name, privilege FROM users"

    return executeQuery(sql, None)

def insertUser(user_name, name, password, privilege):

    sql = "INSERT INTO users (user_name, full_name, password, privilege) VALUES (%s, %s, %s, %s)"
    val = (user_name, name,  password, privilege)

    executeQuery(sql, val)

#################################################################################
#                                                                               #
#                            DOCUMENT TYPE TABLE                                #
#                                                                               #
#################################################################################

def selectDocumentTypeByName(name):

    sql = "SELECT document_type_id FROM document_types WHERE type_name=%s"
    val = (name,)

    my_result = executeQuery(sql, val)

    return my_result

def insertDocumentType(name):

    sql = "INSERT INTO document_types (type_name) VALUES (%s)"
    val = (name,)

    executeQuery(sql, val)

def selectAllDocumentTypeNames():
    
    sql = "SELECT type_name FROM document_types"

    my_result = executeQuery(sql, ())

    return my_result


#################################################################################
#                                                                               #
#                               DOCUMENT TABLE                                  #
#                                                                               #
#################################################################################

def insertDocument(document_name, jurisdiction, year, description, document_type_id):
    
    sql = "INSERT INTO documents (document_name, jurisdiction, year, description, document_type) VALUES (%s, %s, %s, %s, %s)"
    val = (document_name, jurisdiction, year, description, document_type_id)

    executeQuery(sql, val)

def selectDocumentById(document_id):
    
    sql = "SELECT * FROM documents WHERE document_id=%s"
    val = (document_id,)

    my_result = executeQuery(sql, val)

    return my_result

def selectDocumentByName(name):

    sql = "SELECT * FROM documents WHERE document_name=%s"
    val = (name,)

    my_result = executeQuery(sql, val)

    return my_result

def selectAllDocuments():

    sql = "SELECT * FROM documents"

    my_result = executeQuery(sql, None)

    return my_result

#################################################################################
#                                                                               #
#                           DOCUMENT VERSION TABLE                              #
#                                                                               #
#################################################################################

def insertDocumentVersion(document_id, version_number, effective_from, effective_to, source_url, file_path, notes):

    sql = "INSERT INTO document_versions (document, version_number, effective_from, effective_to, source_url, file_path, notes) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    val = (document_id, version_number, effective_from, effective_to, source_url, file_path, notes)

    executeQuery(sql, val)

def selectDocumentVersionByDocumentIdAndVersion(doc_id, version):

    sql = "SELECT * FROM document_versions WHERE document=%s AND version_number=%s"
    val = (doc_id, version)

    return executeQuery(sql, val)

#################################################################################
#                                                                               #
#                            CONTRACT GROUP TABLE                               #
#                                                                               #
#################################################################################

def insertContractGroup(group_name, contact_details):

    sql = "INSERT INTO contract_groups (group_name, contact_details) VALUES (%s, %s)"
    val = (group_name, contact_details)

    executeQuery(sql, val)

def selectContractGroupByName(group_name):

    sql = "SELECT * FROM contract_groups WHERE group_name=%s"
    val = (group_name,)

    return executeQuery(sql, val)

def selectAllContractGroups():

    sql = "SELECT * FROM contract_groups"

    return executeQuery(sql, None)

#################################################################################
#                                                                               #
#                             CONTRACT TYPES TABLE                              #
#                                                                               #
#################################################################################

def selectAllContractTypes():

    sql = "SELECT * FROM contract_types"

    return executeQuery(sql, None)

def selectContractTypeByName(name):

    sql = "SELECT * FROM contract_types WHERE type_name=%s"
    val = (name,)

    return executeQuery(sql, val)

#################################################################################
#                                                                               #
#                               CONTRACTS TABLE                                 #
#                                                                               #
#################################################################################

def insertContract(contract_group, previous_version, contract_name, contract_type,
                   version_number, file_path, source_url, uploaded_by,
                   period_start, period_end):

    sql = (
        "INSERT INTO contracts "
        "(contract_group, previous_version, contract_name, contract_type, "
        "version_number, file_path, source_url, uploaded_by, period_start, period_end) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    val = (contract_group, previous_version, contract_name, contract_type,
           version_number, file_path, source_url, uploaded_by, period_start, period_end)

    executeQuery(sql, val)

def findPreviousVersion(contract_type, contract_group):

    sql = (
        "SELECT * FROM contracts "
        "WHERE contract_type=%s AND contract_group=%s "
        "ORDER BY contract_id DESC LIMIT 1"
    )
    val = (contract_type, contract_group)

    return executeQuery(sql, val)

def selectContractById(contract_id):

    sql = "SELECT * FROM contracts WHERE contract_id=%s"
    val = (contract_id,)

    return executeQuery(sql, val)

def selectAllContracts():

    sql = "SELECT * FROM contracts"

    return executeQuery(sql, None)

def selectContractForPage():

    sql = (
        "SELECT c.contract_id, c.contract_name, c.version_number, "
        "c.period_start, c.period_end, cg.group_name, ct.type_name "
        "FROM contracts c "
        "JOIN contract_groups cg ON c.contract_group = cg.group_id "
        "JOIN contract_types ct ON c.contract_type = ct.contract_type_id"
    )

    return executeQuery(sql, None)

#################################################################################
#                                                                               #
#                              CATEGORIES TABLE                                 #
#                                                                               #
#################################################################################

def insertCategory(code, name):

    sql = "INSERT INTO categories (category_code, category_name) VALUES (%s, %s)"
    val = (code, name)
    
    executeQuery(sql, val)

def selectCategoryByName(name):
    
    sql = "SELECT * FROM categories WHERE category_name=%s"
    val = (name,)

    return executeQuery(sql, val)

#################################################################################
#                                                                               #
#                                 RULES TABLE                                   #
#                                                                               #
#################################################################################

def insertRule(name, code, description, category, approved_by, metadata):

    sql = "INSERT INTO rules (rule_name, rule_code, description, category, approved_by, rule_metadata) VALUES (%s, %s, %s, %s, %s, %s)"
    val=(name, code, description, category, approved_by, metadata)

    executeQuery(sql, val)

def selectRuleByCode(code):

    sql = "SELECT * FROM rules WHERE rule_name=%s"
    val = (code,)

    return executeQuery(sql, val)

def selectRuleById(rule_id):

    sql = "SELECT * FROM rules WHERE rule_id=%s"
    val = (rule_id,)

    return executeQuery(sql, val)

#################################################################################
#                                                                               #
#                              RULE_BASIS TABLE                                 #
#                                                                               #
#################################################################################

def insertRuleBasis(rule, document_version, section_name):

    sql = "INSERT INTO rule_basis (rule, document_version, section_name) VALUES (%s, %s, %s)"
    val = (rule, document_version, section_name)

    executeQuery(sql, val)


#################################################################################
#                                                                               #
#                           RULES_SNAPSHOTS TABLE                               #
#                                                                               #
#################################################################################

def insertRulesSnapshot(label, approved_by, created_at):

    sql = "INSERT INTO rules_snapshots (label, approved_by, created_at) VALUES (%s, %s, %s)"
    val = (label, approved_by, created_at)
    
    executeQuery(sql, val)

def selectLastRulesSnapshot():
    
    sql = "SELECT snapshot_id FROM rules_snapshots ORDER BY approved_at DESC"

    return executeQuery(sql, None)

def selectRulesSnapshotByLabel(label):
    
    sql = "SELECT * FROM rules_snapshots WHERE label=%s"
    val = (label,)

    return executeQuery(sql, val)

#################################################################################
#                                                                               #
#                            SNAPSHOT_RULES TABLE                               #
#                                                                               #
#################################################################################

def insertSnapshotRule(rule, snapshot):

    sql = "INSERT INTO snapshot_rules (rule, snapshot) VALUES (%s, %s)"
    val = (rule, snapshot)

    executeQuery(sql, val)


#################################################################################
#                                                                               #
#                               RISK_LEVELS TABLE                               #
#                                                                               #
#################################################################################

def selectIdAndNameFromAllRiskLevels():

    sql = "SELECT risk_level_id, risk_name FROM risk_levels"
    return executeQuery(sql, None)

def insertRiskLevels(name, description):

    sql = "INSERT INTO risk_levels (risk_name, description) VALUES (%s, %s)"
    val = (name, description)

    executeQuery(sql, val)

def selectRiskLevelByID(risk_level_id):

    sql = "SELECT * FROM risk_levels WHERE risk_level_id=%s"
    val = (risk_level_id,)

    return executeQuery(sql, val)


#################################################################################
#                                                                               #
#                           COMPLIANCE_REPORTS TABLE                            #
#                                                                               #
#################################################################################

def insertComplianceReport(contract_id, snapshot_id, prior_report_id, compliance_status):

    sql = "INSERT INTO compliance_reports (contract, snapshot, prior_report, compliance_status) VALUES (%s, %s, %s, %s)"
    val = (contract_id, snapshot_id, prior_report_id, compliance_status)

    executeQuery(sql, val)

def selectComplianceReportByContractId(contract_id):

    sql = "SELECT * FROM compliance_reports WHERE contract=%s ORDER BY report_id DESC LIMIT 1"
    val = (contract_id,)

    return executeQuery(sql, val)

def selectReportForPage():

    sql = (
        "SELECT r.report_id, r.compliance_status, r.created_at, "
        "c.contract_name, c.version_number "
        "FROM compliance_reports r "
        "JOIN contracts c ON r.contract = c.contract_id"
    )

    return executeQuery(sql, None)

#################################################################################
#                                                                               #
#                            COMPLIANCE_RISKS TABLE                             #
#                                                                               #
#################################################################################

def insertComplianceRisk(report_id, risk_level_id, rule_id, finding_text, description):

    sql = "INSERT INTO compliance_risks (report, risk_level, rule, finding_text, description) VALUES (%s, %s, %s, %s, %s)"
    val = (report_id, risk_level_id, rule_id, finding_text, description)

    executeQuery(sql, val)

def selectComplianceRiskFromReportId(report_id):

    sql = "SELECT * FROM compliance_risks WHERE report=%s"
    val = (report_id,)

    return executeQuery(sql, val)

#################################################################################
#                                                                               #
#                                AUDIT_LOGS TABLE                               #
#                                                                               #
#################################################################################

def insertAuditLog(entity_type, entity_id, action, actor, delta):

    sql = "INSERT INTO audit_logs (entity_type, entity_id, action, actor, delta) VALUES (%s, %s, %s, %s, %s)"
    val = (entity_type, entity_id, action, actor, delta)

    executeQuery(sql, val)

#################################################################################
#                                                                               #
#                      LEGISLATION_UPDATE_REVIEWS TABLE                         #
#                                                                               #
#################################################################################

def createLegislationUpdateReviewsTable():

    sql = '''
    CREATE TABLE IF NOT EXISTS legislation_update_reviews (
        review_id INT AUTO_INCREMENT PRIMARY KEY,
        document_version_id INT NOT NULL,
        proposed_changes JSON,
        status VARCHAR(50) DEFAULT 'PENDING',
        reviewed_by VARCHAR(255),
        reviewed_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_version_id)
            REFERENCES document_versions(version_id)
    );
    '''

    executeQuery(sql, None)

'''
try:

    connection = create_db_server_connection()
    db_cursor = connection.cursor()
    
    connection.commit()
    
except Error as err:
        
    print(f"Error: '{err}'")
    
finally:
        
    if connection.is_connected():
        db_cursor.close()
        connection.close()
'''