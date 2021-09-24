from abc import abstractclassmethod
from pathlib import Path

from zipfile import ZipFile
import json
import os


def main():
    plugin_name = "bw_tools"
    version = "2.0.1"
    min_designer_version = "11.2.0"
    author = "Ben Wilson"
    email = "ben.q.wilson@gmail.com"
    platform = "any"
    metadata_format_version = "1"

    plugin_name_version = f"{plugin_name}_{version.replace('.', '_')}"

    ignore_folders = [
        "__pycache__",
        "bw_generate_slider_outputs",
        "bw_print_node_info",
    ]
    ignore_extention = [".psd"]

    with ZipFile(f"{plugin_name_version}.sdplugin", "w") as zip_obj:
        for root, folders, files in os.walk(Path.cwd().joinpath(plugin_name)):
            abs_path = Path(root)

            if abs_path.name in ignore_folders:
                continue

            rel_path = abs_path.relative_to(Path.cwd())
            zip_path = (
                Path(plugin_name_version) / plugin_name_version / rel_path
            )

            for file_name in files:
                if os.path.splitext(file_name)[1] in ignore_extention:
                    continue
                zip_obj.write(abs_path / file_name, zip_path / file_name)

        main_init = Path.cwd() / "__init__.py"
        zip_obj.write(
            main_init,
            Path(f"/{plugin_name_version}/{plugin_name_version}/__init__.py"),
        )

        license_path = Path.cwd() / "LICENSE"
        zip_obj.write(
            license_path,
            Path(f"/{plugin_name_version}/{plugin_name_version}/LICENSE"),
        )

        readme = Path.cwd() / "README.md"
        zip_obj.write(
            readme,
            Path(f"/{plugin_name_version}/{plugin_name_version}/README.md"),
        )

        plugin_info = {
            "metadata_format_version": metadata_format_version,
            "name": plugin_name_version,
            "version": version,
            "author": author,
            "email": email,
            "min_designer_version": min_designer_version,
            "platform": platform,
        }
        plugin_info_path = Path.cwd() / "pluginInfo.json"
        with open(plugin_info_path, "w") as settings_file:
            json.dump(plugin_info, settings_file, indent=4)

        zip_obj.write(
            plugin_info_path, Path(f"/{plugin_name_version}/pluginInfo.json")
        )
        plugin_info_path.unlink()


if __name__ == "__main__":
    main()
