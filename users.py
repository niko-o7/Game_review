from werkzeug.security import check_password_hash, generate_password_hash
import db

def create_user(username, password):
    password_hash = generate_password_hash(password)
    sql = "INSERT INTO users (username, password_hash) VALUES (?,?)"
    db.execute(sql, [username, password_hash])

def check_login(username, password):
    sql = "Select id, password_hash FROM users WHERE username = ?"
    result = db.query(sql, [username])
    if not result:
        return None

    user_id = result[0]["id"]
    password_hash = result[0]["password_hash"]
    if check_password_hash(password_hash, password):
        return user_id
    else:
        return None
    
def get_user(user_id):
    sql = """SELECT id, username, image IS NOT NULL has_image
            FROM users
            WHERE id = ?"""
    user = db.query(sql, [user_id])
    return user[0] if user else None

def get_image(user_id):
    sql = "SELECT image FROM users WHERE id = ?"
    image = db.query(sql, [user_id])
    return image[0]["image"]

def update_image(user_id, image):
    sql = "UPDATE users SET image = ? WHERE id = ?"
    db.execute(sql, [image, user_id])