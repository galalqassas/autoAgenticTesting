import importlib.metadata



def check_deps(packages):
    print(f"Checking packages: {packages}")

    try:
        # Get all installed packages, normalized to lowercase and hyphens
        installed_dists = {
            d.metadata["Name"].lower().replace("_", "-")
            for d in importlib.metadata.distributions()
        }
        print(f"Found {len(installed_dists)} installed packages.")

        missing_packages = []
        for package in packages:
            pkg_name = (
                package.split("==")[0]
                .split(">=")[0]
                .split("<=")[0]
                .split(">")[0]
                .split("<")[0]
                .strip()
                .lower()
                .replace("_", "-")
            )
            print(f"Checking {package} -> {pkg_name}")

            if pkg_name not in installed_dists:
                print(f"  Missing: {pkg_name}")
                missing_packages.append(package)
            else:
                print(f"  Found: {pkg_name}")

        if not missing_packages:
            print("All dependencies installed.")
        else:
            print(f"Missing: {missing_packages}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    check_deps(["pytest", "fastapi", "non_existent_package"])
