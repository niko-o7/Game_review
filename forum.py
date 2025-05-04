import sqlite3
import db

def get_threads(page, page_size):
    sql= """SELECT t.*, users.username
            FROM threads t
            JOIN users ON t.user_id = users.id
            GROUP BY t.id
            ORDER BY t.id DESC
            LIMIT ? OFFSET ?
            """
    limit = page_size
    offset = page_size * (page - 1)
    return db.query(sql, [limit, offset])

def thread_count():
    sql = "SELECT COUNT(*) FROM threads"
    return db.query(sql)[0][0]

def add_thread(title, genres, grade, review, user_id):
    sql = "INSERT INTO threads (title, genres, grade, review, user_id) VALUES (?,?,?,?,?)"
    db.execute(sql, [title, genres, grade, review, user_id])
    thread_id = db.last_insert_id()
    return thread_id

def get_thread(thread_id):
    
    sql = """
        SELECT 
            t.id as thread_id, 
            t.title, 
            t.genres, 
            t.grade, 
            t.review, 
            t.user_id,
            u.username as author_username,
            u.id as author_id
        FROM threads t
        JOIN users u ON t.user_id = u.id
        WHERE t.id = ?
    """
    return db.query(sql, [thread_id])[0]

def update_thread(thread_id, review):
    sql = "UPDATE threads SET review = ? WHERE id = ?"
    db.execute(sql, [review, thread_id])

def remove_thread(thread_id):
    sql = "DELETE FROM threads WHERE id = ?"
    db.execute(sql, [thread_id])

def search(query, page=1, per_page=15):
    offset = (page - 1) * per_page

    sql= """SELECT t.id as thread_id, t.title, u.username, COUNT(*) OVER() as total_results
            FROM threads t
            JOIN users u ON t.user_id = u.id
            WHERE t.title LIKE ? OR t.genres LIKE ? OR t.review LIKE ?
            ORDER BY t.id DESC
            LIMIT ? OFFSET ?
        """
    search = f"%{query}%"
    results = db.query(sql, [search, search, search, per_page, offset])
    if not results:
        return []
    total_results = results[0]["total_results"]
    return results, total_results


def add_comment(thread_id, user_id, content):

    sql = "INSERT INTO comments (thread_id, user_id, content) VALUES (?, ?, ?)"
    db.execute(sql, (thread_id, user_id, content))

def get_comments(thread_id):
    try:
        sql = """
        SELECT c.*, u.username
        FROM comments c
        JOIN users u on c.user_id = u.id
        WHERE c.thread_id = ?
        ORDER BY c.created_at DESC
        """
        return db.query(sql, [thread_id])
    except:
        return

def delete_comment(comment_id, user_id):
    sql = "DELETE FROM comments WHERE id = ? AND user_id = ?"
    db.execute(sql, (comment_id, user_id))



# Posts by, for profile

def user_reviews(user_id):
    sql = """
    SELECT id as thread_id, title, genres, grade, review
    FROM threads
    WHERE user_id = ?
    ORDER BY thread_id
    """
    return db.query(sql, [user_id])

def total_reviews(user_id):
    sql = "SELECT COUNT(*) as count FROM threads WHERE user_id = ?"
    amount = db.query(sql, [user_id])
    return amount[0]["count"] if amount else 0