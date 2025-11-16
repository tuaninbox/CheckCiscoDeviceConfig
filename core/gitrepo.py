from git import Repo
import datetime
from pathlib import Path

backup_dir = Path("./backups")
print(backup_dir)
def git_commit_and_push():
    # Initialize repo if needed
    if not (backup_dir / ".git").exists():
        repo = Repo.init(backup_dir)
        repo.config_writer().set_value("user", "name", "BackupBot").release()
        repo.config_writer().set_value("user", "email", "backup@example.com").release()
        # Add remote (only once)
        repo.create_remote("origin", "git@github.com:YOUR_USERNAME/YOUR_REPO.git")
        repo.git.branch("-M", "main")
    else:
        repo = Repo(backup_dir)

    # Stage all changes
    repo.git.add(A=True)

    # Commit with timestamp
    msg = f"Backup on {datetime.datetime.now().isoformat()}"
    try:
        repo.index.commit(msg)
        print("Committed:", msg)
    except Exception as e:
        print("Nothing to commit:", e)

    # Push to GitHub
    try:
        repo.git.push("origin", "main")
        print("Pushed to GitHub")
    except Exception as e:
        print("Push failed:", e)

# Usage after backup
# git_commit_and_push()
