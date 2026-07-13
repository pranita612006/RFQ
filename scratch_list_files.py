import os

def find_files():
    patterns = ['.bas', '.cls', '.frm', '.accdb', '.mp4', '.avi', '.wmv', '.zip', '.txt', '.pdf']
    results = []
    for root, dirs, files in os.walk(r'd:\N-RFQ'):
        # Skip venv and .git
        if 'venv' in root or '.git' in root:
            continue
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in patterns or 'vba' in file.lower() or 'access' in file.lower():
                full_path = os.path.join(root, file)
                results.append((full_path, os.path.getsize(full_path)))
    
    print(f"Found {len(results)} files:")
    for path, size in results:
        print(f"{path} ({size} bytes)")

if __name__ == '__main__':
    find_files()
