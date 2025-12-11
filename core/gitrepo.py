from git import Repo
import datetime
from pathlib import Path
from core.logging_manager import setup_loggers
from config.config_loader import load_backup_config

# Initialize loggers for this module
success_logger, fail_logger = setup_loggers(logger_name="gitrepo")

backup_dir = load_backup_config()

# try:
#     # Read backup_dir from gitrepo.ini
#     config = configparser.ConfigParser()
#     config.read(config_file)
#     backup_dir = Path(config["gitrepo"]["backup_dir"]).expanduser()
# except KeyError:
#     fail_logger.error(f"Missing 'backup_dir' in config.ini under [gitrepo] section or {config_file} does not exist")
#     raise

def git_commit_and_push(push=True):
    # Initialize repo if needed
    if not (backup_dir / ".git").exists():
        repo = Repo.init(backup_dir)
        repo.config_writer().set_value("user", "name", "username").release()
        repo.config_writer().set_value("user", "email", "email@domain.com").release()
        # Add remote (only once)
        # repo.create_remote("origin", "git@github.com:YOUR_USERNAME/YOUR_REPO.git")
        repo.git.branch("-M", "main")
        success_logger.info("Initialized new Git repository in backup directory")
    else:
        repo = Repo(backup_dir)

    # Detect changes
    changed_files = [item.a_path for item in repo.index.diff(None)]  # modified files
    untracked_files = repo.untracked_files                           # new files
    deleted_files = [item.a_path for item in repo.index.diff(None) if item.change_type == 'D']

    files_to_commit = changed_files + untracked_files + deleted_files

    if not files_to_commit:
        print("No changes detected, nothing to commit.")
        success_logger.warning("No changes detected, nothing to commit")
        return

    # Stage only changed files
    repo.index.add(files_to_commit)

    # Commit with timestamp
    msg = f"Backup at {datetime.datetime.now().isoformat()}"
    try:
        repo.index.commit(msg)
        print("Committed:", msg)
        print("Files committed:", files_to_commit)
        success_logger.info(f"Committed backup: {msg} | Files: {files_to_commit}")
    except Exception as e:
        print("Commit failed:", e)
        fail_logger.error(f"Commit failed: {e}")

    if push:
        # Push to GitHub (optional)
        try:
            repo.git.push("origin", "main")
            # print("Pushed to GitHub")
            success_logger.info(f"Pushed backup in {backup_dir} to GitHub successfully")
        except Exception as e:
            # print("Push failed:", e)
            fail_logger.error(f"Push failed: {e}")


if __name__ == "__main__":
    git_commit_and_push()
    # pass
