import subprocess


def run_tests():
    result = subprocess.run(
        ["python3", "-m", "unittest", "discover"], capture_output=True, text=True)

    print(result.stdout)
    print(result.stderr)

    if result.returncode == 0:
        print("Tests passed")
    else:
        print("Tests failed!")


if __name__ == "__main__":
    run_tests()
