import os

for root, dirs, files in os.walk("."):
    for dir_name in dirs:
        if dir_name == "__pycache__":
            full_path = os.path.join(root, dir_name)
            print(f"Deleting: {full_path}")
            os.system(f"sudo rm -rf \"{full_path}\"")  # برای لینوکس/مک
            # os.system(f"rmdir /s /q \"{full_path}\"")  # برای ویندوز