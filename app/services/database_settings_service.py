import os
import shutil
import sqlite3


class DatabaseSettingsService:
    def database_exists(self, db_path: str) -> bool:
        return bool(db_path) and os.path.exists(db_path)

    def fetch_download_rows(self, db_path: str):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, media_url, file_path, file_size, user_id, post_id, downloaded_at "
            "FROM downloads ORDER BY user_id, post_id, id"
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def delete_users(self, db_path: str, user_ids):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        for uid in user_ids:
            if uid is None:
                cursor.execute("DELETE FROM downloads WHERE user_id IS NULL")
            else:
                cursor.execute("DELETE FROM downloads WHERE user_id = ?", (uid,))
        conn.commit()
        conn.close()

    def delete_all_downloads(self, db_path: str):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM downloads")
        conn.commit()

        try:
            cursor.execute("VACUUM")
        except Exception:
            pass

        conn.close()

    def export_database(self, db_path: str, export_path: str):
        shutil.copy(db_path, export_path)

    def get_file_type(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"]:
            return "Image"
        if ext in [".mp4", ".mkv", ".webm", ".mov", ".avi", ".flv", ".wmv", ".m4v"]:
            return "Video"
        if ext in [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"]:
            return "Document"
        if ext in [".zip", ".rar", ".7z", ".tar", ".gz"]:
            return "Compressed"
        return "Other"

    def format_size(self, size) -> str:
        if size is None:
            return "0 B"
        if size < 1024:
            return f"{size} B"
        if size < 1024**2:
            return f"{size / 1024:.2f} KB"
        if size < 1024**3:
            return f"{size / 1024**2:.2f} MB"
        return f"{size / 1024**3:.2f} GB"

    def build_summary(self, rows):
        users = {rec[4] for rec in rows}
        total_size = sum(rec[3] or 0 for rec in rows)
        return {
            "users": len(users),
            "files": len(rows),
            "size_str": self.format_size(total_size),
        }

    def group_rows_for_tree(self, rows):
        usuarios = {}
        for rec in rows:
            rec_id, media_url, file_path, file_size, user_id, post_id, downloaded_at = rec
            usuarios.setdefault(user_id, []).append(rec)
        return usuarios

    def build_tree_payload(self, rows):
        usuarios = self.group_rows_for_tree(rows)
        payload = []

        for user, registros in usuarios.items():
            user_entry = {
                "user": user,
                "posts": {},
                "no_post": []
            }

            for rec in registros:
                rec_id, media_url, file_path, file_size, user_id, post_id, downloaded_at = rec
                item = {
                    "id": rec_id,
                    "file_name": os.path.basename(file_path) if file_path else "",
                    "file_type": self.get_file_type(file_path or ""),
                    "size_str": self.format_size(file_size),
                    "downloaded_at": downloaded_at,
                }

                if post_id:
                    user_entry["posts"].setdefault(post_id, []).append(item)
                else:
                    user_entry["no_post"].append(item)

            payload.append(user_entry)

        return payload